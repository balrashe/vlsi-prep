---
name: broll-library
description: Index your own footage once, then search it in plain English and match it to a script. Also known as personal-broll-library. Output text/assets. Use when the user drops in a video and asks for the "B-roll Library" style or /broll-library.
---

# B-roll Library

Style copied from @iamajene's AI Editing Pack, adapted to the user's brand. Spec status: **TOOL (no visual spec)**.
Reference measurements: `~/editing-refs/ajene/DesQj6ro0HP/STYLE.md`. If the status says a reference is needed, ask the user for 2-3 reels in this style, study them (frames every 0.5 s with ffmpeg, measure positions, sizes, colours, pacing) and update this file before the first real edit.

## Before the first edit
1. Check `~/.claude/skills/reel-kit/brand.local.json`. If it is missing, interview the user **one question at a time**: brand colours, fonts, how they film (phone or camera, framing, vertical or horizontal), where their raw files and B-roll live. Save the answers to `brand.local.json` (same keys as `brand.json`).
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
- Index: for every clip in the user's B-roll folder, extract 3 frames (10%, 50%, 90%), describe them (what, where, motion, framing, colours) and transcribe any speech; store one JSON line per clip in `<broll folder>/.broll-index.jsonl` with path, duration and description.
- Search: plain-English query, match against descriptions, return the top 5 with path, timecode and thumbnail.
- Script match: for each script line, propose the best clip and in/out points. Never reuse the same shot twice in one reel unless asked.
