#!/usr/bin/env bash
# Pull a reference reel: video, transcript, 1fps keyframes, contact sheet. Usage: reference.sh <url> <slug>
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; d="$root/refs/$2"; mkdir -p "$d/frames"
yt-dlp -q -f "bv*+ba/b" --merge-output-format mp4 -o "$d/ref.%(ext)s" "$1"
ffmpeg -v error -y -i "$d/ref.mp4" -vf fps=1,scale=360:-1 "$d/frames/%03d.jpg"
ffmpeg -v error -y -i "$d/ref.mp4" -vf "select='gt(scene,0.3)',showinfo,scale=360:-1" -vsync vfr "$d/frames/cut_%03d.jpg" 2> "$d/cuts.log" || true
grep -o 'pts_time:[0-9.]*' "$d/cuts.log" | cut -d: -f2 > "$d/cuts.txt" || true
ffmpeg -v error -y -i "$d/ref.mp4" -vf "fps=1,scale=180:-1,tile=6x6" -frames:v 1 "$d/sheet.jpg"
"$root/.venv/bin/python" "$root/scripts/transcribe.py" "$d/ref.mp4" "$d/transcript.json"
echo "ref -> $d ($(wc -l < "$d/cuts.txt") hard cuts)"
