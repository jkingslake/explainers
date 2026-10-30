"""Text-to-speech with an on-disk cache. Engine and voice come from explainer.toml.

speak(text) -> Clip(path, duration). Identical text + voice settings are only ever
synthesised once, so re-rendering a scene after a layout fix costs nothing.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import CACHE_DIR, settings

WORDS_PER_SECOND = 2.6  # ~155 wpm, used by the "silent" engine


@dataclass
class Clip:
    path: Path | None  # None for the silent engine
    duration: float


def speech_text(text: str) -> str:
    """Apply [pronunciations] from explainer.toml (subtitles keep the original)."""
    for written, spoken in settings().get("pronunciations", {}).items():
        text = re.sub(rf"\b{re.escape(written)}\b", spoken, text)
    return text


def speak(text: str) -> Clip:
    voice = settings()["voice"]
    engine = os.environ.get("EXPLAINER_TTS", voice["engine"])
    spoken = speech_text(" ".join(text.split()))
    if engine == "silent":
        return Clip(None, max(1.0, len(spoken.split()) / WORDS_PER_SECOND))

    key = json.dumps([engine, spoken, {k: v for k, v in voice.items() if k != "engine"}], sort_keys=True)
    digest = hashlib.sha1(key.encode()).hexdigest()[:16]
    ext = "wav" if engine == "kokoro" else "mp3"
    path = CACHE_DIR / "tts" / f"{digest}.{ext}"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.part.{ext}")
        {"kokoro": _kokoro, "elevenlabs": _elevenlabs, "openai": _openai}[engine](spoken, voice, tmp)
        tmp.replace(path)  # atomic: safe with parallel renders
    return Clip(path, _duration(path))


# ---------------------------------------------------------------- engines
_kokoro_model = None
_kokoro_lock = threading.Lock()


def _kokoro(text: str, voice: dict, out: Path) -> None:
    global _kokoro_model
    import soundfile as sf
    from kokoro_onnx import Kokoro

    with _kokoro_lock:
        if _kokoro_model is None:
            d = CACHE_DIR / "kokoro"
            if not (d / "kokoro-v1.0.onnx").exists():
                raise RuntimeError("Kokoro model missing: run `bash scripts/setup.sh`")
            _kokoro_model = Kokoro(str(d / "kokoro-v1.0.onnx"), str(d / "voices-v1.0.bin"))
        samples, rate = _kokoro_model.create(
            text, voice=voice.get("kokoro_voice", "am_michael"), speed=float(voice.get("speed", 1.0)), lang="en-us"
        )
    sf.write(out, samples, rate, format="WAV")


def _elevenlabs(text: str, voice: dict, out: Path) -> None:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key or not voice.get("elevenlabs_voice_id"):
        raise RuntimeError("ElevenLabs needs ELEVENLABS_API_KEY and voice.elevenlabs_voice_id in explainer.toml")
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice['elevenlabs_voice_id']}",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": key},
        json={
            "text": text,
            "model_id": voice.get("elevenlabs_model", "eleven_multilingual_v2"),
            "voice_settings": {"speed": float(voice.get("speed", 1.0))},
        },
        timeout=300,
    )
    r.raise_for_status()
    out.write_bytes(r.content)


def _openai(text: str, voice: dict, out: Path) -> None:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OpenAI TTS needs OPENAI_API_KEY")
    r = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": voice.get("openai_model", "gpt-4o-mini-tts"),
            "voice": voice.get("openai_voice", "onyx"),
            "input": text,
            "response_format": "mp3",
            "speed": float(voice.get("speed", 1.0)),
        },
        timeout=300,
    )
    r.raise_for_status()
    out.write_bytes(r.content)


def _duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(out.stdout.strip())
