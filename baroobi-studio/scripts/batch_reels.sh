#!/usr/bin/env bash
# Voice + render a list of reels back to back with the cloned voice. Usage: batch_reels.sh slug [slug...]
set -uo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
for s in "$@"; do
  echo "=== $s: voice"
  "$root/.venv/bin/python" -I "$root/scripts/clone_voice.py" speak "$s" || { echo "FAIL voice $s"; continue; }
  rm -rf "$root/projects/$s/work"
  echo "=== $s: render"
  "$root/scripts/make_reel.sh" "$s" 1 2>&1 | grep -v "GL Driver" | grep -E "voice,|not heard|error\(s\)|✗|format|^->" || echo "FAIL render $s"
done
echo "BATCH DONE"
