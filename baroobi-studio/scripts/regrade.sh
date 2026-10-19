#!/bin/bash
# trial-reel re-grade: new hash, stripped metadata, ~1% shift in frame and audio timing
cd /home/user/vlsi-prep/baroobi-studio/renders
for s in "$@"; do
  ffmpeg -loglevel error -y -i $s-b-v1.mp4 \
    -vf "scale=trunc(iw*1.02/2)*2:trunc(ih*1.02/2)*2,crop=1080:1920,eq=saturation=0.98,setpts=PTS/1.01" \
    -af "atempo=1.01" -map_metadata -1 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart $s-v2.mp4
  echo "$s-v2.mp4 $(ffprobe -v error -show_entries format=duration -of csv=p=0 $s-v2.mp4)"
done
