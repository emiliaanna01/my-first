#!/usr/bin/env python3
"""Synthesize the reel's sound design and mix it with the voice-over.

usage: python3 motion/audio/sfx.py <vo_dir> <out_wav>

Every effect is generated here (no samples), placed on the film's cue points.
Output: 48 kHz stereo WAV, 20 s, pre-loudness-normalisation.
"""
import json
import sys

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(SR * d)) / SR


def env(d, a=0.002, decay=0.3, curve=1.0):
    t = t_(d)
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / decay) ** curve
    return e


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def sweep_tone(f0, f1, d, shape=1.0):
    t = t_(d)
    k = (t / d) ** shape
    f = f0 * (f1 / f0) ** k
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def noise(d):
    return rng.standard_normal(int(SR * d))


def sweep_filter_noise(d, f0, f1, q=3.0, steps=64):
    """Band-passed noise whose centre frequency glides f0 -> f1 (block-wise)."""
    x = noise(d)
    out = np.zeros_like(x)
    n = len(x)
    blk = n // steps
    for i in range(steps):
        a, b = i * blk, n if i == steps - 1 else (i + 1) * blk
        fc = f0 * (f1 / f0) ** (i / (steps - 1))
        lo, hi = max(30, fc / (1 + 1 / q)), min(SR / 2 - 100, fc * (1 + 1 / q))
        seg = bp(x[max(0, a - 2000):b], lo, hi)[-(b - a):]
        out[a:b] = seg
    return out / (np.abs(out).max() + 1e-9)


def ir(decay=1.2, d=2.0, bright=6000):
    t = t_(d)
    l = lp(noise(d), bright) * np.exp(-t / (decay / 6.9))
    r = lp(noise(d), bright) * np.exp(-t / (decay / 6.9))
    return np.stack([l, r], 1) / 40


def stereo(x, pan=0.0):
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l, x * r], 1)


def auto_pan(x, p0, p1):
    p = np.linspace(p0, p1, len(x))
    return np.stack([x * np.cos((p + 1) * np.pi / 4), x * np.sin((p + 1) * np.pi / 4)], 1)


# ---------------- instruments ----------------
def sub_hit(d=1.2, f0=62, f1=34, gain=1.0, click=0.5):
    body = sweep_tone(f0, f1, d, 0.35) * env(d, 0.003, d / 3.5)
    tr = hp(noise(0.02), 2500) * env(0.02, 0.0005, 0.004) * click
    out = body.copy()
    out[: len(tr)] += tr
    return np.tanh(out * 1.6) * gain


def impact(d=2.4, gain=1.0):
    sub = sweep_tone(70, 30, d, 0.3) * env(d, 0.002, 0.55)
    mid = np.tanh(lp(noise(d), 900) * 3) * env(d, 0.001, 0.09) * 0.6
    crack = hp(noise(d), 3000) * env(d, 0.0005, 0.03) * 0.5
    return np.tanh((sub * 1.4 + mid + crack) * 1.3) * gain


def whoosh(d=0.6, f0=300, f1=4000, rise=0.7, gain=0.6):
    x = sweep_filter_noise(d, f0, f1, q=2.2)
    t = t_(d) / d
    e = np.where(t < rise, (t / rise) ** 2, ((1 - t) / (1 - rise)) ** 1.5)
    return x * e * gain


def click(f=3200, d=0.035, gain=0.35):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) * 0.6 + hp(noise(d), 4000) * 0.4) * np.exp(-t / 0.006) * gain


def type_click(seed, gain=0.14):
    f = 2400 + 900 * ((seed * 0.618) % 1)
    return click(f, 0.03, gain)


def power_down(d=0.9, gain=0.5):
    tone = sweep_tone(520, 38, d, 0.6) * np.exp(-t_(d) / 0.45)
    buzz = signal.sawtooth(2 * np.pi * np.cumsum(np.linspace(110, 30, int(SR * d))) / SR) * np.exp(-t_(d) / 0.25) * 0.25
    return lp(tone + buzz, 2500) * gain


def riser(d=1.8, f0=200, f1=2400, gain=0.4):
    t = t_(d) / d
    tone = sweep_tone(f0, f1, d, 1.6) * 0.25 + sweep_tone(f0 * 1.5, f1 * 1.5, d, 1.6) * 0.12
    air = sweep_filter_noise(d, 400, 9000, q=1.5) * 0.7
    return (tone + air) * (t ** 2.2) * gain


def shimmer(d=0.9, gain=0.22):
    t = t_(d)
    parts = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([2093, 2637, 3136, 4186, 5274]))
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 18 * t)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return (parts / 5 * trem + sweep_filter_noise(d, 3000, 11000, 2.5) * 0.5) * e * gain


def zap(d=0.25, gain=0.35):
    return sweep_tone(1800, 120, d, 0.5) * np.exp(-t_(d) / 0.07) * gain


def blip(f0=660, f1=1320, d=0.18, gain=0.3):
    return sweep_tone(f0, f1, d, 0.4) * env(d, 0.002, 0.05) * gain


def bell(f=880, d=2.2, gain=0.22):
    t = t_(d)
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / (d * k)) for m, a, k in [(1, 1, .35), (2.01, .5, .2), (3.02, .25, .12), (4.2, .15, .08)])
    return x * gain


def swell(d=0.8, f=110, gain=0.25):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * m * t) / m for m in (1, 2, 3, 4))
    return lp(x, 1800) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * gain


# ---------------- arrangement ----------------
dry = np.zeros((N, 2))
wet_send = np.zeros((N, 2))


def put(t0, x, pan=0.0, send=0.25, st=None):
    s = st if st is not None else stereo(x, pan)
    a = int(t0 * SR)
    if a >= N:
        return
    b = min(N, a + len(s))
    dry[a:b] += s[: b - a]
    wet_send[a:b] += s[: b - a] * send


# beat 1 — hook
put(0.00, sub_hit(1.4, 60, 32, 0.9), send=0.2)
put(0.00, click(4200, 0.04, 0.3), pan=0.25, send=0.4)
for i in range(9):  # "One fault" types at 0.10 + i*0.046
    put(0.10 + i * 0.046, type_click(i), pan=-0.3 + i * 0.07, send=0.15)
for i, k in enumerate([0.55, 0.62, 0.70, 0.80, 0.86]):  # LED stutter
    put(k, click(5200 - i * 300, 0.02, 0.12), pan=0.25, send=0.3)
put(0.95, power_down(1.0, 0.32), send=0.3)
put(0.95, sub_hit(0.9, 48, 28, 0.45, 0), send=0.1)
put(2.02, riser(0.2, 300, 3000, 0.5), send=0.3)
put(2.20, whoosh(0.55, 200, 6000, 0.25, 0.7), st=auto_pan(whoosh(0.55, 200, 6000, 0.25, 0.7), 0.4, -0.6), send=0.35)
put(2.22, sub_hit(1.0, 70, 36, 0.6, 0.3), send=0.25)

# beat 2 — problem (word impacts)
for k, tk in enumerate([2.5, 3.6, 4.7]):
    put(tk - 0.11, whoosh(0.12, 1200, 5000, 0.8, 0.25), pan=0, send=0.2)
    put(tk, sub_hit(0.7, 80 - k * 6, 40, 0.65, 0.6), send=0.3)
    put(tk, click(1800 + k * 400, 0.05, 0.22), send=0.4)
put(5.48, whoosh(0.4, 400, 7000, 0.92, 0.5), send=0.3)
put(5.86, zap(0.3, 0.35), send=0.5)
put(5.86, sub_hit(0.6, 90, 45, 0.35, 0.8), send=0.3)

# beat 3 — solution
put(6.00, whoosh(0.7, 3000, 250, 0.12, 0.4), st=auto_pan(whoosh(0.7, 3000, 250, 0.12, 0.4), 0, 0) * np.array([1.0, 1.0]), send=0.4)
put(6.00, sub_hit(0.8, 55, 30, 0.4, 0), send=0.1)
for i, tk in enumerate([5.98, 6.04, 6.10, 6.18, 6.30, 6.36]):  # tiles arriving
    put(tk, whoosh(0.35, 800, 2600, 0.55, 0.07), pan=[-0.6, 0.6, -0.5, 0.5, -0.8, 0.8][i], send=0.25)
put(6.12, blip(500, 760, 0.12, 0.12), send=0.4)
put(6.36, blip(620, 930, 0.12, 0.12), send=0.4)
put(6.90, click(2600, 0.03, 0.15), pan=0.5, send=0.3)       # AUTO toggle tile
put(7.30, shimmer(0.9, 0.2), st=auto_pan(shimmer(0.9, 0.2), -0.7, 0.7), send=0.5)
put(8.15, bell(1046, 1.6, 0.16), send=0.6)
put(8.15, riser(1.85, 160, 2600, 0.42), send=0.35)
put(9.05, whoosh(0.55, 600, 3000, 0.6, 0.3), st=auto_pan(whoosh(0.55, 600, 3000, 0.6, 0.3), 0.6, -0.2), send=0.3)
put(9.60, click(3600, 0.05, 0.35), send=0.5)
put(9.62, swell(0.38, 55, 0.3), send=0.2)

# beat 4 — main impact
put(10.00, impact(2.6, 1.0), send=0.45)
put(10.00, bell(523, 2.4, 0.12), send=0.7)
put(10.35, whoosh(0.5, 2000, 6000, 0.3, 0.15), st=auto_pan(whoosh(0.5, 2000, 6000, 0.3, 0.15), -0.6, 0.6), send=0.3)
put(11.15, shimmer(0.7, 0.16), st=auto_pan(shimmer(0.7, 0.16), -0.6, 0.6), send=0.5)
put(13.00, whoosh(0.5, 150, 5000, 0.96, 0.75), send=0.25)

# beat 5 — benefit
put(13.50, sub_hit(1.0, 58, 32, 0.6, 0.4), send=0.3)
put(13.50, whoosh(0.4, 3000, 600, 0.1, 0.2), send=0.3)
put(14.60, click(2200, 0.03, 0.28), pan=0.15, send=0.25)
put(14.63, blip(880, 1320, 0.1, 0.12), pan=0.15, send=0.3)
put(15.35, shimmer(0.75, 0.18), st=auto_pan(shimmer(0.75, 0.18), -0.5, 0.5), send=0.5)
put(16.50, whoosh(0.5, 200, 7000, 0.95, 0.7), send=0.3)

# beat 6 — end frame
put(17.00, swell(0.8, 82, 0.28), send=0.5)
put(17.00, sub_hit(1.4, 52, 30, 0.45, 0.2), send=0.3)
put(17.50, blip(700, 1400, 0.16, 0.22), send=0.5)
put(18.30, shimmer(0.7, 0.07), st=auto_pan(shimmer(0.7, 0.07), -0.6, 0.6), send=0.4)
put(18.42, blip(520, 1040, 0.14, 0.1), send=0.3)
for i in range(15):  # handle typed at 18.7 + i*0.03
    put(18.70 + i * 0.03, type_click(i + 20, 0.04), pan=-0.3 + i * 0.04, send=0.15)
put(19.00, sub_hit(1.0, 46, 28, 0.6, 0), send=0.2)
put(19.00, bell(880, 2.4, 0.08), send=0.8)

# reverb bus
rev = np.stack([signal.fftconvolve(wet_send[:, c], ir(1.6, 2.4)[:, c])[:N] for c in range(2)], 1)
sfx = dry + rev * 0.9
sfx = hp(sfx.T, 25).T

# ---------------- voice-over ----------------
vo = np.zeros((N, 2))
meta = json.load(open(f"{sys.argv[1]}/vo.json"))
for m in meta:
    x, sr = sf.read(m["file"])
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr)
    x = hp(x, 90)
    a = int(m["t"] * SR)
    b = min(N, a + len(x))
    vo[a:b] += stereo(x[: b - a] / (np.abs(x).max() + 1e-9) * 0.8, 0)
vo_rev = np.stack([signal.fftconvolve(vo[:, c], ir(0.6, 1.0, 5000)[:, c])[:N] for c in range(2)], 1)
vo_bus = vo + vo_rev * 0.18

# sidechain duck SFX under the voice (-6 dB)
lvl = np.abs(vo).max(1)
k = int(0.03 * SR)
envv = np.convolve(lvl, np.ones(k) / k, "same")
envv = signal.sosfilt(signal.butter(1, 6, "lowpass", fs=SR, output="sos"), envv)
duck = 1 - 0.68 * np.clip(envv / (envv.max() + 1e-9) * 3, 0, 1)
mix = sfx * duck[:, None] * 0.75 + vo_bus * 1.0

# fade tail, soft clip
fade = np.ones(N)
fade[-int(0.35 * SR):] = np.linspace(1, 0, int(0.35 * SR)) ** 1.5
mix *= fade[:, None]
mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.2) * 0.9
sf.write(sys.argv[2], mix.astype(np.float32), SR, subtype="FLOAT")
print("wrote", sys.argv[2])
