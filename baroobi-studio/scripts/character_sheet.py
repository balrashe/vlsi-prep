"""Character sheet: front, 3/4 and side views plus the Rhubarb mouth chart. Output: assets/character/character-sheet.png"""
import json, os, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_character as bc

CH, R = bc.CH, os.path.join(bc.CH, "rig")
font = ImageFont.truetype(os.path.join(bc.ROOT, "assets", "fonts", "Inter.woff2"), 36) if False else ImageFont.load_default(size=34)

def side_view():
    im = np.array(Image.open(os.path.join(CH, "cut", "p04.png")).convert("RGBA"))
    a = im[..., 3]; bgr = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2BGR)
    out = Image.fromarray(np.dstack([cv2.cvtColor(bc.stylize(bgr, a), cv2.COLOR_BGR2RGB), a]))
    return out.crop(out.getbbox())

views = [("front", Image.open(f"{R}/front/base.png")), ("3/4", Image.open(f"{R}/skeptic/base.png")), ("side (closest photo)", side_view())]
W, H = 2400, 1900
sheet = Image.new("RGBA", (W, H), (243, 244, 247, 255)); d = ImageDraw.Draw(sheet)
d.text((60, 40), "baroobi  /  character sheet v1", fill=(31, 35, 40), font=ImageFont.load_default(size=56))
for i, (lab, im) in enumerate(views):
    im = im.copy(); im.thumbnail((740, 1000))
    x = 60 + i * 780; sheet.alpha_composite(im, (x + (740 - im.width) // 2, 150 + (1000 - im.height)))
    d.text((x, 1170), lab, fill=(87, 96, 106), font=font)
m = json.load(open(f"{R}/front/meta.json")); base = Image.open(f"{R}/front/base.png")
labels = {"X": "rest", "A": "M B P", "B": "K S T EE", "C": "EH AE", "D": "AA", "E": "AO ER", "F": "UW OW W", "G": "F V", "H": "L"}
for k, s in enumerate("XABCDEFGH"):
    im = base.copy(); mo = Image.open(f"{R}/front/mouth_{s}.png").rotate(-m["mouth"]["rot"], resample=Image.BICUBIC, expand=True)
    im.alpha_composite(mo, (int(m["mouth"]["cx"] - mo.width / 2), int(m["mouth"]["cy"] - mo.height / 2)))
    cx, cy = int(m["mouth"]["cx"]), int(m["mouth"]["cy"])
    tile = im.crop((cx - 120, cy - 150, cx + 120, cy + 110)).resize((240, 260))
    x = 60 + k * 258; sheet.alpha_composite(tile, (x, 1260))
    d.text((x, 1540), f"{s}  {labels[s]}", fill=(31, 35, 40), font=ImageFont.load_default(size=28))
d.text((60, 1640), "Built from your Drive photos (p10 front, p07 3/4, p04 side). Same navy shirt in every pose used on screen.",
       fill=(87, 96, 106), font=ImageFont.load_default(size=30))
sheet.convert("RGB").save(os.path.join(CH, "character-sheet.png"))
print("ok")
