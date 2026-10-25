#!/usr/bin/env python3
"""Score + sound design + mix for the 'Forgetting curve' reel.

usage: python3 motion/forget/audio.py <vo_dir> <out_wav>
Then loudness-normalise to -14 LUFS with ffmpeg (see motion/audio/README.md).
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "audio"))
from dsp import (SR, adsr, bp, bp_sweep, convolve, crush, delay_pingpong, glide, hp, ir, lp, mtof, noise, osc, pan,  # noqa: E402
                 pan_move, perc, place, t_, widen)
from sfx import boom, chime, glitch, mech_click, pop, reverse_swell, stutter, tink, whoosh  # noqa: E402

DUR = 19.6
N = int(SR * DUR)
BEAT = 0.5
STOPS = [(9.62, 10.38)]   # music drops out for the "THE FIX?" pattern interrupt

# ---------------- score: bright minimal pop, 120 BPM, F major ----------------
PROG = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 53, 57, 60], [46, 50, 53, 57]]   # Fmaj7 Am7 Dm7 Bbmaj7, 2 s each


def chord_at(t):
    return PROG[int(t // 2) % 4]


def pluck(f, d=0.5, bright=3200, gain=0.25):
    x = osc(f, d, "saw") * 0.5 + osc(f * 1.004, d, "tri") * 0.5
    x = lp(x, bright) * perc(d, 0.002, 0.16)
    return x * gain


def kick(g=1.0):
    d = 0.35
    x = osc(glide(140, 48, d, 0.3), d) * perc(d, 0.001, 0.11)
    return np.tanh(x * 1.6) * g


def snap(g=0.22):
    d = 0.12
    return (hp(noise(d), 1800) * perc(d, 0.0005, 0.02) + bp(noise(d), 900, 2500) * perc(d, 0.0005, 0.04) * 0.6) * g


def shaker(g=0.05):
    d = 0.07
    return hp(noise(d), 6000) * adsr(d, 0.012, 0.03, 0.3, 0.03) * g


def score():
    plucks = np.zeros((N, 2)); drums = np.zeros((N, 2)); bass = np.zeros((N, 2)); pad = np.zeros((N, 2))
    kicks = []
    for i in range(int(DUR / BEAT * 4)):           # 16th grid
        t = i * BEAT / 4
        if t >= 19.0:
            break
        step = i % 16
        ch = chord_at(t)
        intro = t < 2.4
        # chord plucks on a syncopated pattern
        if step in (2, 6, 7, 10, 14) and not intro:
            for k, m in enumerate(ch):
                place(plucks, t + k * 0.008, pan(pluck(mtof(m + 12), 0.45, 2600 if t < 12 else 3600, 0.09), -0.3 + k * 0.2))
        if intro and step in (0, 6, 12):
            place(plucks, t, pan(pluck(mtof(ch[0] + 24), 0.6, 2000, 0.12), 0.2))
        # drums
        if not intro:
            if step % 4 == 0:
                place(drums, t, pan(kick(0.8 if t < 8 else 0.95)))
                kicks.append(t)
            if step in (4, 12):
                place(drums, t, pan(snap(0.2)))
            if step % 2 == 1 and t > 8:
                place(drums, t, pan(shaker(0.045), 0.35))
        # bass on the root, 8ths with octave hop
        if not intro and step % 2 == 0:
            m = ch[0] - 24 + (12 if step % 8 == 6 else 0)
            d = 0.22
            x = lp(osc(mtof(m), d, "saw") * 0.4 + osc(mtof(m), d) * 0.8, 700) * adsr(d, 0.004, 0.08, 0.6, 0.04)
            place(bass, t, pan(np.tanh(x * 1.4) * 0.35))
    # soft pad underneath, and a held chord at the end
    for b in range(10):
        a = b * 2.0
        d = 2.3 if a < 18 else 1.8
        x = sum(osc(mtof(m), d, "saw") + osc(mtof(m) * 1.006, d, "saw") for m in chord_at(a)) / 8
        place(pad, a, widen(lp(x, 1300) * adsr(d, 0.3, 0.6, 0.8, 0.5) * 0.08, 0.013, 0.8))
    end = sum(osc(mtof(m), 2.0) * 0.5 + osc(mtof(m) * 2, 2.0) * 0.12 for m in [53, 60, 64, 69]) * perc(2.0, 0.003, 0.7)
    place(plucks, 18.4, widen(end * 0.12))
    # sidechain on pad/bass/plucks
    g = np.ones(N)
    for tk in kicks:
        a = int(tk * SR); n = min(N - a, int(0.4 * SR))
        g[a:a + n] = np.minimum(g[a:a + n], 1 - 0.45 * np.exp(-np.arange(n) / SR / 0.1))
    m = (plucks + pad + bass) * g[:, None] + drums
    m = m + delay_pingpong(plucks * g[:, None], 0.375, 0.28, 4) * 0.35
    m += convolve(plucks * 0.5 + pad * 0.4 + drums * 0.05, ir(1.4, 2.0, 7000)) * 0.5
    # stops
    sg = np.ones(N); f = int(0.01 * SR)
    for a, b in STOPS:
        ia, ib = int(a * SR), int(b * SR)
        sg[ia:ib] = 0; sg[ia - f:ia] = np.linspace(1, 0, f); sg[ib:ib + f] = np.linspace(0, 1, f)
    m *= sg[:, None]
    k = int(0.8 * SR); fade = np.ones(N); fade[-k:] = np.linspace(1, 0, k) ** 1.4
    return hp(m * fade[:, None], 30)


# ---------------- sound design ----------------
def scribble(d=0.32, g=0.16):
    x = bp(noise(d), 1200, 5000)
    rng = np.random.default_rng(3)
    env = np.repeat(rng.uniform(0.3, 1, int(d * 60) + 1), int(SR / 60))[: len(x)]
    return lp(x * env, 6000) * adsr(d, 0.01, 0.1, 0.8, 0.05) * g


def scratch(d=0.18, g=0.25):
    return bp_sweep(noise(d), 800, 4000, 2.5) * perc(d, 0.003, 0.08) * g


def tick(g=0.14, f=4200):
    return mech_click(f, g)


def boing(f0, f1, d=0.28, g=0.22):
    return osc(glide(f0, f1, d, 0.5), d) * perc(d, 0.002, 0.1) * (1 + 0.3 * np.sin(2 * np.pi * 28 * t_(d))) * g


def thud(g=0.4):
    return boom(0.5, 120, 50, g, 0.2)


def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2))

    def put(t0, x, p=0.0, rev=0.15):
        s = x if x.ndim == 2 else pan(x, p)
        place(dry, t0, s); place(send, t0, s * rev)

    put(0.00, boom(1.0, 70, 34, 0.75, 0.6), rev=0.2)
    put(0.00, whoosh(0.18, 3000, 800, 0.1, 0.25, False))
    put(0.16, pop(400, 900, 0.16))
    put(0.36, whoosh(0.3, 1500, 5000, 0.4, 0.08, False), 0.0)
    put(0.55, pop(520, 1200, 0.2), -0.1)
    put(1.18, scribble(0.32, 0.16), 0.15)
    put(1.54, pop(700, 1500, 0.18), 0.35)
    put(1.62, stutter(glitch(0.1, 0.13, 5), 6, 0.1, 0.8), 0.0, 0.1)
    put(2.28, pan_move(whoosh(0.32, 400, 6000, 0.6, 0.45), 0.7, -0.7), rev=0.15)
    put(2.86, scratch(0.18, 0.26), 0.1)
    put(3.27, pop(380, 760, 0.22))
    put(3.33, boing(300, 700, 0.25, 0.08))
    put(4.02, whoosh(0.26, 200, 5000, 0.95, 0.5), rev=0.2)
    put(4.25, pop(260, 520, 0.22), rev=0.2)
    for i in range(12):
        tt = 4.36 + 0.64 * E_in((i + 1) / 12) - 0.64 / 12
        put(tt, tick(0.1, 4600 - i * 60), 0.0, 0.05)
    for n in range(9):
        put(5.11 + n * 0.045, tink(1568 * 2 ** ((n % 5) / 12), 0.035), -0.5 + n * 0.12, 0.3)
    put(5.88, reverse_swell(0.15, 0.2), rev=0)
    put(6.03, boom(1.4, 80, 32, 0.9, 0.8), rev=0.3)
    for i in range(8):
        put(6.03 + i * 0.045, tick(0.07, 3000 + i * 150), 0.0, 0.0)
    for k in range(6):
        put(7.14 + k * 0.05, whoosh(0.35, 2400, 300, 0.25, 0.09, True), -0.6 + k * 0.24, 0.1)
    put(8.0, whoosh(0.25, 800, 4000, 0.5, 0.18, False), 0.0)
    put(8.25, scribble(0.95, 0.07), 0.0, 0.05)
    put(8.7, whoosh(0.3, 1500, 5000, 0.4, 0.06, False), 0.0)
    put(9.05, pop(600, 1300, 0.14), 0.2)
    put(9.66, boom(0.8, 90, 40, 0.75, 0.9), rev=0.25)
    put(9.66, stutter(glitch(0.08, 0.16, 9), 3, 0.06), 0.0, 0.2)
    put(10.38, whoosh(0.2, 4000, 900, 0.1, 0.25, False), 0.0)
    put(10.45, whoosh(0.6, 500, 1400, 0.6, 0.05, False), 0.4)
    put(11.2, pop(500, 1000, 0.12), 0.2)
    put(11.62, mech_click(2600, 0.32, 1), 0.0, 0.2)
    put(11.64, boing(300, 900, 0.3, 0.14), 0.0, 0.3)
    for k, tt in enumerate([12.31, 12.99, 13.78]):
        put(tt - 0.02, whoosh(0.14, 1200, 4000, 0.7, 0.12, False))
        put(tt, pop(520 * 2 ** (k * 4 / 12), 1100 * 2 ** (k * 4 / 12), 0.2), 0.0, 0.25)
    put(14.62, whoosh(0.4, 3000, 600, 0.2, 0.18, False), rev=0.2)
    put(15.25, boing(420, 120, 0.32, 0.22), 0.0, 0.15)
    put(15.25, thud(0.35), rev=0.1)
    put(15.75, pop(650, 1400, 0.16), 0.3)
    put(16.28, whoosh(0.24, 300, 7000, 0.92, 0.45), rev=0.2)
    put(16.5, pop(300, 700, 0.2))
    put(16.6, whoosh(0.4, 500, 1300, 0.6, 0.05, False), 0.4)
    put(17.0, mech_click(2400, 0.32, 2), 0.0, 0.2)
    put(17.0, pop(600, 1600, 0.22), 0.0, 0.4)
    put(17.02, chime(1760, 1.4, 0.07), 0.0, 0.6)
    put(17.36, pop(450, 900, 0.12), -0.1)
    put(17.58, pop(520, 1040, 0.16), 0.1)
    put(18.4, boom(1.0, 55, 32, 0.4, 0.0), rev=0.3)
    wet = convolve(send, ir(1.2, 1.8, 7000))
    return hp(dry + wet * 0.8, 30)


def E_in(x):
    return x * x


# ---------------- mix ----------------
def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    vo = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR:
            x = signal.resample_poly(x, SR, sr)
        x = hp(x, 90); x = x / (np.abs(x).max() + 1e-9) * 0.8
        place(vo, m["t"], pan(x))
    vo = vo + convolve(vo, ir(0.5, 0.8, 5000)) * 0.25
    lvl = np.abs(vo).max(1); k = int(0.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 5, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    music = score(); sfx = design()
    buses = {"vo": vo, "sfx": sfx * 0.7 * (1 - 0.5 * d), "music": music / (np.abs(music).max() + 1e-9) * 0.36 * (1 - 0.55 * d)}
    mix = sum(buses.values())
    fade = np.ones(N); k = int(0.25 * SR); fade[-k:] = np.linspace(1, 0, k) ** 1.5
    mix = np.tanh(mix * fade[:, None] / (np.abs(mix).max() + 1e-9) * 1.25) * 0.9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    v = signal.sosfilt(sos, buses["vo"].mean(1)); rest = signal.sosfilt(sos, (buses["sfx"] + buses["music"]).mean(1))
    for m in meta:
        a, b = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        r = lambda x: np.sqrt(np.mean(x[a:b] ** 2)) + 1e-9
        print(f"{m['t']:6.2f}s  {m['text']:<58} {20 * np.log10(r(v) / r(rest)):5.1f} dB")
    print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
