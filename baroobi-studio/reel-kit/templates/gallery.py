"""Format gallery: ~4 s of every visual editing style on one clip, labelled, so the user can pick.

    python gallery.py <work_dir> <project_dir>

work_dir needs talk.mp4 (speaker, 1080x1920), talk_alpha.webm (same, background removed), bgplate.jpg (clean
blurred backdrop), words.json (timings on talk.mp4) and assets/*.jpg (screenshots used as UI and B-roll).
"""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lib  # noqa: E402

W, H, SEG = 1080, 1920, 4.0
E = lib.E


def main(work, proj):
    b = lib.brand()
    F, acc = b["fonts"], b["accent"]
    os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
    for f in ["talk_alpha.webm", "bgplate.jpg"] + [f"assets/{x}" for x in os.listdir(os.path.join(work, "assets"))]:
        shutil.copy(os.path.join(work, f), os.path.join(proj, "assets", os.path.basename(f)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(work, "talk.mp4"), "-vn", "-c:a", "aac", "-b:a", "192k",
                    os.path.join(proj, "assets", "talk.m4a")], check=True)
    words = json.load(open(os.path.join(work, "words.json")))

    back, front, media, js = [], [], [], []
    segs = []

    def seg(name, aspect="9:16"):
        segs.append((name, aspect))
        return len(segs) - 1

    def T(k, off):                       # absolute time of an offset inside segment k
        return round(k * SEG + off, 3)

    def speaker(k, ms, box, src=(0, 0, W, H), radius=0, plate=True, z="spk"):
        """Speaker cut-out (over the clean plate unless plate=False) cropped from `src` into `box`."""
        x, y, w, h = box; sx, sy, sw, sh = src; s = max(w / sw, h / sh)
        media.append(
            f'<div class="{z}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:{radius}px" data-show="{T(k, 0)}" data-hide="{T(k, SEG)}">'
            f'<div class="stage" style="transform:translate({-sx * s:.1f}px,{-sy * s:.1f}px) scale({s:.4f})">'
            + (f'<img class="plate" src="assets/bgplate.jpg" alt="">' if plate else "")
            + f'<video id="v{k}" src="assets/talk_alpha.webm" data-start="{T(k, 0)}" data-duration="{SEG}" data-media-start="{ms}" '
              f'data-track-index="{1 + k % 2}" muted playsinline></video></div></div>')

    def audio(k, ms):
        media.append(f'<audio id="a{k}" src="assets/talk.m4a" data-start="{T(k, 0)}" data-duration="{SEG}" data-media-start="{ms}" '
                     f'data-track-index="{3 + k % 2}" data-volume="1"></audio>')

    def caps(k, ms, y, size=64, color="#fff", accents=(), n=1, cls="cap"):
        """One phrase at a time (brand: one word) from the words spoken in this window."""
        ws = [dict(w, s=w["s"] - ms, e=w["e"] - ms) for w in words if ms <= w["s"] < ms + SEG - 0.15]
        for p in lib.phrases(ws, n):
            txt = " ".join(f'<span style="color:{acc}">{E(w["w"])}</span>' if w["w"].strip(".,").lower() in accents else E(w["w"]) for w in p["words"])
            front.append(f'<div class="{cls}" style="top:{y}px;font-size:{size}px;color:{color}" data-show="{T(k, p["s"])}" data-hide="{T(k, min(p["e"], SEG))}">{txt}</div>')

    def layer(k, html, where):
        (back if where == "back" else front).append(f'<div class="lay" data-show="{T(k, 0)}" data-hide="{T(k, SEG)}">{html}</div>')

    def img(src, x, y, w, h, extra="", cls="pic", attrs=""):
        return f'<img class="{cls}" src="assets/{src}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{extra}" {attrs} alt="">'

    # ---- 1 business reels: full frame, title box, fanned phone cards, big one-word caption
    k = seg("Business Reels"); speaker(k, 0, (0, 0, W, H)); audio(k, 0)
    cards = "".join(img(f"console{i}.jpg", x, y, 250, 444, f"transform:rotate({r}deg)", "phone", f'data-pop="{T(k, 0.5 + i * 0.12)}"')
                    for i, (x, y, r) in enumerate([(30, 980, -14), (215, 900, -6), (415, 870, 0), (615, 900, 6), (800, 980, 14)]))
    layer(k, cards, "front")
    layer(k, '<div class="t1">Almost every console</div><div class="tbox">now runs on your PC</div>', "front")
    caps(k, 0, 1500, 92, accents=("console", "open"))

    # ---- 2 personal reels: B-roll top, face bottom, word on the seam, price tag sticker
    k = seg("Personal Reels"); audio(k, 4)
    layer(k, img("gta.jpg", 0, 0, W, 950, "object-fit:cover", "kb", f'data-kb="{T(k, 0)}"')
          + f'<div class="tag" data-pop="{T(k, 0.9)}"><i></i>FREE</div>', "back")
    speaker(k, 4, (0, 960, W, 960), (0, 420, W, 960))
    layer(k, '<div class="seam" style="top:950px"></div>', "front")
    caps(k, 4, 905, 72, accents=("pc", "gta", "5", "free"))

    # ---- 3 explainer panel: animated explanation on top, you in a rounded panel at the bottom
    k = seg("Explainer Panel"); audio(k, 0)
    nodes = [("console2.jpg", "Console game", 130), ("github.jpg", "Open-source emulator", 440), ("gta.jpg", "Your PC", 750)]
    html = '<div class="dark"></div><svg class="sv" viewBox="0 0 1080 1100">' + "".join(
        f'<path d="M{x + 200} 420 L{nodes[i + 1][2]} 420" data-draw="{T(k, 0.7 + i * 0.9)}"/>' for i, (_, _, x) in enumerate(nodes[:-1])) + "</svg>"
    html += "".join(f'<div class="node" style="left:{x - 70}px;top:300px" data-pop="{T(k, 0.3 + i * 0.9)}">{img(s, 0, 0, 340, 200, "position:relative", "nimg")}<b>{E(t)}</b></div>'
                    for i, (s, t, x) in enumerate(nodes))
    layer(k, html, "back")
    speaker(k, 0, (60, 1180, 960, 680), (0, 430, W, 765), 40)
    caps(k, 0, 1080, 64)

    # ---- 4 glass explainer: glass cards, a counter, a graph that draws on
    k = seg("Glass Explainer"); audio(k, 2)
    html = ('<div class="warm"></div>'
            f'<div class="glass" style="left:70px;top:150px;width:440px;height:300px" data-pop="{T(k, 0.2)}"><small>Consoles in this reel</small>'
            f'<div class="big" data-count="{T(k, 0.4)}" data-to="6">0</div></div>'
            f'<div class="glass" style="left:570px;top:150px;width:440px;height:300px" data-pop="{T(k, 0.5)}"><small>Licence</small><div class="big2">Open source</div></div>'
            f'<div class="glass" style="left:70px;top:500px;width:940px;height:520px" data-pop="{T(k, 0.9)}"><small>Games you can play on PC</small>'
            f'<svg viewBox="0 0 900 400" class="gsv"><path d="M20 360 C 200 340, 300 300, 420 230 S 700 80, 880 40" data-draw="{T(k, 1.2)}"/></svg></div>')
    layer(k, html, "back")
    speaker(k, 2, (60, 1180, 960, 680), (0, 430, W, 765), 40)
    caps(k, 2, 1080, 64)

    # ---- 5 visual essay: black and orange, you cut out, the evidence above you
    k = seg("Visual Essay"); audio(k, 4)
    html = (f'<div class="blk"></div>{img("github.jpg", 90, 170, 900, 588, "border-radius:18px", "pic", f"data-pop={T(k, 0.2)}")}'
            f'<div class="hl" style="left:300px;top:395px;width:520px;height:58px" data-pop="{T(k, 0.9)}"></div>'
            f'<div class="kick" data-pop="{T(k, 0.2)}">THE EVIDENCE</div>')
    layer(k, html, "back")
    speaker(k, 4, (90, 860, 900, 1060), (0, 380, W, 1272), 0, plate=False)
    caps(k, 4, 1640, 70, color="#fff", accents=("pc", "notch", "gta", "5"))

    # ---- 6 split reel: your face on top, a diagram underneath
    k = seg("Split Reel"); audio(k, 2)
    speaker(k, 2, (0, 0, W, 960), (0, 380, W, 960))
    steps = ["Open a browser", "Load GTA V", "Play it"]
    html = '<div class="dark" style="top:960px;height:960px"></div>' + "".join(
        f'<div class="step" style="top:{1080 + i * 250}px" data-pop="{T(k, 0.4 + i * 1.0)}"><em>{i + 1}</em>{E(s)}</div>' for i, s in enumerate(steps))
    layer(k, html, "front")
    layer(k, '<div class="seam" style="top:955px"></div>', "front")
    caps(k, 2, 900, 64)

    # ---- 7 B-roll and stacked text: B-roll full frame, key phrases stack up
    k = seg("B-roll and Stacked Text"); audio(k, 4)
    layer(k, img("wolverine.jpg", 0, 0, W, H, "object-fit:cover;filter:brightness(.55)", "kb", f'data-kb="{T(k, 0)}"'), "back")
    stack = ["ANY GAME", "ON YOUR PC", "IN A BROWSER"]
    layer(k, "".join(f'<div class="stk" style="top:{640 + i * 150}px" data-pop="{T(k, 0.3 + i * 1.1)}">{E(s)}</div>' for i, s in enumerate(stack)), "front")
    caps(k, 4, 1600, 56)

    # ---- 8 fitted captions: one huge accent word, the rest fitted around it
    k = seg("Fitted Captions"); speaker(k, 0, (0, 0, W, H)); audio(k, 0)
    fits = [(0.0, "almost every", "CONSOLE"), (1.5, "has been", "OPEN"), (2.4, "source, so you can", "PLAY")]
    for i, (s, small, big) in enumerate(fits):
        e = fits[i + 1][0] if i + 1 < len(fits) else SEG
        front.append(f'<div class="fit" data-show="{T(k, s)}" data-hide="{T(k, e)}"><span>{E(small)}</span><b>{E(big)}</b></div>')

    # ---- 9 image cluster: images clustered above your head, small quiet captions
    k = seg("Image Cluster"); speaker(k, 2, (0, 0, W, H), (0, -80, W, H)); audio(k, 2)
    cl = [("console0.jpg", 70, 120, -6), ("console1.jpg", 400, 70, 3), ("console3.jpg", 720, 150, 7), ("console4.jpg", 250, 330, -2), ("console5.jpg", 580, 360, 4)]
    layer(k, "".join(img(s, x, y, 300, 166, f"transform:rotate({r}deg)", "clus", f'data-pop="{T(k, 0.2 + i * 0.25)}"') for i, (s, x, y, r) in enumerate(cl)), "front")
    caps(k, 2, 1560, 40, cls="cap quiet")

    # ---- 10 YouTube clips: animation on top, you underneath, word on the seam
    k = seg("YouTube Clips"); audio(k, 12)
    av = "".join(f'<i class="av{" hot" if i == 4 else ""}" style="left:{250 + (i % 3) * 210}px;top:{230 + (i // 3) * 210}px" data-pop="{T(k, 0.1 + i * 0.07)}"></i>' for i in range(9))
    layer(k, f'<div class="blk" style="height:960px"></div><div class="glow"></div>{av}<div class="chip" data-pop="{T(k, 0.2)}">CLIP 1 OF 5 · RANKED</div>', "back")
    speaker(k, 12, (0, 960, W, 960), (0, 420, W, 960))
    caps(k, 12, 880, 64)

    # ---- 11 cut-out backdrop: you cut out over full-screen images that change with each idea
    k = seg("Cut-out Backdrop"); audio(k, 4)
    for i, (s, a, e) in enumerate([("console0.jpg", 0, 1.4), ("gta.jpg", 1.4, 2.7), ("wolverine.jpg", 2.7, SEG)]):
        back.append(f'<div class="lay" data-show="{T(k, a)}" data-hide="{T(k, e)}">{img(s, 0, 0, W, H, "object-fit:cover")}</div>')
    speaker(k, 4, (0, 420, W, 1500), (0, 300, W, 1333), plate=False)
    caps(k, 4, 1500, 72)

    # ---- 12 cut-out grid: you in the centre of four images that change together
    k = seg("Cut-out Grid"); audio(k, 2)
    for g, (a, e) in enumerate([(0, 2.0), (2.0, SEG)]):
        cells = "".join(img(f"console{(g * 2 + i) % 6}.jpg", (i % 2) * 540, (i // 2) * 960, 540, 960, "object-fit:cover") for i in range(4))
        back.append(f'<div class="lay" data-show="{T(k, a)}" data-hide="{T(k, e)}">{cells}</div>')
    speaker(k, 2, (140, 560, 800, 1360), (0, 250, W, 1836), plate=False)
    caps(k, 2, 1580, 72)

    # ---- 13 depth UI: a real interface behind your head, chest caption, a UI card under it
    k = seg("Depth UI"); audio(k, 0)
    layer(k, f'<img class="plate2" src="assets/bgplate.jpg" alt=""><div class="win" data-pop="{T(k, 0.2)}"><div class="bar"><i></i><i></i><i></i></div>{img("github.jpg", 0, 52, 920, 600, "position:absolute")}</div>', "back")
    speaker(k, 0, (0, 0, W, H), plate=False)
    layer(k, f'<div class="uicard" data-pop="{T(k, 0.8)}"><div class="ava">GH</div><div><b>awesome-emulators</b><small>github.com · open source</small></div><span>Star</span></div>', "front")
    caps(k, 0, 1170, 64)

    # ---- 14 ranking format: S-F table on the chest, cards drop in
    k = seg("Ranking Format"); speaker(k, 4, (0, 0, W, H)); audio(k, 4)
    tiers = "".join(f'<div class="trow" style="top:{4 + i * 72}px"><div class="tlab" style="background:{b["tiers"][t]}">{t}</div><div class="ttrk"></div></div>' for i, t in enumerate("SABCDEF"))
    html = f'<div class="rt">BEST CONSOLES<br>TO EMULATE</div><div class="table">{tiers}</div>'
    for i, (s, t, at) in enumerate([("console0.jpg", 0, 0.5), ("console1.jpg", 1, 2.0)]):
        html += (f'<div class="rcard" data-rank="{T(k, at)}" data-ty="{1001 + t * 72}" data-tx="{240 + i * 0}">{img(s, 0, 0, 574, 322, "position:absolute;object-fit:cover")}'
                 f'<b>{["PS3", "SWITCH"][i]}</b></div>')
    layer(k, html, "front")
    caps(k, 4, 925, 54)

    # ---- 15 coaching call clips: clean talking head, title box, low captions with an accent word
    k = seg("Coaching Call Clips"); speaker(k, 12, (0, 0, W, H)); audio(k, 12)
    layer(k, f'<div class="t1" style="top:110px">The bit everyone</div><div class="tbox" style="top:200px">skips in this video</div><div class="chip" style="top:1780px" data-pop="{T(k, 0.3)}">CLIP 2 · RANKED #1</div>', "front")
    caps(k, 12, 1440, 64, accents=("link", "gaming", "comment"))

    # ---- 16 split-screen lesson (16:9): notes document left, you right
    k = seg("Split-Screen Lesson + Lesson Document", "16:9"); audio(k, 0)
    doc = "".join(f'<p data-hl="{T(k, 0.2 + i * 0.9)}">{E(l)}</p>' for i, l in enumerate(
        ["1. Every console has an emulator", "2. Emulators are open source", "3. Your PC runs the games", "4. Some run in a browser"]))
    layer(k, f'<div class="wide"><div class="doc"><h3>Lesson: playing console games on PC</h3>{doc}</div></div>', "back")
    speaker(k, 0, (0 + 1080 * 0.58, 656, 1080 * 0.42, 608), (140, 430, 800, 1073))
    caps(k, 0, 1170, 40)

    # ---- 17 educational YouTube (16:9): you full frame, a lower third and an explainer card
    k = seg("Educational YouTube", "16:9"); audio(k, 4)
    layer(k, '<div class="wide"></div>', "back")
    speaker(k, 4, (0, 656, W, 608), (0, 450, W, 608))
    layer(k, f'<div class="lt" data-pop="{T(k, 0.4)}"><b>Emulator</b> software that runs console games on a PC</div>'
             f'<div class="exp" data-pop="{T(k, 1.6)}">{img("gta.jpg", 0, 0, 380, 214, "position:relative;border-radius:10px")}<small>GTA V in a browser</small></div>', "front")

    # labels
    for i, (name, aspect) in enumerate(segs):
        front.append(f'<div class="label" data-show="{T(i, 0)}" data-hide="{T(i, SEG)}"><em>{i + 1:02d}/{len(segs)}</em> {E(name)}{" · 16:9" if aspect == "16:9" else ""}</div>')
    dur = len(segs) * SEG

    css = lib.font_css(b, proj) + f"""
.lay, .spk, .back, .front {{ position: absolute; inset: 0; opacity: 0; }}
#back {{ position: absolute; inset: 0; z-index: 1; }} #media {{ position: absolute; inset: 0; z-index: 2; }} #front {{ position: absolute; inset: 0; z-index: 3; }}
.spk {{ inset: auto; overflow: hidden; }}
.stage {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; transform-origin: 0 0; }}
.stage video, .stage .plate {{ position: absolute; inset: 0; width: {W}px; height: {H}px; object-fit: cover; }}
.plate2 {{ position: absolute; inset: 0; width: {W}px; height: {H}px; object-fit: cover; }}
.pic, .kb, .phone, .clus, .nimg {{ position: absolute; object-fit: cover; }}
.phone {{ border-radius: 26px; border: 4px solid #fff; box-shadow: 0 18px 40px rgba(0,0,0,.45); }}
.cap {{ position: absolute; left: 40px; right: 40px; text-align: center; font-family: "{F['caption'][0]}"; font-weight: {F['caption'][2]}; line-height: 1;
  letter-spacing: -0.02em; text-shadow: 0 3px 14px rgba(0,0,0,.5); opacity: 0; }}
.cap.quiet {{ font-weight: 600; text-shadow: 0 1px 6px rgba(0,0,0,.4); }}
.t1 {{ position: absolute; left: 60px; right: 60px; top: 200px; text-align: center; font: 700 76px/1 "{F['caption'][0]}"; color: #fff; text-shadow: 0 3px 14px rgba(0,0,0,.45); }}
.tbox {{ position: absolute; left: 50%; top: 292px; transform: translateX(-50%); white-space: nowrap; padding: 10px 28px; background: {b['title_box']['bg']};
  color: {b['title_box']['fg']}; border-radius: {b['title_box'].get('radius', 0)}px; font: 700 70px/1.05 "{F['caption'][0]}"; }}
.tag {{ position: absolute; left: 640px; top: 300px; padding: 26px 46px 26px 80px; background: #fff; color: #111; font: 900 86px/1 "{F['card'][0]}";
  border-radius: 14px 30px 30px 14px; transform: rotate(-5deg); box-shadow: 0 12px 30px rgba(0,0,0,.35); }}
.tag i {{ position: absolute; left: 30px; top: 50%; width: 20px; height: 20px; margin-top: -10px; border-radius: 50%; background: #111; }}
.seam {{ position: absolute; left: 0; right: 0; height: 12px; background: #100c09; }}
.dark {{ position: absolute; left: 0; right: 0; top: 0; height: 1180px; background: radial-gradient(ellipse at 50% 30%, #23201d, #0d0c0b 70%); }}
.warm {{ position: absolute; inset: 0; background: linear-gradient(160deg, #3a2a20, #15110e 60%); }}
.blk {{ position: absolute; left: 0; right: 0; top: 0; height: {H}px; background: #050505; }}
.sv {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1100px; }} .sv path {{ stroke: {acc}; stroke-width: 8; fill: none; stroke-linecap: round; }}
.node {{ position: absolute; width: 340px; }} .node .nimg {{ border-radius: 18px; border: 3px solid #fff; }}
.node b {{ display: block; margin-top: 18px; text-align: center; font: 700 34px "{F['caption'][0]}"; color: #fff; }}
.glass {{ position: absolute; border-radius: 28px; background: rgba(255,255,255,.10); border: 1.5px solid rgba(255,255,255,.28); box-shadow: 0 20px 50px rgba(0,0,0,.35);
  padding: 34px; color: #fff; font-family: "{F['caption'][0]}"; }}
.glass small {{ font: 600 30px "{F['caption'][0]}"; color: rgba(255,255,255,.75); }}
.glass .big {{ font: 900 150px/1.1 "{F['card'][0]}"; color: {acc}; }} .glass .big2 {{ font: 800 66px/1.6 "{F['caption'][0]}"; }}
.gsv {{ position: absolute; left: 20px; top: 90px; width: 900px; height: 400px; }} .gsv path {{ stroke: {acc}; stroke-width: 10; fill: none; stroke-linecap: round; }}
.hl {{ position: absolute; border: 6px solid {acc}; border-radius: 10px; box-shadow: 0 0 0 9999px rgba(0,0,0,.0); }}
.kick {{ position: absolute; left: 90px; top: 90px; font: 800 40px "{F['caption'][0]}"; color: {acc}; letter-spacing: .08em; }}
.step {{ position: absolute; left: 90px; right: 90px; height: 190px; border-radius: 26px; background: #1d1a17; border: 2px solid #3a332d; display: flex; align-items: center;
  gap: 34px; padding: 0 40px; font: 700 58px "{F['caption'][0]}"; color: #fff; }}
.step em {{ font-style: normal; width: 96px; height: 96px; border-radius: 50%; background: {acc}; display: flex; align-items: center; justify-content: center; font: 900 54px "{F['card'][0]}"; }}
.stk {{ position: absolute; left: 0; right: 0; text-align: center; font: 900 120px/1 "{F['card'][0]}"; color: #fff; letter-spacing: -0.02em; text-shadow: 0 6px 24px rgba(0,0,0,.5); }}
.stk:last-child {{ color: {acc}; }}
.fit {{ position: absolute; left: 60px; right: 60px; top: 1290px; text-align: center; color: #fff; opacity: 0; text-shadow: 0 4px 20px rgba(0,0,0,.5); font-family: "{F['caption'][0]}"; }}
.fit span {{ display: block; font: 700 66px/1 "{F['caption'][0]}"; }} .fit b {{ display: block; font: 900 190px/0.95 "{F['card'][0]}"; color: {acc}; letter-spacing: -0.03em; }}
.clus {{ border-radius: 16px; border: 4px solid #fff; box-shadow: 0 14px 34px rgba(0,0,0,.4); }}
.glow {{ position: absolute; left: 140px; top: 120px; width: 800px; height: 760px; background: radial-gradient(circle, rgba(224,138,58,.45), rgba(224,138,58,0) 65%); }}
.av {{ position: absolute; width: 170px; height: 170px; border-radius: 50%; background: radial-gradient(circle at 50% 38%, #9a948c 0 22%, transparent 23%),
  radial-gradient(ellipse at 50% 100%, #9a948c 0 38%, transparent 39%), #5d5953; }}
.av.hot {{ background: radial-gradient(circle at 50% 38%, #fff3e6 0 22%, transparent 23%), radial-gradient(ellipse at 50% 100%, #fff3e6 0 38%, transparent 39%), {acc};
  box-shadow: 0 0 60px rgba(224,138,58,.8); }}
.chip {{ position: absolute; left: 50%; top: 70px; transform: translateX(-50%); padding: 12px 26px; border-radius: 999px; background: rgba(0,0,0,.6); color: #fff;
  font: 700 30px "{F['caption'][0]}"; letter-spacing: .06em; white-space: nowrap; }}
.win {{ position: absolute; left: 80px; top: 150px; width: 920px; height: 652px; border-radius: 24px; overflow: hidden; background: #0f0f0f; box-shadow: 0 30px 60px rgba(0,0,0,.35); }}
.win .bar {{ height: 52px; background: #1b1b1b; display: flex; gap: 12px; align-items: center; padding-left: 22px; }} .win .bar i {{ width: 16px; height: 16px; border-radius: 50%; background: #555; }}
.uicard {{ position: absolute; left: 150px; top: 1272px; width: 780px; height: 133px; border-radius: 40px; background: rgba(20,20,20,.85); border: 1px solid rgba(255,255,255,.18);
  display: flex; align-items: center; gap: 24px; padding: 0 30px; color: #fff; font-family: "{F['caption'][0]}"; }}
.uicard .ava {{ width: 84px; height: 84px; border-radius: 50%; background: #fff; color: #111; display: flex; align-items: center; justify-content: center; font: 900 32px "{F['card'][0]}"; }}
.uicard b {{ display: block; font: 700 34px "{F['caption'][0]}"; }} .uicard small {{ font: 500 26px "{F['caption'][0]}"; color: #aaa; }}
.uicard span {{ margin-left: auto; background: #fff; color: #111; border-radius: 999px; padding: 14px 30px; font: 700 28px "{F['caption'][0]}"; }}
.rt {{ position: absolute; left: 60px; right: 60px; top: 188px; text-align: center; font: italic 800 64px/60px "{F['title'][0]}"; color: {acc}; text-shadow: 0 4px 14px rgba(0,0,0,.45); }}
.table {{ position: absolute; left: 157px; top: 997px; width: 768px; height: 506px; background: #020202; }}
.trow {{ position: absolute; left: 4px; right: 4px; height: 68px; display: flex; gap: 4px; }}
.tlab {{ width: 72px; display: flex; align-items: center; justify-content: center; font: 800 30px "{F['caption'][0]}"; color: #111; }} .ttrk {{ flex: 1; background: #1b1d1c; }}
.rcard {{ position: absolute; left: 252px; top: 1087px; width: 578px; height: 326px; border: 2px solid #f4f4f4; overflow: hidden; transform-origin: 0 0; opacity: 0; }}
.rcard b {{ position: absolute; left: 0; right: 0; bottom: 18px; text-align: center; font: 900 74px "{F['card'][0]}"; color: {b['card_name_color']}; text-shadow: 0 4px 16px rgba(0,0,0,.8); }}
.wide {{ position: absolute; left: 0; top: 656px; width: 1080px; height: 608px; background: #111; }}
.wide ~ * {{ }}
.doc {{ position: absolute; left: 24px; top: 24px; width: 580px; height: 560px; border-radius: 14px; background: #fbfaf7; padding: 28px; font-family: "{F['caption'][0]}"; }}
.doc h3 {{ font: 800 30px "{F['caption'][0]}"; margin-bottom: 18px; color: #111; }} .doc p {{ font: 600 26px/1.3 "{F['caption'][0]}"; color: #333; padding: 10px 12px; border-radius: 8px; }}
.lt {{ position: absolute; left: 40px; top: 1130px; padding: 14px 22px; border-radius: 10px; background: rgba(0,0,0,.72); color: #fff; font: 600 26px "{F['caption'][0]}"; border-left: 6px solid {acc}; }}
.lt b {{ color: {acc}; margin-right: 10px; }}
.exp {{ position: absolute; left: 640px; top: 690px; width: 410px; padding: 14px; border-radius: 16px; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.3); }}
.exp small {{ display: block; margin-top: 8px; font: 600 22px "{F['caption'][0]}"; color: #fff; }}
.label {{ position: absolute; left: 36px; top: 1840px; padding: 10px 20px; border-radius: 12px; background: rgba(0,0,0,.66); color: #fff; font: 700 28px "{F['caption'][0]}"; opacity: 0; }}
.label em {{ font-style: normal; color: {acc}; margin-right: 8px; }}"""
    body = (f'<div id="back">{"".join(back)}</div><div id="media">{"".join(media)}</div><div id="front">{"".join(front)}</div>')
    js = f"""
document.querySelectorAll('[data-show]').forEach((el) => {{ tl.set(el, {{ opacity: 1 }}, +el.dataset.show); tl.set(el, {{ opacity: 0 }}, +el.dataset.hide); }});
document.querySelectorAll('[data-pop]').forEach((el) => tl.fromTo(el, {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.28, ease: 'back.out(2)' }}, +el.dataset.pop));
document.querySelectorAll('[data-kb]').forEach((el) => tl.fromTo(el, {{ scale: 1 }}, {{ scale: 1.08, duration: {SEG}, ease: 'none' }}, +el.dataset.kb));
document.querySelectorAll('[data-draw]').forEach((el) => {{ const L = el.getTotalLength(); el.style.strokeDasharray = L;
  tl.fromTo(el, {{ strokeDashoffset: L }}, {{ strokeDashoffset: 0, duration: 0.7, ease: 'power2.inOut' }}, +el.dataset.draw); }});
document.querySelectorAll('[data-count]').forEach((el) => {{ const o = {{ v: 0 }};
  tl.to(o, {{ v: +el.dataset.to, duration: 1.2, ease: 'power2.out', onUpdate: () => (el.textContent = Math.round(o.v)) }}, +el.dataset.count); }});
document.querySelectorAll('[data-hl]').forEach((el) => tl.fromTo(el, {{ backgroundColor: 'rgba(224,138,58,0)' }}, {{ backgroundColor: 'rgba(224,138,58,.28)', duration: 0.2 }}, +el.dataset.hl));
document.querySelectorAll('.rcard').forEach((el) => {{ const t = +el.dataset.rank;            // big card, then it drops into its row
  tl.fromTo(el, {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: 'back.out(1.8)' }}, t);
  tl.to(el, {{ x: +el.dataset.tx - 252, y: +el.dataset.ty - 1087, scale: 0.19, duration: 0.42, ease: 'power3.inOut' }}, t + 1.0); }});"""
    open(os.path.join(proj, "index.html"), "w").write(lib.shell("format-gallery", dur, b.get("fps", 30), W, H, css, body, js))
    print(f"-> {proj}/index.html ({dur:.0f}s, {len(segs)} formats)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
