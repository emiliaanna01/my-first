"""Synthesized sound design (no stock library needed): whoosh, pop, shimmer, tap, and a lo-fi music bed.

Usage: python tools/sound.py OUTDIR --seconds 17
Writes OUTDIR/whoosh.wav, pop.wav, shimmer.wav, tap.wav, swoosh_soft.wav and OUTDIR/lofi.wav (mellow 80 BPM bed:
electric-piano 7th chords, soft kick, brushed hats, vinyl crackle, low-passed).
"""
import argparse, os, wave
import numpy as np

SR = 48000


def save(path, x):
    x = np.clip(x / (np.abs(x).max() + 1e-9) * 0.89, -1, 1)
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y


def sweep_noise(dur, f0, f1, rng, q=0.25):
    """Band-limited noise whose center frequency sweeps f0 -> f1 (a whoosh body)."""
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    spec = np.fft.rfft(noise); freqs = np.fft.rfftfreq(n, 1 / SR)
    out = np.zeros(n)
    seg = 16
    for k in range(seg):  # piecewise band-pass via FFT on overlapping windows
        c = f0 * (f1 / f0) ** (k / (seg - 1))
        band = np.exp(-0.5 * ((np.log(freqs + 1) - np.log(c)) / q) ** 2)
        part = np.fft.irfft(spec * band, n)
        win = np.exp(-0.5 * ((t - dur * k / (seg - 1)) / (dur / seg)) ** 2)
        out += part * win
    return out


def whoosh(rng, dur=0.42, f0=300, f1=3000):
    x = sweep_noise(dur, f0, f1, rng)
    t = np.arange(len(x)) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6 * np.exp(-1.5 * t / dur)
    return x * env


def pop(freq=880, dur=0.12):
    t = np.arange(int(dur * SR)) / SR
    f = freq * (1 + 0.6 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 50)


def shimmer(rng, dur=0.9):
    t = np.arange(int(dur * SR)) / SR
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * (3 + k)) for k, f in enumerate((1568, 2093, 2637, 3136, 4186)))
    return x * (1 - np.exp(-t * 80)) + 0.15 * sweep_noise(dur, 4000, 9000, rng) * np.exp(-t * 4)


def tap():
    t = np.arange(int(0.08 * SR)) / SR
    return np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 90) + 0.5 * np.sin(2 * np.pi * 2800 * t) * np.exp(-t * 140)


def epiano(freq, dur):
    t = np.arange(int(dur * SR)) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) * np.exp(-t * 3) + 0.12 * np.sin(6 * np.pi * freq * t) * np.exp(-t * 6)
    env = (1 - np.exp(-t * 60)) * np.exp(-t * 0.9)
    trem = 1 + 0.18 * np.sin(2 * np.pi * 4.5 * t)
    return tone * env * trem


def lofi(seconds, rng):
    bpm = 80; beat = 60 / bpm; bar = 4 * beat
    n = int(seconds * SR); mix = np.zeros(n)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]  # Fmaj7 Em7 Dm7 Cmaj7
    for b in range(int(seconds / bar) + 1):
        for m in chords[b % 4]:
            x = epiano(midi(m), bar * 1.05) * 0.22
            s = int(b * bar * SR) + int(rng.uniform(0, 0.02) * SR)  # slightly loose, humanized
            e = min(n, s + len(x)); mix[s:e] += x[:e - s]
        bass = epiano(midi(chords[b % 4][0] - 12), bar) * 0.35
        s = int(b * bar * SR); e = min(n, s + len(bass)); mix[s:e] += bass[:e - s]
    kick_t = np.arange(int(0.25 * SR)) / SR
    kick = np.sin(2 * np.pi * (50 + 70 * np.exp(-kick_t * 30)) * kick_t) * np.exp(-kick_t * 12) * 0.55
    hat = rng.normal(0, 1, int(0.05 * SR)); hat = np.diff(hat, prepend=0) * np.exp(-np.arange(len(hat)) / SR * 70) * 0.06
    snare_t = np.arange(int(0.18 * SR)) / SR
    snare = (rng.normal(0, 1, len(snare_t)) * 0.18 + np.sin(2 * np.pi * 190 * snare_t) * 0.2) * np.exp(-snare_t * 22)
    for k in range(int(seconds / (beat / 2)) + 1):
        s = int(k * beat / 2 * SR)
        for sample, cond in ((kick, k % 8 in (0, 5)), (snare, k % 8 in (2, 6)), (hat, True)):
            if cond:
                swing = int(0.035 * SR) if k % 2 else 0
                e = min(n, s + swing + len(sample))
                if s + swing < n:
                    mix[s + swing:e] += sample[:e - s - swing] * (0.6 if sample is hat and k % 2 else 1)
    crackle = (rng.random(n) < 0.0009) * rng.normal(0, 0.25, n) + rng.normal(0, 0.004, n)
    mix = onepole_lp(mix, 2600) + crackle
    fade = np.minimum(1, np.minimum(np.arange(n) / (0.6 * SR), (n - np.arange(n)) / (1.2 * SR)))
    return mix * fade


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("outdir"); ap.add_argument("--seconds", type=float, default=17)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    rng = np.random.default_rng(5)
    save(f"{a.outdir}/whoosh.wav", whoosh(rng))
    save(f"{a.outdir}/swoosh_soft.wav", whoosh(rng, 0.32, 500, 2200) * 0.6)
    save(f"{a.outdir}/pop.wav", pop())
    save(f"{a.outdir}/shimmer.wav", shimmer(rng))
    save(f"{a.outdir}/tap.wav", tap())
    save(f"{a.outdir}/lofi.wav", lofi(a.seconds, rng))


if __name__ == "__main__":
    main()
