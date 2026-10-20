---
name: business-reels
description: Full screen, split screen and full-screen animation, switching on every cut. Also known as business-short-form-reels. Output 9:16. Use when the user drops in a video and asks for the "Business Reels" style or /business-reels.
---

# Business Reels

Style copied from @iamajene's AI Editing Pack, adapted to the user's brand. Spec status: **MEASURED (1 s of output in DesQj6ro0HP, t=10.5-11.1)**.
Reference measurements: `~/editing-refs/ajene/DesQj6ro0HP/STYLE.md`. If the status says a reference is needed, ask the user for 2-3 reels in this style, study them (frames every 0.5 s with ffmpeg, measure positions, sizes, colours, pacing) and update this file before the first real edit.

## Before the first edit
1. Check `~/.claude/skills/reel-kit/brand.local.json`. If it is missing, interview the user **one question at a time**: brand colours, fonts, how they film (phone or camera, framing, vertical or horizontal), where their raw files and B-roll live. Save the answers to `brand.local.json` (same keys as `brand.json`).
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
- Captions: white `#ffffff` sentence case, Inter 600 (his look: SF Pro / Inter family), 1-3 words per phrase, hard on and hard off (no fade), soft shadow, no box. Lowercase run about 40-52 px tall on 1080x1920. `lib.phrases()` + `lib.caption_html()` do this.
- Accent word: one word per phrase in italic serif (Instrument Serif Italic) in the accent colour, about 1.15x the caption size.
- Hook title: line 1 white bold sans with soft shadow, line 2 black text in a solid white box (no radius, ~24 px side padding), top of frame (y ~107-400).
- Accent colour: brand accent (his: `#e08a3a`).

## This style
- Talking head full frame, hook title box at the top (line 1 white bold ~78 px tall, line 2 black in white box).
- Fanned phone cards: 6-7 vertical screenshots (rounded ~24 px, white 3-4 px border, drop shadow) in an arc around and in front of the speaker, slight 3D yaw/tilt, overlapping, y ~530-1560.
- One-word caption, big white bold (~64 px tall) over the cards.
- Layout switches on every cut between: full-frame face, split (B-roll top / face bottom), full-screen animation.
- Not measurable from the reference: how often each layout appears, card entry motion. Ask for a reference reel.
