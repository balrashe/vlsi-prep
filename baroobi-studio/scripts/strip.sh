#!/usr/bin/env bash
# One frame per beat (at 80% of the beat) tiled into a strip for review. Usage: strip.sh <slug> <out.jpg>
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; s="$1"; out="$2"; tmp="$(mktemp -d)"
ts=$(python3 -c "import json;d=json.load(open('$root/projects/$s/work/timing.json'));print(' '.join(str(round(x['start']+0.8*(x['end']-x['start']),2)) for x in d['steps']))")
i=0; args=()
for t in $ts; do ffmpeg -v error -y -ss "$t" -i "$root/renders/$s-v1.mp4" -frames:v 1 -vf scale=270:-1 "$tmp/$i.jpg"; args+=(-i "$tmp/$i.jpg"); i=$((i+1)); done
ffmpeg -v error -y "${args[@]}" -filter_complex "hstack=$i" "$out"; rm -rf "$tmp"
