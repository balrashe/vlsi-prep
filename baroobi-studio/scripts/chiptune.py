"""8-bit audio bed, generated locally (no samples, no licences): square-wave arps, triangle bass, noise drums,
plus retro hits on the cues the video gives it. Usage from build_video.py: render(total, hits, out_wav, with_voice)
hits = [(seconds, "blip" | "coin" | "power")]
"""
import subprocess
import wave

import numpy as np

SR = 44100
BPM = 112
STEP = 60 / BPM / 4                      # one 16th note
PROG = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]   # C  G  Am  F


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def square(f, d, duty=0.25, vol=1.0):
    t = np.arange(int(d * SR)) / SR
    w = np.where((t * f) % 1 < duty, 1.0, -1.0)
    env = np.exp(-t * 9) * 0.85 + 0.15
    env[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    return w * env * vol


def triangle(f, d, vol=1.0):
    t = np.arange(int(d * SR)) / SR
    w = 2 * np.abs(2 * ((t * f) % 1) - 1) - 1
    env = np.minimum(1, (d - t) / 0.02)
    return w * env * vol


def noise(d, decay, vol, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(int(d * SR)) / SR
    return rng.uniform(-1, 1, len(t)) * np.exp(-t * decay) * vol


def kick(vol=1.0):
    t = np.arange(int(0.16 * SR)) / SR
    f = 150 * np.exp(-t * 28) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) * vol


def place(buf, sig, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def music(total):
    buf = np.zeros(int(total * SR) + SR)
    n_steps = int(total / STEP) + 1
    for k in range(n_steps):
        t = k * STEP
        chord = PROG[(k // 16) % 4]
        arp = [chord[0], chord[1], chord[2], chord[1] + 12][k % 4] + 12
        place(buf, square(hz(arp), STEP * 0.9, 0.25, 0.10), t)
        if k % 2 == 0:
            place(buf, triangle(hz(chord[0] - 24 + (12 if k % 8 == 4 else 0)), STEP * 1.8, 0.30), t)
        if k % 8 == 0:
            place(buf, kick(0.55), t)
        if k % 8 == 4:
            place(buf, noise(0.12, 30, 0.22, k), t)
        if k % 2 == 1:
            place(buf, noise(0.03, 120, 0.06, k), t)
    fade = int(1.2 * SR)
    end = int(total * SR)
    buf[end - fade:end] *= np.linspace(1, 0, fade)
    buf[end:] = 0
    return buf


def sfx(kind):
    if kind == "blip":
        t = np.arange(int(0.09 * SR)) / SR
        f = 520 + 900 * t / 0.09
        return np.where((np.cumsum(f) / SR) % 1 < 0.5, 1.0, -1.0) * np.exp(-t * 22) * 0.35
    if kind == "coin":
        return np.concatenate([square(988, 0.07, 0.5, 0.35), square(1319, 0.32, 0.5, 0.35)])
    if kind == "power":
        return np.concatenate([square(hz(n), 0.055, 0.5, 0.3) for n in (72, 76, 79, 84, 88)])
    raise ValueError(kind)


def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def render(total, hits, out, with_voice):
    """Music under a voiceover sits ~-28 LUFS; on its own (animatic) ~-18 LUFS. Hits ride on top."""
    m = music(total)
    h = np.zeros_like(m)
    for t, kind in hits:
        place(h, sfx(kind), t)
    tmp_m, tmp_h = out + ".music.wav", out + ".hits.wav"
    write(tmp_m, m * 0.5); write(tmp_h, h)
    target = -28 if with_voice else -18
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp_m, "-i", tmp_h, "-filter_complex",
                    f"[0]loudnorm=I={target}:TP=-3:LRA=7[m];[1]volume={0.55 if with_voice else 0.8}[h];"
                    "[m][h]amix=inputs=2:normalize=0,alimiter=limit=0.8:level=0[o]",
                    "-map", "[o]", "-ar", "48000", "-ac", "1", "-t", f"{total}", out], check=True)
    for f in (tmp_m, tmp_h):
        __import__("os").remove(f)
