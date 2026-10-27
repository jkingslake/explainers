# explainers

Claude-generated explainer videos of my papers and other papers, in the style of
3Blue1Brown: narrated Manim animations that build the mathematical model up from
intuition, starring a small towel with a face.

## Videos

| Paper | Video |
|---|---|
| Kingslake, Ng & Sole (2015), *Modelling channelized surface drainage of supraglacial lakes*, J. Glaciol. | [`videos/kingslake-2015-modelling-channelized-surface`](videos/kingslake-2015-modelling-channelized-surface) |

**Reference pilot:** [`examples/pilot/out/pilot.mp4`](examples/pilot/out/pilot.mp4) is a
2-minute taste of Schoof (2007) on marine ice sheet instability.

Every video keeps the paper's own framing: its question, order of argument, notation and
explanations (see `CLAUDE.md`).

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
   **Then it asks you** how to say any names, places, Greek letters or symbols it isn't
   sure of. You get a short clip of the voice reading each one; reply "all fine" or with
   corrections like `2 = NIV-lee-sen`. Answers are remembered, so each word is asked about once.
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
* `[pronunciations]`: how the voice should say particular words, e.g. `"Nivlisen" = "NIV lee sen"`
  (subtitles keep the original spelling). `[pronunciations_ok]` lists words checked and fine
  as written. Both are filled in from your answers to the pronunciation question, or by hand
  with `tools/pronounce.py set` / `ok`. Preview a respelling with
  `.venv/bin/python tools/pronounce.py say "Nivlisen" "NIV lee sen"`.
* `video.target_minutes` and `video.fps`.
* `[mascot]`: the towel's colours.

## Publishing to YouTube

Once set up, `/explain` uploads every finished video to your channel as **private** (with its
title, description, chapters, tags and subtitles) and records the link in
`videos/<slug>/youtube.json`. You review it in YouTube Studio and press publish. Settings are in
the `[youtube]` table of `explainer.toml`.

One-time setup (about 10 minutes):

1. In the [Google Cloud console](https://console.cloud.google.com/), create a project and enable
   the **YouTube Data API v3**.
2. Under **Google Auth Platform → Audience**, choose External, add your Google account as a test
   user, then click **Publish app** (sign-ins for apps left in "Testing" expire after 7 days). You
   don't need Google's verification for your own channel; you'll see an "unverified app" warning
   when you sign in, which you can click through.
3. Under **Clients**, create an OAuth client of type **TVs and Limited Input devices**.
4. In the cloud environment's settings (environment menu in the session title bar → Edit), add
   environment variables `YOUTUBE_CLIENT_ID` and `YOUTUBE_CLIENT_SECRET` with the client's values.
5. Start a new session and ask Claude to sign in to YouTube. It runs
   `python tools/youtube_upload.py auth` and shows you a link and a code: open the link on your phone,
   enter the code and choose your channel.
6. To keep that sign-in for future sessions, open `.cache/youtube_token.json` and copy its
   `refresh_token` into the environment's settings as `YOUTUBE_REFRESH_TOKEN`.

Notes:
* YouTube keeps uploads from API projects that haven't passed its
  [API audit](https://support.google.com/youtube/contact/yt_api_form) private. After an audit you can
  set `privacy = "unlisted"` or `"public"` for fully automatic publishing.
* The phone sign-in's permission can't upload subtitle files. To have them uploaded too, sign in on
  your own computer instead with a **Desktop app** OAuth client:
  `python tools/youtube_upload.py auth --local`. That prints the refresh token to use as
  `YOUTUBE_REFRESH_TOKEN`. Otherwise, add `out/<slug>.srt` in YouTube Studio (Subtitles → Upload file).
* Upload by hand: `python tools/youtube_upload.py upload videos/<slug> [--privacy unlisted] [--dry-run]`.

## Running it by hand

```bash
bash scripts/setup.sh                                  # apt deps, LaTeX, uv env, TTS model (~2 min)
.venv/bin/python tools/fetch_paper.py 2401.01234       # → papers/<slug>/
.venv/bin/python tools/render.py examples/pilot        # 480p draft
.venv/bin/python tools/render.py examples/pilot --final
.venv/bin/python tools/frames.py examples/pilot/out/pilot-draft.mp4
```

See `CLAUDE.md` for the house style and the `explainer_kit` API.
