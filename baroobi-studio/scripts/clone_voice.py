"""Clone baroobi's voice in local VoiceStudio (VoxCPM2, Apache-2.0) and voice a reel script.

  clone_voice.py profile <sample.(wav|m4a|mp3)>   build/refresh the "baroobi" voice profile from a clean sample
  clone_voice.py speak <slug>                      voice scripts/<slug>/beats.json -> assets/voice/<slug>.wav

The backend must be running (tools/VoiceStudio: `bun scripts/dev-backend.mjs`, http://127.0.0.1:3900).
OmniVoice, VoiceStudio's default engine, is CC-BY-NC, so it is never used here: these reels are commercial.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.environ.get("VOICESTUDIO_URL", "http://127.0.0.1:3900")
ENGINE = "voxcpm2"
PROFILE_NAME = os.environ.get("VOICE_PROFILE_NAME", "baroobi")
STATE = os.environ.get("VOICE_PROFILE_STATE", os.path.join(ROOT, "assets", "voice", "profile.json"))
REF_SECONDS = 25          # VoxCPM2 caps references at 30 s
GAP = 0.16                # silence between beats

# spoken forms so the clone never guesses at digits or acronyms
SAY = [(r"\b69\b", "sixty-nine"), (r"\b20\b", "twenty"), (r"\b1 job\b", "one job"),
       (r"\b2025\b", "twenty twenty-five"), (r"\b2026\b", "twenty twenty-six"),
       (r"\bMIT\b", "M.I.T."), (r"\bAPI\b", "A.P.I."), (r"\bCV\b", "C.V.")]


def call(path, fields=None, files=None, method="POST"):
    """multipart via curl: keeps this stdlib-only and streams large files."""
    cmd = ["curl", "-s", "--fail-with-body", "-X", method, f"{API}{path}"]
    for k, v in (fields or {}).items():
        cmd += ["-F", f"{k}={v}"]
    for k, v in (files or {}).items():
        cmd += ["-F", f"{k}=@{v}"]
    out = subprocess.run(cmd, capture_output=True, check=False)
    if out.returncode:
        raise RuntimeError(f"{method} {path} failed: {out.stdout[:400]!r}")
    return out.stdout


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).decode())


def build_profile(sample):
    """Clean the sample, pick the best ~25 s of continuous speech, register it with its transcript."""
    work = os.path.join(ROOT, "assets", "voice", "work")
    os.makedirs(work, exist_ok=True)
    clean = os.path.join(work, "sample_clean.wav")
    ffmpeg("-i", sample, "-ac", "1", "-ar", "48000",
           "-af", "highpass=f=70,silenceremove=start_periods=1:start_threshold=-45dB,loudnorm=I=-18:TP=-2", clean)
    words_json = os.path.join(work, "sample_words.json")
    subprocess.run([os.path.join(ROOT, ".venv", "bin", "python"), os.path.join(ROOT, "scripts", "transcribe.py"),
                    clean, words_json, "small.en"], check=True)
    words = json.load(open(words_json))["words"]
    if not words:
        raise SystemExit("No speech found in the sample.")
    # longest window up to REF_SECONDS on word boundaries; denser speech breaks ties
    best, bi, bj = (-1, -1.0), 0, 0
    for i in range(len(words)):
        j = i
        while j + 1 < len(words) and words[j + 1]["end"] - words[i]["start"] <= REF_SECONDS:
            j += 1
        span = words[j]["end"] - words[i]["start"]
        score = (round(span), (j - i + 1) / max(span, 0.5))
        if score > best:
            best, bi, bj = score, i, j
    t0, t1 = max(0, words[bi]["start"] - 0.05), words[bj]["end"] + 0.1
    ref = os.path.join(work, "ref.wav")
    ffmpeg("-i", clean, "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", ref)
    ref_text = " ".join(w["word"] for w in words[bi:bj + 1])
    old = json.load(open(STATE)) if os.path.exists(STATE) else {}
    if old.get("profile_id"):
        try:
            call(f"/profiles/{old['profile_id']}", method="DELETE")
        except RuntimeError:
            pass
    prof = json.loads(call("/profiles", {"name": PROFILE_NAME, "ref_text": ref_text, "language": "English"},
                           {"ref_audio": ref}))
    pid = prof.get("id") or prof.get("profile_id")
    json.dump({"profile_id": pid, "engine": ENGINE, "ref_seconds": round(t1 - t0, 2), "ref_text": ref_text,
               "sample": os.path.basename(sample)}, open(STATE, "w"), indent=1)
    print(f"profile {pid}: {t1 - t0:.1f}s reference from {os.path.basename(sample)}")
    print(f'  "{ref_text}"')


def speak(slug):
    prof = json.load(open(STATE))
    beats = json.load(open(os.path.join(ROOT, "scripts", slug, "beats.json")))
    work = os.path.join(ROOT, "assets", "voice", "work", slug)
    os.makedirs(work, exist_ok=True)
    parts = []
    for i, st in enumerate(beats["steps"]):
        text = st["say"]
        for pat, rep in SAY:
            text = re.sub(pat, rep, text)
        out = os.path.join(work, f"beat{i + 1:02d}.wav")
        audio = call("/generate", {"text": text, "profile_id": prof["profile_id"], "engine": ENGINE,
                                   "language": "English", "seed": 7})
        raw = out.replace(".wav", ".raw.wav")
        open(raw, "wb").write(audio)
        trim = "silenceremove=start_periods=1:start_threshold=-45dB"
        ffmpeg("-i", raw, "-af", f"{trim},areverse,{trim},areverse", out)    # trim both ends of the beat
        d = duration(out)                       # proves it decoded as audio, not an error body
        print(f"  {i + 1:02d} {d:5.2f}s  {text}")
        parts.append(out)
    gap = os.path.join(work, "gap.wav")
    ffmpeg("-f", "lavfi", "-i", f"anullsrc=r=48000:cl=mono", "-t", str(GAP), gap)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for k, p in enumerate(parts):
            f.write(f"file '{p}'\n")
            if k < len(parts) - 1:
                f.write(f"file '{gap}'\n")
    dest = os.path.join(ROOT, "assets", "voice", f"{slug}.wav")
    ffmpeg("-f", "concat", "-safe", "0", "-i", lst, "-ar", "48000", "-ac", "1",
           "-af", "loudnorm=I=-16:TP=-1.5", dest)
    json.dump({"source": "voice clone", "engine": ENGINE, "profile": prof["profile_id"]},
              open(os.path.join(ROOT, "assets", "voice", f"{slug}.meta.json"), "w"))
    print(f"-> {dest} ({duration(dest):.2f}s)")


if __name__ == "__main__":
    {"profile": lambda: build_profile(sys.argv[2]), "speak": lambda: speak(sys.argv[2])}[sys.argv[1]]()
