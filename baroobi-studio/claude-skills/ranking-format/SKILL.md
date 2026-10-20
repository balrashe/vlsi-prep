---
name: ranking-format
description: Tier-list reel: S to F table, cards drop in one at a time. Output 9:16. Use when the user drops in a video and asks for the "Ranking Format" style or /ranking-format.
---

# Ranking Format

Style copied from @iamajene's AI Editing Pack, adapted to the user's brand. Spec status: **MEASURED (t=4.8-6.0), template built**.
Reference measurements: `~/editing-refs/ajene/DesQj6ro0HP/STYLE.md`. If the status says a reference is needed, ask the user for 2-3 reels in this style, study them (frames every 0.5 s with ffmpeg, measure positions, sizes, colours, pacing) and update this file before the first real edit.

## Before the first edit
1. Check `~/.claude/skills/reel-kit/brand.local.json`. If it is missing, interview the user **one question at a time**: brand colours, fonts, how they film (phone or camera, framing, vertical or horizontal), where their raw files and B-roll live. Save the answers to `brand.local.json` (same keys as `brand.json`).
2. Ask for 2 or 3 reference videos of this style and adapt the spec below to them.
3. First time on a machine: run `~/.claude/skills/reel-kit/setup.sh` (ffmpeg, yt-dlp, local Whisper).

## Workflow (every time)
1. **Cut**: `~/.claude/skills/reel-kit/.venv/bin/python -I ~/.claude/skills/reel-kit/cut.py <raw> <work>` gives `cut.mp4`, `words.json` (word timings on the cut) and `edl.json`.
2. **Plan**: read `words.json`, list the beats (what is on screen when), and confirm anything factual. Never invent numbers, quotes or UI.
3. **Build**: `python ~/.claude/skills/reel-kit/templates/ranking.py spec.json <project>` builds the composition; read the docstring at the top of that file for the spec format.
4. **Preview**: `~/.claude/skills/reel-kit/preview.sh <project>` renders a draft and a contact sheet. Show the user the preview and the sheet.
5. **Notes**: take the user's notes in plain English, change only what they asked, preview again.
6. **Final**: render only after the user explicitly approves: `~/.claude/skills/reel-kit/final.sh <project> <out.mp4> [fps]`.

## Shared look
- Captions: white `#ffffff` sentence case, Inter 600 (his look: SF Pro / Inter family), 1-3 words per phrase, hard on and hard off (no fade), soft shadow, no box. Lowercase run about 40-52 px tall on 1080x1920. `lib.phrases()` + `lib.caption_html()` do this.
- Accent word: one word per phrase in italic serif (Instrument Serif Italic) in the accent colour, about 1.15x the caption size.
- Hook title: line 1 white bold sans with soft shadow, line 2 black text in a solid white box (no radius, ~24 px side padding), top of frame (y ~107-400).
- Accent colour: brand accent (his: `#e08a3a`).

## This style
- Talking head full frame.
- Title: accent-colour italic heavy caps (Montserrat ExtraBold Italic), 2 lines centred, y ~194-310, soft dark shadow.
- Tier table x 157-925, y 997-1503: 7 rows S A B C D E F, 68 px rows with 4 px black gaps and border. Label column 72 px: S `#f3707e`, A `#f6bb7f`, B `#fdff82`, C `#86ff84`, D `#84bff9`, E `#7e77f9`, F `#f167f8`, bold black letter. Track `#1b1d1c`.
- Each item appears big over the table (x 252-829, y 1087-1413, white 2 px border, logo + heavy condensed yellow name) when it is named, then shrinks into its row (108x64 slot). The shrink is inferred; the reference cut before it.
- Caption sits just above the table (y ~934-973).
