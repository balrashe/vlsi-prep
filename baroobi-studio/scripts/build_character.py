"""Build the reusable character from photo cutouts: stylized mouthless bases, Rhubarb mouth set (A-H + X),
blink overlays, and a meta file with mouth/eye anchors. Output: assets/character/rig/<pose>/...

Usage: build_character.py   (poses and photos are listed in POSES below)
"""
import json
import os

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, "assets", "character")
MODEL = os.path.join(ROOT, "tools", "models", "face_landmarker.task")

# pose name -> source photo id (see assets/character/norm). All three wear the same navy camp-collar shirt.
POSES = {"front": "p10", "explain": "p09", "skeptic": "p07"}
EYE_DIST = 120          # px between eye centres in the rig, so the head is the same size in every pose
CANVAS_W = 1000
BELOW_CHIN = 620        # px of torso kept under the chin

LIPS_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
EYE_L = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
EYE_R = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]


def landmarks(rgb, refine=2):
    """Face mesh points in image px. Re-runs on a face crop, since full-body photos can fit the mesh low."""
    pts = _landmarks(rgb)
    for _ in range(refine):
        (x0, y0), (x1, y1) = pts.min(0), pts.max(0)
        cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) * 0.95
        X0, Y0 = int(max(0, cx - r)), int(max(0, cy - r))
        crop = rgb[Y0:int(cy + r), X0:int(cx + r)]
        k = 640 / crop.shape[1]
        pts = _landmarks(cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)) / k + [X0, Y0]
    return pts


def _landmarks(rgb):
    opts = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL), num_faces=1)
    with mp.tasks.vision.FaceLandmarker.create_from_options(opts) as lm:
        res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)))
    h, w = rgb.shape[:2]
    return np.array([(p.x * w, p.y * h) for p in res.face_landmarks[0]])


def stylize(bgr, alpha, k=18):
    s = bgr.copy()
    for _ in range(4):
        s = cv2.bilateralFilter(s, 9, 40, 9)
    z = s.reshape(-1, 3).astype(np.float32)
    m = alpha.reshape(-1) > 128
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1)
    _, lab, cen = cv2.kmeans(z[m], k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    z[m] = cen[lab.flatten()]
    return cv2.medianBlur(z.reshape(s.shape).astype(np.uint8), 5)


def mouth_shapes(w, lip, out_dir):
    """Draw the 9 Rhubarb shapes, flat colours to match the posterized face. w = mouth width in px."""
    S = 4                                  # supersample
    box_w, box_h = int(w * 1.3), int(w * 1.1)
    dark, teeth, tongue = (52, 26, 30), (238, 234, 226), (188, 92, 100)
    lipc = tuple(int(c) for c in lip)
    lip_hi = tuple(min(255, int(c * 1.12)) for c in lip)

    def ell(d, cx, cy, rx, ry, fill):
        d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill)

    def shape(name, ow, oh, iw=0, ih=0, top_teeth=0, bot_teeth=0, tongue_h=0, tongue_up=False, line=False):
        im = Image.new("RGBA", (box_w * S, box_h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx, cy = box_w / 2, box_h / 2
        ell(d, cx, cy, ow * w / 2, oh * w / 2, lipc + (255,))
        ell(d, cx, cy + oh * w * 0.12, ow * w * 0.42, oh * w * 0.3, lip_hi + (255,))  # lower-lip highlight
        if line:
            d.line([((cx - ow * w * 0.47) * S, (cy - 1) * S), (cx * S, (cy + 1) * S),
                    ((cx + ow * w * 0.47) * S, (cy - 1) * S)], fill=dark + (255,), width=int(3 * S), joint="curve")
        if iw:
            rx, ry = iw * w / 2, ih * w / 2
            inner = Image.new("L", im.size, 0)
            ImageDraw.Draw(inner).ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
            fill = Image.new("RGBA", im.size, (0, 0, 0, 0))
            fd = ImageDraw.Draw(fill)
            fd.rectangle([0, 0, im.size[0], im.size[1]], fill=dark + (255,))
            if tongue_h:
                ty = cy + ry - tongue_h * w if not tongue_up else cy - ry * 0.35
                ell(fd, cx, ty + tongue_h * w * 0.5, rx * 0.7, tongue_h * w * 0.6, tongue + (255,))
            if top_teeth:
                fd.rectangle([0, (cy - ry) * S, im.size[0], (cy - ry + top_teeth * w) * S], fill=teeth + (255,))
            if bot_teeth:
                fd.rectangle([0, (cy + ry - bot_teeth * w) * S, im.size[0], (cy + ry) * S], fill=teeth + (255,))
            im.paste(fill, (0, 0), inner)
        im = im.resize((box_w, box_h), Image.LANCZOS)
        im.save(os.path.join(out_dir, f"mouth_{name}.png"))

    shape("X", 0.80, 0.20, line=True)                                         # rest
    shape("A", 0.84, 0.24, line=True)                                         # M B P, pressed
    shape("B", 0.92, 0.34, 0.72, 0.15, top_teeth=0.075, bot_teeth=0.06)       # K S T EE, clenched
    shape("C", 0.96, 0.52, 0.76, 0.32, top_teeth=0.09, tongue_h=0.08)         # EH AE, open
    shape("D", 1.00, 0.76, 0.80, 0.56, top_teeth=0.10, tongue_h=0.14)         # AA, wide
    shape("E", 0.72, 0.52, 0.48, 0.32, top_teeth=0.06, tongue_h=0.06)         # AO ER, rounded
    shape("F", 0.52, 0.44, 0.22, 0.15)                                        # UW OW W, pucker
    shape("G", 0.90, 0.38, 0.70, 0.16, top_teeth=0.13)                        # F V, teeth on lip
    shape("H", 0.92, 0.50, 0.72, 0.30, top_teeth=0.08, tongue_h=0.12, tongue_up=True)  # L, tongue up
    return box_w, box_h


def blink(base, alpha, pts, out):
    """Closed-eye overlay: lids filled with nearby skin tone plus a lash line."""
    over = Image.new("RGBA", (base.shape[1], base.shape[0]), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for ring in (EYE_L, EYE_R):
        p = pts[ring]
        x0, y0 = p.min(0)
        x1, y1 = p.max(0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        # lid colour: mid-tone of both cheeks (above the eye is brow, right under it is often shadow)
        cheek = np.vstack([base[y - 10:y + 10, x - 10:x + 10].reshape(-1, 3) for x, y in pts[[50, 280]].astype(int)])
        skin = np.median(cheek, axis=0)
        rx, ry = (x1 - x0) / 2 * 1.1, (y1 - y0) / 2 * 1.35
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=tuple(int(c) for c in skin[::-1]) + (255,))
        d.arc([cx - rx * 0.9, cy - ry * 1.2, cx + rx * 0.9, cy + ry * 0.9], 20, 160, fill=(40, 26, 24, 255), width=4)
    over.save(out)


def build(pose, pid):
    out_dir = os.path.join(CH, "rig", pose)
    os.makedirs(out_dir, exist_ok=True)
    rgba = np.array(Image.open(os.path.join(CH, "cut", f"{pid}.png")).convert("RGBA"))
    pts = landmarks(np.array(Image.open(os.path.join(CH, "norm", f"{pid}.jpg")).convert("RGB")))
    eye_l, eye_r = pts[EYE_L].mean(0), pts[EYE_R].mean(0)
    s = EYE_DIST / np.linalg.norm(eye_r - eye_l)
    rgba = cv2.resize(rgba, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    pts = pts * s
    face_cx, chin_y = pts[[234, 454]].mean(0)[0], pts[152][1]
    top = int(np.argmax(rgba[..., 3].max(1) > 128)) - 20
    x0, y0 = int(face_cx - CANVAS_W / 2), top
    H = int(chin_y + BELOW_CHIN - y0)
    canvas = np.zeros((H, CANVAS_W, 4), np.uint8)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(rgba.shape[1], x0 + CANVAS_W), min(rgba.shape[0], y0 + H)
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = rgba[sy0:sy1, sx0:sx1]
    pts = pts - [x0, y0]
    alpha = canvas[..., 3]
    bgr = cv2.cvtColor(canvas[..., :3], cv2.COLOR_RGB2BGR)

    # erase the real mouth before stylizing so the drawn shapes own it
    lips = pts[LIPS_OUTER].astype(np.int32)
    mask = np.zeros(alpha.shape, np.uint8)
    cv2.fillPoly(mask, [lips], 255)
    lip_col = np.median(bgr[mask > 0], axis=0)[::-1]
    mask = cv2.dilate(mask, np.ones((9, 9), np.uint8))
    bgr = cv2.inpaint(bgr, mask, 9, cv2.INPAINT_TELEA)
    sty = stylize(bgr, alpha)

    a = cv2.GaussianBlur(alpha, (3, 3), 0)
    Image.fromarray(np.dstack([cv2.cvtColor(sty, cv2.COLOR_BGR2RGB), a])).save(os.path.join(out_dir, "base.png"))
    mw = 0.84 * EYE_DIST       # neutral speaking width; the photos are mid-smile, so measured corners run wide
    bw, bh = mouth_shapes(mw, lip_col * 0.92, out_dir)
    blink(sty, alpha, pts, os.path.join(out_dir, "blink.png"))
    mc = pts[[13, 14]].mean(0)
    tilt = float(np.degrees(np.arctan2(*(pts[291] - pts[61])[::-1])))
    meta = {"photo": pid, "width": CANVAS_W, "height": H,
            "mouth": {"cx": round(float(mc[0]), 1), "cy": round(float(mc[1]), 1), "w": bw, "h": bh,
                      "rot": round(tilt, 1)},
            "head": {"cx": round(float(face_cx - x0), 1), "cy": round(float(pts[168][1]), 1)}}
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"), indent=1)
    print(pose, meta)


if __name__ == "__main__":
    for pose, pid in POSES.items():
        build(pose, pid)
