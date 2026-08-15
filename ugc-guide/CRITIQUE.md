# Self-critique — round 1

Rendered all 9 pages, screenshotted, and read them against BUILD-PROMPT.md and the two
skills. Three specific weaknesses, in severity order, and what I did about each.

---

## 1. The accent broke its own budget — badly

The brief says `--accent` is for "structural accent, labels, rules, **one per page maximum**."
Counting page 5 as built: blue eyebrow, blue `GRABS THE EAR`, blue `GRABS THE EYE`, blue callout
border, blue tag border, blue tag text, blue scrubber tick, and **five blue squares** down the
mistakes list. Eight or nine accent moments on one page. Page 4 was as bad: four blue "leads
with" labels plus four blue spec keys.

The five squares were the worst of it. A square in front of a list item is not information —
the hairline rows already separate the items — so it was decoration, and a row of small repeated
blue marks is the same visual move as the generic icon row the brief bans. The same squares
appeared again on page 9.

**Fixed.** Deleted both marker sets outright. Demoted the page-5 pair labels and the page-4 spec
keys to `--muted`. The rule I settled on and applied everywhere: the eyebrow and the scrubber
tick are the persistent *system*, and beyond those each page gets exactly one accent moment —
the callout rule on 2, the chart on 3, the "leads with" labels on 4, the callout on 5, the step
numbers on 6, the move card on 7, nothing on 8, the CTA frame on 9.

## 2. Page 5's vertical rhythm was arbitrary

I had four equal flexible spacers absorbing the leftover height, which produced four identical
~55px gaps. That meant the gap between the lede and the hook pair was exactly the gap between
the callout and the format box — spacing that claims those relationships are equivalent when
they are not. Apple-design §16 puts it directly: every spacing value should be one you can
defend. I could not defend these; they were just leftover space divided by four.

**Fixed.** Replaced them with a real scale — 24px between related blocks — and left exactly two
flexible breaks, both at genuine section boundaries: after the lede, and before the closing
failure list. Two deliberate breaks instead of four accidental ones.

## 3. Headline rags were left to chance

Page 2 broke as "Brands will pay you to post / about their app. That's the / whole thing." —
`That's the` dangling at the end of a line, splitting the second sentence across the rag for no
reason. Page 9 had a similar loose last line. On a document whose whole personality is carried
by the display face, letting the biggest type in it break wherever the box happens to end is
the one place carelessness shows most.

**Fixed.** `text-wrap: balance` on the display face, the page headlines, the question headings
and the card titles, so line lengths even out and breaks land closer to sense.

---

## Also changed, from the first render

**The rail was decoration.** It carried the section number — which the eyebrow directly beside
it already said, in words. Two elements doing one job. Rather than delete it, I rebuilt it as a
**nine-tick progress scrubber** with the current page's tick filled: it now reports position in
the document at a glance, which nothing else does, and a scrubber is the right instrument to
borrow for a guide about short-form video. Slimmer too, which returned 32px of column width and
resolved the page-3 overflow.

**The cover's slack was split.** Equal voids above and below the headline read as an accident;
all the slack now pools above it, and the subhead is measured to break on its own sentence
rather than mid-clause.

---

## Known and deliberate

- **`views-grid.png` and `payments.png` are placeholders.** Labelled boxes at the reserved size,
  per the brief. The page-2 proof band is a fixed 356px — over a third of the page — so dropping
  the real file in changes nothing about the layout.
- **The page-9 Discord screenshot block is omitted entirely**, not left as a gap, per the brief's
  instruction for that optional asset.
- **Fonts are embedded, not linked.** The brief asked for Google Fonts plus a fallback stack so
  the PDF still reads if fonts fail. Embedding as base64 woff2 satisfies the same goal more
  strongly — the file is self-contained and the faces cannot fail to load at print time. Full
  fallback stacks are declared anyway.
- **`--accent` `#2D6CFF` measures 4.36:1 on `--ink`**, below the 4.5 floor for small text. It is
  unchanged for rules, ticks and chart fills; small accent *text* uses `#4C82FF`, the same hue
  lifted two steps, at 5.5:1.
- **The "30 days" cover stat is the document's only unbacked claim.** Flagged in the handoff
  README, kept because the copy is locked. Cutting it and running two requirements is a
  one-line change.

---

# Self-critique — round 2

Re-rendered after the three fixes. One more real problem, found by looking rather than by
measuring — the overflow checks were all green while this was happening.

## 4. Omitting the optional asset produced exactly the gap it was meant to prevent

The brief says of `discord.png`: "If absent, omit the block entirely rather than leaving a gap."
I omitted the block, and page 9 came back with roughly 600px of nothing between the three points
and the CTA — the gap, achieved by following the instruction literally. Without that screenshot
the page simply has less content than a letter page holds, and no amount of omitting fixes that.

Two attempts before it worked. Stretching the three list rows to fill the height left three
lines of text floating in 300px rows. Stretching the CTA panel instead left the same void inside
the panel, under the URL. Both were the same mistake: distributing empty space evenly is not the
same as composing a page.

**Fixed** by giving the page a deliberate shape instead: content sits at the top, the CTA is
anchored at the base at its natural size with the URL enlarged to 36px, and the air sits between
them where it reads as a closing composition rather than a hole. The list rows got real padding
so the top half carries weight. This is the standard back-page structure — statement, then the
one action, pinned to the bottom of the page.

If `discord.png` does arrive, it belongs in that middle space and the page gets tighter.

---

# Verification

Measured in headless Chromium at 816×1056 after every change:

- **9 pages in the PDF.** No page overflows its box; no content splits across a break.
- **Uniform clearance above every folio** — 21px on pages 2–9, 55px on the cover.
- **No purple** at any opacity. **No emoji** — the only non-ASCII glyphs in the document are
  `→` and `√`, both carrying meaning on the ladder axis.
- **No external requests.** Fonts are inlined; the only `src`/`href` values are the two asset
  images and the Discord link.
- **Numbering appears on page 6 only**, as intended.
