---
name: claude-mascot-3d
description: Clean, high-end 3D animated reels starring Claude's mascot (the Claude Code logo creature) in a soft studio set, 9:16 at 60 fps, rendered with Three.js in HyperFrames. Use when the user wants a "Claude animation", "3D mascot reel", "the clean 3D style", or asks to animate how a repo, tool or idea works with Claude's mascot as the character.
---

# Claude mascot 3D reels

The approved look (baroobi, 2026-10-21): a glossy vinyl-toy Claude mascot in a seamless studio, one idea per beat, the
mascot always the focus, soft light, clean background, smooth camera, landing ripples when he jumps. 60 fps.

Kit: `~/.claude/skills/reel-kit/mascot3d/`
- `new_reel.py <project> --duration N`: scaffolds a project from `template.html` (a working 3-beat example).
- `assets/clawd.js`: the mascot. `makeClawd(scene)`, `pose(C, t, {...})`.
- `assets/stage.js`: studio, lights, AO + depth of field + light bloom, contact shadow, ripples, camera keys, looks.
- `assets/recipes.js`: props (3D type, falling papers, floating panels and terminals, cards, speech bubbles, walk paths, arcs).

## The mascot: keep it faithful

Proportions follow the Claude Code logo glyph:

```
 ▐▛███▜▌
▝▜█████▛▘
  ▘▘ ▝▝
```

- **Body:** a 6 x 4 block.
- **Eyes:** two tall glossy eye slits near the top corners, with small catchlights.
- **Arms:** one square stub arm on each side at mid height.
- **Legs:** four thin short legs, two under each half with a gap in the middle.

Never add claws, pincers, feet, a mouth or oval eyes; it stops reading as Claude and reads as a crab. Colour `#d06a45` under ACES (the brand orange).

`pose()` options:
- **Placement:** `p` [x,y,z], `ry` facing.
- **Jumps:** `jumps` [[t0, height, airtime]], with crouch, stretch and squash built in.
- **Walking:** `walk` 0-1, `phase`.
- **Head:** `look` pitch, `tilt`, `lookUp`.
- **Arms:** `wave`, `armL` / `armR` lift, `tap` (typing), `snap` (small arm bob).
- **Effects:** `glow`, `blinkOff`.

Always call `S.shadow(C)` after posing. Add `S.ripples([[landTime, x, z]], u)` for every landing, where landTime = t0 + airtime.

## Look rules (what made it look premium, and what made it look cheap)

1. **Clean background.** Only the studio cyc. No stars, dust, neon grids, light-beam cones or pixel-mosaic wipes; the user rejected all of these as messy. Change mood with `beat(look)` (warm, teal, violet, gold, green, blue), not with clutter.
2. **One idea per beat, the mascot in every shot.** Props support him; nothing busy behind him.
3. **Smooth, not pixelated.** Rounded geometry, physical materials, bevelled 3D type. No voxels.
4. **Light and white surfaces.**
   - White paper, cards and panels clip easily. Keep their colour tinted (~`0xd9d4ca`) and the emissive on panels low (0.35-0.7).
   - Keep the camera outside any light cone.
5. **Portrait framing is narrow.** At fov 30 the half-width visible at distance d is about 0.15 x d. Keep the mascot and props within x ≈ ±0.12 d, or they get cut.
6. **Captions sit at the top (y≈300)**, uppercase Montserrat 800, keyword in the accent box (`#e08a3a`). Keep 3D props below y≈10 world units so they never collide with the caption.
7. **Camera:** 2-3 keys per beat, eased, with a slow dolly or orbit. Hard cut between beats; no transitions.
8. **Use real facts only.** Numbers on screen must come from the source (repo, transcript). Illustrative UI text (job titles, terminal output) must match what the tool really does.

## Workflow

1. **Script the beats** from verified facts: 4-8 beats, 3-5 s each, one idea per beat. Write the captions as [start, end, words].
2. **Scaffold:** `python ~/.claude/skills/reel-kit/mascot3d/new_reel.py <project> --duration <last beat end>`.
3. **Edit the two EDIT blocks** in `index.html`:
   - The beat clock (`BEATS`) and `CAPS`.
   - One `beat(look, setup)` per idea. `setup(group)` builds props and returns `update(u, t)`, where `u` is the beat-local time. Keep everything a pure function of time: no `Math.random`, no `Date`. Use `rnd(i)`.
4. **Check:** `npx --yes hyperframes@0.8.172 check`. The only expected failures are `contrast_aa_failure` on the white-on-orange keyword box (2.67:1, a brand choice) and WebGL `ReadPixels` console warnings. Fix anything else.
5. **Stills first:** `npx --yes hyperframes@0.8.172 snapshot -o snap --at <mid-beat times> --no-end --describe false --timeout 120000`. Look at every beat. Fix framing, overexposure and anything hidden behind the mascot before rendering.
6. **Preview:** `npx --yes hyperframes@0.8.172 render -q draft -f 30 -o preview.mp4 --quiet`, then show the user.
7. **Final at 60 fps** only after the user approves: `npx --yes hyperframes@0.8.172 render -q delivery -o final.mp4 --quiet`.
   - The composition is `data-fps="60"`.
   - Software WebGL renders slowly: expect roughly 10-20 min per 5 s at 60 fps on a CPU-only container, so run it in the background.

## Gotchas learned building this

- **Stage sweep:** the cyc must be `DoubleSide`, or the floor turns into a black void.
- **Moving props:** call `group.updateMatrixWorld(true)` before reading a prop's world position (e.g. cards flying off a board).
- **Rejected looks:** the old voxel or crab mascot, star fields, neon grids and light cones all made the style look cheap or messy.
- **Rights:** the mascot is Anthropic's character. Use it for Claude or Claude Code topics, not as the user's own brand mascot.
