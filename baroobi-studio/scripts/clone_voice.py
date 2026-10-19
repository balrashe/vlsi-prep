"""Clone baroobi's voice in local VoiceStudio (VoxCPM2, Apache-2.0) and voice a reel script.

  clone_voice.py profile <sample.(wav|m4a|mp3)>   build/refresh the "baroobi" voice profile from a clean sample
  clone_voice.py speak <slug>                      voice scripts/<slug>/beats.json -> assets/voice/<slug>.wav
  clone_voice.py redo <slug> <n[,n]>               regenerate beats n (Whisper-checked), keep the rest
  clone_voice.py retrim <slug>                     re-cut existing beats to their words and rejoin

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
REF_SECONDS = float(os.environ.get("VOICE_REF_SECONDS", 25))   # VoxCPM2 caps at 30 s; longer = slower on CPU
GAP = 0.06                # between sentences: v2 at 0.12 still read loose to him

# Whisper mishearings of his own sample, fixed so the reference transcript matches what he said
HEARD = [(r"\bMaroobie\b|\bBaroobie\b|\bbaroobie\b", "baroobi"), (r"\bcloud code\b", "Claude Code")]

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
    for pat, rep in HEARD:
        ref_text = re.sub(pat, rep, ref_text, flags=re.I)
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


def transcript(path):
    out = path + ".json"
    subprocess.run([os.path.join(ROOT, ".venv", "bin", "python"), os.path.join(ROOT, "scripts", "transcribe.py"),
                    path, out, "small.en"], check=True, capture_output=True)
    return json.load(open(out))


def heard(path):
    return transcript(path)["text"]


def speech_onset(raw):
    """VoxCPM2 opens every take with ~70 ms of hiss (>80% of its energy above 4 kHz) before a short silence.
    Joined after the previous line, that burst was the v1 "weird sound at the end of each clip".
    Returns the first voiced moment after it."""
    import wave
    import numpy as np
    with wave.open(raw) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
    n = int(sr * 0.01)
    db = [20 * np.log10(np.sqrt(np.mean(x[i:i + n] ** 2)) + 1e-9) for i in range(0, len(x) - n, n)]
    k = 0
    while k < len(db) and db[k] > -45 and k < 25:     # skip the opening burst
        k += 1
    while k < len(db) and db[k] <= -40:               # skip the silence after it
        k += 1
    return k * 0.01


def speech_offset(raw, after):
    """End of the line: from Whisper's last word end, run on until the level stays under -40 dB for 80 ms
    (Whisper's word ends run early, and a fixed pad either clipped "credits" or kept dead air)."""
    import wave
    import numpy as np
    with wave.open(raw) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
    n = int(sr * 0.01)
    k, quiet = int(after / 0.01), 0
    while k * n + n < len(x) and k * 0.01 < after + 0.35:
        db = 20 * np.log10(np.sqrt(np.mean(x[k * n:k * n + n] ** 2)) + 1e-9)
        quiet = quiet + 1 if db <= -40 else 0
        if quiet >= 8:                                # a "t" closure before a final "s" is ~40 ms of quiet
            return (k - 7) * 0.01 + 0.03
        k += 1
    return min(len(x) / sr, k * 0.01)


def tighten(raw, out):
    """Cut a generated line to its speech: past the opening hiss, and on to where the last word's sound dies."""
    w = transcript(raw)["words"]
    if not w:
        ffmpeg("-i", raw, out)
        return
    t0, t1 = max(0.0, speech_onset(raw) - 0.015), speech_offset(raw, w[-1]["end"])
    ffmpeg("-i", raw, "-af", f"atrim={t0:.3f}:{t1:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,"
           f"afade=t=out:st={max(0, t1 - t0 - 0.04):.3f}:d=0.04", out)


def norm_words(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower().replace("-", " ")).split()


def speak(slug, redo=None):
    """redo: 1-based beat numbers to regenerate (others are reused). Redone beats retry seeds until Whisper
    hears >= 85% of the line's words in order, so "And it worked" never ships as "It ain't work"."""
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
        if redo is not None and (i + 1) not in redo and os.path.exists(out):
            parts.append(out)
            continue
        for seed in ((7,) if redo is None else (11, 23, 42, 77, 101)):
            audio = call("/generate", {"text": text, "profile_id": prof["profile_id"], "engine": ENGINE,
                                       "language": "English", "seed": seed})
            raw = out.replace(".wav", ".raw.wav")
            open(raw, "wb").write(audio)
            duration(raw)                       # proves it decoded as audio, not an error body
            tighten(raw, out)
            d = duration(out)
            if redo is None:
                break
            got = heard(out)
            want = norm_words(re.sub(r"\d+", lambda m: m.group(), st["say"]))
            ok = __import__("difflib").SequenceMatcher(None, want, norm_words(got)).ratio() >= 0.85
            print(f"     seed {seed}: heard \"{got}\" {'OK' if ok else 'retry'}")
            if ok:
                break
        print(f"  {i + 1:02d} {d:5.2f}s  {text}")
        parts.append(out)
    join(slug, parts, prof)


def retrim(slug):
    """Re-cut every existing beat from its raw take, then rejoin (no regeneration)."""
    work = os.path.join(ROOT, "assets", "voice", "work", slug)
    n = len(json.load(open(os.path.join(ROOT, "scripts", slug, "beats.json")))["steps"])
    parts = []
    for i in range(1, n + 1):
        out = os.path.join(work, f"beat{i:02d}.wav")
        tighten(out.replace(".wav", ".raw.wav"), out)
        print(f"  {i:02d} {duration(out):5.2f}s")
        parts.append(out)
    join(slug, parts, json.load(open(STATE)))


def join(slug, parts, prof):
    work = os.path.join(ROOT, "assets", "voice", "work", slug)
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
           # any pause over 0.12 s shrinks to 0.07 s (his edits leave ~0.09 s)
           "-af", "silenceremove=stop_periods=-1:stop_duration=0.12:stop_threshold=-40dB:stop_silence=0.07,"
                  "loudnorm=I=-16:TP=-1.5", dest)
    json.dump({"source": "voice clone", "engine": ENGINE, "profile": prof["profile_id"]},
              open(os.path.join(ROOT, "assets", "voice", f"{slug}.meta.json"), "w"))
    print(f"-> {dest} ({duration(dest):.2f}s)")


if __name__ == "__main__":
    {"profile": lambda: build_profile(sys.argv[2]), "speak": lambda: speak(sys.argv[2]),
     "redo": lambda: speak(sys.argv[2], {int(x) for x in sys.argv[3].split(",")}),
     "retrim": lambda: retrim(sys.argv[2])}[sys.argv[1]]()
