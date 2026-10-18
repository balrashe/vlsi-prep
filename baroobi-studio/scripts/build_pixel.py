"""8-bit baroobi: chibi pixel sprite in the reference's style (8 px grid, dark outline, cream halo).

Drawn on a 96x96 grid from primitives, then upscaled 8x with nearest-neighbour.
Output: assets/character/pixel/<gesture>.png, mouth_<A-H,X>.png, blink.png, meta.json
Usage: build_pixel.py [preview.png]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "character", "pixel")
GW, GH = 100, 96   # grid
S = 8           # px per grid cell on screen
CX = 40         # body centre column (room on the right for a pointing arm)

C = {  # palette, sampled by eye from the Drive photos (p10/p09/p07)
    "line": (40, 26, 22), "halo": (255, 249, 238),
    "skin": (206, 140, 98), "skin_lo": (176, 112, 78), "skin_hi": (226, 166, 122),
    "hair": (34, 24, 21), "hair_hi": (68, 47, 37),
    "beard": (48, 33, 27), "beard_hi": (74, 52, 41),
    "brow": (30, 21, 18), "white": (250, 248, 244), "iris": (74, 44, 28), "pupil": (22, 14, 11),
    "shirt": (46, 64, 96), "shirt_lo": (33, 47, 72), "shirt_hi": (66, 88, 126),
    "lip": (196, 104, 100), "mouth": (58, 24, 27), "teeth": (246, 241, 232), "tongue": (198, 98, 106),
}


class Layer:
    def __init__(self):
        self.im = Image.new("RGBA", (GW, GH), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def ell(self, box, col):
        self.d.ellipse(box, fill=C[col] + (255,))

    def rect(self, box, col):
        self.d.rectangle(box, fill=C[col] + (255,))

    def poly(self, pts, col):
        self.d.polygon(pts, fill=C[col] + (255,))

    def px(self, pts, col):
        for p in pts:
            self.d.point(p, fill=C[col] + (255,))

    @property
    def mask(self):
        return np.array(self.im)[..., 3] > 0


def dilate(m, n=1):
    out = m.copy()
    for _ in range(n):
        o = out.copy()
        o[1:] |= out[:-1]; o[:-1] |= out[1:]; o[:, 1:] |= out[:, :-1]; o[:, :-1] |= out[:, 1:]
        out = o
    return out


def stack(layers):
    """Paint layers bottom-up, each with its own 1-cell dark outline (sticker style), then a cream halo."""
    canvas = np.zeros((GH, GW, 4), np.uint8)
    for L in layers:
        m = L.mask
        ring = dilate(m) & ~m
        canvas[ring] = C["line"] + (255,)
        a = np.array(L.im)
        canvas[m] = a[m]
    sil = canvas[..., 3] > 0
    halo = dilate(sil) & ~sil
    canvas[halo] = C["halo"] + (255,)
    return canvas


def torso():
    L = Layer()
    L.d.rounded_rectangle((CX - 24, 66, CX + 24, GH + 4), radius=9, fill=C["shirt"] + (255,))
    L.rect((CX + 14, 70, CX + 24, GH), "shirt_lo")                       # shade right side
    L.rect((CX - 6, 60, CX + 6, 72), "skin_lo")                          # neck
    L.poly([(CX - 7, 66), (CX + 7, 66), (CX, 80)], "skin")               # open collar V
    L.poly([(CX - 7, 65), (CX - 14, 67), (CX - 6, 82), (CX, 80)], "shirt_hi")   # collar flaps
    L.poly([(CX + 7, 65), (CX + 14, 67), (CX + 6, 82), (CX, 80)], "shirt_hi")
    L.px([(CX, y) for y in range(81, GH)], "shirt_lo")                    # placket
    L.px([(CX + 2, 86), (CX + 2, 92)], "shirt_lo")                       # buttons
    return L


def head():
    L = Layer()
    # ears
    L.ell((CX - 21, 34, CX - 14, 46), "skin_lo")
    L.ell((CX + 14, 34, CX + 21, 46), "skin_lo")
    # face
    L.ell((CX - 17, 14, CX + 17, 58), "skin")
    L.rect((CX + 9, 24, CX + 15, 48), "skin_lo")                           # right-side shade
    L.ell((CX - 13, 20, CX - 4, 30), "skin_hi")                            # forehead light
    # curly hair: dome + bumps along the top and down the temples
    L.ell((CX - 17, 5, CX + 17, 26), "hair")
    for x, y, r in [(-14, 11, 3), (-11, 7, 4), (-5, 5, 4), (1, 4, 4), (7, 5, 4), (12, 7, 4), (15, 11, 3)]:
        L.ell((CX + x - r, y - r, CX + x + r, y + r), "hair")
    L.rect((CX - 17, 15, CX - 15, 30), "hair")                              # short faded sides
    L.rect((CX + 15, 15, CX + 17, 30), "hair")
    L.px([(CX - 16, y) for y in range(24, 31, 2)] + [(CX + 16, y) for y in range(25, 31, 2)], "hair_hi")
    for x, y in [(-11, 5), (-5, 3), (1, 2), (7, 3), (12, 6), (-8, 9), (4, 8), (-2, 7), (10, 10), (-13, 12)]:
        L.px([(CX + x, y), (CX + x + 1, y), (CX + x, y + 1)], "hair_hi")
    # forehead and a curly hairline
    L.ell((CX - 13, 14, CX + 13, 36), "skin")
    L.rect((CX + 8, 22, CX + 13, 30), "skin_lo")
    L.rect((CX - 9, 19, CX - 7, 21), "skin_hi")
    L.rect((CX - 13, 14, CX + 13, 15), "hair")
    L.px([(CX - 12 + k, 16) for k in range(0, 25, 2)], "hair")
    L.px([(CX - 11 + k, 17) for k in range(0, 23, 4)], "hair")
    # brows
    L.poly([(CX - 13, 29), (CX - 9, 27), (CX - 4, 28), (CX - 4, 29), (CX - 9, 29), (CX - 13, 30)], "brow")
    L.poly([(CX + 4, 28), (CX + 9, 27), (CX + 13, 29), (CX + 13, 30), (CX + 9, 29), (CX + 4, 29)], "brow")
    # eyes: white, iris, pupil, catch light
    for ex in (CX - 9, CX + 8):
        L.ell((ex - 4, 31, ex + 4, 37), "white")
        L.rect((ex - 2, 32, ex + 1, 36), "iris")
        L.rect((ex - 1, 33, ex, 35), "pupil")
        L.px([(ex - 2, 32)], "white")
        L.px([(ex - 4 + k, 31) for k in range(9)], "line")              # upper lid line
    # nose
    L.rect((CX + 1, 36, CX + 2, 42), "skin_lo")
    L.px([(CX - 2, 43), (CX + 3, 43)], "line")
    L.px([(CX - 1, 43), (CX + 2, 43)], "skin_lo")
    # full but trimmed beard: sideburns -> jaw -> chin, cheeks stay visible
    L.poly([(CX - 17, 30), (CX - 15, 30), (CX - 13, 40), (CX - 8, 45), (CX + 8, 45), (CX + 13, 40),
            (CX + 15, 30), (CX + 17, 30), (CX + 17, 44), (CX + 11, 55), (CX, 60), (CX - 11, 55), (CX - 17, 44)], "beard")
    L.poly([(CX - 8, 46), (CX - 3, 44), (CX + 3, 44), (CX + 8, 46), (CX + 6, 47), (CX - 6, 47)], "beard")  # moustache
    for x, y in [(-15, 38), (-12, 47), (-7, 53), (0, 57), (7, 53), (12, 47), (15, 38), (-3, 55), (4, 56)]:
        L.px([(CX + x, y), (CX + x + 1, y + 1)], "beard_hi")
    L.rect((CX - 1, 46, CX + 1, 46), "skin_lo")                            # philtrum gap
    return L


MOUTH = (CX, 50)   # 9-wide window inside the beard   # centre of the mouth window


def arm(gesture):
    """Gesture arm(s) drawn above the torso. Returns a list of layers."""
    if gesture == "rest":
        return []
    L = Layer()
    if gesture == "point":            # arm across the chest, index finger out to the right (the reference's main pose)
        L.poly([(CX + 18, 68), (CX + 25, 66), (CX + 34, 72), (CX + 42, 70), (CX + 44, 79), (CX + 32, 84), (CX + 18, 80)], "shirt")
        L.poly([(CX + 31, 81), (CX + 43, 77), (CX + 44, 79), (CX + 33, 84)], "shirt_lo")
        L.d.rounded_rectangle((CX + 41, 67, CX + 50, 77), radius=2, fill=C["skin"] + (255,))      # fist
        L.rect((CX + 49, 67, CX + 59, 69), "skin")                                                 # index finger
        L.rect((CX + 49, 69, CX + 58, 69), "skin_lo")
        L.rect((CX + 43, 65, CX + 47, 66), "skin")                                                 # thumb on top
        L.px([(CX + 42 + k, 72) for k in range(0, 8, 2)] + [(CX + 42 + k, 75) for k in range(1, 8, 2)], "skin_lo")
        return [L]
    if gesture == "wave":             # open palm raised beside the head
        L.poly([(CX + 18, 70), (CX + 25, 66), (CX + 32, 56), (CX + 38, 56), (CX + 36, 70), (CX + 27, 82), (CX + 18, 80)], "shirt")
        L.poly([(CX + 32, 60), (CX + 37, 60), (CX + 35, 70), (CX + 29, 74)], "shirt_lo")
        L.d.rounded_rectangle((CX + 29, 44, CX + 39, 56), radius=2, fill=C["skin"] + (255,))      # palm
        for k, h in enumerate((7, 9, 9, 7)):                                                       # four fingers
            x = CX + 30 + k * 2 + (k > 1)
            L.rect((x, 44 - h, x + 1, 44), "skin")
        L.rect((CX + 26, 46, CX + 29, 49), "skin")                                                 # thumb
        L.px([(CX + 33, 52), (CX + 34, 51), (CX + 35, 52)], "skin_lo")
        return [L]
    if gesture == "thumb":            # thumbs up at chest height, thumb on the inside edge
        L.poly([(CX + 18, 70), (CX + 25, 66), (CX + 33, 72), (CX + 39, 68), (CX + 42, 78), (CX + 28, 84), (CX + 18, 80)], "shirt")
        L.d.rounded_rectangle((CX + 36, 61, CX + 46, 71), radius=2, fill=C["skin"] + (255,))      # fist
        L.rect((CX + 36, 52, CX + 39, 61), "skin")                                                 # thumb up
        L.px([(CX + 39 + k, y) for y in (63, 65, 67, 69) for k in range(0, 7)], "skin_lo")       # curled fingers
        L.px([(CX + 39 + k, y) for y in (64, 66, 68, 70) for k in range(0, 7)], "skin")
        return [L]
    if gesture == "shrug":            # both forearms out, palms up
        sides = []
        for sgn in (-1, 1):
            A = Layer()
            x0 = CX + sgn * 20
            pts = [(x0, 68), (x0 + sgn * 7, 66), (x0 + sgn * 15, 72), (x0 + sgn * 17, 80), (x0 + sgn * 5, 84), (x0 - sgn * 2, 80)]
            A.poly(pts, "shirt")
            hx = x0 + sgn * 20
            A.d.rounded_rectangle((min(hx - 6, hx + 6), 64, max(hx - 6, hx + 6), 71), radius=2, fill=C["skin"] + (255,))
            A.px([(hx + sgn * k, 63) for k in range(-5, 7)], "skin")      # fingers
            A.rect((min(hx - 6, hx + 6), 70, max(hx - 6, hx + 6), 71), "skin_lo")
            sides.append(A)
        return sides
    raise ValueError(gesture)


def mouths():
    """Rhubarb set as pixel overlays, centred on MOUTH. Rows top->bottom; chars: l lip, m mouth, t teeth, g tongue."""
    shapes = {
        "X": [" m     m ", "  mmmmm  ", "   lll   "],     # rest: slight smile
        "A": [" lmmmmml ", "  lllll  "],
        "B": [" lllllll ", "ltttttttl", " lllllll "],
        "C": [" lllllll ", "ltttttttl", "lmmmmmmml", " lllllll "],
        "D": [" lllllll ", "ltttttttl", "lmmmmmmml", "lmmgggmml", "lmmgggmml", " lllllll "],
        "E": ["  lllll  ", " ltttttl ", " lmmmmml ", " lmmgmml ", "  lllll  "],
        "F": ["   lll   ", "  lmmml  ", "  lmmml  ", "   lll   "],
        "G": [" lllllll ", "ltttttttl", " lllllll ", "  lllll  "],
        "H": [" lllllll ", "ltttttttl", "lmmgggmml", "lmmmmmmml", " lllllll "],
    }
    key = {"l": "lip", "m": "mouth", "t": "teeth", "g": "tongue"}
    out = {}
    for name, rows in shapes.items():
        L = Layer()
        x0, y0 = MOUTH[0] - 4, MOUTH[1] - len(rows) // 2
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch in key:
                    L.px([(x0 + c, y0 + r)], key[ch])
        out[name] = L
    return out


def blink():
    L = Layer()
    for ex in (CX - 9, CX + 8):
        L.d.rounded_rectangle((ex - 5, 30, ex + 5, 38), radius=2, fill=C["skin"] + (255,))   # covers whites + catch light
        L.px([(ex - 4 + k, 34) for k in range(9)], "line")
        L.px([(ex - 3 + k, 35) for k in range(7)], "skin_lo")
    return L


def up(a):
    return Image.fromarray(a).resize((GW * S, GH * S), Image.NEAREST)


def build():
    os.makedirs(OUT, exist_ok=True)
    gestures = ["point", "wave", "thumb", "shrug", "rest"]
    for g in gestures:
        layers = [torso()] + [head()] + arm(g)
        up(stack(layers)).save(os.path.join(OUT, f"{g}.png"))
    for name, L in mouths().items():
        up(np.array(L.im)).save(os.path.join(OUT, f"mouth_{name}.png"))
    up(np.array(blink().im)).save(os.path.join(OUT, "blink.png"))
    json.dump({"grid": [GW, GH], "scale": S, "size": [GW * S, GH * S], "gestures": gestures, "mouth": [MOUTH[0] * S, MOUTH[1] * S]},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)
    return gestures


def preview(path):
    gestures = build()
    tiles = []
    for g in gestures:
        im = Image.open(os.path.join(OUT, f"{g}.png")).convert("RGBA")
        bg = Image.new("RGBA", im.size, (243, 244, 247, 255)); bg.alpha_composite(im)
        bg.alpha_composite(Image.open(os.path.join(OUT, "mouth_C.png")))
        tiles.append(bg.resize((384, 368), Image.NEAREST))
    base = Image.open(os.path.join(OUT, "rest.png")).convert("RGBA")
    face = []
    for s in "XABCDEFGH":
        bg = Image.new("RGBA", base.size, (243, 244, 247, 255)); bg.alpha_composite(base)
        bg.alpha_composite(Image.open(os.path.join(OUT, f"mouth_{s}.png")))
        face.append(bg.crop((CX * S - 160, 240, CX * S + 160, 560)).resize((213, 213), Image.NEAREST))
    sheet = Image.new("RGB", (max(384 * 5, 213 * 9), 384 + 213), (255, 255, 255))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * 384, 0))
    for i, t in enumerate(face):
        sheet.paste(t, (i * 213, 384))
    sheet.save(path)


if __name__ == "__main__":
    preview(sys.argv[1]) if len(sys.argv) > 1 else build()
