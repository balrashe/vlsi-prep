"""Scaffold a mascot reel project from the template.

    python new_reel.py <project_dir> [--duration 12]

Copies the template, the stage/mascot/recipe modules, the 3D font and the brand fonts. Then edit the two
"EDIT" blocks in <project_dir>/index.html (beat clock + captions, and one beat() per idea).
"""
import argparse, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--duration", type=float, default=12)
    a = ap.parse_args()
    if os.path.exists(os.path.join(a.project, "index.html")):
        raise SystemExit(f"{a.project}/index.html already exists; not overwriting")
    os.makedirs(os.path.join(a.project, "assets", "fonts"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "assets")):
        shutil.copy(os.path.join(HERE, "assets", f), os.path.join(a.project, "assets", f))
    for f in ("Montserrat.woff2", "Inter.woff2"):
        shutil.copy(os.path.join(FONTS, f), os.path.join(a.project, "assets", "fonts", f))
    mono = os.path.join(FONTS, "JetBrainsMono.woff2")
    if os.path.exists(mono):
        shutil.copy(mono, os.path.join(a.project, "assets", "fonts", "JetBrainsMono.woff2"))
    html = open(os.path.join(HERE, "template.html")).read().replace("__DURATION__", f"{a.duration:g}")
    open(os.path.join(a.project, "index.html"), "w").write(html)
    print(f"-> {a.project}/index.html (edit the BEATS/CAPS block and the beat() block)")


if __name__ == "__main__":
    main()
