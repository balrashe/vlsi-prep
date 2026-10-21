"""Tight jump-cut from a raw talking-head file.

Transcribes with word timestamps, keeps only the spans where words are spoken, closes every pause
longer than MAX_GAP down to a short breath, and writes the cut video plus the words retimed to it.

    python cut.py raw.mp4 out_dir [--gap 0.18] [--pad 0.06] [--model small.en] [--fps 30]

out_dir/cut.mp4      1080x1920 (centre-cropped if the source is not 9:16) or 1920x1080 with --wide
out_dir/words.json   [{"w": "word", "s": start, "e": end}] on the cut timeline
out_dir/edl.json     the source ranges that were kept, for notes like "put back the bit about X"
"""
import argparse, json, os, subprocess, sys


def transcribe(path, model, dur):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    for vad in (True, False):
        # the voice-activity filter sometimes drops fast, loud phone takes; fall back to no filter if it kept too little
        segs, _ = m.transcribe(path, word_timestamps=True, vad_filter=vad, beam_size=5)
        words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)}
                 for s in segs for w in (s.words or []) if w.word.strip()]
        if len(words) >= 0.8 * dur:
            break
    return words


def keep_ranges(words, gap, pad, dur):
    """Merge word spans; any silence over `gap` is cut, leaving `pad` of air on each side."""
    out = []
    for w in words:
        s, e = max(0, w["s"] - pad), min(dur, w["e"] + pad)
        if out and s - out[-1][1] <= gap:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [r for r in out if r[1] - r[0] > 0.12]


def probe(path):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration",
                                            "-of", "json", path]))
    st = next(s for s in j["streams"] if "width" in s)
    return st["width"], st["height"], float(j["format"]["duration"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("out")
    ap.add_argument("--gap", type=float, default=0.18)
    ap.add_argument("--pad", type=float, default=0.06)
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--wide", action="store_true", help="16:9 output instead of 9:16")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    w, h, dur = probe(a.raw)
    words = transcribe(a.raw, a.model, dur)
    if not words:
        sys.exit("no speech found")
    ranges = keep_ranges(words, a.gap, a.pad, dur)

    W, H = (1920, 1080) if a.wide else (1080, 1920)
    fit = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={a.fps},setsar=1"
    parts, labels = [], ""
    for i, (s, e) in enumerate(ranges):
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS,{fit}[v{i}];"
                     f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={max(0, e - s - 0.012):.3f}:d=0.012[a{i}];")
        labels += f"[v{i}][a{i}]"
    graph = "".join(parts) + f"{labels}concat=n={len(ranges)}:v=1:a=1[v][a]"
    out_mp4 = os.path.join(a.out, "cut.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.raw, "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4], check=True)

    # move every word onto the cut timeline
    shift, t_out, retimed = [], 0.0, []
    for s, e in ranges:
        shift.append((s, e, t_out - s)); t_out += e - s
    for wd in words:
        for s, e, d in shift:
            if s <= wd["s"] < e:
                retimed.append({"w": wd["w"], "s": round(wd["s"] + d, 3), "e": round(min(wd["e"], e) + d, 3)}); break
    json.dump(retimed, open(os.path.join(a.out, "words.json"), "w"), indent=1)
    json.dump({"source": os.path.abspath(a.raw), "ranges": ranges, "duration": round(t_out, 3)},
              open(os.path.join(a.out, "edl.json"), "w"), indent=1)
    print(f"{len(ranges)} ranges kept, {dur:.1f}s -> {t_out:.1f}s, {len(retimed)} words -> {out_mp4}")


if __name__ == "__main__":
    main()
