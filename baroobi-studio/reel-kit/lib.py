"""Shared pieces for every reel-kit template: brand, fonts, caption phrasing and the HTML shell."""
import html, json, os, re, shutil

KIT = os.path.dirname(os.path.abspath(__file__))
E = html.escape


def brand(path=None):
    b = json.load(open(os.path.join(KIT, "brand.json")))
    if path and os.path.exists(path):
        over = json.load(open(path))
        for k, v in over.items():
            b[k] = {**b[k], **v} if isinstance(v, dict) and isinstance(b.get(k), dict) else v
    return b


def font_css(b, proj):
    """Copy the brand fonts into the project and declare them."""
    os.makedirs(os.path.join(proj, "assets", "fonts"), exist_ok=True)
    css = []
    for role, spec in b["fonts"].items():
        fam, file, weight = spec[0], spec[1], spec[2]
        style = spec[3] if len(spec) > 3 else "normal"
        src = file if os.path.isabs(file) else os.path.join(KIT, "fonts", file)
        shutil.copy(src, os.path.join(proj, "assets", "fonts", os.path.basename(src)))
        css.append(f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{os.path.basename(src)}") format("woff2"); '
                   f'font-weight: {weight if role != "caption" else "100 900"}; font-style: {style}; }}')
    return "\n".join(css)


def phrases(words, max_words=3, gap=0.22):
    """Group words the way his captions read: 1-3 words, a new phrase after a pause or punctuation."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        brk = (len(cur) >= max_words or re.search(r"[.,!?;:]$", w["w"]) or nxt is None or nxt["s"] - w["e"] > gap)
        if brk:
            out.append(cur); cur = []
    res = []
    for i, p in enumerate(out):
        end = out[i + 1][0]["s"] if i + 1 < len(out) else p[-1]["e"] + 0.4
        res.append({"s": p[0]["s"], "e": end, "words": p})
    return res


def caption_html(ph, accent_words=(), cls="cap"):
    """One div per phrase; accent words switch to the italic serif in the accent colour."""
    acc = {a.lower() for a in accent_words}
    rows = []
    for i, p in enumerate(ph):
        inner = " ".join(
            f'<span class="acc">{E(w["w"])}</span>' if re.sub(r"[^\w£$%]", "", w["w"].lower()) in acc else E(w["w"])
            for w in p["words"])
        rows.append(f'<div class="{cls}" data-s="{p["s"]:.3f}" data-e="{p["e"]:.3f}">{inner}</div>')
    return "\n".join(rows)


CAPTION_JS = """
document.querySelectorAll('.cap').forEach((c) => {           // hard on, hard off: no fade, as measured
  tl.set(c, { opacity: 1 }, +c.dataset.s); tl.set(c, { opacity: 0 }, +c.dataset.e);
});"""


def shell(title, duration, fps, w, h, css, body, js):
    return f"""<!doctype html>
<html lang="en" data-resolution="{'portrait' if h > w else 'landscape'}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={w}, height={h}" />
<title>{E(title)}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: #000; }}
#root {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; }}
{css}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{duration:.3f}" data-width="{w}" data-height="{h}" data-fps="{fps}">
{body}
</div>
<script>
function build() {{
  const tl = gsap.timeline({{ paused: true }});
{js}
  tl.set({{}}, {{}}, {duration:.3f});
  window.__timelines["main"] = tl;
}}
document.fonts.ready.then(build);
</script>
</body>
</html>
"""
