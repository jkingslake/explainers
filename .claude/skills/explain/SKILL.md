---
name: explain
description: Turn a research paper (arXiv link, DOI, journal URL, or PDF) into a narrated 3Blue1Brown-style Manim explainer video with the towel mascot, branded with the channel name. Use whenever the user gives a paper and wants an explainer or video of it.
argument-hint: <arxiv-url | doi | url | inbox/paper.pdf> [notes, e.g. "focus on section 3", "10 minutes", "--review"]
---

# Explain a paper as a video

Paper and notes: `$ARGUMENTS`

You are making a video in the style of 3Blue1Brown: patient, visual, intuition first,
the mathematics built up piece by piece until the viewer could have derived it. Read
`CLAUDE.md` (the style guide and kit reference) and `examples/pilot/scenes.py` (a small,
working reference video) before writing any scene code.

**Keep the paper's framing. This rule overrides everything below.** The video explains the
paper the way its authors framed it: their question and motivation, the order of their
argument, their notation and symbol names, the quantities they define (for example a
stability parameter), their idealised cases and simulations, and their own physical
explanations of each result. Never recast the work around a new ratio, parameter,
analogy, derivation or storyline of your own, however much simpler it seems. Visuals and
the towel exist to illustrate the paper's own statements. If you spot another way of seeing
a result, record it in `analysis.md` under "Notes beyond the paper" and keep it out of the
script unless the user asks for it.

Work through the phases in order. This runs end to end without stopping, **unless** the
arguments contain `--review`: then stop after Phase 3, show the user the script, and wait.

Keep the user posted with one short line per phase (e.g. "Analysis done: 9 equations,
3 key results. Writing the script."). Long renders: run them with `run_in_background`
and keep working (e.g. on the next scene) while they go.

## Phase 0: Toolchain

```bash
bash scripts/setup.sh --check     # anything missing?
bash scripts/setup.sh             # if so (about 2 min on a fresh container)
source .venv/bin/activate
```

## Phase 1: Fetch

```bash
python tools/fetch_paper.py "<source>"     # last line printed = <slug>
```

* Exit code 2 means no PDF could be downloaded (paywall, or a host that blocks scripts).
  Show the user the URLs it tried and ask them to upload the PDF to `inbox/` (via GitHub)
  or attach it, then re-run with that path. If the user attached a PDF to the chat, use its
  path directly. Never try to get around a paywall or bot check.
* Create `videos/<slug>/` and copy `papers/<slug>/meta.json` to `videos/<slug>/meta.json`
  (`papers/` is git-ignored; `videos/` is committed).
* **Own paper?** If the channel name's surname (`explainer.toml`) is among the
  authors, the narration may say "we" and "in our paper". Otherwise say "the authors"
  or use their names.

## Phase 2: Understand the paper thoroughly → `videos/<slug>/analysis.md`

Read **all** of `papers/<slug>/paper.md`, including appendices and supplementary material.
If `papers/<slug>/source/` exists, read the `.tex` files: they hold the exact equations.
Look at every page image in `papers/<slug>/pages/` that has a figure or a display equation.

Then write `analysis.md`, the scientific backbone of the video. Follow the paper's own
structure, equation numbers and notation throughout, and explain each step the way the
paper does. It must contain:

1. **The question.** One paragraph: what problem, why it matters, what was unknown.
2. **Takeaway.** The paper's main result in one sentence a curious 16-year-old would follow.
3. **Setup and assumptions.** For each assumption: what it means physically, why it is
   reasonable, and what would change without it.
4. **Notation and palette.** A table with one row per symbol: meaning, units, typical
   value, and its colour for the whole video (from `QUANTITY_COLORS`, most important
   quantities first).
5. **The model.** Every governing equation, with each term explained in words ("this
   term is the rate at which ... ; it is negative because ...").
6. **Derivations.** Every step from the model to the key results, with nothing skipped,
   including steps the paper skips. Check the algebra with sympy in
   `videos/<slug>/checks.py` and run it. Record any typo or error you find in the paper.
7. **Scales and dimensionless numbers.** What sets the size of things. Limits, asymptotics
   and regimes.
8. **Results.** Figure by figure: what is plotted, what it shows, and why the model
   produces it.
9. **Reproduction.** Implement the core model in `videos/<slug>/model.py` (numpy/scipy)
   and reproduce at least one key result or figure qualitatively. Every animated curve
   in the video should come from this code, not from hand-drawn shapes. Note any
   mismatch with the paper.
10. **Limitations and open questions.** Include those the authors state and those they don't.
11. **Aha moments.** The 3 to 5 insights the video must land, as the paper states them.
12. **Likely confusions.** Places a smart viewer would get lost. These become the
    towel's questions.
13. **Notes beyond the paper.** Anything you derived or noticed that the paper does not
    say (reformulations, extra numbers, alternative intuitions). Not used in the video.

When the paper is mostly empirical (data, not a model), the "model" is the analysis
pipeline: what was measured, how it was processed, the statistical model, and why the
inference holds. Treat that with the same depth.

## Phase 3: Script → `videos/<slug>/script.md`

Length: `video.target_minutes` from `explainer.toml` unless the user said otherwise
(about 150 spoken words per minute). The scenes follow the paper's sections in the
paper's order, using its terms. Default arc:

1. **Cold open** (30 to 60 s): the paper's own motivation (its observations or question)
   as a striking visual, with no title yet.
2. **Title card** (`self.title_card(...)`).
3. **The setup**: the physical system as the paper describes it, built visually.
4. **Building the model**: the paper's equations in its order, one assumption or term at a
   time, each paired with a picture.
5. **The analysis**: the paper's derivations and the quantities it defines, shown as a
   sequence of transformations.
6. **Results**: the paper's cases and simulations, animated from `model.py`, with sliders
   or parameter sweeps where they build intuition.
7. **Caveats and open questions**: the limitations the paper discusses.
8. **Recap**: the paper's conclusions in 3 or 4 lines, then the end card (`self.end_card(...)`).

For each scene write: `## SceneName — chapter title`, target duration, and then
alternating **Narration** (the exact words to be spoken) and **Visual** (what is on
screen and how it moves). Mark towel beats (`TOWEL: confused, asks "..."`). Aim for 3 to 6
towel appearances in a 10-minute video, at the moments a viewer would actually be confused.

Narration is read aloud by a text-to-speech voice, so write it for the ear:
* Spell out symbols and maths: "h sub g", "d h by d t", "the square root of g h", "theta".
  Never write LaTeX, Unicode maths or bare symbols in narration.
* Short sentences. No parentheses, footnotes, "e.g." or "i.e.". Avoid "this" with no clear referent.
* Numbers as they'd be said: "about two hundred metres a year", "ten to the minus three".
* Add awkward recurring terms to `[pronunciations]` in `explainer.toml` instead of
  misspelling them in the script, so the subtitles stay correct.

If `--review` was given, stop here. Show the user the scene list with durations and the
first two scenes in full, and ask for changes.

## Phase 4: Animate → `videos/<slug>/scenes.py`

* `from manim import *` and `from explainer_kit import *`; put `PALETTE` at the top; end
  with `SCENES = [ColdOpen, Title, ..., End]`. One class per script scene, each with a
  docstring that gives its chapter title. Keep each scene 30 to 120 s, so re-renders are cheap.
* Every narration sentence goes in `with self.narrate("...") as n:` and the animations
  inside it are timed with `n.frac(...)`. Copy the narration from `script.md` word for word.
* Import curves and data from `model.py`; don't hand-draw results.
* Follow the style rules and Manim notes in `CLAUDE.md`.

## Phase 5: Draft, review, fix (repeat until clean)

```bash
python tools/render.py videos/<slug>                  # 480p draft, all scenes in parallel
python tools/render.py videos/<slug> --only SceneName # quick re-render of one scene
python tools/frames.py videos/<slug>/out/<slug>-draft.mp4   # contact sheets
```

**Look at every contact sheet** (Read the PNGs). Check for:
* text or equations overlapping each other or the towel, or running off the frame
* stale objects left on screen after they stop being discussed
* more than about 5 s with nothing moving, or text-heavy frames (more than ~12 words of prose)
* colours that break the palette, unreadable contrast, labels far from what they label
* visuals out of sync with the narration (compare with `out/<slug>-draft.srt`)

Fix and re-render the affected scenes. Then re-read `analysis.md` against the script:
check that every claim in the narration is supported by the paper or by your checks.

## Phase 6: Final render

```bash
python tools/render.py videos/<slug> --final
```

Write `videos/<slug>/README.md`: title, paper link, runtime, a YouTube-ready description,
chapter timestamps (`out/<slug>.chapters.txt`), and a short "simplifications made"
section listing anything the video glosses over.

## Phase 7: Deliver

* Commit `videos/<slug>/` (analysis, script, scenes, model, checks, README, and
  `out/<slug>.mp4` + `.srt` + `.chapters.txt` when the mp4 is under 95 MB; above that,
  render at `--quality m` for the committed copy). Push to the working branch.
* Send the final mp4 to the user (SendUserFile) when that tool is available.

## Phase 8: Publish to YouTube

The channel owner has asked for finished videos to be uploaded automatically. If
`[youtube] enabled = true` in `explainer.toml`:

```bash
python tools/youtube_upload.py check                       # credentials available?
python tools/youtube_upload.py upload videos/<slug> --dry-run   # review title, description, tags
python tools/youtube_upload.py upload videos/<slug>        # uploads at [youtube] privacy (default private)
```

* Title, description and tags come from `videos/<slug>/README.md` (its first heading, the
  "YouTube description" section with `CHAPTERS` and an optional `Tags:` line). Keep that section
  in the paper's framing too.
* Upload at the configured privacy; never raise it to public yourself unless the user asks.
* Commit the `youtube.json` it writes, and give the user the link and the Studio link.
* If `check` reports missing credentials, skip the upload and tell the user once that they can
  enable it by following README, "Publishing to YouTube". Never ask for tokens in chat.
* Never upload a video twice; `youtube.json` records an upload and the tool refuses a second.
* Finish with: runtime, chapter list, the aha moments covered, and anything the user
  should check (simplifications, places where the reproduction differed from the paper,
  errors found in the paper).
