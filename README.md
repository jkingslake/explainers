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

## How to use it

### Once, before your first video

1. **Get the pipeline onto `main`.** New Claude Code sessions start from the repo's default
   branch, and the `/explain` command lives in the repo, so merge any branch that holds
   pipeline changes (ask Claude: "open a pull request and merge it").
2. **Check `explainer.toml`.** Set `channel.name` (shown on every title and end card) and,
   if you like, a different narration voice (see [Settings](#settings-explainertoml)).
3. **Optional: YouTube.** Follow [Publishing to YouTube](#publishing-to-youtube) once, and every
   finished video is uploaded to your channel as private for you to review.
4. **Optional: faster starts.** Put `bash scripts/setup.sh` in your cloud environment's
   setup script (environment menu in the session title bar → Edit). Otherwise Claude installs
   the tools itself at the start of each run, which takes about 2 minutes.

### Make a video

1. **Start a session** on this repo: at [claude.ai/code](https://claude.ai/code) or in the
   Claude app, pick the `explainers` repository and start a new session. On your own computer,
   run `claude` inside a clone of the repo.
2. **Give it a paper.** Type `/explain` followed by anything that identifies the paper:

   | Input | Example |
   |---|---|
   | arXiv link or id | `/explain 2401.01234` (also pulls the LaTeX source, for exact equations) |
   | DOI | `/explain 10.3189/2015JoG14J158` (finds an open-access copy if there is one) |
   | Journal or preprint page | `/explain https://egusphere.copernicus.org/preprints/...` |
   | PDF | upload it to `inbox/` on GitHub, then `/explain inbox/my-paper.pdf` |

   Add notes after the paper to steer it, e.g.
   `/explain 10.1038/... focus on the model in section 3, about 8 minutes`.
   Add `--review` to see the script before any animation is made.
3. **Answer one question.** After writing the script, Claude sends you a short audio clip of
   the voice reading every name, place, Greek letter or symbol it isn't sure about, numbered.
   Listen, then reply "all fine" or with corrections such as `2 = NIV-liss-en, 14 = ZEE-tuh`
   (capitals for the stressed syllable). Each word is only asked about once, ever.
4. **Let it run.** Everything else is automatic and usually takes an hour or two, mostly
   rendering. Claude posts one line as each stage finishes (see [What happens](#what-happens)).
5. **Get the video.** When it's done you get:
   * the video, sent to you in the session to watch straight away;
   * everything committed to the session's branch under `videos/<slug>/`: the 1080p video,
     subtitles, YouTube chapters, and the analysis, script and code behind it;
   * an upload to YouTube as private, if you've set that up;
   * a summary of anything you should check: simplifications, places where the
     re-implemented model differs from the paper, and any errors or typos found in the paper.

### Ask for changes

Watch it, then say what you'd like in the same session, in plain words. For example:

* "The cold open is too long; cut it to 30 seconds."
* "Spend longer on Eqn 12 and show where the v cubed comes from."
* "The towel's bubble covers the graph at 6:40."
* "Say Kingslake as KINGS-lake." (remembered for every future video)
* "Use a British voice."

Claude edits the scenes, re-renders only what changed, checks the frames again, and sends
you the new version. Ask "upload the new version to YouTube" if an earlier one is already there.

### Keep the work

Each session saves its work on its own branch. To keep a video, plus any new pronunciations
or settings, for future sessions, ask Claude to open a pull request and merge it into `main`.

### What happens

1. **Fetch** the paper: PDF, text, page images, and LaTeX source when it's on arXiv.
2. **Analyse** it in depth (`analysis.md`): assumptions, every equation term by term, full
   derivations checked with sympy, scales, results, limitations, and the key insights.
   It re-implements the model in `model.py`, so the animations come from real simulations.
3. **Script** it (`script.md`), following the paper's own structure, with the towel asking the
   questions a viewer would ask. Then the pronunciation question.
4. **Animate** it (`scenes.py`) with the shared kit in `explainer_kit/`.
5. **Review** draft renders frame by frame (contact sheets) and fix layout and timing.
6. **Render** at 1080p with narration, subtitles (`.srt`) and YouTube chapters, then commit.
7. **Publish** to YouTube as private, when set up.

### If something goes wrong

* **"Could not download a PDF"**: the paper is paywalled, or the publisher blocks scripts. The
  message lists the links it tried; download the PDF yourself, upload it to `inbox/` on GitHub,
  and run `/explain inbox/<file>.pdf`.
* **A word still sounds wrong in the finished video**: tell Claude how it should sound; it
  updates the pronunciation and re-renders just those sentences.
* **The video is over 95 MB**: GitHub won't take files over 100 MB, so Claude commits a 720p
  copy instead and still sends you the full-quality one.
* **The session was interrupted**: start a new session on the same branch and say "carry on
  with the video for <paper>". Everything finished so far is in `videos/<slug>/`.

## Settings: `explainer.toml`

* `channel.name` is the name on every title card ("An explainer by ...") and end card.
* `voice.engine`:
  * `kokoro` is free and runs locally (the default).
  * `elevenlabs` gives the best quality, and you can clone your own voice. Set
    `ELEVENLABS_API_KEY` and `elevenlabs_voice_id`.
  * `openai` and `silent` (no audio) are also available.
* `voice.kokoro_voice`: try `am_michael`, `bm_george`, `bm_fable`, `af_heart` or `bf_emma`.
* `[pronunciations]`: how the voice should say particular words, e.g. `"Nivlisen" = "Nivlissen"`
  (subtitles keep the original spelling). `[pronunciations_ok]` lists words checked and fine
  as written. Both are filled in from your answers to the pronunciation question, or by hand
  with `tools/pronounce.py set` / `ok`.
* `video.target_minutes` and `video.fps`.
* `[mascot]`: the towel's colours.
* `[youtube]`: upload privacy, category, tags, playlist and description footer.

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

Never paste these values into the chat; they only go in the environment settings.

Notes:
* YouTube keeps uploads from API projects that haven't passed its
  [API audit](https://support.google.com/youtube/contact/yt_api_form) private. After an audit you can
  set `privacy = "unlisted"` or `"public"` for fully automatic publishing.
* The phone sign-in's permission can't upload subtitle files. To have them uploaded too, sign in on
  your own computer instead with a **Desktop app** OAuth client:
  `python tools/youtube_upload.py auth --local`. That prints the refresh token to use as
  `YOUTUBE_REFRESH_TOKEN`. Otherwise, add `out/<slug>.srt` in YouTube Studio (Subtitles → Upload file).

## Running it by hand

Everything Claude runs is an ordinary script:

```bash
bash scripts/setup.sh                                               # apt deps, LaTeX, uv env, TTS model (~2 min)
.venv/bin/python tools/fetch_paper.py 2401.01234                    # → papers/<slug>/
.venv/bin/python tools/pronounce.py check videos/<slug> --audio     # uncertain words + listening clip
.venv/bin/python tools/pronounce.py say "Nivlisen" "Nivlissen"      # preview a respelling
.venv/bin/python tools/render.py videos/<slug>                      # 480p draft (all scenes in parallel)
.venv/bin/python tools/render.py videos/<slug> --only Intro         # re-render one scene
.venv/bin/python tools/frames.py videos/<slug>/out/<slug>-draft.mp4 # contact sheets for review
.venv/bin/python tools/render.py videos/<slug> --final              # 1080p with subtitles and chapters
.venv/bin/python tools/youtube_upload.py upload videos/<slug> --dry-run   # check title/description
```

See `CLAUDE.md` for the house style and the `explainer_kit` API.
