"""Writes one SKILL.md per editing style. Specs marked MEASURED come from
~/editing-refs/ajene/DesQj6ro0HP/STYLE.md; the rest need a reference video before they are trusted."""
import os, textwrap

OUT = os.path.dirname(os.path.abspath(__file__))
KIT = "~/.claude/skills/reel-kit"

SHARED_LOOK = """- **Brand first**: `brand.local.json` holds the user's brand from the interview (2026-10-21): his orange `#e08a3a` kept, baroobi's own reel fonts (Montserrat Bold captions, one word at a time, ~64 px; white rounded title box radius 18 with black Montserrat Bold; Montserrat Black card names), iPhone selfie vertical footage, raw files on Google Drive. His layouts and motion stay; colours and type come from the brand file.
- Captions: white `#ffffff` sentence case, Inter 600 (his look: SF Pro / Inter family), 1-3 words per phrase, hard on and hard off (no fade), soft shadow, no box. Lowercase run about 40-52 px tall on 1080x1920. `lib.phrases()` + `lib.caption_html()` do this.
- Accent word: one word per phrase in italic serif (Instrument Serif Italic) in the accent colour, about 1.15x the caption size.
- Hook title: line 1 white bold sans with soft shadow, line 2 black text in a solid white box (no radius, ~24 px side padding), top of frame (y ~107-400).
- Accent colour: brand accent (his: `#e08a3a`)."""

SKILLS = {
 # name: (title, aspect, status, his description, layout spec, template)
 "business-reels": ("Business Reels", "9:16", "MEASURED (1 s of output in DesQj6ro0HP, t=10.5-11.1)",
  "Full screen, split screen and full-screen animation, switching on every cut. Also known as business-short-form-reels.",
  """- Talking head full frame, hook title box at the top (line 1 white bold ~78 px tall, line 2 black in white box).
- Fanned phone cards: 6-7 vertical screenshots (rounded ~24 px, white 3-4 px border, drop shadow) in an arc around and in front of the speaker, slight 3D yaw/tilt, overlapping, y ~530-1560.
- One-word caption, big white bold (~64 px tall) over the cards.
- Layout switches on every cut between: full-frame face, split (B-roll top / face bottom), full-screen animation.
- Not measurable from the reference: how often each layout appears, card entry motion. Ask for a reference reel.""", None),
 "personal-reels": ("Personal Reels", "9:16", "MEASURED (t=7.5-8.4)",
  "Fast cuts, your own B-roll, one-word captions. Also known as personal-short-form-reels.",
  """- Split screen: top half your own B-roll (y 0-950), bottom half your face (y 960-1920), thin dark divider ~10 px `#100c09`.
- One word on screen at a time, centred on the divider (y ~919-974), bold sans; numbers/prices in the accent colour, other words white.
- Price-tag sticker on product B-roll: white tag shape with hole dot, rotated about -5 degrees, black heavy sans ~70 px, soft shadow.
- B-roll comes from the user's library (use the broll-library skill to find shots).
- Not measurable: B-roll shot length, zoom punch-ins.""", None),
 "explainer-panel": ("Explainer Panel", "9:16", "NEEDS A REFERENCE VIDEO (not shown in DesQj6ro0HP)",
  "You in a panel at the bottom, animated explanations on top.",
  """- Working layout until a reference is supplied: animated explanation canvas top ~55%, speaker in a rounded panel bottom ~45%, captions on the seam (shared caption style).
- One animated diagram or card per idea; it changes when the idea changes in the transcript.""", None),
 "glass-explainer": ("Glass Explainer", "9:16", "NEEDS A REFERENCE VIDEO",
  "The panel edit with glass cards, counters and drawn graphs.",
  """- Same layout as explainer-panel, but the top canvas uses frosted glass cards (backdrop blur, 1 px light border, soft shadow), number counters that count up on the spoken number, and line/bar graphs that draw on (SVG stroke-dashoffset).""", None),
 "visual-essay": ("Visual Essay", "9:16", "NEEDS A REFERENCE VIDEO",
  "Black and orange, you cut out, the evidence shown above you.",
  """- Black background, accent orange. Speaker matted (background removed, `npx hyperframes remove-background`) in the lower half. Evidence (screenshots, headlines, documents) above the speaker, one per claim, with the key phrase highlighted in orange.""", None),
 "split-reel": ("Split Reel", "9:16", "NEEDS A REFERENCE VIDEO",
  "Your face on top, diagram animations underneath.",
  """- Face top half, diagram animation bottom half, caption on the seam. Diagrams are built in HTML/SVG and step forward on each spoken step.""", None),
 "broll-stacked-text": ("B-roll and Stacked Text", "9:16", "NEEDS A REFERENCE VIDEO",
  "Tight cut, B-roll, captions with stacked key phrases.",
  """- Tight jump cut, B-roll cutaways, normal 1-3 word captions plus key phrases that stack (each new key phrase adds a line under the previous ones until the idea ends).""", None),
 "fitted-captions": ("Fitted Captions", "9:16", "NEEDS A REFERENCE VIDEO",
  "One big accent word with the rest fitted around it.",
  """- Per phrase: one accent word set very large, the remaining words sized so the block is a fitted rectangle around it (justified lines, different sizes per line).""", None),
 "image-cluster": ("Image Cluster", "9:16", "NEEDS A REFERENCE VIDEO",
  "Clusters of images above your head, small quiet captions.",
  """- 3-6 images arranged as a loose cluster above the speaker's head, refreshed per idea. Captions smaller than the shared style (about 0.7x), low contrast-safe placement.""", None),
 "youtube-clips": ("YouTube Clips", "9:16", "MEASURED (t=14.0-16.0)",
  "A long video in, ranked vertical clips out.",
  """- Input: a long horizontal video. Find the 3-10 strongest standalone moments (hook in the first 3 s, complete thought, under 60 s), rank them with a one-line reason each, cut each to 9:16.
- Layout: top/bottom split. Top = animated graphic on black with an accent radial glow (example: 3x3 grid of grey avatar circles, centre one in the accent colour, glowing). Bottom = the speaker, centre-cropped.
- One-word white bold caption on the bottom edge of the top panel (y ~1028-1063).""", None),
 "cutout-backdrop": ("Cut-out Backdrop", "9:16", "NEEDS A REFERENCE VIDEO",
  "You cut out over full-screen images that change with every idea.",
  """- Speaker matted (remove-background) over a full-screen image that changes on every new idea; hard cut between images.""", None),
 "cutout-grid": ("Cut-out Grid", "9:16", "NEEDS A REFERENCE VIDEO",
  "You in the centre of four images that change together.",
  """- 2x2 image grid filling the frame, speaker matted in the centre over the seam; all four images change together on each idea.""", None),
 "depth-ui-reel": ("Depth UI", "9:16", "MEASURED (t=2.0-3.0)",
  "You full frame, real interfaces and screens behind your head, chest captions.",
  """- Speaker full frame and matted (remove-background) so a real interface sits BEHIND the head: panel x 80-1000, y 150-948, radius ~24 px, dark UI (example: a YouTube channel page). The head and shoulders occlude the panel.
- Caption at chest height: y ~1156-1208, white semibold, one word or number per beat ("400,000", then "subscribers").
- UI card under the caption: dark rounded card (x 150-930, y 1272-1405, radius ~40, 1 px light border) with avatar, bold white name ~34 px, grey handle and stat, white pill button.
- Use real screenshots of the thing being discussed, never invented UI numbers.""", None),
 "ranking-format": ("Ranking Format", "9:16", "MEASURED (t=4.8-6.0), template built",
  "Tier-list reel: S to F table, cards drop in one at a time.",
  """- Talking head full frame.
- Title: accent-colour italic heavy caps (Montserrat ExtraBold Italic), 2 lines centred, y ~194-310, soft dark shadow.
- Tier table x 157-925, y 997-1503: 7 rows S A B C D E F, 68 px rows with 4 px black gaps and border. Label column 72 px: S `#f3707e`, A `#f6bb7f`, B `#fdff82`, C `#86ff84`, D `#84bff9`, E `#7e77f9`, F `#f167f8`, bold black letter. Track `#1b1d1c`.
- Each item appears big over the table (x 252-829, y 1087-1413, white 2 px border, logo + heavy condensed yellow name) when it is named, then shrinks into its row (108x64 slot). The shrink is inferred; the reference cut before it.
- Caption sits just above the table (y ~934-973).""", "templates/ranking.py"),
 "educational-youtube": ("Educational YouTube", "16:9", "NEEDS A REFERENCE VIDEO",
  "Raw long-form lesson into a YouTube edit: overlays, split screen and explainer animations. Also known as educational-youtube-editor.",
  """- 1920x1080. Tight cut (cut.py --wide --gap 0.35 for long form), chapter title cards, lower-third overlays for terms, split screen (screen recording left, speaker right) for demos, explainer animations for concepts.""", None),
 "split-screen-lesson": ("Split-Screen Lesson", "16:9", "NEEDS A REFERENCE VIDEO",
  "Your notes document on the left, you on the right.",
  """- 1920x1080: lesson document left (~60%), speaker right (~40%). The document scrolls and highlights the line being spoken (pairs with lesson-document).""", None),
 "coaching-call-clips": ("Coaching Call Clips", "16:9", "PARTLY MEASURED (t=13.0-14.0 shows a 9:16 title-box output after /coaching-call-clips)",
  "A recorded call in, ranked clips out, graphics beside you.",
  """- Input: a recorded call. Find and rank the strongest standalone answers (one-line reason each), cut each clip, speaker on one side with supporting graphics beside them.
- Measured output frame: clean talking head, mic in shot, title box at the top (y 107-260: line 1 white bold, line 2 black in white box), 2-3 word captions low at chest (y ~1430-1480) with one accent serif word.""", None),
 "lesson-document": ("Lesson Document", "16:9", "NEEDS A REFERENCE VIDEO",
  "The on-screen teaching document you scroll through in a split-screen lesson.",
  """- Builds the document itself as an HTML page (headings, numbered points, code or quotes) from the transcript or notes, with scroll positions and highlight timings that split-screen-lesson consumes.""", None),
 "broll-library": ("B-roll Library", "tool", "TOOL (no visual spec)",
  "Index your own footage once, then search it in plain English and match it to a script. Also known as personal-broll-library.",
  """- Index: for every clip in the user's B-roll folder, extract 3 frames (10%, 50%, 90%), describe them (what, where, motion, framing, colours) and transcribe any speech; store one JSON line per clip in `<broll folder>/.broll-index.jsonl` with path, duration and description.
- Search: plain-English query, match against descriptions, return the top 5 with path, timecode and thumbnail.
- Script match: for each script line, propose the best clip and in/out points. Never reuse the same shot twice in one reel unless asked.""", None),
 "video-to-content": ("Video to Written Content", "tool", "TOOL (no visual spec)",
  "A video in, emails and social posts out, written in your voice. Also known as video-to-written-content.",
  """- Transcribe (cut.py writes words.json; or run faster-whisper directly), then write: 1 email newsletter, 1 LinkedIn post, 1 X thread, 3 short captions. Use only claims that are in the video; flag anything that needs a source. Match the user's voice from 2-3 past posts they supply.""", None),
}

for name, (title, aspect, status, desc, spec, tmpl) in SKILLS.items():
    visual = aspect != "tool"
    wide = aspect == "16:9"
    tmpl_txt = (f"`python {KIT}/{tmpl} spec.json <project>` builds the composition; read the docstring at the top of that file for the spec format."
                if tmpl else "No prebuilt template yet. Build the HyperFrames composition in `<project>/index.html` with `lib.py` (`lib.shell`, `lib.font_css`, `lib.phrases`, `lib.caption_html`, `lib.CAPTION_JS`) following the layout spec below, and the `hyperframes-core` skill for media and timing rules. If this layout is used twice, turn it into `templates/<name>.py` like `templates/ranking.py`.")
    body = f"""---
name: {name}
description: {desc} Output {aspect if visual else 'text/assets'}. Use when the user drops in a video and asks for the "{title}" style or /{name}.
---

# {title}

Style copied from @iamajene's AI Editing Pack, adapted to the user's brand. Spec status: **{status}**.
Reference measurements: `~/editing-refs/ajene/DesQj6ro0HP/STYLE.md`. If the status says a reference is needed, ask the user for 2-3 reels in this style, study them (frames every 0.5 s with ffmpeg, measure positions, sizes, colours, pacing) and update this file before the first real edit.

## Before the first edit
1. Check `{KIT}/brand.local.json` (filled on 2026-10-21; ask which Drive folder holds the raw files if it still says "to confirm"). If it is missing, interview the user **one question at a time**: brand colours, fonts, how they film (phone or camera, framing, vertical or horizontal), where their raw files and B-roll live. Save the answers to `brand.local.json` (same keys as `brand.json`).
2. Ask for 2 or 3 reference videos of this style and adapt the spec below to them.
3. First time on a machine: run `{KIT}/setup.sh` (ffmpeg, yt-dlp, local Whisper).

## Workflow (every time)
1. **Cut**: `{KIT}/.venv/bin/python -I {KIT}/cut.py <raw> <work>{' --wide' if wide else ''}` gives `cut.mp4`, `words.json` (word timings on the cut) and `edl.json`.
2. **Plan**: read `words.json`, list the beats (what is on screen when), and confirm anything factual. Never invent numbers, quotes or UI.
3. **Build**: {tmpl_txt if visual else 'Produce the outputs described below.'}
4. **Preview**: `{KIT}/preview.sh <project>` renders a draft and a contact sheet. Show the user the preview and the sheet.
5. **Notes**: take the user's notes in plain English, change only what they asked, preview again.
6. **Final**: render only after the user explicitly approves: `{KIT}/final.sh <project> <out.mp4> [fps]`.

## Shared look
{SHARED_LOOK if visual else '- Text outputs: plain, direct, in the user voice. No em dashes.'}

## This style
{spec}
"""
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "SKILL.md"), "w").write(body)
print(len(SKILLS), "skills written")
