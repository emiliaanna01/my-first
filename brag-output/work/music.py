"""Soundtrack for the RoundHouse launch video: 120 BPM, D major, 54 s, on the video's beat grid.

Writes a 48 kHz stereo WAV. Usage: python3 music.py OUT.wav
"""
import sys
import wave

import numpy as np

SR = 48000
BPM = 120
BEAT = 60 / BPM            # 0.5 s = 15 video frames
BAR = 4 * BEAT
LENGTH = 54.0
TAIL = 0.0
N = int(SR * (LENGTH + TAIL))
rng = np.random.default_rng(7)

# Video cut frames (30 fps) and which ones are colour wipes.
CUTS = [0, 120, 270, 420, 630, 810, 990, 1140, 1320, 1440]
WIPES = {420, 810, 990, 1140, 1320}

dry = np.zeros((2, N))
wet = np.zeros((2, N))     # send to reverb


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, sig, t, pan=0.0, gain=1.0):
    i = int(round(t * SR))
    if i >= N:
        return
    sig = sig[: N - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(sig)] += sig * l * 1.414
    buf[1, i:i + len(sig)] += sig * r * 1.414


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X * m, len(x))


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


# ---- instruments ----
def epiano(m, dur, vel=1.0):
    n = int(SR * (dur + 1.2))
    t = np.arange(n) / SR
    f = midi(m)
    mod = 1.6 * np.exp(-t / 0.35) * np.sin(2 * np.pi * f * t)
    x = np.sin(2 * np.pi * f * t + mod) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.4)
    e = env(n, 0.004, 0.9) * np.where(t < dur, 1, np.exp(-(t - dur) / 0.25))
    return x * e * vel


def pad(m, dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = midi(m)
    x = sum(np.sin(2 * np.pi * f * (1 + d) * t + ph) for d, ph in [(-0.003, 0), (0.0, 1.1), (0.0031, 2.3)])
    x += 0.18 * np.sin(2 * np.pi * 2 * f * t)
    a = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.6)
    return x * a / 3


def bell(m, vel=1.0, dur=2.2):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = midi(m)
    x = np.sin(2 * np.pi * f * t + 0.9 * np.exp(-t / 0.2) * np.sin(2 * np.pi * 3.5 * f * t))
    x += 0.3 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.25)
    return x * env(n, 0.002, 0.55) * vel


def bass(m, dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = midi(m)
    x = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * 2 * f * t)
    x = np.tanh(1.6 * x) / np.tanh(1.6)
    e = np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.04) * (0.75 + 0.25 * np.exp(-t / 0.2))
    return x * e


def kick():
    n = int(SR * 0.45)
    t = np.arange(n) / SR
    f = 45 + 75 * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.18) * np.minimum(1, t / 0.002)


def shaker(vel):
    n = int(SR * 0.09)
    x = fft_filter(rng.standard_normal(n), lo=6000, hi=12000)
    t = np.arange(n) / SR
    return x * np.minimum(1, t / 0.012) * np.exp(-t / 0.025) * vel


def snap():
    n = int(SR * 0.25)
    x = fft_filter(rng.standard_normal(n), lo=1200, hi=5000)
    t = np.arange(n) / SR
    return x * np.exp(-t / 0.06) * np.minimum(1, t / 0.003)


def air(length, peak_at_end=True):
    n = int(SR * length)
    x = fft_filter(rng.standard_normal(n), lo=500, hi=3500)
    t = np.arange(n) / SR
    e = (t / length) ** 2.2 if peak_at_end else np.exp(-t / (length / 3))
    return x * e


def tick(m):
    n = int(SR * 0.06)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * midi(m) * t) * np.exp(-t / 0.012)


# ---- arrangement ----
# Bars of 2 s. 0-1 intro, 2-18 groove, 19-21 breakdown (calculator), 22-26 groove, 26 ends on D.
PROG = [  # (bass root, chord voicing)
    (38, [57, 61, 64, 66]),          # Dmaj9
    (35, [54, 57, 61, 62]),          # Bm9
    (31, [54, 57, 59, 62]),          # Gmaj9
    (33, [57, 62, 64, 66]),          # A6sus
]
BARS = int(LENGTH / BAR)  # 27
for b in range(BARS):
    t0 = b * BAR
    root, chord = PROG[b % 4]
    last = b == BARS - 1
    if last:
        root, chord = 38, [57, 62, 66, 69]
    breakdown = 19 <= b <= 21
    groove = (2 <= b <= 18) or b >= 22

    for m in chord:  # pad bed throughout
        place(wet, pad(m, BAR + 0.3), t0, pan=(m % 5 - 2) * 0.2, gain=0.05)
        place(dry, pad(m, BAR + 0.3), t0, pan=(m % 5 - 2) * 0.2, gain=0.045)

    if groove or breakdown:
        # e-piano stabs on 1 and the "and" of 2
        for k, (bt, ln) in enumerate([(0, 0.9), (1.5, 0.4), (3, 0.5)] if groove else [(0, 1.8)]):
            for j, m in enumerate(chord):
                sig = epiano(m, ln, 0.9 if k == 0 else 0.6)
                place(dry, sig, t0 + bt * BEAT + j * 0.008, pan=-0.3 + j * 0.2, gain=0.11)
                place(wet, sig, t0 + bt * BEAT, gain=0.03)
        # bass
        pattern = [(0, 1.4), (1.5, 0.4), (2, 0.9), (3.5, 0.4)] if groove else [(0, 3.8)]
        for bt, ln in pattern:
            place(dry, bass(root + 12 + (12 if bt == 3.5 else 0), ln * BEAT), t0 + bt * BEAT, gain=0.10 if groove else 0.06)

    if groove:
        for q in range(4):
            if q in (0, 2):
                place(dry, kick(), t0 + q * BEAT, gain=0.30)
            if q in (1, 3):
                place(dry, snap(), t0 + q * BEAT, pan=0.1, gain=0.16)
                place(wet, snap(), t0 + q * BEAT, gain=0.05)
        for s in range(16):
            v = 0.20 if s % 2 else 0.10
            place(dry, shaker(v), t0 + s * BEAT / 4 + (0.012 if s % 2 else 0), pan=0.35, gain=1.0)

    # bell motif every two bars from the reveal on (D major pentatonic)
    if b >= 2 and b % 2 == 0 and not breakdown and not last:
        motif = [(0, 81), (1, 78), (1.5, 76), (2.5, 74), (3.5, 76), (5, 78), (6, 81), (6.5, 83)]
        for bt, m in motif:
            sig = bell(m, 0.8)
            place(dry, sig, t0 + bt * BEAT, pan=0.25, gain=0.08)
            place(wet, sig, t0 + bt * BEAT, gain=0.06)
    if b < 2:  # intro: sparse bells
        for bt, m in [(0, 74), (2, 81), (3, 78)]:
            place(wet, bell(m, 0.7), t0 + bt * BEAT, gain=0.07)
            place(dry, bell(m, 0.7), t0 + bt * BEAT, gain=0.03)

# riser into the process scene (end of breakdown)
rise = air(BAR * 1.0)
place(wet, rise, 44.0 - BAR, gain=0.05)
place(dry, rise, 44.0 - BAR, gain=0.04)

# ---- sfx on the grid, in key ----
for c in CUTS[1:]:
    t = c / 30
    if c in WIPES:
        place(dry, air(0.5), t - 0.5, pan=-0.2, gain=0.07)
        place(wet, air(0.5), t - 0.5, gain=0.05)
        place(dry, bell(86, 0.6), t, pan=0.3, gain=0.05)
        place(wet, bell(86, 0.6), t, gain=0.06)
    else:
        place(dry, bell(74, 0.6, 1.2), t, pan=-0.25, gain=0.045)
        place(wet, bell(74, 0.6, 1.2), t, gain=0.05)

# hook word landings (beats 0, 1, 2, 3 roughly match the words)
for bt, m in [(0.5, 74), (1, 78), (2, 81), (2.5, 86)]:
    place(wet, bell(m, 0.5, 1.2), bt * BEAT, gain=0.04)

# workflow nodes light up on beats (630 + 45 + i*30)
for i, m in enumerate([74, 78, 81]):
    t = (630 + 45 + i * 30) / 30
    place(dry, bell(m + 12, 0.6, 1.0), t, pan=-0.3 + 0.3 * i, gain=0.05)
    place(wet, bell(m + 12, 0.6, 1.0), t, gain=0.05)

# calculator counting ticks (frames 1180-1260 = 16ths), climbing the D major scale
scale = [74, 76, 78, 79, 81, 83, 85, 86]
for k in range(int((1260 - 1180) / 7.5) + 1):
    t = (1180 + k * 7.5) / 30
    place(dry, tick(scale[min(k * len(scale) // 11, 7)] + 12), t, pan=0.2, gain=0.035)
place(dry, bell(86, 0.8), 1260 / 30, gain=0.05)
place(wet, bell(86, 0.8), 1260 / 30, gain=0.07)

# Diagnose / Build / Run hits
for i, m in enumerate([62, 66, 69]):
    t = (1335 + i * 15) / 30
    place(dry, kick(), t, gain=0.28)
    place(dry, bell(m + 12, 0.8), t, gain=0.05)
    place(wet, bell(m + 12, 0.8), t, gain=0.07)

# CTA button click (frame 1440 + 90)
place(dry, tick(93), 1530 / 30, gain=0.06)
place(wet, bell(90, 0.5, 1.2), 1530 / 30, gain=0.05)

# ---- reverb (exponential noise IR, convolved by FFT) ----
irn = int(SR * 2.2)
ti = np.arange(irn) / SR
ir = rng.standard_normal((2, irn)) * np.exp(-ti / 0.55)
ir = np.stack([fft_filter(ir[k], hi=6000) for k in range(2)])
L = N + irn
F = 1 << (L - 1).bit_length()
rev = np.stack([np.fft.irfft(np.fft.rfft(wet[k], F) * np.fft.rfft(ir[k], F), F)[:N] for k in range(2)])
rev /= np.max(np.abs(rev)) + 1e-9
mix = dry + rev * 0.35 * np.max(np.abs(dry))

# fade out the last bar's tail, gentle glue
t = np.arange(N) / SR
mix *= np.clip((LENGTH - t) / 1.6, 0, 1) ** 1.5
mix *= np.minimum(1, t / 0.02)
mix = np.tanh(mix / (np.max(np.abs(mix)) * 0.9) * 1.1) * 0.8

out = (np.clip(mix.T, -1, 1) * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print("wrote", sys.argv[1], f"{N / SR:.2f}s")
