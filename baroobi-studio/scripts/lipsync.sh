#!/usr/bin/env bash
# Rhubarb mouth cues (A-H + X) for a voiceover. Usage: lipsync.sh <voice.wav|m4a> <out.json> [script.txt]
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
wav="$(mktemp --suffix=.wav)"
ffmpeg -v error -y -i "$1" -ac 1 -ar 16000 "$wav"
extra=(); [[ $# -ge 3 ]] && extra=(--dialogFile "$3")
"$root/tools/rhubarb/rhubarb" -q -f json --extendedShapes GHX "${extra[@]}" "$wav" > "$2"
rm -f "$wav"; echo "cues -> $2"
