"""Generate the HyperFrames project for one reel from its beat sheet.

Usage: build_video.py <slug>

Inputs  scripts/<slug>/beats.json             beats, headline words, cards, poses
        assets/voice/<slug>.(wav|m4a|mp3)     your recording (optional; without it the timing is synthetic)
        assets/character/rig/                 the character (build_character.py)
Output  projects/<slug>/index.html + assets/  ready for `hyperframes check` / `render`

With a voiceover: word times come from Whisper (transcribe.py) aligned to the script, mouth cues from Rhubarb
(lipsync.sh). Without one: both are estimated from the text so the animatic still moves.
"""
import difflib
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIG = os.path.join(ROOT, "assets", "character", "rig")
POSES = ["front", "explain", "skeptic"]
BLINKS = {"front", "explain"}     # skeptic's eye area is too shadowed to fake lids cleanly
SHAPES = "XABCDEFGH"
CHAR_W = 660                      # on-screen width of the character
FPS = 30

NUM_WORDS = {"69": "sixtynine", "20": "twenty", "1": "one", "2025": "twentytwentyfive", "2026": "twentytwentysix"}


def norm(w):
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    return NUM_WORDS.get(w, w)


def script_words(steps):
    out = []
    for i, st in enumerate(steps):
        for w in st["say"].split():
            out.append({"step": i, "text": w})
    return out


# ---------- timing ----------

def synth_times(words):
    """Creator read-aloud pace (the reference reel runs ~3.7 words/s) with sentence pauses."""
    t = 0.15
    for w in words:
        spoken = NUM_WORDS.get(re.sub(r"\D", "", w["text"]), "") or re.sub(r"[^A-Za-z]", "", w["text"])
        d = 0.07 + 0.036 * max(2, len(spoken))
        w["start"], w["end"] = round(t, 3), round(t + d, 3)
        t += d + (0.26 if w["text"][-1] in ".?!" else 0.12 if w["text"][-1] in ",:" else 0.02)
    return t + 0.6


def whisper_times(words, wjson):
    """Align script words to Whisper words; unmatched script words are interpolated between neighbours."""
    ww = json.load(open(wjson))["words"]
    a, b = [norm(w["text"]) for w in words], [norm(w["word"]) for w in ww]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            words[blk.a + k]["start"] = ww[blk.b + k]["start"]
            words[blk.a + k]["end"] = ww[blk.b + k]["end"]
    known = [i for i, w in enumerate(words) if "start" in w]
    for i, w in enumerate(words):
        if "start" in w:
            continue
        lo = max([k for k in known if k < i], default=None)
        hi = min([k for k in known if k > i], default=None)
        t0 = words[lo]["end"] if lo is not None else 0.0
        t1 = words[hi]["start"] if hi is not None else t0 + 0.4
        n = (hi if hi is not None else i + 1) - (lo if lo is not None else -1)
        pos = i - (lo if lo is not None else -1)
        w["start"] = round(t0 + (t1 - t0) * (pos - 1) / n, 3)
        w["end"] = round(t0 + (t1 - t0) * pos / n, 3)
    unmatched = len(words) - len(known)
    if unmatched:
        print(f"  {unmatched} script words not heard by Whisper (interpolated): "
              + ", ".join(w["text"] for i, w in enumerate(words) if i not in known))
    return max(w["end"] for w in words) + 0.8


def synth_cues(words):
    """Letter-group visemes when no audio exists (Rhubarb A-H + X)."""
    cues = []

    def shape(g):
        if g[0] in "mbp":
            return "A"
        if g[0] in "fv":
            return "G"
        if g[0] == "l":
            return "H"
        if re.match(r"[ou]|w", g):
            return "F" if g[0] in "uw" else "E"
        if g[0] == "a":
            return "D"
        if g[0] in "eiy":
            return "C"
        return "B"

    prev_end = 0.0
    for w in words:
        if w["start"] - prev_end > 0.06:
            cues.append({"start": prev_end, "end": w["start"], "value": "X"})
        spoken = NUM_WORDS.get(re.sub(r"\D", "", w["text"]), "") or re.sub(r"[^a-z]", "", w["text"].lower())
        groups = re.findall(r"[aeiouy]+|[^aeiouy]+", spoken) or ["b"]
        d = (w["end"] - w["start"]) / len(groups)
        for k, g in enumerate(groups):
            cues.append({"start": round(w["start"] + k * d, 3), "end": round(w["start"] + (k + 1) * d, 3),
                         "value": shape(g)})
        prev_end = w["end"]
    cues.append({"start": prev_end, "end": prev_end + 5, "value": "X"})
    return cues


# ---------- markup ----------

E = html.escape


def icon(name, cls=""):
    paths = {
        "book": '<path d="M2 3h6a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H2zM22 3h-6a3 3 0 0 0-3 3v14a2 2 0 0 1 2-2h7z"/>',
        "check": '<path d="M20 6 9 17l-5-5"/>',
        "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
        "warn": '<path d="M12 3 2 21h20zM12 10v5M12 18h.01"/>',
        "doc": '<path d="M6 2h8l5 5v15H6z"/><path d="M14 2v5h5"/>',
    }
    return (f'<svg class="ico {cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>')


CLAUDE_MARK = ('<svg class="cmark" viewBox="0 0 24 24"><g stroke="#d97757" stroke-width="2.6" stroke-linecap="round">'
               + "".join(f'<line x1="12" y1="12" x2="{12 + 9 * __import__("math").cos(a * 0.5236):.1f}" '
                         f'y2="{12 + 9 * __import__("math").sin(a * 0.5236):.1f}"/>' for a in range(12))
               + "</g></svg>")


def card_html(i, c, beats):
    t, sid = c["type"], f"s{i}"
    owner, name = beats["repo_owner"], beats["repo_name"]
    if t == "terminal":
        rows = []
        for k, (kind, txt) in enumerate(c["lines"]):
            if kind == "cmd":
                rows.append(f'<div class="tl cmd reveal" ><span class="gt">&gt;</span> {E(txt)}</div>')
            elif kind == "ok":
                rows.append(f'<div class="tl ok reveal">{icon("check")} {E(txt)}</div>')
            else:
                rows.append(f'<div class="tl dim reveal">{E(txt)}</div>')
        body = "".join(rows)
        return (f'<div class="card term"><div class="bar"><i class="d r"></i><i class="d y"></i><i class="d g"></i>'
                f'{CLAUDE_MARK}<b>Claude Code</b></div><div class="body">{body}</div></div>')
    if t == "stats":
        cols = "".join(f'<div class="stat reveal"><div class="num" data-to="{E(n)}">0</div><div class="lab">{E(l)}</div></div>'
                       for n, l in c["items"])
        return f'<div class="card stats"><div class="row">{cols}</div><div class="src">{E(c["source"])}</div></div>'
    if t == "docs":
        cells = "".join(f'<span class="doc">{icon("doc")}</span>' for _ in range(c["count"]))
        return f'<div class="card docs"><div class="grid">{cells}</div><div class="src reveal">{E(c["label"])}</div></div>'
    if t == "quote":
        txt = re.sub(r"\[(.+?)\]", lambda m: f'<mark>{E(m.group(1))}</mark>', E(c["text"]))
        return (f'<div class="card quote"><div class="bar">{icon("book")}<span class="mono">{E(c["file"])}</span></div>'
                f'<div class="body"><p class="reveal">{txt}</p></div></div>')
    if t in ("repo", "teaser"):
        if t == "teaser":
            title = (f'<span class="own">{E(c["owner"])}</span> / <span class="blur">VoiceStudio</span>'
                     f'<span class="pub">{icon("lock")} next video</span>')
        else:
            title = f'<span class="own">{E(owner)}</span> / <b>{E(name)}</b><span class="pub">Public</span>'
        extra = ""
        if c.get("chips"):
            extra = '<div class="chips">' + "".join(f'<span class="chip reveal">{E(x)}</span>' for x in c["chips"]) + "</div>"
        if c.get("checks"):
            extra = "".join(f'<div class="tl ok reveal">{icon("check")} {E(x)}</div>' for x in c["checks"])
        foot = '<div class="foot reveal"><span class="lic">MIT license</span></div>' if t == "repo" else ""
        return (f'<div class="card repo"><div class="rtitle">{icon("book")}{title}</div>'
                f'<div class="desc reveal">{E(c["desc"])}</div>{extra}{foot}</div>')
    if t == "comment":
        return (f'<div class="card comment"><div class="cmhead"><img class="ava" src="assets/avatar.png" alt="">'
                f'<b>{E(c["handle"])}</b><span class="dim">Reels</span></div>'
                f'<div class="cmbox"><span class="typed">' + "".join(f'<span class="ch">{E(ch)}</span>' for ch in c["text"]) + '</span><span class="caret"></span>'
                f'<span class="post">Post</span></div><div class="src">I&#39;ll DM you the link</div></div>')
    if t == "note":
        return (f'<div class="card note"><div class="nh">{icon("warn")} {E(c["head"])}</div>'
                f'<div class="nb reveal">{E(c["body"])}</div></div>')
    if t == "badge":
        return (f'<div class="card badge"><div class="bigcheck">{icon("check")}</div><div><div class="bh">{E(c["head"])}</div>'
                f'<div class="bb reveal">{E(c["body"])}</div></div></div>')
    raise ValueError(t)


CSS = """
@font-face { font-family: "Inter"; src: url("assets/fonts/Inter.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "JetBrains Mono"; src: url("assets/fonts/JetBrainsMono.woff2") format("woff2"); font-weight: 100 800; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #f3f4f7; }
#root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #f3f4f7;
  font-family: "Inter", sans-serif; color: #1f2328; }
.mono, .tl, .pill, .path, .chip, .src, .lic { font-family: "JetBrains Mono", monospace; }
.step { position: absolute; inset: 0; }
.pill { position: absolute; left: 72px; top: 296px; padding: 6px 18px; border-radius: 22px; background: #ddf4ff;
  border: 2px solid #b6e3ff; color: #0969da; font-size: 34px; font-weight: 500; }
.path { position: absolute; right: 70px; top: 302px; font-size: 32px; color: #57606a; }
.path b { color: #0969da; }
.title { position: absolute; left: 72px; top: 376px; width: 938px; }
.tline { font-weight: 800; font-size: 124px; line-height: 1.04; letter-spacing: -0.045em; white-space: nowrap; }
.tline.l2 { color: #0969da; }
.tw { display: inline-block; margin-right: 0.24em; }
.tw:last-child { margin-right: 0; }
.rule { position: absolute; left: 72px; top: 664px; width: 938px; height: 3px; background: #d0d7de; }
.cardwrap { position: absolute; left: 72px; top: 720px; width: 938px; }
.card { background: #fff; border: 2px solid #d0d7de; border-radius: 14px; box-shadow: 0 8px 24px rgba(31,35,40,.07); overflow: hidden; }
.bar { display: flex; align-items: center; gap: 14px; height: 76px; padding: 0 26px; background: #f6f8fa; border-bottom: 2px solid #d0d7de;
  font-size: 34px; }
.d { width: 20px; height: 20px; border-radius: 50%; display: inline-block; }
.d.r { background: #ff5f57; } .d.y { background: #febc2e; } .d.g { background: #28c840; }
.cmark { width: 34px; height: 34px; margin-left: 10px; }
.body { padding: 26px 28px 30px; }
.tl { font-size: 32px; line-height: 1.35; padding: 8px 0; display: flex; align-items: center; gap: 14px; white-space: nowrap; }
.tl.cmd { background: #f6f8fa; border: 2px solid #d8dee4; border-radius: 10px; padding: 12px 18px; margin: 6px 0; }
.tl .gt { color: #bc4c00; font-weight: 700; }
.tl.ok { color: #1a7f37; } .tl.dim { color: #57606a; }
.ico { width: 1em; height: 1em; flex: none; }
.stats .row { display: flex; padding: 34px 20px 10px; }
.stat { flex: 1; text-align: center; }
.num { font-size: 132px; font-weight: 800; letter-spacing: -0.05em; color: #0969da; line-height: 1; }
.lab { font-size: 30px; color: #57606a; margin-top: 10px; font-weight: 500; }
.src { font-size: 26px; color: #8c959f; text-align: center; padding: 14px 0 26px; }
.docs .grid { display: grid; grid-template-columns: repeat(23, 1fr); gap: 6px; padding: 30px 28px 6px; color: #0969da; }
.doc { display: block; font-size: 32px; line-height: 0; }
.quote p { font-size: 40px; line-height: 1.42; font-weight: 500; }
mark { background: #fff8c5; color: #1f2328; padding: 0 6px; border-radius: 6px; }
.quote .bar { gap: 16px; color: #57606a; }
.repo { padding: 30px 32px 30px; }
.rtitle { display: flex; align-items: center; gap: 14px; font-size: 40px; color: #0969da; white-space: nowrap; }
.rtitle .ico { color: #57606a; }
.own { font-weight: 500; }
.pub { margin-left: 8px; font-size: 24px; color: #57606a; border: 2px solid #d0d7de; border-radius: 20px; padding: 2px 14px;
  display: inline-flex; gap: 8px; align-items: center; }
.blur { filter: blur(9px); font-weight: 700; }
.desc { font-size: 36px; color: #1f2328; margin: 18px 0 6px; }
.chips { display: flex; gap: 14px; margin-top: 18px; flex-wrap: wrap; }
.chip { font-size: 30px; color: #0969da; background: #ddf4ff; border-radius: 22px; padding: 6px 18px; }
.foot { margin-top: 20px; }
.lic { font-size: 26px; color: #57606a; }
.comment { padding: 30px 32px 0; }
.cmhead { display: flex; align-items: center; gap: 16px; font-size: 34px; }
.cmhead .dim { color: #8c959f; font-size: 28px; }
.ava { width: 72px; height: 72px; border-radius: 50%; object-fit: cover; border: 2px solid #d0d7de; }
.cmbox { margin-top: 24px; height: 104px; border: 2px solid #d0d7de; border-radius: 52px; display: flex; align-items: center;
  padding: 0 34px; font-size: 46px; font-weight: 700; }
.caret { width: 4px; height: 52px; background: #0969da; margin-left: 4px; }
.post { margin-left: auto; color: #0969da; font-weight: 700; font-size: 34px; }
.note { background: #fff8c5; border-color: #d4a72c; padding: 34px 34px; }
.nh { font-size: 42px; font-weight: 800; display: flex; gap: 16px; align-items: center; color: #7d4e00; }
.nb { font-size: 34px; margin-top: 16px; color: #4d2d00; line-height: 1.35; }
.badge { display: flex; gap: 30px; align-items: center; padding: 36px 34px; border-color: #4ac26b; background: #f0fff4; }
.bigcheck { width: 120px; height: 120px; border-radius: 50%; background: #1a7f37; color: #fff; display: grid; place-items: center;
  font-size: 72px; flex: none; }
.bh { font-size: 52px; font-weight: 800; letter-spacing: -0.03em; }
.bb { font-size: 32px; color: #57606a; margin-top: 8px; }
#char { position: absolute; left: 72px; bottom: 0; width: 660px; height: 800px; }
.pose { position: absolute; left: 0; bottom: 0; width: 660px; }
.pose img.base, .pose img.blink { position: absolute; left: 0; top: 0; width: 100%; }
.pose img.mouth { position: absolute; opacity: 0; }
.pose img.blink { opacity: 0; }
#gridmeter { position: absolute; left: 748px; top: 1712px; display: grid; grid-template-columns: repeat(13, 18px);
  grid-auto-rows: 18px; gap: 2px; }
.gcell i { display: block; width: 18px; height: 18px; background: #ebedf0; border-radius: 3px; }
"""


def build(slug):
    beats = json.load(open(os.path.join(ROOT, "scripts", slug, "beats.json")))
    steps = beats["steps"]
    proj = os.path.join(ROOT, "projects", slug)
    os.makedirs(os.path.join(proj, "assets", "fonts"), exist_ok=True)

    words = script_words(steps)
    voice = sorted(glob.glob(os.path.join(ROOT, "assets", "voice", f"{slug}.*")))
    voice = [v for v in voice if v.rsplit(".", 1)[-1].lower() in ("wav", "m4a", "mp3", "aac")]
    work = os.path.join(proj, "work")
    os.makedirs(work, exist_ok=True)
    if voice:
        vo = os.path.join(proj, "assets", "vo.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voice[0], "-ac", "1", "-ar", "48000", vo], check=True)
        wj, cj = os.path.join(work, "words.json"), os.path.join(work, "cues.json")
        if not os.path.exists(wj) or os.path.getmtime(wj) < os.path.getmtime(voice[0]):
            subprocess.run([os.path.join(ROOT, ".venv", "bin", "python"), os.path.join(ROOT, "scripts", "transcribe.py"),
                            vo, wj, "small.en"], check=True)
        if not os.path.exists(cj) or os.path.getmtime(cj) < os.path.getmtime(voice[0]):
            dialog = os.path.join(work, "dialog.txt")
            open(dialog, "w").write(" ".join(s["say"] for s in steps))
            subprocess.run([os.path.join(ROOT, "scripts", "lipsync.sh"), vo, cj, dialog], check=True)
        total = whisper_times(words, wj)
        audio_dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                   "-of", "csv=p=0", vo]).decode())
        total = max(total, audio_dur + 0.3)
        cues = json.load(open(cj))["mouthCues"]
        mode = "voice"
    else:
        total = synth_times(words)
        cues = synth_cues(words)
        mode = "animatic"
    total = round(total * FPS) / FPS

    # step windows: start just before the first word, end where the next starts
    starts = []
    for i in range(len(steps)):
        first = next(w for w in words if w["step"] == i)
        starts.append(0.0 if i == 0 else round(max(0.0, first["start"] - 0.12), 3))
    ends = starts[1:] + [total]

    # headline words -> spoken word times
    reveals = []
    for i, st in enumerate(steps):
        sw = [w for w in words if w["step"] == i]
        used = set()
        lines = []
        for li, line in enumerate(st["title"]):
            toks = []
            for tok in line.split():
                t = starts[i] + 0.05
                for k, w in enumerate(sw):
                    if k not in used and norm(w["text"]) == norm(tok):
                        used.add(k)
                        t = max(starts[i], w["start"] - 0.05)
                        break
                toks.append((tok, round(t, 3)))
            lines.append(toks)
        reveals.append(lines)

    # assets
    for f in ("Inter.woff2", "JetBrainsMono.woff2"):
        shutil.copy(os.path.join(ROOT, "assets", "fonts", f), os.path.join(proj, "assets", "fonts", f))
    metas = {}
    for p in POSES:
        d = os.path.join(proj, "assets", "rig", p)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(os.path.join(RIG, p)):
            shutil.copy(os.path.join(RIG, p, f), d)
        metas[p] = json.load(open(os.path.join(RIG, p, "meta.json")))
    from PIL import Image
    fb = Image.open(os.path.join(RIG, "front", "base.png"))
    m = metas["front"]["head"]
    fb.crop((int(m["cx"] - 190), int(m["cy"] - 190), int(m["cx"] + 190), int(m["cy"] + 190))).resize((144, 144)).save(
        os.path.join(proj, "assets", "avatar.png"))

    # DOM
    k = CHAR_W / 1000
    pose_html = []
    for p in POSES:
        mm = metas[p]
        mo = mm["mouth"]
        w, h = mo["w"] * k, mo["h"] * k
        mouths = "".join(
            f'<img class="mouth m-{s}" src="assets/rig/{p}/mouth_{s}.png" alt="" style="left:{mo["cx"] * k - w / 2:.1f}px;'
            f'top:{mo["cy"] * k - h / 2:.1f}px;width:{w:.1f}px;height:{h:.1f}px;transform:rotate({mo["rot"]}deg)">'
            for s in SHAPES)
        blink = f'<img class="blink" src="assets/rig/{p}/blink.png" alt="">' if p in BLINKS else ""
        pose_html.append(f'<div class="pose" id="pose-{p}" style="height:{mm["height"] * k:.1f}px">'
                         f'<img class="base" src="assets/rig/{p}/base.png" alt="">{blink}{mouths}</div>')

    step_html = []
    for i, st in enumerate(steps):
        lines = "".join(
            f'<div class="tline l{li + 1}">' + "".join(f'<span class="tw" data-t="{t}">{E(tok)}</span>' for tok, t in ln)
            + "</div>" for li, ln in enumerate(reveals[i]))
        step_html.append(
            f'<section class="step clip" id="s{i}" data-start="{starts[i]}" data-duration="{round(ends[i] - starts[i], 3)}" '
            f'data-track-index="1"><div class="pill">$ {i + 1:02d}/{len(steps):02d}</div>'
            f'<div class="title">{lines}</div><div class="cardwrap">{card_html(i, st["card"], beats)}</div></section>')

    cells = "".join('<span class="gcell"><i></i></span>' for _ in range(65))
    audio = (f'<audio id="vo" src="assets/vo.wav" data-start="0" data-duration="{total}" data-track-index="3" '
             f'data-volume="1"></audio>') if mode == "voice" else ""
    data = {"total": total, "steps": [{"start": s, "end": e, "pose": st["pose"], "card": st["card"]["type"],
                                       "on": next((w["start"] for w in words if w["step"] == i
                                                   and norm(w["text"]) == norm(st["card"].get("on", "~"))), None)}
                                      for i, (s, e, st) in enumerate(zip(starts, ends, steps))],
            "cues": [[round(c["start"], 3), c["value"]] for c in cues if c["start"] < total],
            "words": [[w["start"], w["end"]] for w in words]}

    page = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>{E(slug)}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920" data-fps="{FPS}">
  <div class="path">{E(beats["repo_owner"])} / <b>{E(beats["repo_name"])}</b></div>
  <div class="rule"></div>
  {"".join(step_html)}
  <div id="char">{"".join(pose_html)}</div>
  <div id="gridmeter">{cells}</div>
  {audio}
</div>
<script>
const DATA = {json.dumps(data)};
const GREENS = ["#9be9a8", "#40c463", "#30a14e", "#216e39"];
function rnd(i) {{ const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); }}

function fitTitles() {{
  document.querySelectorAll(".tline").forEach((el) => {{
    let fs = 124;
    el.style.fontSize = fs + "px";
    while (el.scrollWidth > 938 && fs > 60) {{ fs -= 2; el.style.fontSize = fs + "px"; }}
  }});
}}

function build() {{
  fitTitles();
  const tl = gsap.timeline({{ paused: true }});
  const T = DATA.total;

  // headline words pop on the spoken word
  document.querySelectorAll(".tw").forEach((el) => {{
    const t = parseFloat(el.dataset.t);
    tl.fromTo(el, {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "back.out(2)" }}, t);
  }});

  DATA.steps.forEach((st, i) => {{
    const s = document.getElementById("s" + i);
    const card = s.querySelector(".card");
    const dur = st.end - st.start;
    tl.fromTo(card, {{ opacity: 0, y: 40, scale: 0.97 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.32, ease: "power3.out" }}, st.start + 0.06);
    tl.fromTo(s.querySelector(".pill"), {{ scale: 0.8 }}, {{ scale: 1, duration: 0.25, ease: "back.out(3)" }}, st.start);
    const rev = s.querySelectorAll(".reveal");
    const gap = Math.min(0.4, (dur * 0.6) / Math.max(1, rev.length));
    rev.forEach((el, k) => tl.fromTo(el, {{ opacity: 0, x: -18 }}, {{ opacity: 1, x: 0, duration: 0.25, ease: "power2.out" }}, st.start + 0.3 + k * gap));
    s.querySelectorAll(".num").forEach((el, k) => {{
      const to = parseInt(el.dataset.to, 10), o = {{ v: 0 }};
      tl.to(o, {{ v: to, duration: 0.7, ease: "power2.out", onUpdate: () => (el.textContent = Math.round(o.v)) }}, st.start + 0.3 + k * gap);
    }});
    const docs = s.querySelectorAll(".doc");
    if (docs.length) tl.fromTo(docs, {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.18, stagger: Math.min(0.025, (dur * 0.7) / docs.length), ease: "back.out(2)" }}, st.start + 0.25);
    const chars = s.querySelectorAll(".typed .ch");
    const t0 = st.on != null ? st.on : st.start + 0.6;
    chars.forEach((el, c) => tl.fromTo(el, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.01 }}, t0 + c * 0.07));
    // pose for this step
    ["front", "explain", "skeptic"].forEach((p) => tl.set("#pose-" + p, {{ opacity: p === st.pose ? 1 : 0 }}, st.start));
    if (i === 0 || DATA.steps[i - 1].pose !== st.pose)
      tl.fromTo("#char", {{ scale: 0.95, y: 14 }}, {{ scale: 1, y: 0, duration: 0.3, ease: "back.out(2.5)", transformOrigin: "50% 100%" }}, st.start);
    // contribution-grid progress, 5 cells per step
    const cells = document.querySelectorAll("#gridmeter i");
    for (let c = 0; c < 5; c++) {{
      const idx = i * 5 + c;
      if (idx >= cells.length) break;
      const col = Math.floor(idx / 5), row = idx % 5, cell = document.querySelectorAll("#gridmeter .gcell")[row * 13 + col];
      tl.to(cell.querySelector("i"), {{ backgroundColor: GREENS[Math.floor(rnd(idx) * 4)], duration: 0.12 }}, st.start + 0.15 + c * 0.06);
    }}
  }});

  // mouth: Rhubarb cues
  tl.set(".m-X", {{ opacity: 1 }}, 0);
  let prev = "X";
  DATA.cues.forEach(([t, v]) => {{
    if (v === prev) return;
    tl.set(".m-" + prev, {{ opacity: 0 }}, t);
    tl.set(".m-" + v, {{ opacity: 1 }}, t);
    prev = v;
  }});

  // idle life: breathing bob + blinks every ~3s
  tl.fromTo("#char .pose", {{ y: 0 }}, {{ y: -7, duration: 1.4, ease: "sine.inOut", yoyo: true, repeat: Math.floor(T / 1.4) }}, 0);
  for (let t = 1.7, n = 0; t < T - 0.3; t += 2.6 + rnd(n++) * 1.6) {{
    tl.set(".blink", {{ opacity: 1 }}, t);
    tl.set(".blink", {{ opacity: 0 }}, t + 0.12);
  }}
  // talking emphasis: a small nod at each sentence start
  DATA.steps.forEach((st) => tl.fromTo("#char .pose", {{ rotation: 0 }}, {{ rotation: 0.6, duration: 0.18, yoyo: true, repeat: 1, transformOrigin: "50% 70%" }}, st.start + 0.1));

  window.__timelines["main"] = tl;
}}
document.fonts.ready.then(build);
</script>
</body>
</html>
"""
    open(os.path.join(proj, "index.html"), "w").write(page)
    json.dump({"mode": mode, "total": total, "words": words, "steps": data["steps"]},
              open(os.path.join(work, "timing.json"), "w"), indent=1)
    print(f"{slug}: {mode}, {total:.2f}s, {len(steps)} steps, {len(cues)} mouth cues")
    for i, s in enumerate(data["steps"]):
        print(f"  {i + 1:02d} {s['start']:6.2f}-{s['end']:6.2f}  {steps[i]['pose']:8s} {steps[i]['say']}")


if __name__ == "__main__":
    build(sys.argv[1])
