#!/usr/bin/env bash
# Voice in assets/voice/<slug>.(wav|m4a|mp3) -> Whisper + Rhubarb -> HyperFrames -> renders/<slug>-v<N>.mp4
# Usage: make_reel.sh <slug> [version]   (no voice file = silent animatic with estimated timing)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; slug="$1"; v="${2:-1}"
"$root/.venv/bin/python" -I "$root/scripts/build_video.py" "$slug"
cd "$root/projects/$slug"
npx --yes hyperframes@0.8.172 check
mode=$(python3 -c "import json;print(json.load(open('work/timing.json'))['mode'])")
out="$root/renders/$slug-$([[ $mode == voice ]] && echo "v$v" || echo animatic).mp4"
npx --yes hyperframes@0.8.172 render -o "$out" --quiet
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of compact "$out"
echo "-> $out"
