#!/usr/bin/env bash
# One-time setup: ffmpeg, yt-dlp, a local Whisper (faster-whisper) in .venv. Safe to re-run.
set -euo pipefail
kit="$(cd "$(dirname "$0")" && pwd)"
command -v ffmpeg >/dev/null || { command -v brew >/dev/null && brew install ffmpeg || sudo apt-get install -y ffmpeg; }
command -v yt-dlp >/dev/null || { command -v brew >/dev/null && brew install yt-dlp || pip3 install --user yt-dlp; }
[ -x "$kit/.venv/bin/python" ] || python3 -m venv "$kit/.venv"
"$kit/.venv/bin/pip" install -q faster-whisper pillow
echo "reel-kit ready: python=$kit/.venv/bin/python"
