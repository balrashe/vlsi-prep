# Draws the "after" terminal for the mods reel: the docs recording's session, restyled the way a theme mod
# can (user/tool/assistant rows, a band above the prompt, a side pane). Engine-owned parts (prompt, footer,
# terminal background) stay as Claude Code draws them, so the frame only shows what a mod can change.
import sys
from PIL import Image, ImageDraw, ImageFont

W, H, FS, LH, X0, Y0 = 1440, 676, 23, 32, 34, 26
R = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", FS)
B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", FS)
CW = R.getlength("M")
BG, TX, DIM = "#1b1b1b", "#ece6f5", "#8d8797"
PK, CY, GR, YL = "#ff5fd2", "#3ee8ff", "#7dff9a", "#ffd23f"

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def put(row, col, text, fg=TX, bold=False, bg=None):
    x, y = X0 + col * CW, Y0 + row * LH
    if bg:
        d.rectangle([x, y - 3, x + len(text) * CW, y + LH - 5], fill=bg)
    d.text((x, y), text, font=B if bold else R, fill=fg)


def box(r0, c0, w, h, color, title="", style="round"):
    # drawn as lines, not box characters: the font's box glyphs don't meet at this cell size
    x0, y0 = X0 + c0 * CW + CW / 2, Y0 + r0 * LH + LH / 2 - 4
    x1, y1 = X0 + (c0 + w - 1) * CW + CW / 2, Y0 + (r0 + h - 1) * LH + LH / 2 - 4
    width = {"round": 2, "double": 2, "bold": 4}[style]
    d.rounded_rectangle([x0, y0, x1, y1], radius=10 if style == "round" else 2, outline=color, width=width)
    if style == "double":
        d.rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], outline=color, width=2)
    if title:
        put(r0, c0 + 2, f" {title} ", color, True, BG)


# user row
box(0, 0, 52, 3, PK, "you")
put(1, 2, "list the files here and read the README", TX, True)
# tool rows
for r, (tool, arg) in enumerate([("Bash", "ls"), ("Read", "README.md"), ("Read", "package.json")], start=4):
    put(r, 1, " ⚡ ", "#1b1b1b", True, CY); put(r, 5, f"{tool:<6}", CY, True); put(r, 12, arg, TX); put(r, 46, "✔ done", GR)
# assistant row
put(8, 1, "✦ claude", GR, True)
put(9, 3, "The project holds README.md, package.json", TX)
put(10, 3, "and the first-mod directory. The README", TX)
put(11, 3, "describes a small Express service.", TX)
# band above the prompt
box(13, 0, 52, 3, YL, "neon mod", "bold")
put(14, 2, "tool calls 3", YL, True); put(14, 17, "context ▰▰▰▱▱▱▱▱", TX); put(14, 37, "theme  neon", PK)
# engine prompt and footer, untouched
put(16, 0, "─" * 52, DIM); put(17, 0, "❯", DIM); d.rectangle([X0 + 2 * CW, Y0 + 17 * LH - 2, X0 + 3 * CW, Y0 + 18 * LH - 8], fill="#e8e3d8")
put(18, 1, "▸▸ auto mode on", "#f2c037"); put(18, 17, "(shift+tab to cycle)", DIM)
# side pane
c = 55
box(0, c, 36, 19, CY, "DASHBOARD", "double")
put(2, c + 2, "TO-DO", PK, True)
for r, (done, t) in enumerate([(True, "reply to comments"), (False, "ship the mods reel"), (False, "review the PR")], start=3):
    put(r, c + 2, "■" if done else "□", GR if done else DIM); put(r, c + 4, t, DIM if done else TX)
put(7, c + 2, "SESSIONS", PK, True)
put(8, c + 2, "●", GR); put(8, c + 4, "research"); put(8, c + 17, "working", GR)
put(9, c + 2, "●", YL); put(9, c + 4, "outreach"); put(9, c + 17, "idle", DIM)
put(11, c + 2, "MODEL ROUTING", PK, True)
put(12, c + 2, "easy  →", DIM); put(12, c + 10, "haiku", CY)
put(13, c + 2, "hard  →", DIM); put(13, c + 10, "opus", CY)
put(15, c + 2, "[ refresh ]", "#1b1b1b", True, CY); put(15, c + 15, "[ /todo ]", CY, True)
img.save(sys.argv[1], quality=95)
