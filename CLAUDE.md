# Explainers

This repo turns research papers into narrated, 3Blue1Brown-style explainer videos made
with Manim (Community Edition). Each video is branded with the channel name in
`explainer.toml`, and the cast includes a little towel with a face, our counterpart to
3b1b's pi creatures.

To make a video, use the `/explain <arxiv | doi | url | pdf>` skill
(`.claude/skills/explain/SKILL.md`). It runs the whole pipeline: fetch → analysis →
script → scenes → draft → review → final render → commit.

## Layout

```
explainer.toml          channel name, narration voice, video settings, mascot colours
explainer_kit/          shared code: ExplainerScene, Towel, style, TTS
examples/pilot/         2-minute reference video; read it before writing scenes
tools/fetch_paper.py    paper → papers/<slug>/ (pdf, text, page images, LaTeX source)
tools/render.py         parallel render + stitch → videos/<slug>/out/<slug>.mp4 + .srt + chapters
tools/frames.py         contact sheets of a render, for visual review
tools/youtube_upload.py upload a finished video to YouTube (title/description from its README)
tools/pronounce.py      find words the voice may mispronounce; listening clip; record fixes
scripts/setup.sh        installs everything (apt, uv env, Kokoro TTS model)
inbox/                  drop PDFs here (e.g. paywalled papers)
papers/<slug>/          fetched material (git-ignored)
videos/<slug>/          one video: analysis.md, script.md, model.py, checks.py, scenes.py, out/
```

Run tools with `.venv/bin/python` (or `source .venv/bin/activate` first).

## House style: what makes it feel like 3Blue1Brown

0. **Keep the paper's framing (always; this outranks the rest).** Explain the paper the way
   its authors framed it: their question, the order of their argument, their notation and
   named quantities, their idealised cases, and their own physical explanations. Never
   recast the work around a ratio, parameter, analogy or storyline of your own. The style
   rules below govern *how* the paper's argument is shown, not *what* the argument is.
   Your own extra insights go in `analysis.md` under "Notes beyond the paper", not in the video.
1. **Question before answer.** Open on a concrete puzzle or a striking picture, not the
   abstract. Make the viewer want the result before you show it.
2. **Show, then name.** The picture comes first and the notation second. Introduce a
   symbol only once it's needed, say what it means in words, and keep it on screen while
   it's in use.
3. **One colour per quantity, for the whole video.** Fix the `PALETTE` in `analysis.md`
   and never reuse a quantity's colour for anything else. Use the colour for the symbol,
   the curve it labels, and the words that name it.
4. **Equations are built, not dumped.** Write an equation term by term. Point at each term
   (Brace, SurroundingRectangle, Indicate) and say what it does physically. Move between
   forms with `TransformMatchingTex` so the viewer sees which pieces moved. Pair every
   equation with a picture of what it does.
5. **Let the maths move.** Simulate the model (`model.py`) and animate it: ValueTracker
   sliders, parameter sweeps, trajectories, before/after. The viewer should *see* the
   instability, the scaling or the balance.
6. **One idea per scene, and a clean screen.** Fade out what's no longer needed. Keep
   on-screen prose to about 12 words at most; the narration carries the words. Something
   should move at least every ~5 seconds, and a key reveal earns a 1 to 2 second pause.
7. **The towel is the viewer.** It asks the naive question at the moment of real
   confusion, looks at what matters (`look_at`), and reacts to the aha moment. It never
   lectures. In a 10-minute video it appears 3 to 6 times, with at least one moment of charm.
8. **Honest and precise.** Separate what the paper shows from what the video simplifies.
   State assumptions and limitations. Cite a figure when you reproduce it
   (`caption("Adapted from Fig. 3, Smith et al. 2021")`). Prefer re-drawing figures from the
   model over screenshots.
9. **Land it.** End with a recap of the 3 or 4 aha moments, then the end card.

Visual defaults: dark background (`BACKGROUND`), the classic 3b1b colours
(`QUANTITY_COLORS`), Computer Modern everywhere (`words()`, `heading()`, `eq()` use it),
at least 0.5 units of margin from the frame edge, and 1080p at 30 fps for finals.

## explainer_kit reference

```python
from manim import *
from explainer_kit import *

class Model(ExplainerScene):
    """Chapter title shown in YouTube chapters"""
    def construct(self):
        with self.narrate("Spoken sentence, exactly as in script.md.") as n:
            self.play(Write(eq_), run_time=n.frac(0.5))   # n.duration, n.remaining, n.frac(f)
        # on exit the block waits for the voice to finish (towels blink meanwhile)
        self.say("Shorthand sentence.", FadeIn(thing))      # plays animations across the sentence
```

* `ExplainerScene.narrate(text)` synthesises speech (cached in `.cache/tts`), adds it to the
  scene, records a subtitle cue, and waits for it to finish. `idle(t)` is a wait with
  blinking. `title_card(title, authors, venue, narration=...)`,
  `end_card(citation, url)`, `paper_figure(png, source)`.
* `Towel(mode="plain", height=2)`. Modes: plain, happy, speaking, surprised, confused,
  thinking, sad, skeptical, smug. Animations: `towel.change(mode, look_at=mob)`,
  `towel.glance(mob)`, `towel.blink()`, `towel.hop()`, `towel.sway()`,
  `self.play(*towel.says("text", side=RIGHT|LEFT|UP, font_size=28, wrap=24))`,
  `towel.thinks(...)`, `self.play(*towel.debubble("happy"))`. Usual spots: `to_corner(DL)`
  or `to_corner(DR)` at height 1.3 to 1.6, away from the main content.
* Style: `words(s, size)`, `heading(s)`, `eq(*tex, t2c=PALETTE_TEX, size)`, `caption(s)`,
  `fits_frame(mob)`, `stack(*mobs)`, colours `BACKGROUND TEXT_COLOR MUTED QUANTITY_COLORS`.
* Animated scenes that need camera moves: `class Zoom(ExplainerScene, MovingCameraScene)`.

## Manim notes (Community Edition; 3b1b's own videos use manimgl, which differs)

* CE names: `Create` (not ShowCreation), `Tex`/`MathTex` (not TexText), `FadeIn(m, shift=UP)`,
  `self.play(m.animate.shift(UP))`, `always_redraw`, `ValueTracker`, `TransformMatchingTex`.
* Split `MathTex` into separate strings for every term you will colour, index or transform:
  `MathTex("q", r"\approx", "C", "h", "^{19/4}")`. With `tex_to_color_map`, colouring
  splits the tex further, so check `len(eq)` before indexing.
* `ImageMobject` cannot go in a `VGroup`; use `Group`.
* `Text` takes plain Unicode; anything mathematical goes in `MathTex`.
* Keep each scene under ~2 minutes so failures and re-renders stay cheap; render scenes
  with `--only` while iterating.
* A scene that fails in the draft render leaves its log in `build/<slug>/l/<Scene>.log`.

## Narration voice

Set in `explainer.toml`: `kokoro` (free, local, the default), `elevenlabs` (best quality,
and it can clone the channel owner's voice; needs `ELEVENLABS_API_KEY`), `openai`, or `silent`
(fast layout drafts: `tools/render.py --silent`). Changing the voice re-synthesises
everything on the next render; the cache is keyed on text and voice settings.

Pronunciation: never guess how the channel owner wants a name, place, Greek letter or
symbol said. `tools/pronounce.py check videos/<slug> --audio` lists the unsettled words and
makes a listening clip; ask the user about them (skill Phase 3b) and record the answers with
`pronounce.py set` (respelling) or `pronounce.py ok` (fine as written). They are stored in
`[pronunciations]` and `[pronunciations_ok]` in `explainer.toml` and apply to every video.

## Conventions

* `videos/<slug>/` is committed. `papers/`, `build/`, `.cache/`, `.venv/` and draft
  renders are not.
* Commit the final mp4 only if it is under 95 MB (GitHub's limit is 100 MB per file).
* Never put paper PDFs from third parties in committed paths other than `inbox/`.
