---
name: video-breakdown
description: Scene-by-scene Video Breakdown Sheet for a baroobi reel - one private claude.ai artifact (dark shot list, mm:ss timestamps, stills from the render that enlarge on click, type badges, what was built, what he says, a YOUR DIRECTION box per scene, autosave, filters, Copy directions). Use whenever Baraa says "breakdown", "breakdown sheet", "scene by scene", "pull up the breakdown", "pull up that artifact", "show me the scenes", "/video-breakdown", or pastes directions in the form [0:10-0:19] Title (TYPE) → note. Also offer it after every new preview.
---

# Video Breakdown Sheet

Baraa approved this on the vibe-coded signs reel (Oct 21 2026): instead of describing an edit in chat, show it as a
shot list he can direct scene by scene. He fills the YOUR DIRECTION boxes, presses Copy directions, pastes the lines
back, and only those scenes change.

Kit (installed with the other skills): `~/.claude/skills/reel-kit/breakdown/`
- `build_breakdown.py`: video + scenes -> one self-contained `breakdown.html` (stills are base64 inside).
- `template.html`: the approved sheet. Do not restyle it; the look is signed off.

## Triggers and what to do

| He says | Do |
|---|---|
| "pull up the breakdown / that artifact / scene by scene" | Open the current video's sheet. Look up its URL on the Notion video page ("Breakdown sheet:") and call Artifact `open`. If none exists yet, build one (below). |
| A new preview is delivered | Build the sheet for it and send the link with the MP4, script and caption. |
| He pastes `[m:ss-m:ss] Title (TYPE) → note` lines | Change only those scenes (see Directions). |

"The current video" is the one being worked on in this conversation. If that is unclear, the latest preview sent.

## Build a sheet

1. **Scenes, from the edit itself** (not guessed from frames). Write `out/scenes.json`, one entry per visual beat:
   - `chapter`: HOOK, BODY, CTA (or the reel's own sections).
   - `a`, `b`: edited-timeline seconds, taken from the composition's segment/cue data (SEGS, cue sheet, phrase timings).
   - `title`: what the beat is, in a few words.
   - `type`: one of B-ROLL, HEADLINE, CARD, BOX REVEAL, STACK, CAPTION, TRANSITION, SFX, TALKING HEAD, SPLIT, OVERLAY, 3D.
   - `built`: what is on screen, factually (layout, card, animation, caption position). No selling, no em dashes.
   - `said`: his words in that span, verbatim (or leave it out and pass `--words`).
   - `at` (optional): the second to grab the still from; pick a frame where the beat is fully on screen.
   - The single intro SFX hit gets its own `SFX` row at 0:00 so he can direct its level.
2. **Build** from the render he will see (the preview or master, never the raw):
   ```bash
   ~/vlsi-prep/baroobi-studio/.venv/bin/python -I ~/.claude/skills/reel-kit/breakdown/build_breakdown.py \
     --video out/v1-preview.mp4 --scenes out/scenes.json --words src/words.json \
     --name "Day Trader skill · v1" --out out/breakdown.html
   ```
   No scene data at hand (an old MP4 from Drive): `--auto --transcribe` proposes cuts and fills in what he says;
   then rename the "Scene N" titles and write `built` for each before publishing.
3. **Look at it**: read a few stills from the file or render the page; check every timestamp lands on its beat.
4. **Publish** with the Artifact tool from the project `out/` folder (copy to the scratchpad if the tool refuses the
   path). First publish: icon `list`. A later version of the same video republishes to the same URL so his link
   keeps working. Keep `breakdown.html` next to the render too.
5. **Record it** (every time, without being asked):
   - Notion video page: a line `Breakdown sheet: <url> (vN)`.
   - Notion Status page under the video, and the memory notes (`baroobi-video-notes` MEMORY.md, one line:
     video -> breakdown URL), so "pull up that artifact" works in any later session.
6. Send the link. Do not re-render anything at this step.

## Directions coming back

1. Parse each pasted line: time range, title, type, note. Match it to the scene by range and title.
2. Change only those scenes. Everything else stays locked: same cut, captions, layout and sound.
3. Re-render only what changed where possible (frame ranges, audio-only remix), splice, master, then make a new
   preview.
4. Rebuild the sheet for the new version, republish to the same URL, update the `(vN)` in Notion.
5. Reply with what changed at each timestamp, one line per direction: `[0:00-0:00] Hit on the open (SFX): lowered to 0.22`.

## Rules

- Stills always come from the render being reviewed, so the sheet never shows something that will not post.
- `said` is verbatim. Misspeaks are flagged in the reply, not corrected in the sheet.
- The artifact is private by default. Never make it public; it shows his face and unreleased work.
- Never invent scene content or numbers; `built` describes only what is actually in the frames.
