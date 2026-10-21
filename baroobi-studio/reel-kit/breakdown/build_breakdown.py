#!/usr/bin/env python3
"""Build the Video Breakdown Sheet (one self-contained HTML file) from a rendered video.

Stills come from the actual render (never the source footage) so the sheet shows exactly what will post.
Scenes come from a scenes.json the editor writes from the composition's segment/cue data. With --auto and no
scenes.json, scene cuts are proposed from ffmpeg's scene-change score so a sheet can be pulled up for any MP4.

    python build_breakdown.py --video out/v1-preview.mp4 --scenes out/scenes.json --name "Day Trader · v1" \
        --words src/words.json --out out/breakdown.html

scenes.json: [{"chapter": "HOOK", "a": 0, "b": 2.05, "title": "...", "type": "SPLIT", "built": "...",
               "said": "...", "at": 1.4}]   ("said" and "at" are optional; "at" defaults to the scene's middle)
words.json:  [[start, end, "word"], ...] on the same timeline as the video (fills "said" when it is missing)
"""
import argparse, base64, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TYPES = {"B-ROLL", "HEADLINE", "CARD", "BOX REVEAL", "STACK", "CAPTION", "TRANSITION", "SFX", "TALKING HEAD", "SPLIT", "OVERLAY", "3D"}


def duration(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def still(video, t, width):
    # -ss before -i is fast but lands on the previous keyframe; after -i is frame-exact, which matters on hard cuts
    jpg = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ss", f"{t:.3f}", "-frames:v", "1",
                          "-vf", f"scale={width}:-2", "-q:v", "5", "-f", "image2", "-vcodec", "mjpeg", "-"],
                         capture_output=True, check=True).stdout
    if not jpg:
        sys.exit(f"no frame at {t:.3f}s in {video}")
    return "data:image/jpeg;base64," + base64.b64encode(jpg).decode()


def auto_scenes(video, dur, threshold):
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    cuts = sorted({round(float(m), 3) for m in re.findall(r"pts_time:([0-9.]+)", log)})
    # merge cuts closer than 0.8 s so a flicker or a text pop does not become its own scene
    edges = [0.0]
    for c in cuts:
        if c - edges[-1] >= 0.8 and dur - c >= 0.8:
            edges.append(c)
    edges.append(dur)
    return [{"chapter": "SCENES", "a": a, "b": b, "title": f"Scene {i + 1}", "type": "TALKING HEAD",
             "built": "Auto-detected cut: describe what is on screen."} for i, (a, b) in enumerate(zip(edges, edges[1:]))]


def transcribe(video):
    from faster_whisper import WhisperModel  # reel venv: /home/user/vlsi-prep/baroobi-studio/.venv
    segs, _ = WhisperModel("small.en", compute_type="int8").transcribe(str(video), word_timestamps=True)
    return [[w.start, w.end, w.word.strip()] for s in segs for w in s.words]


def said_between(words, a, b):
    return " ".join(w[2].replace("_", " ") for w in words if a <= (w[0] + w[1]) / 2 < b).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--scenes")
    ap.add_argument("--auto", action="store_true", help="propose scenes from scene-change detection")
    ap.add_argument("--threshold", type=float, default=0.05, help="0.05 catches top-card swaps in split layouts")
    ap.add_argument("--words")
    ap.add_argument("--transcribe", action="store_true", help="no words.json: transcribe the render with faster-whisper")
    ap.add_argument("--name", required=True, help='sheet title, e.g. "Day Trader skill · v3"')
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=432, help="still width in px (432 keeps 20 scenes near 1 MB)")
    args = ap.parse_args()

    video = Path(args.video)
    dur = duration(video)
    if args.scenes:
        scenes = json.loads(Path(args.scenes).read_text())
    elif args.auto:
        scenes = auto_scenes(video, dur, args.threshold)
    else:
        sys.exit("pass --scenes scenes.json or --auto")
    words = json.loads(Path(args.words).read_text()) if args.words else (transcribe(video) if args.transcribe else [])

    for i, s in enumerate(scenes):
        s["id"] = f"s{i + 1:02d}"
        s["a"], s["b"] = float(s["a"]), float(min(s["b"], dur))
        if s.get("type") not in TYPES:
            sys.exit(f'{s["id"]}: type {s.get("type")!r} is not one of {sorted(TYPES)}')
        if not s.get("said") and words:
            s["said"] = said_between(words, s["a"], s["b"])
        s.setdefault("said", "")
        s["at"] = float(s.get("at", (s["a"] + s["b"]) / 2))
        s["img"] = still(video, min(s["at"], dur - 0.05), args.width)

    data = {"name": args.name, "file": video.name, "duration": round(dur, 3), "scenes": scenes}
    tpl = (HERE / "template.html").read_text()
    # json.dumps escapes "<" nowhere, so guard "</script>" in any text field
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = re.sub(r"[^\w ]+", " ", args.name.split("·")[0]).strip()[:40] + " Breakdown"
    html = tpl.replace("/*__DATA__*/null", blob).replace("__TITLE__", title)
    Path(args.out).write_text(html)
    print(f"{args.out}: {len(scenes)} scenes, {len(html) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
