# BUILD PROMPT — Tech UGC Starter Guide

Paste this whole file into Claude Code as your first message.

---

## Task

Build a 9-page print-ready guide as a **single self-contained HTML file** named `guide.html`, exported to PDF at US Letter. All copy is locked in `COPY.md`. Set it, do not rewrite it. Fix typos only.

## Do this first, before writing any code

1. Read `skills/apple-design/SKILL.md` and `skills/frontend-design/SKILL.md` in full.
2. Read `COPY.md` in full.
3. Write a short design plan: palette as named hex values, the two or three typefaces with their roles, a layout concept, and the one signature element. Check it against the constraints below. Only then write code.

## Design direction

This is fixed. Do not substitute your own direction.

**Mode:** dark. The audience reads on a phone at night, and the embedded screenshots are dark UI. A light document would fight them.

**Palette** (adjust values slightly for contrast, do not change the roles):
- `--ink` #0B0D10 — page background
- `--raised` #14181E — cards, boxes
- `--line` #222B36 — hairlines and dividers
- `--text` #F2F5F8 — primary text
- `--muted` #7F8A99 — captions, labels, folios
- `--accent` #2D6CFF — structural accent, labels, rules, one per page maximum
- `--money` #F4B942 — reserved exclusively for dollar figures and view counts. Nothing else may use this colour.

**Typography:**
- Display: a heavy grotesque with tight negative tracking. First choice Archivo at 800/900. Alternatives: Archivo Expanded, General Sans, Söhne Breit.
- Body: a humanist sans with real character. First choice Instrument Sans. Do not use Inter.
- Utility: a monospace for eyebrows, folios, ladder values, and captions. First choice JetBrains Mono.
- Load via Google Fonts with a solid local fallback stack. The PDF must still read correctly if fonts fail.

**Signature element:** the view-to-payout ladder on page 3. This is the one thing readers will screenshot and repost. Spend your effort here. It should feel engineered, not decorative. Everything else on the page stays quiet.

## Print spec

- `@page { size: letter; margin: 0; }`
- Each page is a `<section class="page">` at 816 × 1056px, `break-after: page`.
- Nothing may overflow or split across a page break. Verify every page individually.
- Footer on every page: page number and `@baroobi.inc`, in the mono face, muted colour.
- Screen view stacks the pages vertically with a gap and a subtle border so it is reviewable in a browser. Print view removes both.

## Assets

Three image files sit in `assets/`. Reference them by these exact names. If a file is missing, render a clearly labelled placeholder box at the correct aspect ratio, never a stock image.

- `assets/views-grid.png` — page 2. Grid of video thumbnails with view counts from a new account. This is the proof that followers do not matter. Give it real space, at least a third of the page.
- `assets/payments.png` — page 7. Payment receipts. Place as supplied.
- `assets/discord.png` — page 9, optional. If absent, omit the block entirely rather than leaving a gap.

## Hard constraints

- **No purple anywhere.** A direct competitor in this niche owns purple. This is the one non-negotiable colour rule.
- No emoji.
- No stock icon sets, no Font Awesome, no generic line-icon rows.
- No gradient mesh, no glow, no glassmorphism, no drop shadows on text.
- No "big number with a small label plus supporting stats plus gradient accent" hero. That is the template answer.
- No decorative numbering unless the content is genuinely sequential. Page 6 is a real sequence, so numbering is correct there. Page 4 is a set of four options, so it is not.
- Every page must survive the question "would this look identical if the subject were project management software?" If yes, redesign it.

## Verification loop

Do not stop at first render.

1. Build it.
2. Render and screenshot all 9 pages.
3. Critique your own output against this brief in writing. Name three specific weaknesses.
4. Fix them.
5. Re-render, re-screenshot, confirm no page overflows and no orphaned headings.
6. Export `guide.pdf` and confirm it is 9 pages.

Deliver `guide.html`, `guide.pdf`, and your written critique.
