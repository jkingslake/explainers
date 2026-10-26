#!/usr/bin/env python3
"""Contact sheets of a rendered video, for checking layout without watching it.

    python tools/frames.py videos/<slug>/out/<slug>-draft.mp4 [--every 3] [--grid 4x3]

Writes build/<slug>/frames/sheet-01.png ... ; each tile is stamped with its timestamp.
Look at every sheet: overlapping text, things running off the frame, unreadable
labels, equations colliding with the towel, empty stretches, stale objects left on
screen.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--every", type=float, default=3.0, help="seconds between frames")
    ap.add_argument("--grid", default="4x3", help="tiles per sheet, COLSxROWS")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    args = ap.parse_args()

    slug = args.video.stem.removesuffix("-draft")
    out = ROOT / "build" / slug / "frames"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("sheet-*.png"):
        old.unlink()

    stamp = "drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6"
    vf = f"fps=1/{args.every},scale=480:-2,{stamp},tile={args.grid}:padding=4:color=gray"
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(args.start), "-copyts"]  # stamps show real video time
    if args.end:
        cmd += ["-to", str(args.end)]
    cmd += ["-i", str(args.video), "-vf", vf, "-fps_mode", "vfr", str(out / "sheet-%02d.png")]
    subprocess.run(cmd, check=True)
    sheets = sorted(out.glob("sheet-*.png"))
    for s in sheets:
        print(s)


if __name__ == "__main__":
    main()
