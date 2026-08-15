# Design plan — Tech UGC Starter Guide

Written before any code, per BUILD-PROMPT. Checked against the brief and against
`skills/frontend-design/SKILL.md` and `skills/apple-design/SKILL.md`.

## Subject, audience, job

Subject: getting paid to post short videos about AI tools. Audience: 18–28, phone-first,
no income from content yet, has seen ten of these guides. The document's single job: make
the reader understand that filming was never the hard part, and that placement is.

The subject's world is **rate cards, analytics readouts, and payout tiers** — the artifacts a
creator actually receives from a brand. That is where the visual language comes from. Not a
marketing brochure. A spec sheet you'd be sent when you get accepted.

## Color

Roles are fixed by the brief. Values adjusted only where contrast required it.

| Token | Value | Role |
|---|---|---|
| `--ink` | `#0B0D10` | page ground |
| `--raised` | `#14181E` | cards, boxes |
| `--line` | `#222B36` | hairlines, dividers |
| `--text` | `#F2F5F8` | primary text — 17.0:1 |
| `--muted` | `#7F8A99` | captions, labels, folios — 5.6:1 |
| `--accent` | `#2D6CFF` | structural: rules, ticks, fills |
| `--accent-tx` | `#4C82FF` | accent **text** only — 5.5:1 |
| `--money` | `#F4B942` | dollar figures and view counts, nothing else — 10.9:1 |

`#2D6CFF` measures 4.36:1 on `--ink`, under the 4.5 floor for small text. It stays exactly as
specified for non-text use (rules, ticks, chart fills); small accent *text* uses `--accent-tx`,
a two-step lift of the same hue. This is the "adjust slightly for contrast" the brief allows.

No purple, anywhere, at any opacity.

## Type

| Role | Face | Weights |
|---|---|---|
| Display | **Archivo** | 800 / 900, tight negative tracking |
| Body | **Instrument Sans** | 400 / 500 / 600 |
| Utility | **JetBrains Mono** | 400 / 500 / 700 |

All three embedded as base64 woff2 variable fonts (126KB total) with full local fallback
stacks. The brief asks for Google Fonts with a fallback so the PDF still reads if fonts fail;
embedding is strictly stronger — it is self-contained *and* cannot fail at print time.

Per apple-design §15, tracking is size-specific rather than one global value: display sizes take
negative tracking (`-0.038em` at 66px), body sits at `0`, and small mono labels take *positive*
tracking (`+0.18em`) because letterforms need air as they shrink. Leading moves inversely to
size — `0.94` on the cover, `1.62` on body copy. Hierarchy is built from weight + size + leading
as a set, not size alone.

## Layout

A **left index rail** runs down every interior page: a 52px column carrying the section number
and a vertical hairline with a tick at each content band. It is not decoration — it is the
document's spine, and it answers "where am I in the nine pages" on every spread. The text
column sits at 616px beside it.

Bands are separated by hairlines rather than boxes wherever possible, so the `--raised` surface
is reserved for things that are genuinely a distinct object: a callout, a spec card, the ladder.

**Structure encodes content, per frontend-design.** Numbering appears exactly once, on page 6,
because that page is the only real sequence in the document. The four video types (p4), the four
points (p2), the five mistakes (p5), the six questions (p8) and the three Discord points (p9)
are all *sets*, not sequences, so they get hairlines and labels instead of `01 / 02 / 03`.

## Signature — the payout ladder, page 3

A six-step staircase drawn as inline SVG, not a row of bars. The form is the argument: payouts
are *tiered*, so a step function is the literally correct chart, and each riser is the moment
your pay jumps. Treads carry the payout in gold, the axis carries the view tier in mono.

The vertical scale is square-root compressed so $80 stays visible next to $3,050, and the chart
says so on its own axis rather than quietly distorting. That note is the detail that makes it
read as an instrument rather than an illustration. `EXAMPLE ONLY` sits in the chart header.

Everything else on page 3 goes quiet: the math box is a three-row spec table, the callout is a
plain bordered block. The boldness is spent in one place.

## Cover

The brief bans the "big number with a small label plus supporting stats" hero, and the copy
requires three stats. Resolved by setting the stats as a **requirements table** — three rows,
mono label left, leader dots, value right in Archivo — instead of three big numbers in columns.
It carries the same information, reads as the entry requirements on a rate card, and is not the
banned pattern. Per the README, no date on the cover.

## The differentiation test

"Would this look identical if the subject were project management software?" No. The money color
is legal only on dollars and view counts, which makes the whole document scan as a financial
readout. The ladder is a payout instrument. The proof frames are labelled with account state
(`NEW ACCOUNT · 0 FOLLOWERS`). The cover's spec table lists followers and a phone as the
hardware requirements. None of that survives a transplant to another subject.

## What I revised after reviewing this plan against the brief

The first pass of this plan reached for a near-black ground with a single hot accent and
numbered markers throughout. That is precisely default (2) in the frontend-design calibration
list, and I had already shipped it once in the previous version of this guide. The brief pins
the palette, so the ground and accent stay — but the numbering went, the accent got demoted
from "colored words" to structural rules only, and the identity moved onto the instrument
motif, which is the part that actually comes from this subject.
