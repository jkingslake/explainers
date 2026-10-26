#!/usr/bin/env python3
"""Upload a finished explainer to YouTube (YouTube Data API v3, OAuth refresh token).

    python tools/youtube_upload.py auth              # one-time sign-in (device code; works from a phone)
    python tools/youtube_upload.py auth --local      # one-time sign-in on your own computer (browser)
    python tools/youtube_upload.py check             # are credentials available?
    python tools/youtube_upload.py upload videos/<slug> [--privacy private|unlisted|public] [--dry-run]
    python tools/youtube_upload.py status videos/<slug>

Credentials come from environment variables YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET and
YOUTUBE_REFRESH_TOKEN, or from .cache/youtube_token.json (written by `auth`, git-ignored).
Never commit them. Metadata comes from videos/<slug>/README.md (title = first heading,
description = the "YouTube description" section, CHAPTERS replaced by out/<slug>.chapters.txt)
and from the [youtube] table in explainer.toml. The result is recorded in videos/<slug>/youtube.json,
and a video that already has one is not uploaded again unless --force is given.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from explainer_kit.config import channel_name, settings  # noqa: E402

TOKEN_FILE = ROOT / ".cache" / "youtube_token.json"
TOKEN_URL = "https://oauth2.googleapis.com/token"
# Device flow only allows the broad youtube scope; the local flow adds force-ssl, which
# captions.insert requires.
DEVICE_SCOPES = "https://www.googleapis.com/auth/youtube"
LOCAL_SCOPES = "https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl"
CHUNK = 8 * 1024 * 1024


class Credentials:
    def __init__(self):
        saved = json.loads(TOKEN_FILE.read_text()) if TOKEN_FILE.exists() else {}
        self.client_id = os.environ.get("YOUTUBE_CLIENT_ID") or saved.get("client_id")
        self.client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET") or saved.get("client_secret")
        self.refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN") or saved.get("refresh_token")
        self._access, self._expiry = None, 0.0

    def missing(self) -> list[str]:
        return [n for n, v in [("YOUTUBE_CLIENT_ID", self.client_id), ("YOUTUBE_CLIENT_SECRET", self.client_secret),
                               ("YOUTUBE_REFRESH_TOKEN", self.refresh_token)] if not v]

    def headers(self) -> dict:
        if time.time() > self._expiry - 60:
            r = requests.post(TOKEN_URL, data={
                "client_id": self.client_id, "client_secret": self.client_secret,
                "refresh_token": self.refresh_token, "grant_type": "refresh_token",
            }, timeout=60)
            if r.status_code != 200:
                raise SystemExit(f"Could not refresh the YouTube access token ({r.status_code}: {r.json().get('error')}). "
                                 "Run `python tools/youtube_upload.py auth` again.")
            tok = r.json()
            self._access, self._expiry = tok["access_token"], time.time() + tok.get("expires_in", 3600)
        return {"Authorization": f"Bearer {self._access}"}


# ------------------------------------------------------------------ sign-in
def save_token(client_id: str, client_secret: str, refresh_token: str) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps({"client_id": client_id, "client_secret": client_secret,
                                      "refresh_token": refresh_token}))
    TOKEN_FILE.chmod(0o600)


def client_from_env_or_prompt() -> tuple[str, str]:
    cid, secret = os.environ.get("YOUTUBE_CLIENT_ID"), os.environ.get("YOUTUBE_CLIENT_SECRET")
    if not (cid and secret):
        if not sys.stdin.isatty():
            raise SystemExit("Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET first (see README, 'Publishing to YouTube').")
        import getpass

        cid = cid or input("OAuth client ID: ").strip()
        secret = secret or getpass.getpass("OAuth client secret: ").strip()
    return cid, secret


def auth_device() -> None:
    cid, secret = client_from_env_or_prompt()
    r = requests.post("https://oauth2.googleapis.com/device/code", data={"client_id": cid, "scope": DEVICE_SCOPES},
                      timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"Device sign-in refused ({r.json().get('error')}). The OAuth client must be of type "
                         "'TVs and Limited Input devices'.")
    d = r.json()
    print(f"\nOn any device, open {d['verification_url']} and enter the code:  {d['user_code']}\n", flush=True)
    interval, deadline = d.get("interval", 5), time.time() + d.get("expires_in", 1800)
    while time.time() < deadline:
        time.sleep(interval)
        t = requests.post(TOKEN_URL, data={
            "client_id": cid, "client_secret": secret, "device_code": d["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }, timeout=60).json()
        if "refresh_token" in t:
            finish_auth(cid, secret, t["refresh_token"])
            return
        if t.get("error") == "slow_down":
            interval += 5
        elif t.get("error") != "authorization_pending":
            raise SystemExit(f"Sign-in failed: {t.get('error')}")
    raise SystemExit("Sign-in code expired; run auth again.")


def auth_local() -> None:
    """Loopback flow for a Desktop-type OAuth client, run on your own computer."""
    cid, secret = client_from_env_or_prompt()
    got: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            got.update({k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Signed in. You can close this tab.")

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": LOCAL_SCOPES,
        "access_type": "offline", "prompt": "consent",
    })
    print(f"Opening your browser. If it doesn't open, visit:\n{url}\n", flush=True)
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        server.handle_request()
    if "error" in got:
        raise SystemExit(f"Sign-in failed: {got['error']}")
    t = requests.post(TOKEN_URL, data={"client_id": cid, "client_secret": secret, "code": got["code"],
                                       "redirect_uri": redirect, "grant_type": "authorization_code"}, timeout=60).json()
    if "refresh_token" not in t:
        raise SystemExit(f"Sign-in failed: {t.get('error')}")
    finish_auth(cid, secret, t["refresh_token"])


def finish_auth(cid: str, secret: str, refresh_token: str) -> None:
    save_token(cid, secret, refresh_token)
    print(f"Signed in. Credentials saved to {TOKEN_FILE.relative_to(ROOT)} (git-ignored).")
    if os.environ.get("CLAUDE_CODE_REMOTE") == "true":
        # Never print the token into a cloud session's transcript.
        print("To keep uploads working in future cloud sessions, open that file and copy its refresh_token into "
              "the environment's settings as YOUTUBE_REFRESH_TOKEN.")
    else:
        print(f"For cloud sessions, add this to the environment's settings as YOUTUBE_REFRESH_TOKEN:\n{refresh_token}")


# ------------------------------------------------------------------ metadata
def clean(s: str) -> str:
    return s.replace("<", "(").replace(">", ")")  # YouTube rejects angle brackets


def unwrap(text: str) -> str:
    """Join hard-wrapped Markdown lines into paragraphs; keep chapter lines (0:00 Title) on their own."""
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for p in paras:
        lines = [ln.strip() for ln in p.strip().splitlines()]
        out.append("\n".join(lines) if all(re.match(r"^\d+:\d{2}", ln) for ln in lines) else " ".join(lines))
    return "\n\n".join(out)


def metadata(vdir: Path) -> dict:
    slug = vdir.name
    readme = (vdir / "README.md").read_text()
    title = re.search(r"^# (.+)$", readme, re.M).group(1).strip()
    m = re.search(r"^## YouTube description\s*\n(.*?)(?=^## |\Z)", readme, re.M | re.S)
    if not m:
        raise SystemExit(f"{vdir}/README.md needs a '## YouTube description' section")
    desc = m.group(1).strip()
    video_tags = []
    t = re.search(r"^Tags:(.*)$", desc, re.M)
    if t:  # optional per-video tags line inside the description section
        video_tags = [x.strip() for x in t.group(1).split(",") if x.strip()]
        desc = (desc[: t.start()] + desc[t.end():]).strip()
    chapters = vdir / "out" / f"{slug}.chapters.txt"
    desc = desc.replace("CHAPTERS", chapters.read_text().strip() if chapters.exists() else "")
    yt = settings().get("youtube", {})
    footer = yt.get("description_footer", "").format(channel=channel_name())
    if footer:
        desc = f"{desc}\n\n{footer}"
    desc = unwrap(desc)
    voice = settings()["voice"]["engine"]
    synthetic = yt.get("synthetic_media", "auto")
    synthetic = (voice == "elevenlabs") if synthetic == "auto" else bool(synthetic)
    body = {
        "snippet": {
            "title": clean(title)[:100],
            "description": clean(desc)[:4900],
            "tags": list(dict.fromkeys(video_tags + yt.get("tags", []))),
            "categoryId": str(yt.get("category_id", "27")),
            "defaultLanguage": yt.get("language", "en"),
            "defaultAudioLanguage": yt.get("language", "en"),
        },
        "status": {
            "privacyStatus": yt.get("privacy", "private"),
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "license": "youtube",
        },
    }
    if synthetic:
        body["status"]["containsSyntheticMedia"] = True
    return body


# ------------------------------------------------------------------ upload
def upload_video(creds: Credentials, path: Path, body: dict) -> dict:
    size = path.stat().st_size
    url = "https://www.googleapis.com/upload/youtube/v3/videos"
    params = {"uploadType": "resumable", "part": "snippet,status"}
    hdr = {**creds.headers(), "Content-Type": "application/json; charset=UTF-8",
           "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}
    r = requests.post(url, params=params, headers=hdr, data=json.dumps(body), timeout=120)
    if r.status_code == 400 and "containsSyntheticMedia" in r.text:
        body["status"].pop("containsSyntheticMedia", None)
        print("note: API did not accept containsSyntheticMedia; set the disclosure in YouTube Studio instead.")
        r = requests.post(url, params=params, headers=hdr, data=json.dumps(body), timeout=120)
    if r.status_code != 200:
        raise SystemExit(f"Upload could not start ({r.status_code}): {r.text[:500]}")
    session = r.headers["Location"]

    sent, retries = 0, 0
    with open(path, "rb") as f:
        while True:
            f.seek(sent)
            chunk = f.read(CHUNK)
            end = sent + len(chunk) - 1
            try:
                r = requests.put(session, data=chunk, timeout=600, headers={
                    **creds.headers(), "Content-Length": str(len(chunk)), "Content-Range": f"bytes {sent}-{end}/{size}"})
            except requests.RequestException as e:
                r = None
                err = str(e)
            if r is not None and r.status_code in (200, 201):
                print(f"  uploaded {size / 1e6:.0f} MB", flush=True)
                return r.json()
            if r is not None and r.status_code == 308:
                rng = r.headers.get("Range")
                sent = int(rng.split("-")[1]) + 1 if rng else 0
                retries = 0
                print(f"  {sent / size:5.0%}", flush=True)
                continue
            if r is not None and r.status_code not in (500, 502, 503, 504):
                raise SystemExit(f"Upload failed ({r.status_code}): {r.text[:500]}")
            retries += 1
            if retries > 6:
                raise SystemExit(f"Upload failed after retries: {err if r is None else r.status_code}")
            time.sleep(2**retries)
            q = requests.put(session, headers={**creds.headers(), "Content-Range": f"bytes */{size}"}, timeout=60)
            if q.status_code in (200, 201):
                return q.json()
            rng = q.headers.get("Range")
            sent = int(rng.split("-")[1]) + 1 if rng else 0


def upload_captions(creds: Credentials, video_id: str, srt: Path, language: str) -> str:
    boundary = "explainers-captions"
    meta = json.dumps({"snippet": {"videoId": video_id, "language": language, "name": "English", "isDraft": False}})
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
            f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + srt.read_bytes() + \
        f"\r\n--{boundary}--\r\n".encode()
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/captions",
                      params={"uploadType": "multipart", "part": "snippet"},
                      headers={**creds.headers(), "Content-Type": f"multipart/related; boundary={boundary}"},
                      data=body, timeout=120)
    if r.status_code == 200:
        return "uploaded"
    if r.status_code == 403:
        return "skipped (sign-in scope doesn't allow captions; upload the .srt in YouTube Studio or use `auth --local`)"
    return f"failed ({r.status_code}): {r.text[:200]}"


def add_to_playlist(creds: Credentials, video_id: str, playlist_id: str) -> str:
    r = requests.post("https://www.googleapis.com/youtube/v3/playlistItems", params={"part": "snippet"},
                      headers=creds.headers(), timeout=60,
                      json={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}})
    return "added" if r.status_code == 200 else f"failed ({r.status_code})"


def cmd_upload(args) -> None:
    vdir = args.video_dir.resolve()
    slug = vdir.name
    record = vdir / "youtube.json"
    if record.exists() and not args.force:
        rec = json.loads(record.read_text())
        raise SystemExit(f"Already uploaded: {rec['url']} (use --force to upload again)")
    mp4 = vdir / "out" / f"{slug}.mp4"
    body = metadata(vdir)
    if args.privacy:
        body["status"]["privacyStatus"] = args.privacy
    if args.dry_run:
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print(f"\nfile: {mp4} ({'found' if mp4.exists() else 'MISSING'})")
        return
    if not mp4.exists():
        raise SystemExit(f"{mp4} not found: run tools/render.py {vdir.relative_to(ROOT)} --final first")
    creds = Credentials()
    if creds.missing():
        raise SystemExit(f"Missing YouTube credentials: {', '.join(creds.missing())} (see README, 'Publishing to YouTube')")

    print(f"Uploading {mp4.name} as {body['status']['privacyStatus']}: {body['snippet']['title']}", flush=True)
    video = upload_video(creds, mp4, body)
    vid = video["id"]
    url = f"https://youtu.be/{vid}"
    srt = vdir / "out" / f"{slug}.srt"
    yt = settings().get("youtube", {})
    caps = upload_captions(creds, vid, srt, yt.get("language", "en")) if srt.exists() else "no .srt"
    playlist = add_to_playlist(creds, vid, yt["playlist_id"]) if yt.get("playlist_id") else "none"
    rec = {
        "video_id": vid,
        "url": url,
        "studio": f"https://studio.youtube.com/video/{vid}/edit",
        "title": video["snippet"]["title"],
        "privacy_requested": body["status"]["privacyStatus"],
        "privacy_now": video.get("status", {}).get("privacyStatus"),
        "uploaded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "captions": caps,
        "playlist": playlist,
    }
    record.write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(rec, indent=2))
    if rec["privacy_now"] == "private" and rec["privacy_requested"] != "private":
        print("YouTube kept the video private: uploads from unaudited API projects are private until the project "
              "passes YouTube's API audit. Change visibility in YouTube Studio.")


def cmd_status(args) -> None:
    rec = json.loads((args.video_dir / "youtube.json").read_text())
    creds = Credentials()
    r = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=creds.headers(), timeout=60,
                     params={"part": "status,processingDetails", "id": rec["video_id"]}).json()
    print(json.dumps(r.get("items", [{}])[0], indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auth")
    a.add_argument("--local", action="store_true", help="browser sign-in on this computer (Desktop OAuth client)")
    sub.add_parser("check")
    u = sub.add_parser("upload")
    u.add_argument("video_dir", type=Path)
    u.add_argument("--privacy", choices=["private", "unlisted", "public"])
    u.add_argument("--dry-run", action="store_true", help="print the metadata without uploading")
    u.add_argument("--force", action="store_true", help="upload even if youtube.json already exists")
    s = sub.add_parser("status")
    s.add_argument("video_dir", type=Path)
    args = ap.parse_args()

    if args.cmd == "auth":
        auth_local() if args.local else auth_device()
    elif args.cmd == "check":
        missing = Credentials().missing()
        print("YouTube credentials: ok" if not missing else f"YouTube credentials missing: {', '.join(missing)}")
        sys.exit(1 if missing else 0)
    elif args.cmd == "upload":
        cmd_upload(args)
    elif args.cmd == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
