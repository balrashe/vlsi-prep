"""Generate the HyperFrames project for one reel from its beat sheet.

Usage: build_video.py <slug>

Inputs  scripts/<slug>/beats.json             beats, headline words, cards, poses
        assets/voice/<slug>.(wav|m4a|mp3)     your recording (optional; without it the timing is synthetic)
        assets/character/voxel/               the Minecraft-style character + room (build_voxel.py, voxel_scene.js)
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numwords  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOX = os.path.join(ROOT, "assets", "character", "voxel")    # build_voxel.py
SHAPES = "XABCDEFGH"
FPS = 30

NUM_WORDS = {"69": "sixtynine", "20": "twenty", "1": "one", "2025": "twentytwentyfive", "2026": "twentytwentysix"}


def norm(w):
    """Compare script words and Whisper words: digits become words on both sides (311 == three hundred eleven)."""
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    if w in NUM_WORDS:
        return NUM_WORDS[w]
    return re.sub(r"[^a-z]", "", numwords.spoken(w)) if w.isdigit() else w


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




def chars(text):
    """Text as one span per character so it can type on."""
    return "".join(f'<span class="ch">{E(c)}</span>' for c in text)


def anim(kind, f, extra=""):
    """data-f: when it appears, as a fraction of the beat (keeps working when the voice timing changes)."""
    return f'data-anim="{kind}" data-f="{f}" {extra}'


def card_html(i, c, beats):
    t = c["type"]
    owner, name = beats["repo_owner"], beats["repo_name"]
    if t == "stats":
        cols = "".join(
            f'<div class="stat" {anim("stamp", 0.08 + k * 0.26)}><div class="num">{E(n)}</div><div class="lab">{E(l)}</div></div>'
            for k, (n, l) in enumerate(c["items"]))
        return f'<div class="card stats"><div class="row">{cols}</div><div class="src">{E(c["source"])}</div></div>'
    if t == "apply":
        jobs = "".join(f'<span class="jobchip" {anim("pop", 0.05 + k * 0.03)}>{E(j)}</span>' for k, j in enumerate(c["jobs"]))
        return (f'<div class="card apply"><div class="abar"><span class="inlogo">in</span><b>Easy Apply</b>'
                f'<span class="ctr" {anim("count", 0.62, f"data-from=1 data-to={c["count"]} data-d=0.9")}>1</span>'
                f'<span class="ctrof">/ {c["count"]} sent</span></div>'
                f'<div class="abody"><div class="jobs">{jobs}</div>'
                f'<div class="field"><span class="flab">Resume</span><span class="file" {anim("pop", 0.12)}>'
                f'{icon("doc")} CV_tailored.pdf {icon("check", "okc")}</span></div>'
                f'<div class="field"><span class="flab">Cover letter <i class="drafted">{CLAUDE_MARK} drafted by Claude</i></span>'
                f'<div class="letter" {anim("type", 0.16, "data-d=0.42")}>{chars(c["letter"])}</div></div>'
                f'<div class="submit" {anim("press", 0.58, "data-off=0.66")}>Submit application</div>'
                f'<div class="submit sent" {anim("pop", 0.66)}>{icon("check")} Application sent</div></div></div>')
    if t == "profile":
        return (f'<div class="card profile"><img class="pava" src="assets/people/{c["avatar"]}" alt="">'
                f'<div class="pinfo"><div class="pname">{E(c["name"])}</div><div class="phandle">@{E(c["handle"])} · GitHub</div>'
                f'<div class="prole" {anim("pop", 0.05)}>{E(c["role"])}</div></div>'
                f'<div class="stamp" {anim("stamp", 0.55)}>{E(c["stamp"])}</div>'
                f'<div class="psrc">{E(c["source"])}</div></div>')
    if t == "repo":
        chips = "".join(f'<span class="chip" {anim("pop", 0.25 + k * 0.1)}>{E(x)}</span>' for k, x in enumerate(c.get("chips", [])))
        checks = "".join(f'<div class="tl ok" {anim("slide", 0.3 + k * 0.2)}>{icon("check")} {E(x)}</div>'
                         for k, x in enumerate(c.get("checks", [])))
        badge = f'<span class="mit" {anim("stamp", 0.15)}>MIT</span>' if c.get("mit") else ""
        return (f'<div class="card repo"><div class="rtitle">{icon("book")}<span class="own">{E(owner)}</span> / <b>{E(name)}</b>'
                f'<span class="pub">Public</span>{badge}</div><div class="desc">{E(c["desc"])}</div>'
                + (f'<div class="chips">{chips}</div>' if chips else "") + checks + "</div>")
    if t == "rank":
        rows = "".join(
            f'<div class="rrow" {anim("slide", 0.06 + k * 0.1)}><span class="rjob">{E(j)}</span>'
            f'<span class="rtrack"><span class="rbar {lvl}" {anim("grow", 0.18 + k * 0.1)} style="width:{w}%"></span></span>'
            f'<span class="rlab {lvl}">{E(lab)}</span></div>' for k, (j, w, lvl, lab) in enumerate(c["rows"]))
        head = c.get("head", "Claude Code")
        return (f'<div class="card term"><div class="bar"><i class="d r"></i><i class="d y"></i><i class="d g"></i>'
                f'{CLAUDE_MARK if head == "Claude Code" else ""}<b>{E(head)}</b><span class="cmd2">{E(c.get("cmd", "/rank"))}</span></div>'
                f'<div class="body">{rows}</div></div>')
    if t == "cvdiff":
        rows = "".join(f'<div class="dl {k}" {anim("slide", 0.08 + n * 0.14)}><span class="dk">{"-" if k == "del" else "+" if k == "add" else " "}</span>{E(x)}</div>'
                       for n, (k, x) in enumerate(c["lines"]))
        return (f'<div class="card doc"><div class="dbar">{icon("doc")}<span class="mono">{E(c["file"])}</span>'
                f'<span class="tag" {anim("stamp", 0.75)}>tailored</span></div><div class="dbody">{rows}</div></div>')
    if t == "chat":
        rows = "".join(f'<div class="bub {who}" {anim("pop", 0.06 + n * 0.3)}><b>{E(label)}</b>'
                       f'<span {anim("type", 0.08 + n * 0.3, "data-d=0.24")}>{chars(x)}</span></div>'
                       for n, (who, label, x) in enumerate(c["msgs"]))
        return f'<div class="card chat"><div class="chead">{CLAUDE_MARK}<b>/interview</b><span>mock round</span></div>{rows}</div>'
    if t == "dm":
        return (f'<div class="card dm"><div class="cmrow" {anim("pop", 0.1)}><span class="fava">?</span>'
                f'<div><b>someone_building</b><div class="ctext">{E(c["word"])}</div></div></div>'
                f'<div class="kw" {anim("stamp", 0.22)}>{E(c["word"])}</div>'
                f'<div class="dmrow" {anim("slide", 0.55)}><img class="ava" src="assets/avatar.png" alt="">'
                f'<div><b>{E(c["handle"])}</b><span class="dmlab">sent you a message</span>'
                f'<div class="dmtext" {anim("type", 0.6, "data-d=0.3")}>{chars(c["dm"])}</div></div></div></div>')
    if t == "terminal":
        rows = []
        for k, (kind, txt) in enumerate(c["lines"]):
            a = anim("slide", round(0.08 + k * 0.17, 2))
            if kind == "cmd":
                rows.append(f'<div class="tl cmd" {a}><span class="gt">&gt;</span> {E(txt)}</div>')
            elif kind == "ok":
                rows.append(f'<div class="tl ok" {a}>{icon("check")} {E(txt)}</div>')
            else:
                rows.append(f'<div class="tl dim" {a}>{E(txt)}</div>')
        head = c.get("head", "Claude Code")                # the window title says where this actually runs
        return (f'<div class="card term"><div class="bar"><i class="d r"></i><i class="d y"></i><i class="d g"></i>'
                f'{CLAUDE_MARK if head == "Claude Code" else ""}<b>{E(head)}</b></div><div class="body">{"".join(rows)}</div></div>')
    if t == "note":
        return (f'<div class="card note" {anim("shake", 0.05)}><div class="nh">{icon("warn")} {E(c["head"])}</div>'
                f'<div class="nb" {anim("slide", 0.3)}>{E(c["body"])}</div></div>')
    if t == "contract":
        return (f'<div class="card contract"><div class="ch1">{E(c["head"])}</div><div class="cline"></div><div class="cline s"></div>'
                f'<div class="crow"><div><div class="clab">Role</div><div class="cval">{E(c["role"])}</div></div>'
                f'<div><div class="clab">Start</div><div class="cval">{E(c["start"])}</div></div></div>'
                f'<svg class="sig" viewBox="0 0 300 70"><path {anim("draw", 0.3)} d="M6 50 C 30 10, 52 10, 50 44 S 80 66, 96 30 '
                f'S 128 8, 132 40 S 160 62, 176 34 S 206 14, 214 42 S 250 56, 294 24"/></svg>'
                f'<div class="signed" {anim("stamp", 0.62)}>{icon("check")} Signed</div></div>')
    if t == "versus":
        a, b = c["left"], c["right"]
        return (f'<div class="card versus"><div class="vs l" {anim("slide", 0.05)}><div class="vlab">{E(a["label"])}</div>'
                f'<div class="vnum">{E(a["value"])}</div><div class="vsub">{E(a["sub"])}</div></div>'
                f'<div class="vsx" {anim("stamp", 0.3)}>vs</div>'
                f'<div class="vs r" {anim("stamp", 0.45)}><div class="vlab">{E(b["label"])}</div>'
                f'<div class="vnum">{E(b["value"])}</div><div class="vsub">{E(b["sub"])}</div></div>'
                f'<div class="src vsrc">{E(c["source"])}</div></div>')
    if t == "shot":
        return (f'<div class="card shot"><img src="assets/shots/{E(c["img"])}" alt="" {anim("pop", 0.02)}>'
                f'<div class="src">{E(c["credit"])}</div></div>')
    if t == "teaser":
        bars = "".join(f'<i style="height:{18 + int(40 * abs(__import__("math").sin(k * 1.7)))}px" {anim("pop", round(0.1 + k * 0.012, 3))}></i>'
                       for k, _ in enumerate(range(40)))
        return (f'<div class="card repo teaser"><div class="rtitle">{icon("book")}<span class="own">{E(c["owner"])}</span> / '
                f'<span class="blur">VoiceStudio</span><span class="pub">{icon("lock")} next video</span></div>'
                f'<div class="wave">{bars}</div><div class="desc">{E(c["desc"])}</div></div>')
    raise ValueError(t)


CSS = """
@font-face { font-family: "Inter"; src: url("assets/fonts/Inter.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "JetBrains Mono"; src: url("assets/fonts/JetBrainsMono.woff2") format("woff2"); font-weight: 100 800; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #1c120b; }
#root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #1c120b;
  font-family: "Inter", sans-serif; color: #1f2328; }
#mc { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; display: block; }
#shade { position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(180deg, rgba(12,7,4,.72) 0%, rgba(12,7,4,.35) 38%, rgba(12,7,4,0) 55%),
              radial-gradient(ellipse at 55% 78%, rgba(0,0,0,0) 45%, rgba(0,0,0,.5) 100%); }
.mono, .tl, .pill, .path, .chip, .src, .lic, .cmd2, .dl, .flab, .file, .psrc, .phandle { font-family: "JetBrains Mono", monospace; }
.step { position: absolute; inset: 0; }
.pill { position: absolute; left: 72px; top: 296px; padding: 6px 18px; border-radius: 22px; background: rgba(255,255,255,.12);
  border: 2px solid rgba(255,255,255,.28); color: #d6ecff; font-size: 34px; font-weight: 500; }
.path { position: absolute; right: 70px; top: 302px; font-size: 32px; color: rgba(255,255,255,.72); }
.path b { color: #79c0ff; }
.title { position: absolute; left: 72px; top: 376px; width: 938px; }
.tline { font-weight: 800; font-size: 124px; line-height: 1.04; letter-spacing: -0.045em; white-space: nowrap; color: #fff;
  text-shadow: 0 6px 24px rgba(0,0,0,.55); }
.tline.l2 { color: #79c0ff; }
.tw { display: inline-block; margin-right: 0.24em; }
.tw:last-child { margin-right: 0; }
.rule { position: absolute; left: 72px; top: 664px; width: 938px; height: 3px; background: rgba(255,255,255,.22); }
.cardwrap { position: absolute; left: 72px; top: 712px; width: 938px; }
.card { background: #fff; border-radius: 18px; box-shadow: 0 18px 50px rgba(0,0,0,.45); overflow: hidden; }
.bar { display: flex; align-items: center; gap: 14px; height: 76px; padding: 0 26px; background: #f6f8fa; border-bottom: 2px solid #d0d7de; font-size: 34px; }
.cmd2 { margin-left: auto; color: #0969da; font-size: 30px; }
.d { width: 20px; height: 20px; border-radius: 50%; display: inline-block; }
.d.r { background: #ff5f57; } .d.y { background: #febc2e; } .d.g { background: #28c840; }
.cmark { width: 34px; height: 34px; flex: none; }
.body { padding: 22px 28px 26px; }
.tl { font-size: 31px; line-height: 1.35; padding: 7px 0; display: flex; align-items: center; gap: 14px; white-space: nowrap; }
.tl.cmd { background: #f6f8fa; border: 2px solid #d8dee4; border-radius: 10px; padding: 11px 18px; margin: 6px 0; }
.tl .gt { color: #bc4c00; font-weight: 700; }
.tl.ok { color: #1a7f37; } .tl.dim { color: #57606a; }
.ico { width: 1em; height: 1em; flex: none; }
.stats .row { display: flex; padding: 34px 20px 8px; }
.stat { flex: 1; text-align: center; }
.num { font-size: 140px; font-weight: 800; letter-spacing: -0.05em; color: #0969da; line-height: 1; }
.lab { font-size: 30px; color: #57606a; margin-top: 10px; font-weight: 600; }
.src { font-size: 25px; color: #8c959f; text-align: center; padding: 12px 0 24px; }
/* job application */
.abar { display: flex; align-items: center; gap: 16px; height: 84px; padding: 0 28px; background: #f3f6f8; border-bottom: 2px solid #dfe3e8; font-size: 36px; }
.inlogo { width: 50px; height: 50px; border-radius: 9px; background: #0a66c2; color: #fff; font-weight: 800; font-size: 34px;
  display: grid; place-items: center; letter-spacing: -0.04em; }
.ctr { margin-left: auto; font-size: 48px; font-weight: 800; color: #0a66c2; }
.ctrof { font-size: 28px; color: #57606a; }
.abody { padding: 20px 28px 26px; }
.jobs { display: flex; gap: 12px; margin-bottom: 14px; }
.jobchip { font-size: 26px; padding: 6px 16px; border-radius: 18px; background: #eef3f8; color: #1f2328; font-weight: 600; }
.field { margin: 12px 0; }
.flab { font-size: 24px; color: #57606a; display: flex; align-items: center; gap: 10px; }
.drafted { font-style: normal; color: #bc4c00; display: inline-flex; align-items: center; gap: 6px; }
.drafted .cmark { width: 26px; height: 26px; }
.file { display: inline-flex; align-items: center; gap: 12px; margin-top: 8px; font-size: 28px; padding: 10px 16px; border: 2px solid #d0d7de; border-radius: 10px; }
.okc { color: #1a7f37; }
.letter { margin-top: 8px; min-height: 120px; font-size: 29px; line-height: 1.35; padding: 14px 18px; border: 2px solid #0a66c2; border-radius: 12px; white-space: pre-wrap; }
.submit { margin-top: 18px; height: 78px; border-radius: 40px; background: #0a66c2; color: #fff; font-size: 34px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; gap: 14px; }
.submit.sent { position: relative; margin-top: -78px; background: #1a7f37; }
/* profile */
.profile { position: relative; display: flex; gap: 30px; align-items: center; padding: 30px 32px 92px; }
.pava { width: 190px; height: 190px; border-radius: 50%; object-fit: cover; border: 5px solid #fff; box-shadow: 0 0 0 3px #d0d7de; flex: none; }
.pname { font-size: 52px; font-weight: 800; letter-spacing: -0.03em; }
.phandle { font-size: 26px; color: #57606a; margin-top: 4px; }
.prole { display: inline-block; margin-top: 14px; font-size: 32px; font-weight: 700; padding: 6px 18px; border-radius: 22px; background: #ddf4ff; color: #0969da; }
.stamp { position: absolute; right: 26px; bottom: 18px; font-size: 32px; font-weight: 800; color: #cf222e; border: 5px solid #cf222e;
  border-radius: 12px; padding: 6px 16px; background: rgba(255,255,255,.9); text-transform: uppercase; letter-spacing: 0.02em; }
.psrc { position: absolute; left: 32px; bottom: 16px; font-size: 22px; color: #8c959f; }
/* repo */
.repo { padding: 30px 32px 30px; }
.rtitle { display: flex; align-items: center; gap: 14px; font-size: 40px; color: #0969da; white-space: nowrap; }
.rtitle .ico { color: #57606a; }
.own { font-weight: 500; }
.pub { margin-left: 8px; font-size: 24px; color: #57606a; border: 2px solid #d0d7de; border-radius: 20px; padding: 2px 14px; display: inline-flex; gap: 8px; align-items: center; }
.mit { margin-left: auto; font-size: 30px; font-weight: 800; color: #fff; background: #1a7f37; border-radius: 10px; padding: 4px 16px; }
.blur { filter: blur(9px); font-weight: 700; }
.desc { font-size: 36px; color: #1f2328; margin: 18px 0 6px; }
.chips { display: flex; gap: 14px; margin-top: 18px; flex-wrap: wrap; }
.chip { font-size: 30px; color: #0969da; background: #ddf4ff; border-radius: 22px; padding: 6px 18px; }
/* rank */
.rrow { display: flex; align-items: center; gap: 18px; padding: 10px 0; font-size: 30px; }
.rjob { width: 330px; font-weight: 600; white-space: nowrap; }
.rtrack { flex: 1; height: 26px; border-radius: 13px; background: #eef1f4; overflow: hidden; }
.rbar { display: block; height: 100%; border-radius: 13px; }
.rbar.hi { background: #1a7f37; } .rbar.mid { background: #d4a72c; } .rbar.lo { background: #cf222e; }
.rlab { width: 150px; text-align: right; font-weight: 700; font-size: 26px; }
.rlab.hi { color: #1a7f37; } .rlab.mid { color: #9a6700; } .rlab.lo { color: #cf222e; }
/* cv diff */
.dbar { display: flex; align-items: center; gap: 14px; height: 76px; padding: 0 28px; background: #f6f8fa; border-bottom: 2px solid #d0d7de; font-size: 32px; color: #57606a; }
.tag { margin-left: auto; font-size: 26px; font-weight: 800; color: #fff; background: #8250df; border-radius: 10px; padding: 4px 14px; }
.dbody { padding: 14px 0 18px; }
.dl { font-size: 29px; padding: 8px 28px; white-space: nowrap; display: flex; gap: 16px; }
.dl.del { background: #ffebe9; color: #82071e; text-decoration: line-through; }
.dl.add { background: #dafbe1; color: #116329; }
.dl.ctx { color: #57606a; }
.dk { width: 18px; font-weight: 700; }
/* chat */
.chat { padding: 22px 26px 26px; }
.chead { display: flex; align-items: center; gap: 12px; font-size: 32px; margin-bottom: 10px; }
.chead span { color: #8c959f; font-size: 26px; }
.bub { margin: 12px 0; padding: 16px 22px; border-radius: 22px; font-size: 30px; line-height: 1.35; max-width: 88%; }
.bub b { display: block; font-size: 22px; margin-bottom: 4px; opacity: .7; }
.bub.q { background: #f1f3f5; border-bottom-left-radius: 6px; }
.bub.a { background: #ddf4ff; margin-left: auto; border-bottom-right-radius: 6px; color: #0a3069; }
/* dm cta */
.dm { padding: 26px 30px 30px; position: relative; }
.cmrow, .dmrow { display: flex; gap: 18px; align-items: center; font-size: 30px; }
.fava { width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg,#f58529,#dd2a7b,#8134af); color: #fff;
  display: grid; place-items: center; font-weight: 800; font-size: 34px; flex: none; }
.ctext { font-size: 40px; font-weight: 800; margin-top: 2px; }
.kw { position: absolute; right: 30px; top: 22px; font-size: 92px; font-weight: 900; color: #0969da; letter-spacing: -0.04em; }
.dmrow { margin-top: 26px; padding: 18px 20px; border-radius: 20px; background: #f3f0ff; }
.dmrow > div { min-width: 0; flex: 1; }
.ava { width: 70px; height: 70px; border-radius: 50%; image-rendering: pixelated; background: #3a2416; flex: none; }
.dmlab { margin-left: 10px; color: #8c959f; font-size: 24px; }
.dmtext { font-size: 23px; color: #0969da; margin-top: 4px; white-space: pre; overflow: hidden; font-family: "JetBrains Mono", monospace; }
/* note */
.note { background: #fff8c5; padding: 34px 34px; }
.nh { font-size: 42px; font-weight: 800; display: flex; gap: 16px; align-items: center; color: #7d4e00; }
.nb { font-size: 34px; margin-top: 16px; color: #4d2d00; line-height: 1.35; }
/* contract */
.contract { padding: 30px 34px 30px; position: relative; }
.ch1 { font-size: 42px; font-weight: 800; letter-spacing: -0.02em; }
.cline { height: 12px; border-radius: 6px; background: #eef1f4; margin-top: 16px; width: 92%; }
.cline.s { width: 64%; }
.crow { display: flex; gap: 70px; margin-top: 22px; }
.clab { font-size: 24px; color: #8c959f; }
.cval { font-size: 34px; font-weight: 700; }
.sig { width: 330px; height: 78px; margin-top: 14px; }
.sig path { fill: none; stroke: #0a3069; stroke-width: 5; stroke-linecap: round; }
.signed { position: absolute; right: 34px; bottom: 34px; font-size: 38px; font-weight: 800; color: #1a7f37; border: 5px solid #1a7f37;
  border-radius: 12px; padding: 6px 18px; display: flex; gap: 10px; align-items: center; }
/* versus */
.versus { position: relative; display: flex; align-items: stretch; gap: 0; padding: 26px 26px 54px; }
.vs { flex: 1; border-radius: 14px; padding: 18px 20px; text-align: center; }
.vs.l { background: #fff1f0; } .vs.r { background: #e9fbef; }
.vlab { font-size: 28px; font-weight: 700; color: #57606a; }
.vnum { font-size: 96px; font-weight: 900; letter-spacing: -0.04em; line-height: 1.05; margin-top: 6px; }
.vs.l .vnum { color: #cf222e; } .vs.r .vnum { color: #1a7f37; }
.vsub { font-size: 26px; color: #57606a; margin-top: 4px; }
.vsx { align-self: center; font-size: 40px; font-weight: 900; color: #8c959f; margin: 0 16px; }
.vsrc { position: absolute; left: 0; right: 0; bottom: 8px; padding: 0; }
/* repo screenshot */
.shot { padding: 0; }
.shot img { display: block; width: 100%; }
.shot .src { padding: 10px 0 12px; }
/* teaser */
.wave { display: flex; align-items: center; gap: 6px; height: 80px; margin-top: 18px; }
.wave i { display: block; width: 14px; border-radius: 7px; background: #8250df; }
#gridmeter { position: absolute; left: 750px; top: 196px; display: grid; grid-template-columns: repeat(13, 18px); grid-auto-rows: 18px; gap: 2px; }
.gcell i { display: block; width: 18px; height: 18px; background: rgba(255,255,255,.14); border-radius: 3px; }
.ch { white-space: pre; }
"""

JS = """
const GREENS = ["#9be9a8", "#40c463", "#30a14e", "#216e39"];
function rnd(i) { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); }
function fitNums() {
  document.querySelectorAll(".num, .vnum").forEach((el) => {
    let fs = parseFloat(getComputedStyle(el).fontSize);
    while (el.scrollWidth > el.parentElement.clientWidth - 8 && fs > 40) { fs -= 4; el.style.fontSize = fs + "px"; }
  });
}
function fitLines() {
  // long commands and links shrink to fit their card instead of running off the edge
  document.querySelectorAll(".tl, .dmtext, .rtitle").forEach((el) => {
    let fs = parseFloat(getComputedStyle(el).fontSize);
    while (el.scrollWidth > el.clientWidth + 1 && fs > 16) { fs -= 1; el.style.fontSize = fs + "px"; }
  });
}
function fitTitles() {
  document.querySelectorAll(".tline").forEach((el) => {
    let fs = 124;
    el.style.fontSize = fs + "px";
    while (el.scrollWidth > 938 && fs > 60) { fs -= 2; el.style.fontSize = fs + "px"; }
  });
}
function build() {
  fitTitles();
  fitNums();
  fitLines();
  const tl = gsap.timeline({ paused: true });
  // headline words pop on the spoken word: these are the captions
  document.querySelectorAll(".tw").forEach((el) => {
    tl.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.12, ease: "power3.out" }, parseFloat(el.dataset.t));
  });
  const cells = document.querySelectorAll("#gridmeter .gcell");
  DATA.steps.forEach((st, i) => {
    const s = document.getElementById("s" + i), dur = st.end - st.start;
    const at = (f) => st.start + Math.min(Math.max(0, dur - 0.12), f * dur);
    // hard cut: the card is simply there on the cut, its contents perform
    s.querySelectorAll("[data-f]").forEach((el) => {
      const t = at(parseFloat(el.dataset.f)), a = el.dataset.anim;
      if (a === "pop") tl.fromTo(el, { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.14, ease: "back.out(3)" }, t);
      else if (a === "slide") tl.fromTo(el, { opacity: 0, x: -28 }, { opacity: 1, x: 0, duration: 0.14, ease: "power3.out" }, t);
      else if (a === "stamp") tl.fromTo(el, { opacity: 0, scale: 2.4 }, { opacity: 1, scale: 1, duration: 0.16, ease: "power4.in" }, t);
      else if (a === "grow") tl.fromTo(el, { scaleX: 0 }, { scaleX: 1, duration: 0.45, ease: "power3.out", transformOrigin: "0% 50%" }, t);
      else if (a === "shake") tl.fromTo(el, { x: -14 }, { x: 0, duration: 0.4, ease: "elastic.out(1.2, 0.25)" }, t);
      else if (a === "press") tl.fromTo(el, { scale: 1 }, { scale: 0.93, duration: 0.07, yoyo: true, repeat: 1 }, t);
      else if (a === "type") {
        const ch = el.querySelectorAll(".ch"), d = parseFloat(el.dataset.d || 0.4) * dur;
        tl.fromTo(ch, { opacity: 0 }, { opacity: 1, duration: 0.001, stagger: d / Math.max(1, ch.length) }, t);
      } else if (a === "count") {
        const o = { v: parseFloat(el.dataset.from) }, to = parseFloat(el.dataset.to);
        tl.to(o, { v: to, duration: parseFloat(el.dataset.d || 0.8) * dur * 0.4, ease: "power2.in",
          onUpdate: () => (el.textContent = Math.round(o.v)) }, t);
      } else if (a === "draw") {
        const L = el.getTotalLength();
        el.style.strokeDasharray = L;
        tl.fromTo(el, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: 0.55, ease: "power1.inOut" }, t);
      }
      if (el.dataset.off) tl.set(el, { opacity: 0 }, at(parseFloat(el.dataset.off)));
    });
    const per = Math.ceil(65 / DATA.steps.length);      // grid fills completely by the last beat
    for (let c = 0; c < per; c++) {
      const idx = i * per + c;
      if (idx >= 65) break;
      const cell = cells[(idx % 5) * 13 + Math.floor(idx / 5)];
      tl.set(cell.querySelector("i"), { backgroundColor: GREENS[Math.floor(rnd(idx) * 4)] }, st.start + c * 0.03);
    }
  });
  window.__timelines["main"] = tl;
}
document.fonts.ready.then(build);
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

    # step windows: cut lands just ahead of the first word (sharp), ends where the next starts
    starts = []
    for i in range(len(steps)):
        first = next(w for w in words if w["step"] == i)
        starts.append(0.0 if i == 0 else round(max(0.0, first["start"] - 0.05), 3))
    ends = starts[1:] + [total]

    # headline words -> spoken word times
    reveals = []
    for i, st in enumerate(steps):
        sw = [w for w in words if w["step"] == i]
        used = set()
        lines = []
        for line in st["title"]:
            toks = []
            for tok in line.split():
                t = starts[i]
                for k, w in enumerate(sw):
                    if k not in used and norm(w["text"]) == norm(tok):
                        used.add(k)
                        t = max(starts[i], w["start"] - 0.04)
                        break
                toks.append((tok, round(t, 3)))
            lines.append(toks)
        reveals.append(lines)

    # assets
    for f in ("Inter.woff2", "JetBrainsMono.woff2"):
        shutil.copy(os.path.join(ROOT, "assets", "fonts", f), os.path.join(proj, "assets", "fonts", f))
    shots = os.path.join(ROOT, "assets", "shots", slug)
    os.makedirs(shots, exist_ok=True)
    for sub, src in (("voxel", VOX), ("people", os.path.join(ROOT, "assets", "people")), ("shots", shots)):
        os.makedirs(os.path.join(proj, "assets", sub), exist_ok=True)
        for f in os.listdir(src):
            shutil.copy(os.path.join(src, f), os.path.join(proj, "assets", sub, f))
    from PIL import Image
    Image.open(os.path.join(VOX, "face_X.png")).resize((144, 144), Image.NEAREST).save(os.path.join(proj, "assets", "avatar.png"))

    # sound: chiptune bed only. Per-card blips were the "weird sound at the end of each clip" (v1 note)
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import chiptune
    chiptune.render(total, [], os.path.join(proj, "assets", "bed.wav"), mode == "voice")

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
    audio = (f'<audio id="bed" src="assets/bed.wav" data-start="0" data-duration="{total}" data-track-index="4" '
             f'data-volume="1"></audio>')
    if mode == "voice":
        audio += (f'<audio id="vo" src="assets/vo.wav" data-start="0" data-duration="{total}" data-track-index="3" '
                  f'data-volume="1"></audio>')
    data = {"total": total, "steps": [{"start": s, "end": e, "pose": st["pose"]} for s, e, st in zip(starts, ends, steps)],
            "cues": [[round(c["start"], 3), c["value"]] for c in cues if c["start"] < total]}
    scene_js = open(os.path.join(ROOT, "scripts", "voxel_scene.js")).read()

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
  <canvas id="mc" width="1080" height="1920"></canvas>
  <div id="shade"></div>
  <div class="path">{E(beats["repo_owner"])} / <b>{E(beats["repo_name"])}</b></div>
  <div class="rule"></div>
  {"".join(step_html)}
  <div id="gridmeter">{cells}</div>
  {audio}
</div>
<script>
window.DATA = {json.dumps(data)};
{JS}
</script>
<script type="module">
{scene_js}
</script>
</body>
</html>
"""
    open(os.path.join(proj, "index.html"), "w").write(page)
    json.dump({"mode": mode, "total": total, "words": words, "steps": data["steps"]},
              open(os.path.join(work, "timing.json"), "w"), indent=1)
    print(f"{slug}: {mode}, {total:.2f}s, {len(steps)} steps, {len(cues)} mouth cues")
    for i, s in enumerate(data["steps"]):
        print(f"  {i + 1:02d} {s['start']:6.2f}-{s['end']:6.2f}  {steps[i]['pose']:6s} {steps[i]['card']['type']:8s} {steps[i]['say']}")


if __name__ == "__main__":
    build(sys.argv[1])
