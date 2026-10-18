"""Tile every pose with each mouth shape composited, for eyeballing the rig. Usage: preview_rig.py <out.jpg> [face]"""
import json, os, sys
from PIL import Image
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "character", "rig")
face = len(sys.argv) > 2
rows = []
for pose in ("front", "explain", "skeptic"):
    m = json.load(open(f"{R}/{pose}/meta.json")); base = Image.open(f"{R}/{pose}/base.png")
    tiles = []
    for sh in "XABCDEFGH" + "*":
        im = base.copy()
        if sh == "*":
            im.alpha_composite(Image.open(f"{R}/{pose}/blink.png")); sh = "X"
        mo = Image.open(f"{R}/{pose}/mouth_{sh}.png").rotate(-m["mouth"]["rot"], resample=Image.BICUBIC, expand=True)
        im.alpha_composite(mo, (int(m["mouth"]["cx"] - mo.width / 2), int(m["mouth"]["cy"] - mo.height / 2)))
        bg = Image.new("RGBA", im.size, (244, 245, 247, 255)); bg.alpha_composite(im)
        if face:
            cx, cy = int(m["mouth"]["cx"]), int(m["mouth"]["cy"]); bg = bg.crop((cx - 170, cy - 260, cx + 170, cy + 120))
        bg.thumbnail((200, 400) if face else (180, 220)); tiles.append(bg.convert("RGB"))
    row = Image.new("RGB", (sum(t.width for t in tiles), max(t.height for t in tiles)), "white")
    x = 0
    for t in tiles: row.paste(t, (x, 0)); x += t.width
    rows.append(row)
sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), "white")
y = 0
for r in rows: sheet.paste(r, (0, y)); y += r.height
sheet.save(sys.argv[1], quality=88)
