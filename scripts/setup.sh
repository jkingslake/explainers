#!/usr/bin/env bash
# One-time (per container) setup: system libraries, LaTeX, Python env and the
# Kokoro text-to-speech model. Safe to re-run; each step is skipped when done.
#
#   bash scripts/setup.sh          # full setup
#   bash scripts/setup.sh --check  # just report what's missing
set -euo pipefail
cd "$(dirname "$0")/.."

APT_PACKAGES=(
  ffmpeg pkg-config libcairo2-dev libpango1.0-dev   # manim rendering
  texlive-latex-base texlive-latex-recommended texlive-latex-extra
  texlive-fonts-recommended texlive-science cm-super dvisvgm   # MathTex
  fonts-cmu                                          # Computer Modern for Text()
  espeak-ng                                          # phonemizer for Kokoro TTS
  poppler-utils                                      # pdftotext / pdftoppm
)
MODEL_DIR=".cache/kokoro"
MODEL_URL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"

missing_apt() {
  local m=()
  for p in "${APT_PACKAGES[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || m+=("$p")
  done
  echo "${m[@]:-}"
}

if [[ "${1:-}" == "--check" ]]; then
  echo "missing apt packages: $(missing_apt)"
  [[ -x .venv/bin/manim ]] && echo "python env: ok" || echo "python env: missing"
  [[ -f "$MODEL_DIR/kokoro-v1.0.onnx" ]] && echo "kokoro model: ok" || echo "kokoro model: missing"
  exit 0
fi

if ! command -v apt-get >/dev/null 2>&1; then
  # e.g. macOS: install the system pieces yourself, then re-run for the Python env + model
  echo "No apt-get here. Install: ffmpeg cairo pango pkg-config espeak-ng poppler and a LaTeX"
  echo "distribution (macOS: brew install ffmpeg cairo pango pkg-config espeak-ng poppler;"
  echo "brew install --cask basictex). Continuing with the Python env and TTS model."
  MISSING=""
else
  MISSING=$(missing_apt)
fi
if [[ -n "$MISSING" ]]; then
  echo "==> apt: installing $MISSING"
  SUDO=""; [[ $EUID -ne 0 ]] && SUDO="sudo"
  $SUDO apt-get update -qq
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq --no-install-recommends $MISSING >/dev/null
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "==> installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> python env (uv sync)"
uv sync --quiet

mkdir -p "$MODEL_DIR"
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [[ ! -s "$MODEL_DIR/$f" ]]; then
    echo "==> downloading Kokoro TTS model: $f"
    curl -fsSL -o "$MODEL_DIR/$f.part" "$MODEL_URL/$f" && mv "$MODEL_DIR/$f.part" "$MODEL_DIR/$f"
  fi
done

echo "==> setup complete. Activate with: source .venv/bin/activate"
