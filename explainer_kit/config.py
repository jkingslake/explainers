"""Loads explainer.toml (channel name, voice, video settings, mascot)."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / ".cache"


@lru_cache(maxsize=1)
def settings() -> dict:
    with open(REPO_ROOT / "explainer.toml", "rb") as f:
        return tomllib.load(f)


def channel_name() -> str:
    return settings()["channel"]["name"]
