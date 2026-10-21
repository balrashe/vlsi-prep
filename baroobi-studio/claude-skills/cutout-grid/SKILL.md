---
name: cutout-grid
description: You in the centre of four images that change together. Output 9:16. Use when the user drops in a video and asks for the "Cut-out Grid" style or /cutout-grid.
---

# Cut-out Grid

Style copied from @iamajene's AI Editing Pack, adapted to the user's brand. Spec status: **NEEDS A REFERENCE VIDEO**.
Reference measurements: `~/editing-refs/ajene/DesQj6ro0HP/STYLE.md`. If the status says a reference is needed, ask the user for 2-3 reels in this style, study them (frames every 0.5 s with ffmpeg, measure positions, sizes, colours, pacing) and update this file before the first real edit.

## Before the first edit
1. Check `~/.claude/skills/reel-kit/brand.local.json` (filled on 2026-10-21; ask which Drive folder holds the raw files if it still says "to confirm"). If it is missing, interview the user **one question at a time**: brand colours, fonts, how they film (phone or camera, framing, vertical or horizontal), where their raw files and B-roll live. Save the answers to `brand.local.json` (same keys as `brand.json`).
2. Ask for 2 or 3 reference videos of this style and adapt the spec below to them.
3. First time on a machine: run `~/.claude/skills/reel-kit/setup.sh` (ffmpeg, yt-dlp, local Whisper).

## Workflow (every time)
1. **Cut**: `~/.claude/skills/reel-kit/.venv/bin/python -I ~/.claude/skills/reel-kit/cut.py <raw> <work>` gives `cut.mp4`, `words.json` (word timings on the cut) and `edl.json`.
2. **Plan**: read `words.json`, list the beats (what is on screen when), and confirm anything factual. Never invent numbers, quotes or UI.
3. **Build**: No prebuilt template yet. Build the HyperFrames composition in `<project>/index.html` with `lib.py` (`lib.shell`, `lib.font_css`, `lib.phrases`, `lib.caption_html`, `lib.CAPTION_JS`) following the layout spec below, and the `hyperframes-core` skill for media and timing rules. If this layout is used twice, turn it into `templates/<name>.py` like `templates/ranking.py`.
4. **Preview**: `~/.claude/skills/reel-kit/preview.sh <project>` renders a draft and a contact sheet. Show the user the preview and the sheet.
5. **Notes**: take the user's notes in plain English, change only what they asked, preview again.
6. **Final**: render only after the user explicitly approves: `~/.claude/skills/reel-kit/final.sh <project> <out.mp4> [fps]`.

## Shared look
- **Brand first**: `brand.local.json` holds the user's brand from the interview (2026-10-21): his orange `#e08a3a` kept, baroobi's own reel fonts (Montserrat Bold captions, one word at a time, ~64 px; white rounded title box radius 18 with black Montserrat Bold; Montserrat Black card names), iPhone selfie vertical footage, raw files on Google Drive. His layouts and motion stay; colours and type come from the brand file.
- Captions: white `#ffffff` sentence case, Inter 600 (his look: SF Pro / Inter family), 1-3 words per phrase, hard on and hard off (no fade), soft shadow, no box. Lowercase run about 40-52 px tall on 1080x1920. `lib.phrases()` + `lib.caption_html()` do this.
- Accent word: one word per phrase in italic serif (Instrument Serif Italic) in the accent colour, about 1.15x the caption size.
- Hook title: line 1 white bold sans with soft shadow, line 2 black text in a solid white box (no radius, ~24 px side padding), top of frame (y ~107-400).
- Accent colour: brand accent (his: `#e08a3a`).

## This style
- 2x2 image grid filling the frame, speaker matted in the centre over the seam; all four images change together on each idea.
