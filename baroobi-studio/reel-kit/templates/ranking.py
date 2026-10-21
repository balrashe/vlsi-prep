"""ranking-format: talking head full frame, S-F tier table on the chest, each item shown big while it is
named, then dropped into its row. Geometry and colours are measured from @iamajene (STYLE.md, Ranking Format).

    python ranking.py spec.json project_dir

spec.json:
{ "video": "work/cut.mp4", "words": "work/words.json",
  "title": ["BEST PLATFORMS", "TO SIGN CLIENTS"],
  "items": [ {"name": "YouTube", "tier": "S", "at": 2.1, "hold": 1.0, "logo": "logos/youtube.png", "sub": "optional line"} ],
  "accent": ["example"], "brand": "my-brand.json" }
`at` is when the item is named (seconds on the cut). Paths are relative to spec.json.
"""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lib  # noqa: E402

W, H = 1080, 1920
# measured on the 1080x1920 frame
TABLE = dict(x=157, y=997, w=768, h=506, border=4)
ROW_H, ROW_GAP, LABEL_W = 68, 4, 72
SLOT_W, SLOT_H, SLOT_GAP = 108, 64, 4
BIG = dict(x=252, y=1087, w=578, h=326)
TIERS = "SABCDEF"


def main(spec_path, proj):
    base = os.path.dirname(os.path.abspath(spec_path))
    sp = json.load(open(spec_path))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    b = lib.brand(rel(sp["brand"]) if sp.get("brand") else None)
    os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
    shutil.copy(rel(sp["video"]), os.path.join(proj, "assets", "talk.mp4"))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                         os.path.join(proj, "assets", "talk.mp4")]))
    words = json.load(open(rel(sp["words"])))
    F = b["fonts"]

    rows, cards, slots = [], [], {t: 0 for t in TIERS}
    for i, t in enumerate(TIERS):
        top = TABLE["border"] + i * (ROW_H + ROW_GAP)
        rows.append(f'<div class="row" style="top:{top}px"><div class="lab" id="lab{t}" style="background:{b["tiers"][t]}">{t}</div>'
                    f'<div class="track"></div></div>')
    items = sorted(sp["items"], key=lambda x: x["at"])
    for k, it in enumerate(items):
        # hold the big card until just before the next item is named, so cards never stack up
        nxt = items[k + 1]["at"] if k + 1 < len(items) else dur
        it.setdefault("hold", max(0.3, min(1.2, nxt - it["at"] - 0.46)))
    for k, it in enumerate(items):
        t = it["tier"].upper()
        r = TIERS.index(t)
        sx = TABLE["x"] + TABLE["border"] + LABEL_W + 4 + slots[t] * (SLOT_W + SLOT_GAP)
        sy = TABLE["y"] + TABLE["border"] + r * (ROW_H + ROW_GAP) + (ROW_H - SLOT_H) / 2
        slots[t] += 1
        logo = ""
        if it.get("logo"):
            name = f"logo{k}{os.path.splitext(it['logo'])[1]}"
            shutil.copy(rel(it["logo"]), os.path.join(proj, "assets", name))
            logo = f'<img class="logo" src="assets/{name}" alt="">'
        else:
            logo = f'<div class="mono">{lib.E(it["name"][0].upper())}</div>'
        sub = f'<div class="sub">{lib.E(it["sub"])}</div>' if it.get("sub") else ""
        cards.append(f'<div class="card" data-layout-allow-overlap id="c{k}" data-at="{it["at"]}" data-hold="{it["hold"]:.2f}" data-tier="{t}" '
                     f'data-sx="{sx:.1f}" data-sy="{sy:.1f}">{logo}<div class="nm">{lib.E(it["name"].upper())}</div>{sub}</div>')

    caps = lib.caption_html(lib.phrases(words, b.get("caption_words", 3)), sp.get("accent", []))
    condensed = F["card"][0] in ("Anton", "Bebas Neue", "Oswald")   # condensed faces get his wide stretch
    cs = b.get("caption_size", 54); acc_italic = len(F["accent"]) > 3 and F["accent"][3] == "italic"
    title = "".join(f'<div>{lib.E(l)}</div>' for l in sp.get("title", []))
    css = lib.font_css(b, proj) + f"""
#talk {{ position: absolute; inset: 0; width: {W}px; height: {H}px; object-fit: cover; }}
.title {{ position: absolute; left: 60px; right: 60px; top: 188px; text-align: center; font: {F['title'][3] if len(F['title']) > 3 else 'normal'} {F['title'][2]} 64px/60px "{F['title'][0]}";
  text-transform: uppercase; letter-spacing: -0.01em; color: {b['accent']}; text-shadow: 0 4px 14px rgba(0,0,0,.45); }}
.cap {{ position: absolute; left: 40px; right: 40px; top: 920px; text-align: center; font: {F['caption'][2]} {cs}px/1 "{F['caption'][0]}";
  letter-spacing: -0.02em; color: {b['caption_color']}; opacity: 0; text-shadow: 0 2px 10px rgba(0,0,0,.35); white-space: nowrap; }}
.cap .acc {{ font: {F['accent'][3] if len(F['accent']) > 3 else 'normal'} {F['accent'][2]} {round(cs * (1.15 if acc_italic else 1))}px/1 "{F['accent'][0]}"; color: {b['accent']}; letter-spacing: 0; }}
#table {{ position: absolute; left: {TABLE['x']}px; top: {TABLE['y']}px; width: {TABLE['w']}px; height: {TABLE['h']}px; background: #020202; }}
.row {{ position: absolute; left: {TABLE['border']}px; right: {TABLE['border']}px; height: {ROW_H}px; display: flex; gap: 4px; }}
.lab {{ width: {LABEL_W}px; height: {ROW_H}px; display: flex; align-items: center; justify-content: center; font: 800 30px "{F['caption'][0]}"; color: #111; }}
.track {{ flex: 1; background: #1b1d1c; }}
.card {{ position: absolute; left: {BIG['x']}px; top: {BIG['y']}px; width: {BIG['w']}px; height: {BIG['h']}px; transform-origin: 0 0; opacity: 0;
  border: 2px solid #f4f4f4; background: radial-gradient(ellipse 70% 80% at 50% 30%, #12306a 0%, #071027 55%, #03060f 100%);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; overflow: hidden; }}
.card .logo {{ width: 124px; height: 124px; object-fit: contain; }}
.card .mono {{ width: 124px; height: 124px; border-radius: 50%; background: {b['accent']}; color: #fff; display: flex; align-items: center; justify-content: center; font: {F['card'][2]} 84px "{F['card'][0]}"; }}
.card .nm {{ font: {F['card'][2]} {78 if condensed else 66}px/0.95 "{F['card'][0]}"; color: {b['card_name_color']}; letter-spacing: {'0.02em' if condensed else '-0.01em'}; text-align: center; padding: 0 20px; text-transform: uppercase;{' transform: scaleX(1.18);' if condensed else ''} }}
.card .sub {{ font: 600 28px "{F['caption'][0]}"; color: #cfd6e6; }}"""
    body = f"""<video id="talk" src="assets/talk.mp4" data-start="0" data-duration="{dur:.3f}" data-track-index="0" playsinline data-has-audio="true"></video>
<div class="title" id="title">{title}</div>
<div id="table">{''.join(rows)}</div>
{''.join(cards)}
{caps}"""
    js = lib.CAPTION_JS + f"""
// each item: pops in big while it is named, holds, then flies into its tier row and the label pulses
document.querySelectorAll('.card').forEach((c) => {{
  const at = +c.dataset.at, hold = +c.dataset.hold, sx = +c.dataset.sx, sy = +c.dataset.sy, s = {SLOT_W / BIG['w']:.4f};
  tl.fromTo(c, {{ opacity: 0, scale: 0.62, x: {BIG['w']} * 0.19, y: {BIG['h']} * 0.19 }}, {{ opacity: 1, scale: 1, x: 0, y: 0, duration: 0.2, ease: 'back.out(1.8)' }}, at);
  tl.to(c, {{ x: sx - {BIG['x']}, y: sy - {BIG['y']}, scale: s, borderWidth: 1, duration: 0.42, ease: 'power3.inOut' }}, at + hold);
  tl.fromTo('#lab' + c.dataset.tier, {{ filter: 'brightness(1)' }}, {{ filter: 'brightness(1.45)', duration: 0.09, yoyo: true, repeat: 1 }}, at + hold + 0.4);
}});"""
    open(os.path.join(proj, "index.html"), "w").write(lib.shell("ranking-format", dur, b.get("fps", 30), W, H, css, body, js))
    print(f"-> {proj}/index.html ({dur:.1f}s, {len(sp['items'])} items)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
