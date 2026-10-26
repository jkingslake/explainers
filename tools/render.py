#!/usr/bin/env python3
"""Render every scene of a video in parallel and stitch them into one MP4 + SRT.

    python tools/render.py videos/<slug>               # draft (480p15, fast)
    python tools/render.py videos/<slug> --final       # 1080p (explainer.toml)
    python tools/render.py videos/<slug> --only Intro Model   # just these scenes
    python tools/render.py videos/<slug> --silent      # no TTS, estimated timings

Scene order comes from `SCENES = [...]` in videos/<slug>/scenes.py.
Output: videos/<slug>/out/<slug>[-draft].mp4 and .srt
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from explainer_kit.config import settings  # noqa: E402

QUALITY_DIR = {"l": "480p15", "m": "720p30", "h": "1080p60", "p": "1440p60", "k": "2160p60"}


def scene_order(scenes_py: Path) -> list[str]:
    tree = ast.parse(scenes_py.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "SCENES" for t in node.targets):
            return [e.id if isinstance(e, ast.Name) else e.value for e in node.value.elts]
    raise SystemExit(f"{scenes_py} needs a SCENES = [SceneA, SceneB, ...] list")


def chapter_titles(scenes_py: Path) -> dict[str, str]:
    """First docstring line of each scene class, used as its YouTube chapter title."""
    tree = ast.parse(scenes_py.read_text())
    return {
        node.name: (ast.get_docstring(node) or node.name).splitlines()[0]
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def ffprobe_duration(path: Path, stream: str | None = None) -> float:
    args = ["ffprobe", "-v", "error"]
    if stream:
        args += ["-select_streams", stream, "-show_entries", "stream=duration"]
    else:
        args += ["-show_entries", "format=duration"]
    out = subprocess.run([*args, "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return float(out.splitlines()[0]) if out and out != "N/A" else 0.0


def render_scene(name: str, scenes_py: Path, media: Path, quality: str, fps: int | None, env: dict) -> Path:
    cmd = [str(ROOT / ".venv/bin/manim"), "render", f"-q{quality}", "--media_dir", str(media / name), "--progress_bar", "none"]
    if fps:
        cmd += ["--frame_rate", str(fps)]
    cmd += [str(scenes_py), name]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=scenes_py.parent, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        log = media / f"{name}.log"
        log.write_text(proc.stdout + proc.stderr)
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-25:])
        raise RuntimeError(f"scene {name} failed (full log: {log})\n{tail}")
    found = sorted((media / name / "videos").rglob(f"{name}.mp4"), key=lambda p: p.stat().st_mtime)
    if not found:
        raise RuntimeError(f"scene {name}: manim produced no video")
    print(f"  rendered {name:<28} {ffprobe_duration(found[-1]):6.1f}s video in {time.time() - t0:5.0f}s", flush=True)
    return found[-1]


def normalise(part: Path, out: Path) -> float:
    """Give every part an AAC stereo track exactly as long as its video so concat stays in sync."""
    dur = ffprobe_duration(part, "v:0") or ffprobe_duration(part)
    has_audio = bool(
        subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(part)],
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(part)]
    if has_audio:
        cmd += ["-map", "0:v:0", "-map", "0:a:0", "-af", "apad"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{dur:.3f}", str(out)]
    subprocess.run(cmd, check=True)
    return dur


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--final", action="store_true", help="full quality render")
    ap.add_argument("--quality", choices=list(QUALITY_DIR), help="override quality")
    ap.add_argument("--only", nargs="+", metavar="SCENE", help="render only these scenes (no stitching)")
    ap.add_argument("--silent", action="store_true", help="skip TTS; timings estimated from word counts")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()

    vdir = args.video_dir.resolve()
    scenes_py = vdir / "scenes.py"
    slug = vdir.name
    vid = settings()["video"]
    quality = args.quality or (vid["final_quality"] if args.final else vid["draft_quality"])
    fps = int(vid.get("fps", 30)) if args.final else None
    names = args.only or scene_order(scenes_py)
    media = ROOT / "build" / slug / quality
    media.mkdir(parents=True, exist_ok=True)

    env = {**os.environ, "PYTHONPATH": f"{ROOT}{os.pathsep}{os.environ.get('PYTHONPATH', '')}", "PYTHONWARNINGS": "ignore"}
    if args.silent:
        env["EXPLAINER_TTS"] = "silent"

    print(f"Rendering {len(names)} scene(s) of {slug} at -q{quality} with {args.jobs} job(s)", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(args.jobs) as pool:
        futures = {n: pool.submit(render_scene, n, scenes_py, media, quality, fps, env) for n in names}
        parts, failed = {}, []
        for n, fut in futures.items():
            try:
                parts[n] = fut.result()
            except RuntimeError as e:
                failed.append(n)
                print(f"\n!! {e}\n", file=sys.stderr, flush=True)
    if failed:
        raise SystemExit(f"{len(failed)} scene(s) failed: {', '.join(failed)}")
    if args.only:
        for n in names:
            print(parts[n])
        return

    out_dir = vdir / "out"
    out_dir.mkdir(exist_ok=True)
    stem = slug if args.final else f"{slug}-draft"
    concat_list = media / "concat.txt"
    cues, offset, lines, chapters = [], 0.0, [], []
    titles = chapter_titles(scenes_py)
    for i, n in enumerate(names):
        norm = media / f"{i:02d}-{n}.norm.mp4"
        dur = normalise(parts[n], norm)
        if not chapters or titles[n] != chapters[-1][1]:  # consecutive scenes may share a chapter
            chapters.append((offset, titles[n]))
        lines.append(f"file '{norm}'")
        cue_file = parts[n].with_suffix(".cues.json")
        if cue_file.exists():
            for c in json.loads(cue_file.read_text()):
                cues.append((offset + c["start"], offset + c["end"], c["text"]))
        offset += dur
    concat_list.write_text("\n".join(lines) + "\n")
    final = out_dir / f"{stem}.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", "-movflags", "+faststart", str(final)],
        check=True,
    )
    with open(out_dir / f"{stem}.srt", "w") as f:
        for i, (a, b, text) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n\n")

    with open(out_dir / f"{stem}.chapters.txt", "w") as f:
        for t, title in chapters:
            f.write(f"{int(t // 60)}:{int(t % 60):02d} {title}\n")

    size = final.stat().st_size / 1e6
    print(f"\nDone in {time.time() - t0:.0f}s: {final} ({offset / 60:.1f} min, {size:.0f} MB)")


if __name__ == "__main__":
    main()
