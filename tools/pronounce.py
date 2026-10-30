#!/usr/bin/env python3
"""Find narration words the voice may mispronounce, make a listening clip, and record fixes.

    python tools/pronounce.py check videos/<slug> [--audio]   # list unsettled words (+ a clip of each)
    python tools/pronounce.py say "Nivlisen" "Niv lee sen"     # preview a respelling, in context
    python tools/pronounce.py set "Nivlisen" "Niv lee sen"     # always say it this way
    python tools/pronounce.py ok "Greenland" "zeta"            # confirmed fine as written

Candidates are words missing from the English word list (names, places, jargon), acronyms,
Greek letters and spoken symbols such as "h L" or "phi b". Words already in [pronunciations]
(respellings) or [pronunciations_ok] in explainer.toml are settled and not listed again, so the
dictionary grows channel-wide. Subtitles keep the written form; only the voice uses respellings.

`check --audio` writes build/<slug>/pronounce/check.mp3: for each numbered item, the voice says
the number, the word, then the phrase it appears in.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from explainer_kit.config import settings  # noqa: E402

TOML = ROOT / "explainer.toml"
WORDLISTS = [Path("/usr/share/dict/american-english"), Path("/usr/share/dict/british-english")]
PREFIXES = ("supra", "super", "sub", "un", "non", "re", "pre", "over", "under", "inter", "intra", "multi", "semi")
GREEK = {
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu",
    "nu", "xi", "omicron", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
}
SYMBOL_WORDS = GREEK | {"nought", "prime", "tilde", "hat", "bar", "dot"}
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’-]*")


# ------------------------------------------------------------------ narration
def narration(vdir: Path) -> list[str]:
    """The spoken sentences: from scenes.py when it exists (what is actually rendered), else script.md."""
    scenes = vdir / "scenes.py"
    if scenes.exists():
        out = []
        for node in ast.walk(ast.parse(scenes.read_text())):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if name in ("narrate", "say") and node.args and isinstance(node.args[0], ast.Constant):
                out.append(str(node.args[0].value))
            for kw in node.keywords:
                if kw.arg == "narration" and isinstance(kw.value, ast.Constant):
                    out.append(str(kw.value.value))
        if out:
            return out
    script = vdir / "script.md"
    return [m.group(1).strip() for m in re.finditer(r"\*\*Narration:\*\*\s*(.+)", script.read_text())]


# ------------------------------------------------------------------ candidates
def dictionary() -> set[str]:
    lists = [p for p in WORDLISTS if p.exists()]
    if not lists:
        raise SystemExit("No English word list: run `bash scripts/setup.sh` (installs wamerican and wbritish)")
    return {w.strip().lower() for p in lists for w in p.read_text(errors="ignore").splitlines()}


def known(word: str, words: set[str]) -> bool:
    w = word.lower().replace("’", "'").strip("'")
    if "-" in w:
        return all(known(p, words) for p in w.split("-") if p)
    w = re.sub(r"'s$", "", w)
    forms = {w}
    for suf, rep in (("s", ""), ("es", ""), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"), ("ly", ""),
                     ("ies", "y"), ("ied", "y"), ("er", ""), ("est", ""), ("bly", "ble"), ("ises", "ize"),
                     ("ise", "ize"), ("ised", "ize"), ("ising", "ize")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            forms.add(w[: -len(suf)] + rep)
    if any(f in words for f in forms):
        return True
    # compounds of two ordinary words (meltwater, drawdown) and common prefixes (subcritical)
    for f in forms:
        if any(f[:i] in words and f[i:] in words for i in range(3, len(f) - 2)):
            return True
        for pre in PREFIXES:
            if f.startswith(pre) and len(f) - len(pre) > 3 and known(f[len(pre):], words):
                return True
    return False


def settled() -> tuple[set[str], set[str]]:
    cfg = settings()
    respelt = {k.lower() for k in cfg.get("pronunciations", {})}
    ok = {w.lower() for w in cfg.get("pronunciations_ok", {}).get("words", [])}
    return respelt, ok


def is_symbol(t: str) -> bool:
    return (len(t) == 1 and t not in ("a", "A", "I")) or t.lower() in SYMBOL_WORDS


def candidates(sentences: list[str]) -> list[dict]:
    words = dictionary()
    respelt, ok = settled()
    found: dict[str, dict] = {}

    def add(phrase: str, kind: str, sentence: str, start: int, end: int):
        key = phrase.lower()
        if key in respelt or key in ok:
            return
        if key not in found:
            # a short stretch of the sentence around the phrase, for context in the clip
            spans = [m.span() for m in re.finditer(r"\S+", sentence)]
            first = max([k for k, (a, _) in enumerate(spans) if a <= start] or [0])
            last = min([k for k, (_, e) in enumerate(spans) if e >= end] or [len(spans) - 1])
            lo, hi = spans[max(first - 5, 0)][0], spans[min(last + 5, len(spans) - 1)][1]
            snippet = sentence[lo:hi].strip(" ,;:")
            found[key] = {"phrase": phrase, "kind": kind, "count": 0, "context": snippet}
        found[key]["count"] += 1

    for s in sentences:
        toks = list(WORD_RE.finditer(s))
        i = 0
        while i < len(toks):
            t = toks[i].group()
            if is_symbol(t):
                j = i
                while j + 1 < len(toks):
                    nxt = toks[j + 1].group()
                    if is_symbol(nxt):
                        j += 1
                    elif nxt in ("by", "over") and j + 2 < len(toks) and is_symbol(toks[j + 2].group()):
                        j += 2
                    else:
                        break
                phrase = s[toks[i].start(): toks[j].end()]
                # a lone letter ("lake B", "discharge Q") is read reliably; runs and Greek letters may not be
                if j > i or t.lower() in SYMBOL_WORDS:
                    add(phrase, "symbol", s, toks[i].start(), toks[j].end())
                i = j + 1
                continue
            if len(t) >= 2 and t.isupper():
                add(t, "acronym", s, toks[i].start(), toks[i].end())
            elif not known(t, words):
                add(t, "name" if t[0].isupper() else "word", s, toks[i].start(), toks[i].end())
            i += 1
    order = {"name": 0, "symbol": 1, "acronym": 2, "word": 3}
    out = sorted(found.values(), key=lambda c: (order[c["kind"]], c["phrase"].lower()))
    return out


# ------------------------------------------------------------------ audio
def clip_for(text: str) -> Path:
    from explainer_kit.tts import speak

    clip = speak(text)
    if clip.path is None:
        raise SystemExit("The 'silent' voice engine can't make listening clips; choose a real engine.")
    return clip.path


def join_clips(paths: list[Path], out: Path, gap: float = 0.7) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs, filt = [], []
    for i, p in enumerate(paths):
        inputs += ["-i", str(p)]
        filt.append(f"[{i}:a]aresample=24000,aformat=channel_layouts=mono,apad=pad_dur={gap}[a{i}]")
    concat = "".join(f"[a{i}]" for i in range(len(paths))) + f"concat=n={len(paths)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filt + [concat]),
                    "-map", "[out]", "-q:a", "4", str(out)], check=True)
    return out


# ------------------------------------------------------------------ explainer.toml edits
def _toml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def set_respelling(word: str, spoken: str) -> None:
    text = TOML.read_text()
    line = f"{_toml_str(word)} = {_toml_str(spoken)}"
    pat = re.compile(rf"^{re.escape(_toml_str(word))}\s*=.*$", re.M)
    if pat.search(text):
        text = pat.sub(line, text)
    elif re.search(r"^\[pronunciations\]\s*$", text, re.M):
        text = re.sub(r"^(\[pronunciations\][^\n]*\n(?:#[^\n]*\n)*)", lambda m: m.group(1) + line + "\n", text,
                      count=1, flags=re.M)
    else:
        text = text.rstrip() + ("\n\n[pronunciations]\n# written = how the voice should say it "
                                "(subtitles keep the written form)\n" + line + "\n")
    TOML.write_text(text)
    _drop_from_ok([word])


def _ok_words(text: str) -> list[str]:
    m = re.search(r"^\[pronunciations_ok\][^\[]*?^words\s*=\s*(\[.*?\])", text, re.M | re.S)
    return json.loads(m.group(1)) if m else []


def _write_ok(text: str, ok: list[str]) -> str:
    arr = "[" + ", ".join(_toml_str(w) for w in ok) + "]"
    if re.search(r"^\[pronunciations_ok\]", text, re.M):
        return re.sub(r"(^\[pronunciations_ok\][^\[]*?^words\s*=\s*)\[.*?\]", lambda m: m.group(1) + arr, text,
                      count=1, flags=re.M | re.S)
    return text.rstrip() + ("\n\n[pronunciations_ok]\n# checked by ear and fine as written; not asked about again\n"
                            f"words = {arr}\n")


def mark_ok(words_: list[str]) -> None:
    text = TOML.read_text()
    ok = _ok_words(text)
    for w in words_:
        if w.lower() not in {o.lower() for o in ok}:
            ok.append(w)
    TOML.write_text(_write_ok(text, ok))


def _drop_from_ok(words_: list[str]) -> None:
    text = TOML.read_text()
    ok = _ok_words(text)
    keep = [o for o in ok if o.lower() not in {w.lower() for w in words_}]
    if keep != ok:
        TOML.write_text(_write_ok(text, keep))


# ------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("video_dir", type=Path)
    c.add_argument("--audio", action="store_true", help="write a numbered listening clip")
    c.add_argument("--json", action="store_true")
    s = sub.add_parser("say")
    s.add_argument("word")
    s.add_argument("spoken", nargs="?", help="respelling to try (default: as written)")
    s.add_argument("--context", default="", help="sentence to say it in")
    st = sub.add_parser("set")
    st.add_argument("word")
    st.add_argument("spoken")
    o = sub.add_parser("ok")
    o.add_argument("words", nargs="+")
    args = ap.parse_args()

    if args.cmd == "check":
        vdir = args.video_dir.resolve()
        cands = candidates(narration(vdir))
        if args.json:
            print(json.dumps(cands, indent=2, ensure_ascii=False))
        else:
            if not cands:
                print("No unsettled words: every unusual word is in [pronunciations] or [pronunciations_ok].")
            for i, cnd in enumerate(cands, 1):
                print(f"{i:>2}. {cnd['phrase']:<22} {cnd['kind']:<8} x{cnd['count']:<3} \"{cnd['context']}\"")
        if args.audio and cands:
            clips = [clip_for(f"{i}. {cnd['phrase']}. {cnd['context']}.") for i, cnd in enumerate(cands, 1)]
            out = join_clips(clips, ROOT / "build" / vdir.name / "pronounce" / "check.mp3")
            print(f"\nListening clip: {out}")
    elif args.cmd == "say":
        spoken = args.spoken or args.word
        text = f"{spoken}. {args.context.replace(args.word, spoken)}" if args.context else f"{spoken}."
        safe = re.sub(r"[^A-Za-z0-9]+", "-", args.word).strip("-").lower()
        out = join_clips([clip_for(text)], ROOT / "build" / "pronounce" / f"say-{safe}.mp3")
        print(out)
    elif args.cmd == "set":
        set_respelling(args.word, args.spoken)
        print(f'"{args.word}" will be said as "{args.spoken}"')
    elif args.cmd == "ok":
        mark_ok(args.words)
        print(f"Marked fine as written: {', '.join(args.words)}")


if __name__ == "__main__":
    main()
