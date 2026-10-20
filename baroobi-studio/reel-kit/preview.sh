#!/usr/bin/env bash
# Draft render + contact sheet for review. Usage: preview.sh <project_dir>
set -euo pipefail
p="$(cd "$1" && pwd)"; cd "$p"
npx --yes hyperframes@0.8.172 check > check.log 2>&1 || { grep -E "✗" check.log | head -8; echo "check found issues (above); rendering the preview anyway"; }
npx --yes hyperframes@0.8.172 render -q draft -o "$p/preview.mp4" --quiet
ffmpeg -v error -y -i "$p/preview.mp4" -vf "fps=1,scale=216:-1,tile=6x5" -frames:v 1 "$p/preview-sheet.jpg"
echo "preview -> $p/preview.mp4  sheet -> $p/preview-sheet.jpg"
