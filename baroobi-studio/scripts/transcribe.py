"""Word-level transcript for caption timing. Usage: transcribe.py <audio_or_video> <out.json> [model]"""
import json, sys
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
model = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else "small.en", device="cpu", compute_type="int8")
segments, info = model.transcribe(src, word_timestamps=True, vad_filter=True)
words, text = [], []
for seg in segments:
    text.append(seg.text.strip())
    words += [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for w in seg.words]
json.dump({"duration": info.duration, "text": " ".join(text), "words": words}, open(out, "w"), indent=1)
print(f"{len(words)} words, {info.duration:.2f}s -> {out}")
