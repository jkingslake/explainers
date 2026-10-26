# explainers

Claude-generated explainer videos of my papers and other papers, in the style of
3Blue1Brown: narrated Manim animations that build the mathematical model up from
intuition, starring a small towel with a face.

**Reference pilot:** [`examples/pilot/out/pilot.mp4`](examples/pilot/out/pilot.mp4) is a
2-minute taste of Schoof (2007) on marine ice sheet instability.

## Making a video

Open a Claude Code session on this repo (claude.ai/code, the Claude app, or `claude` in a
terminal) and type:

```
/explain https://arxiv.org/abs/2401.01234
```

Anything that identifies a paper works:

| Input | Example |
|---|---|
| arXiv link or id | `/explain 2401.01234` (also pulls the LaTeX source, for exact equations) |
| DOI | `/explain 10.1029/2006JF000664` (finds an open-access copy if there is one) |
| Journal or preprint page | `/explain https://egusphere.copernicus.org/preprints/...` |
| PDF | upload it to `inbox/` on GitHub, then `/explain inbox/my-paper.pdf` |

Add notes after the link to steer it: `/explain 10.1038/... focus on the model in section 3, about 8 minutes`.
Add `--review` to stop after the script so you can edit it before any animation is made.

Claude then works through these steps on its own:

1. **Fetch** the paper: PDF, text, page images, and LaTeX source when it's on arXiv.
2. **Analyse** it in depth (`analysis.md`): assumptions, every equation term by term, full
   derivations checked with sympy, scales, results, limitations, and the aha moments.
   It re-implements the model in `model.py`, so the animations come from real simulations.
3. **Script** it (`script.md`): cold open, title, building the model, analysis, results,
   caveats and recap, with the towel asking the questions a viewer would ask.
4. **Animate** it (`scenes.py`) with the shared kit in `explainer_kit/`.
5. **Review** draft renders frame by frame (contact sheets) and fix layout and timing.
6. **Render** at 1080p with narration, subtitles (`.srt`) and YouTube chapters, then commit it.

Everything ends up in `videos/<slug>/`. Paywalled papers: the fetcher lists the links it
tried. Download the PDF yourself, put it in `inbox/`, and run `/explain inbox/<file>.pdf`.

## Settings: `explainer.toml`

* `channel.name` is the name on every title card ("An explainer by ...") and end card.
* `voice.engine`:
  * `kokoro` is free and runs locally (the default).
  * `elevenlabs` gives the best quality, and you can clone your own voice. Set
    `ELEVENLABS_API_KEY` and `elevenlabs_voice_id`.
  * `openai` and `silent` (no audio) are also available.
* `voice.kokoro_voice`: try `am_michael`, `bm_george`, `bm_fable`, `af_heart` or `bf_emma`.
* `[pronunciations]`: add a table such as `"Kingslake" = "Kings lake"` to fix how the voice
  says a word; subtitles keep the original spelling.
* `video.target_minutes` and `video.fps`.
* `[mascot]`: the towel's colours.

## Running it by hand

```bash
bash scripts/setup.sh                                  # apt deps, LaTeX, uv env, TTS model (~2 min)
.venv/bin/python tools/fetch_paper.py 2401.01234       # → papers/<slug>/
.venv/bin/python tools/render.py examples/pilot        # 480p draft
.venv/bin/python tools/render.py examples/pilot --final
.venv/bin/python tools/frames.py examples/pilot/out/pilot-draft.mp4
```

See `CLAUDE.md` for the house style and the `explainer_kit` API.
