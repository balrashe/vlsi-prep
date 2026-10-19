"""Style "b" (trial-reel variant): dark glass panels that SHOW the thing being talked about.

Real app screenshots in an app window that zooms to the part he is talking about, with highlight boxes and a
cursor; live gauges, typed terminals, node diagrams, an editor timeline, receipts, and an Instagram comment CTA.
Everything is timed in fractions of the beat (data-f) like the v1 cards, so it follows the voice.
"""
import html
import json
import os

from PIL import Image

E = html.escape
PANEL_W = 840          # inside the IG safe box (x 120-960) where the panel runs below y 900


def anim(kind, f, extra=""):
    return f'data-anim="{kind}" data-f="{f}" {extra}'


def chars(text):
    return "".join(f'<span class="ch">{E(c)}</span>' for c in text)


def ico(name):
    p = {
        "check": '<path d="M20 6 9 17l-5-5"/>',
        "x": '<path d="M6 6l12 12M18 6 6 18"/>',
        "warn": '<path d="M12 3 2 21h20zM12 10v5M12 18h.01"/>',
        "send": '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/>',
        "heart": '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"/>',
        "star": '<path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    }[name]
    return (f'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round">{p}</svg>')


def _screen(k, s, shots_dir, vh):
    """One screenshot inside the app viewport. zooms: [[f, x, y, w]] (fractions of the image), marks: [[f, x, y, w, h, label]]."""
    iw, ih = Image.open(os.path.join(shots_dir, s["img"])).size
    dh = round(PANEL_W * ih / iw, 1)
    marks = "".join(
        f'<div class="mark" {anim("mark", f)} style="left:{x * 100:.2f}%;top:{y * 100:.2f}%;width:{w * 100:.2f}%;height:{h * 100:.2f}%">'
        + (f'<span class="mlab">{E(lab)}</span>' if lab else "") + "</div>"
        for f, x, y, w, h, lab in s.get("marks", []))
    zooms = s.get("zooms", [[0, 0, 0, 1]])
    show = anim("show", s.get("f", 0), f'data-off="{s["off"]}"' if "off" in s else "")
    label = f'<div class="scrlab">{E(s["label"])}</div>' if s.get("label") else ""
    return (f'<div class="scr" {show}><div class="zoom" data-zooms=\'{json.dumps(zooms)}\' '
            f'data-vw="{PANEL_W}" data-ih="{dh}" style="height:{dh}px">'
            f'<img src="assets/shots/{E(s["img"])}" alt="" style="width:{PANEL_W}px;height:{dh}px">{marks}</div>{label}</div>')


def card(c, beats, shots_dir):
    t = c["type"]
    if t == "app":
        vh = c.get("h", 600)
        scr = c["screens"]
        for k in range(len(scr) - 1):
            scr[k]["off"] = scr[k + 1]["f"]
        screens = "".join(_screen(k, s, shots_dir, vh) for k, s in enumerate(scr))
        cur = ""
        if c.get("cursor"):
            # cursor points come as [f, x, y] in fractions of screen 0's image; place them through the zoom active then
            iw, ih = Image.open(os.path.join(shots_dir, scr[0]["img"])).size
            dh, zs = PANEL_W * ih / iw, scr[0].get("zooms", [[0, 0, 0, 1]])
            path = []
            for f, x, y in c["cursor"]:
                z = [q for q in zs if q[0] <= f][-1]
                path.append([f, round((x - z[1]) / z[3] * PANEL_W), round((y - z[2]) * dh / z[3])])
            cur = (f'<div class="cursor" data-path=\'{json.dumps(path)}\'><svg viewBox="0 0 24 24"><path d="M3 2l7 19 2.6-7.4L20 11z" '
                   f'fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg><i class="ring"></i></div>')
        return (f'<div class="pane app"><div class="pbar"><i class="d r"></i><i class="d y"></i><i class="d g"></i>'
                f'<b>{E(c["title"])}</b><span class="real">{E(c.get("tag", "real screenshot"))}</span></div>'
                f'<div class="view" style="height:{vh}px">{screens}{cur}'
                + "".join(f'<div class="ovstamp" {anim("stamp", f)} style="{st}">{E(txt)}</div>' for f, txt, st in c.get("stamps", []))
                + '</div>'
                f'<div class="pcred">{E(c["credit"])}</div></div>')
    if t == "gauge":
        v, mx = c["value"], c["max"]
        rot = -90 + 180 * min(1, v / mx)
        ticks = "".join(f'<line x1="200" y1="34" x2="200" y2="{52 if k % 2 else 62}" transform="rotate({-90 + k * 18} 200 200)"/>'
                        for k in range(11))
        rows = "".join(f'<div class="grow2" {anim("slide", f)}><span>{E(a)}</span><b>{E(b)}</b></div>' for f, a, b in c.get("rows", []))
        return (f'<div class="pane gauge"><div class="ghead">{E(c["head"])}</div>'
                f'<svg class="gsvg" viewBox="0 0 400 230"><path class="gtrack" d="M30 200 A170 170 0 0 1 370 200"/>'
                f'<path class="garc" {anim("draw", 0.12)} d="M30 200 A170 170 0 0 1 {200 + 170 * __import__("math").sin(__import__("math").radians(rot)):.1f} '
                f'{200 - 170 * __import__("math").cos(__import__("math").radians(rot)):.1f}"/>'
                f'<g class="gticks">{ticks}</g>'
                f'<g class="needle" {anim("needle", 0.12, f"data-rot={rot:.1f}")}><line x1="200" y1="200" x2="200" y2="56"/><circle cx="200" cy="200" r="12"/></g></svg>'
                f'<div class="gnum"><span {anim("count", 0.12, f"data-from=0 data-to={v} data-d=1.6")}>0</span><small>{E(c["unit"])}</small></div>'
                f'{rows}<div class="pcred">{E(c["credit"])}</div></div>')
    if t == "bigterm":
        rows = []
        for f, kind, txt in c["lines"]:
            if kind == "cmd":
                rows.append(f'<div class="bt cmd" {anim("show", f)}><span class="gt">$</span> '
                            f'<span {anim("type", f, "data-d=0.22")}>{chars(txt)}</span></div>')
            elif kind == "bar":
                rows.append(f'<div class="bt barrow" {anim("show", f)}><span>{E(txt)}</span><i class="btrack"><i class="bfill" '
                            f'{anim("fill", f, "data-d=0.3")}></i></i></div>')
            else:
                rows.append(f'<div class="bt {kind}" {anim("slide", f)}>{ico("check") + " " if kind == "ok" else ""}{E(txt)}</div>')
        return (f'<div class="pane bigterm"><div class="pbar"><i class="d r"></i><i class="d y"></i><i class="d g"></i>'
                f'<b>{E(c.get("title", "Terminal"))}</b></div><div class="btbody">{"".join(rows)}</div></div>')
    if t == "flow":
        h = c.get("h", 560)
        ids = {n["id"]: n for n in c["nodes"]}
        lines = "".join(
            f'<line {anim("draw", f)} x1="{ids[a]["x"]}" y1="{ids[a]["y"]}" x2="{ids[b]["x"]}" y2="{ids[b]["y"]}"/>' for a, b, f in c["edges"])
        nodes = "".join(
            f'<div class="npin" {anim("pop", n["f"])} style="left:{n["x"]}px;top:{n["y"]}px"><div class="node {n.get("cls", "")}">'
            f'<b>{E(n["t"])}</b>' + (f'<small>{E(n["sub"])}</small>' if n.get("sub") else "") + "</div></div>" for n in c["nodes"])
        badge = f'<div class="fbadge" {anim("stamp", c["badge"][0])}>{E(c["badge"][1])}</div>' if c.get("badge") else ""
        return (f'<div class="pane flow"><div class="fcan" style="height:{h}px"><svg class="fsvg" viewBox="0 0 {PANEL_W} {h}" '
                f'style="height:{h}px">{lines}</svg>{nodes}{badge}</div>'
                + (f'<div class="pcred">{E(c["credit"])}</div>' if c.get("credit") else "") + "</div>")
    if t == "receipt":
        rows = "".join(f'<div class="rc" {anim("slide", f)}><span>{E(a)}</span><b>{E(b)}</b></div>' for f, a, b in c["rows"])
        tf, tl, tv = c["total"]
        return (f'<div class="pane receipt"><div class="rchead">{E(c["head"])}</div><div class="rcsub">{E(c["sub"])}</div>{rows}'
                f'<div class="rctot" {anim("stamp", tf)}><span>{E(tl)}</span><b>{E(tv)}</b></div>'
                f'<div class="pcred">{E(c["credit"])}</div></div>')
    if t == "tracks":
        rows = []
        for tr in c["rows"]:
            clips = "".join(f'<i class="clipx" {anim("grow", f)} style="left:{l}%;width:{w}%;background:{tr["color"]}">{E(lab)}</i>'
                            for f, l, w, lab in tr["clips"])
            rows.append(f'<div class="trk" {anim("slide", tr["f"])}><span class="tname">{E(tr["name"])}</span><span class="tlane">{clips}</span></div>')
        return (f'<div class="pane tracks"><div class="pbar"><i class="d r"></i><i class="d y"></i><i class="d g"></i>'
                f'<b>{E(c["title"])}</b><span class="real">{E(c.get("tag", ""))}</span></div>'
                f'<div class="tbody"><div class="ruler">{"".join(f"<i>0:{k * 4:02d}</i>" for k in range(6))}</div>{"".join(rows)}'
                f'<i class="playhead" {anim("sweep", 0.05)}></i></div></div>')
    if t == "xlist":
        rows = "".join(f'<div class="xl {k}" {anim("stamp", f)}>{ico("check" if k == "ok" else "x")}<span>{E(x)}</span></div>'
                       for f, k, x in c["items"])
        return (f'<div class="pane xlist">' + (f'<div class="ghead">{E(c["head"])}</div>' if c.get("head") else "")
                + rows + (f'<div class="pcred">{E(c["credit"])}</div>' if c.get("credit") else "") + "</div>")
    if t == "cta2":
        word = c["word"]
        return (f'<div class="pane cta2"><div class="post"><img class="cav" src="assets/avatar.png" alt="">'
                f'<div><b>baroobi.inc</b><span>Comment the word below</span></div>{ico("heart")}</div>'
                f'<div class="ccom" {anim("pop", 0.08)}><span class="cuser">you</span><span class="cword" {anim("type", 0.1, "data-d=0.16")}>{chars(word)}</span>'
                f'<span class="csend" {anim("press", 0.36)}>{ico("send")}</span></div>'
                f'<div class="notif" {anim("drop", 0.5)}><img class="cav" src="assets/avatar.png" alt="">'
                f'<div><b>baroobi.inc</b><small>now</small><div class="ntext" {anim("type", 0.56, "data-d=0.24")}>{chars(c["dm"])}</div></div></div></div>')
    return None


CSS = """
.vb #shade { background: linear-gradient(180deg, rgba(8,6,10,.86) 0%, rgba(8,6,10,.7) 45%, rgba(8,6,10,.15) 66%, rgba(8,6,10,0) 74%),
  radial-gradient(ellipse at 55% 85%, rgba(0,0,0,0) 45%, rgba(0,0,0,.55) 100%); }
.vb .pill, .vb .path, .vb .rule, .vb #gridmeter { display: none; }
#segs { position: absolute; left: 72px; top: 236px; width: 938px; display: flex; gap: 8px; }
#segs i { flex: 1; height: 10px; border-radius: 5px; background: rgba(255,255,255,.18); overflow: hidden; display: block; }
#segs i b { display: block; height: 100%; background: var(--acc); transform-origin: 0 50%; transform: scaleX(0); }
.repochip { position: absolute; right: 70px; top: 272px; font: 500 28px "JetBrains Mono", monospace; color: rgba(255,255,255,.7); }
.repochip b { color: var(--acc); font-weight: 600; }
.hbadge { position: absolute; left: 72px; top: 266px; font: 800 30px "Inter"; letter-spacing: .06em; color: #fff; background: var(--acc);
  padding: 6px 18px; border-radius: 10px; text-transform: uppercase; }
.vb .title { top: 330px; }
.vb .tline { font-size: 100px; }
.vb .tline.l2 { color: var(--acc); }
.vb .cardwrap { left: 120px; top: 592px; width: 840px; }
.pane { background: rgba(13,17,23,.94); border: 2px solid rgba(255,255,255,.12); border-radius: 22px; overflow: hidden; color: #e6edf3;
  box-shadow: 0 24px 70px rgba(0,0,0,.6), 0 0 0 1px rgba(0,0,0,.4); position: relative; }
.pbar { display: flex; align-items: center; gap: 12px; height: 62px; padding: 0 22px; background: #161b22; border-bottom: 2px solid #30363d; font-size: 28px; }
.pbar b { font-weight: 700; }
.real { margin-left: auto; font: 600 20px "JetBrains Mono", monospace; color: #7ee787; border: 2px solid #238636; border-radius: 16px; padding: 2px 12px; }
.pcred { font: 500 20px "JetBrains Mono", monospace; color: #8b949e; padding: 10px 22px 14px; }
.view { position: relative; overflow: hidden; background: #010409; }
.scr { position: absolute; inset: 0; }
.scr + .scr { opacity: 0; }
.zoom { position: absolute; left: 0; top: 0; width: 840px; transform-origin: 0 0; }
.zoom img { display: block; }
.mark { position: absolute; border: 5px solid var(--acc); border-radius: 12px; box-shadow: 0 0 0 4000px rgba(0,0,0,.0), 0 0 26px var(--acc); }
.mlab { position: absolute; left: -5px; top: -46px; font: 800 24px "Inter"; background: var(--acc); color: #fff; padding: 4px 12px; border-radius: 8px; white-space: nowrap; }
.scrlab { position: absolute; left: 18px; bottom: 16px; font: 800 30px "Inter"; background: rgba(0,0,0,.78); color: #fff; padding: 8px 18px;
  border-radius: 12px; border-left: 6px solid var(--acc); }
.cursor { position: absolute; left: 0; top: 0; width: 46px; height: 46px; z-index: 5; filter: drop-shadow(0 4px 8px rgba(0,0,0,.6)); }
.cursor svg { width: 46px; height: 46px; }
.cursor .ring { position: absolute; left: -22px; top: -22px; width: 56px; height: 56px; border-radius: 50%; border: 5px solid #fff; opacity: 0; }
.ovstamp { position: absolute; z-index: 6; font: 900 64px "Inter"; letter-spacing: -0.03em; color: #fff; background: var(--acc);
  padding: 8px 24px; border-radius: 16px; box-shadow: 0 12px 40px rgba(0,0,0,.6); white-space: nowrap; }
/* gauge */
.gauge { padding: 22px 30px 0; text-align: center; }
.ghead { font: 800 34px "Inter"; text-align: left; color: #e6edf3; margin-bottom: 6px; }
.gsvg { width: 600px; height: 345px; display: block; margin: 0 auto -40px; }
.gtrack, .garc { fill: none; stroke-width: 26; stroke-linecap: round; }
.gtrack { stroke: #21262d; } .garc { stroke: var(--acc); }
.gticks line { stroke: #6e7681; stroke-width: 4; }
.needle line { stroke: #fff; stroke-width: 8; stroke-linecap: round; } .needle circle { fill: #fff; }
.gnum { font: 900 150px "Inter"; letter-spacing: -0.05em; line-height: 1; color: #fff; }
.gnum small { font-size: 40px; color: #8b949e; margin-left: 12px; letter-spacing: 0; font-weight: 700; }
.grow2 { display: flex; justify-content: space-between; font: 600 30px "Inter"; padding: 12px 6px; border-top: 2px solid #21262d; color: #c9d1d9; text-align: left; }
.grow2 b { font-family: "JetBrains Mono", monospace; color: var(--acc); }
/* big terminal */
.btbody { padding: 22px 26px 28px; font-family: "JetBrains Mono", monospace; }
.bt { font-size: 30px; line-height: 1.4; padding: 6px 0; display: flex; align-items: center; gap: 12px; white-space: nowrap; }
.bt.cmd { opacity: 0; color: #fff; font-size: 31px; }
.bt.cmd .ch { opacity: 0; }
.bt .gt { color: var(--acc); font-weight: 800; }
.bt.out { color: #8b949e; } .bt.ok { color: #7ee787; } .bt.warn { color: #f2cc60; }
.barrow { opacity: 0; gap: 18px; color: #c9d1d9; }
.btrack { flex: 1; height: 22px; border-radius: 11px; background: #21262d; overflow: hidden; display: block; }
.bfill { display: block; height: 100%; background: linear-gradient(90deg, var(--acc), #7ee787); transform-origin: 0 50%; }
/* flow */
.fcan { position: relative; }
.fsvg { position: absolute; left: 0; top: 0; width: 840px; }
.fsvg line { stroke: var(--acc); stroke-width: 5; stroke-dasharray: 2000; opacity: .85; }
.npin { position: absolute; width: 0; height: 0; }
.node { position: absolute; left: 0; top: 0; transform: translate(-50%, -50%); background: #161b22; border: 3px solid #30363d; border-radius: 16px; padding: 12px 20px;
  text-align: center; white-space: nowrap; box-shadow: 0 10px 30px rgba(0,0,0,.5); }
.node b { display: block; font: 800 30px "Inter"; }
.node small { display: block; font: 500 21px "JetBrains Mono", monospace; color: #8b949e; margin-top: 4px; }
.node.hub { border-color: var(--acc); background: #1f1418; padding: 18px 28px; }
.node.hub b { font-size: 38px; }
.node.hot { border-color: var(--acc); box-shadow: 0 0 30px var(--acc); }
.fbadge { position: absolute; right: 24px; top: 20px; font: 900 64px "Inter"; color: var(--acc); letter-spacing: -0.03em; }
/* receipt */
.receipt { background: #fbfaf6; color: #1f2328; padding: 30px 36px 6px; font-family: "JetBrains Mono", monospace; border: none; }
.rchead { font: 900 44px "Inter"; letter-spacing: -0.02em; }
.rcsub { font-size: 24px; color: #57606a; margin: 4px 0 16px; padding-bottom: 16px; border-bottom: 3px dashed #c4c8cc; }
.rc { display: flex; justify-content: space-between; font-size: 29px; padding: 9px 0; }
.rctot { display: flex; justify-content: space-between; font: 900 64px "Inter"; padding: 18px 0 8px; margin-top: 10px; border-top: 3px dashed #c4c8cc; }
.rctot b { color: #1a7f37; }
.receipt .pcred { color: #8c959f; padding: 6px 0 16px; }
/* tracks */
.tbody { position: relative; padding: 16px 22px 26px; }
.ruler { display: flex; justify-content: space-between; margin-left: 176px; font: 500 20px "JetBrains Mono", monospace; color: #6e7681; margin-bottom: 10px; }
.trk { display: flex; align-items: center; gap: 14px; height: 78px; }
.tname { width: 162px; font: 800 26px "Inter"; color: #c9d1d9; }
.tlane { position: relative; flex: 1; height: 58px; background: #0d1117; border: 2px solid #21262d; border-radius: 10px; }
.clipx { position: absolute; top: 5px; bottom: 5px; border-radius: 8px; font: 700 21px "Inter"; font-style: normal; color: #fff; padding: 0 10px;
  display: flex; align-items: center; overflow: hidden; white-space: nowrap; transform-origin: 0 50%; }
.playhead { position: absolute; top: 6px; bottom: 14px; left: 198px; width: 4px; background: #fff; box-shadow: 0 0 12px #fff; }
/* xlist */
.xlist { padding: 26px 32px 10px; }
.xl { display: flex; align-items: center; gap: 22px; font: 800 52px "Inter"; padding: 14px 0; letter-spacing: -0.02em; }
.xl .ico { width: 58px; height: 58px; padding: 8px; border-radius: 14px; }
.xl.ok .ico { background: #238636; color: #fff; } .xl.no .ico { background: #da3633; color: #fff; }
.xl.no span { color: #ffb4ad; }
.xlist .pcred { padding: 8px 0 16px; }
/* comment CTA */
.cta2 { padding: 24px 26px 28px; background: #000; border-color: #262626; }
.post { display: flex; align-items: center; gap: 16px; font-size: 28px; }
.post b { display: block; font-size: 30px; } .post span { color: #a8a8a8; font-size: 24px; }
.post .ico { margin-left: auto; width: 40px; height: 40px; color: #fff; }
.cav { width: 70px; height: 70px; border-radius: 50%; image-rendering: pixelated; background: #3a2416; border: 3px solid #ff3d7f; flex: none; }
.ccom { display: flex; align-items: center; gap: 16px; margin-top: 22px; height: 92px; border: 2px solid #363636; border-radius: 46px; padding: 0 14px 0 28px; }
.cuser { font: 700 26px "Inter"; color: #a8a8a8; }
.cword { font: 900 46px "Inter"; color: #fff; letter-spacing: .02em; }
.cword .ch { opacity: 0; }
.csend { margin-left: auto; width: 66px; height: 66px; border-radius: 50%; background: #0095f6; display: grid; place-items: center; color: #fff; }
.csend .ico { width: 34px; height: 34px; }
.big { position: absolute; right: 30px; top: 18px; font: 900 34px "Inter"; color: #000; background: #fff; border-radius: 10px; padding: 4px 14px; display: none; }
.notif { display: flex; gap: 16px; align-items: center; margin-top: 22px; padding: 18px 20px; border-radius: 26px; background: rgba(60,60,67,.92);
  border: 1px solid rgba(255,255,255,.12); }
.notif > div { min-width: 0; flex: 1; }
.notif b { font-size: 28px; } .notif small { float: right; color: #a8a8a8; font-size: 22px; }
.ntext { font: 500 23px "JetBrains Mono", monospace; color: #7cc4ff; margin-top: 4px; white-space: pre; overflow: hidden; }
"""

JS = """
function buildB(tl, DATA) {
  // zooming screenshots: [[f, x, y, w]] fractions of the image; scale so w fills the viewport, top-left at (x, y)
  DATA.steps.forEach((st, i) => {
    const s = document.getElementById("s" + i), dur = st.end - st.start;
    const at = (f) => st.start + Math.min(Math.max(0, dur - 0.12), f * dur);
    s.querySelectorAll(".zoom").forEach((el) => {
      const vw = parseFloat(el.dataset.vw), ih = parseFloat(el.dataset.ih);
      const zs = JSON.parse(el.dataset.zooms);
      const tf = (z) => ({ scale: 1 / z[3], x: -z[1] * vw / z[3], y: -z[2] * ih / z[3] });
      tl.set(el, tf(zs[0]), st.start);
      zs.slice(1).forEach((z) => tl.to(el, { ...tf(z), duration: 0.45, ease: "power3.inOut" }, at(z[0])));
      // a mark sits in image space, so its border would scale with the zoom: counter-scale the stroke
      el.querySelectorAll(".mark").forEach((m) => {
        const k = zs.filter((z) => z[0] <= parseFloat(m.dataset.f)).pop() || zs[0];
        m.style.borderWidth = (5 * k[3]).toFixed(2) + "px";
        m.style.borderRadius = (12 * k[3]).toFixed(2) + "px";
        const lab = m.querySelector(".mlab");
        if (lab) { lab.style.transform = `scale(${k[3]})`; lab.style.transformOrigin = "0 100%"; lab.style.top = (-46 * k[3]) + "px"; }
      });
    });
    s.querySelectorAll(".cursor").forEach((el) => {
      const path = JSON.parse(el.dataset.path);
      tl.set(el, { x: path[0][1], y: path[0][2] }, st.start);
      path.slice(1).forEach((p) => tl.to(el, { x: p[1], y: p[2], duration: 0.32, ease: "power2.inOut" }, at(p[0]) - 0.32));
      const ring = el.querySelector(".ring"), last = path[path.length - 1];
      tl.fromTo(ring, { opacity: 0.9, scale: 0.3 }, { opacity: 0, scale: 1.6, duration: 0.35, ease: "power2.out" }, at(last[0]));
    });
    s.querySelectorAll("[data-f]").forEach((el) => {
      const t = at(parseFloat(el.dataset.f)), a = el.dataset.anim;
      if (a === "show") tl.set(el, { opacity: 1 }, t);
      else if (a === "mark") tl.fromTo(el, { opacity: 0, scale: 1.35 }, { opacity: 1, scale: 1, duration: 0.18, ease: "power3.out" }, t);
      else if (a === "needle") tl.fromTo(el, { rotation: -90, svgOrigin: "200 200" }, { rotation: parseFloat(el.dataset.rot), svgOrigin: "200 200", duration: 1.6 * dur * 0.4, ease: "power2.out" }, t);
      else if (a === "fill") tl.fromTo(el, { scaleX: 0 }, { scaleX: 1, duration: parseFloat(el.dataset.d) * dur, ease: "power1.inOut" }, t);
      else if (a === "sweep") tl.fromTo(el, { x: 0 }, { x: 590, duration: dur * 0.9, ease: "none" }, t);
      else if (a === "drop") tl.fromTo(el, { opacity: 0, y: -60 }, { opacity: 1, y: 0, duration: 0.2, ease: "back.out(2)" }, t);
    });
  });
  document.querySelectorAll("#segs i b").forEach((b, i) => {
    const st = DATA.steps[i];
    tl.fromTo(b, { scaleX: 0 }, { scaleX: 1, duration: st.end - st.start, ease: "none" }, st.start);
  });
}
"""
