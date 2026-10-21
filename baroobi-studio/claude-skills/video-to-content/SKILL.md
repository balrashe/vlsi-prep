---
name: video-to-content
description: A video in, emails and social posts out, written in your voice. Also known as video-to-written-content. Output text/assets. Use when the user drops in a video and asks for the "Video to Written Content" style or /video-to-content.
---

# Video to Written Content

Style copied from @iamajene's AI Editing Pack, adapted to the user's brand. Spec status: **TOOL (no visual spec)**.
Reference measurements: `~/editing-refs/ajene/DesQj6ro0HP/STYLE.md`. If the status says a reference is needed, ask the user for 2-3 reels in this style, study them (frames every 0.5 s with ffmpeg, measure positions, sizes, colours, pacing) and update this file before the first real edit.

## Before the first edit
1. Check `~/.claude/skills/reel-kit/brand.local.json` (filled on 2026-10-21; ask which Drive folder holds the raw files if it still says "to confirm"). If it is missing, interview the user **one question at a time**: brand colours, fonts, how they film (phone or camera, framing, vertical or horizontal), where their raw files and B-roll live. Save the answers to `brand.local.json` (same keys as `brand.json`).
2. Ask for 2 or 3 reference videos of this style and adapt the spec below to them.
3. First time on a machine: run `~/.claude/skills/reel-kit/setup.sh` (ffmpeg, yt-dlp, local Whisper).

## Workflow (every time)
1. **Cut**: `~/.claude/skills/reel-kit/.venv/bin/python -I ~/.claude/skills/reel-kit/cut.py <raw> <work>` gives `cut.mp4`, `words.json` (word timings on the cut) and `edl.json`.
2. **Plan**: read `words.json`, list the beats (what is on screen when), and confirm anything factual. Never invent numbers, quotes or UI.
3. **Build**: Produce the outputs described below.
4. **Preview**: `~/.claude/skills/reel-kit/preview.sh <project>` renders a draft and a contact sheet. Show the user the preview and the sheet.
5. **Notes**: take the user's notes in plain English, change only what they asked, preview again.
6. **Final**: render only after the user explicitly approves: `~/.claude/skills/reel-kit/final.sh <project> <out.mp4> [fps]`.

## Shared look
- Text outputs: plain, direct, in the user voice. No em dashes.

## This style
- Transcribe (cut.py writes words.json; or run faster-whisper directly), then write: 1 email newsletter, 1 LinkedIn post, 1 X thread, 3 short captions. Use only claims that are in the video; flag anything that needs a source. Match the user's voice from 2-3 past posts they supply.
