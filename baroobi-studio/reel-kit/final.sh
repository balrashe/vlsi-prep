#!/usr/bin/env bash
# Final render, only after the preview is approved. Usage: final.sh <project_dir> <out.mp4> [fps]
set -euo pipefail
p="$(cd "$1" && pwd)"; out="$2"; fps="${3:-}"
cd "$p"; npx --yes hyperframes@0.8.172 check > check.log 2>&1 || { grep -E "✗" check.log | head -8; echo "check found issues (above): confirm they are intended before delivering"; }
npx --yes hyperframes@0.8.172 render -q delivery ${fps:+-f $fps} -o "$out" --quiet
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$out"
