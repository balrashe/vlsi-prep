"""Minecraft-style baroobi: HD block-skin textures (16 px per head face) and room textures for the Three.js scene.

Matches the reference he sent: dark curly hair that sticks out past the head, full beard, thick brows,
white shirt, dark crossbody strap, dark-oak plank wall, white lower panel, potted plant.
Output: assets/character/voxel/*.png (tiny, nearest-neighbour; Three.js scales them up).
"""
import os
import random

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "character", "voxel")

P = {
    ".": None,
    "S": (222, 160, 112), "s": (198, 136, 94), "h": (236, 182, 136),          # skin, shade, light
    "H": (50, 33, 25), "j": (88, 60, 43), "k": (32, 21, 16),                 # hair, highlight, dark
    "B": (56, 37, 28), "b": (82, 55, 40),                                    # beard, beard light
    "R": (38, 25, 19),                                                       # brow
    "W": (242, 238, 230), "P": (28, 19, 15),                                 # eye white, pupil
    "L": (164, 92, 84), "T": (246, 243, 236), "M": (66, 28, 28), "G": (190, 92, 98),
    "C": (238, 238, 234), "c": (212, 212, 207), "d": (184, 184, 179),        # shirt
    "X": (38, 38, 42), "x": (72, 72, 78),                                    # strap
}

FACE = [  # head front, 16x16. Mouth window = cols 5-10, rows 11-13 (replaced per viseme)
    "HHjHHHHjHHHHjHHH",
    "HjHHHkHHHjHHHkHH",
    "HHHHjHHHHHHjHHHH",
    "HHHSHjSSSjHSSHHH",
    "HHhhhSSSSSShhSHH",
    "HHSRRRRSSRRRRSHH",
    "HHSWWPWSSWPWWSHH",
    "BHSWWPWSSWPWWSHB",
    "BBSSSSsssSSSSSBB",
    "BBShSSssssSShSBB",
    "BBBSSBBBBBBSSBBB",
    "BBBBBLLLLLLBBBBB",
    "BBBBBBLLLLBBBBBB",
    "BBBBBBBBBBBBBBBB",
    "kBBbBBBBBBBBbBBk",
    "kkBBBBBbBBBBBBkk",
]

MOUTHS = {  # Rhubarb A-H + X, 6x3 at cols 5-10 rows 11-13; B = keep beard
    "X": ["LLLLLL", "BLLLLB", "BBBBBB"],
    "A": ["BLLLLB", "BLLLLB", "BBBBBB"],
    "B": ["LTTTTL", "BLLLLB", "BBBBBB"],
    "C": ["LTTTTL", "LMMMML", "BLLLLB"],
    "D": ["TTTTTT", "MMMMMM", "LMGGML"],
    "E": ["BLTTLB", "BMMMMB", "BLLLLB"],
    "F": ["BBLLBB", "BLMMLB", "BBLLBB"],
    "G": ["BTTTTB", "BLLLLB", "BBBBBB"],
    "H": ["LTTTTL", "LMGGML", "BLLLLB"],
}

SIDE = [  # head side, 16x16; col 0 = face edge, col 15 = back of head (flipped for the other side)
    "HHHjHHHHjHHHHjHH",
    "HjHHHHkHHHHjHHHH",
    "HHHHjHHHHHjHHHHH",
    "SHHHHHHjHHHHHHjH",
    "SSHHHHHHHHHHHHHH",
    "SSSHHHHHHHHHjHHH",
    "SSSSSHsssHHHHHHH",
    "SSSSSsSSsHHHHHHH",
    "BSSSSsSSsHHHHjHH",
    "BBSSSsssskHHHHHH",
    "BBBSSSSSSSsHHHHH",
    "BBBBSSSSSSsskHHH",
    "BBBBBSSSSSSsssss",
    "BBBBBBSSSSSsssss",
    "kBBBBBSSSSssssss",
    "kkBBBBSSSSssssss",
]


def img(rows, out, flip=False):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            c = P[ch]
            if c:
                im.putpixel((w - 1 - x if flip else x, y), c + (255,))
    im.save(os.path.join(OUT, out))
    return im


def noise_fill(w, h, base, spots, seed, density=0.18):
    rnd = random.Random(seed)
    rows = []
    for y in range(h):
        rows.append("".join(rnd.choice(spots) if rnd.random() < density else base for _ in range(w)))
    return rows


def face_variants():
    for m, rows in MOUTHS.items():
        for blink in (False, True):
            f = [list(r) for r in FACE]
            for r in range(3):
                for c in range(6):
                    f[11 + r][5 + c] = rows[r][c]
            if blink:
                for c in range(3, 7):
                    f[6][c], f[7][c] = "S", "P"
                for c in range(9, 13):
                    f[6][c], f[7][c] = "S", "P"
            img(["".join(r) for r in f], f"face_{m}{'_b' if blink else ''}.png")


def hair_overlay():
    """Second skin layer, drawn on a slightly bigger box: curls stick out past the head like his photos."""
    rnd = random.Random(7)
    top = noise_fill(16, 16, "H", "jjk", 3, 0.3)
    img(top, "hair_top.png")
    def edge(rows_solid, bumps):
        rows = []
        for y in range(16):
            if y < rows_solid:
                rows.append("".join(rnd.choice("HHHjk") for _ in range(16)))
            elif y < rows_solid + bumps:
                rows.append("".join(("H" if rnd.random() < 0.55 else ".") for _ in range(16)))
            else:
                rows.append("." * 16)
        return rows
    img(edge(2, 2), "hair_front.png")
    img(edge(4, 3), "hair_side.png")
    img(edge(10, 3), "hair_back.png")


def body():
    rnd = random.Random(11)
    front = [list(r) for r in noise_fill(16, 24, "C", "c", 5, 0.05)]
    for y in range(3):                                   # open collar showing the neck
        for x in range(6 - y // 2, 10 + y // 2):
            front[y][x] = "S" if y < 2 else "s"
    for x in (5, 10):
        front[0][x] = front[1][x] = "d"
    for y in (5, 9, 13, 17, 21):                         # placket buttons
        front[y][8] = "d"
    for y in range(24):                                  # crossbody strap, shoulder to hip
        x0 = 1 + int(y * 13 / 23)
        for dx in (0, 1, 2):
            if 0 <= x0 + dx < 16 and front[y][x0 + dx] not in "Ss":
                front[y][x0 + dx] = "x" if dx == 0 else "X"
    img(["".join(r) for r in front], "body_front.png")
    back = noise_fill(16, 24, "C", "c", 6, 0.05)
    img(back, "body_back.png")
    img(noise_fill(8, 24, "C", "c", 8, 0.08), "body_side.png")
    top = [list(r) for r in noise_fill(16, 8, "C", "c", 9, 0.1)]
    for x in range(5, 11):
        for y in range(2, 6):
            top[y][x] = "s"
    img(["".join(r) for r in top], "body_top.png")


def arm():
    rows = noise_fill(8, 18, "C", "c", 12, 0.06) + ["dddddddd"] + ["S" * 8] * 2 + ["SSsSSsSS"] + ["SSSSSSSS"] * 2
    img(rows, "arm_side.png")
    img(["C" * 8] * 8, "arm_top.png")
    img(["S" * 8] * 8, "arm_bottom.png")


def room():
    rnd = random.Random(21)
    plank = []
    tones = [(70, 46, 29), (78, 52, 33), (62, 41, 26)]
    for y in range(16):
        row = []
        for x in range(16):
            band = y // 4
            if y % 4 == 3:
                row.append((40, 26, 17))
            elif (band % 2 == 0 and x == 11) or (band % 2 == 1 and x == 4):
                row.append((46, 30, 20))
            else:
                t = tones[(band + (x // 6)) % 3]
                j = rnd.randint(-6, 6)
                row.append(tuple(max(0, c + j) for c in t))
        plank.append(row)
    im = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            im.putpixel((x, y), plank[y][x])
    im.save(os.path.join(OUT, "dark_oak.png"))
    panel = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            v = 226 + rnd.randint(-5, 5) - (14 if y == 0 or x == 0 else 0)
            panel.putpixel((x, y), (v, v - 2, v - 6))
    panel.save(os.path.join(OUT, "panel.png"))
    pot = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            v = rnd.randint(-8, 8)
            pot.putpixel((x, y), (150 + v, 62 + v // 2, 46 + v // 2) if y > 2 else (110, 46, 34))
    pot.save(os.path.join(OUT, "pot.png"))
    leaf = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            if rnd.random() < 0.7:
                g = rnd.choice([(74, 142, 52), (54, 112, 40), (96, 168, 66)])
                leaf.putpixel((x, y), g + (255,))
    leaf.save(os.path.join(OUT, "leaves.png"))


def build():
    os.makedirs(OUT, exist_ok=True)
    face_variants()
    img(SIDE, "head_right.png")
    img(SIDE, "head_left.png", flip=True)
    img(noise_fill(16, 16, "H", "jk", 4, 0.25), "head_back.png")
    img(noise_fill(16, 16, "H", "jjk", 2, 0.3), "head_top.png")
    img(noise_fill(16, 16, "B", "bs", 1, 0.2), "head_bottom.png")
    hair_overlay()
    body()
    arm()
    room()
    print("voxel textures ->", OUT, len(os.listdir(OUT)))


if __name__ == "__main__":
    build()
