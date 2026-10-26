"""Score, foley and voice for the RoundHouse reel -> out/project/assets/audio/mix.wav (-14 LUFS).

Music is synthesised here (104 BPM): curious and sparse until the RoundHouse reveal, then fuller and resolved.
Foley reuses papercut's paper sounds plus a few UI ones (notification ping, click, key, whoosh, rip).
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".claude", "skills", "papercut", "engine"))
import sfx as P  # noqa: E402
from sfx import SR, _bp, _env, _lp  # noqa: E402

OUT = os.path.join(HERE, "out")
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def place(buf, x, t, g=1.0):
    s = int(round(t * SR))
    if s < 0:
        x, s = x[-s:], 0
    e = min(len(buf), s + len(x))
    if e > s:
        buf[s:e] += x[: e - s] * g


# ---------- instruments ----------
def pluck(f, dur=.45, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * t) * np.exp(-t / (dur * .38))
    over = np.sin(2 * np.pi * f * 4.0 * t) * np.exp(-t / .03) * .35 * bright
    third = np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / (dur * .15)) * .25 * bright
    return (body + over + third) * np.minimum(1, t / .003)


def kick(rng):
    n = int(.32 * SR)
    t = np.arange(n) / SR
    f = 45 + 75 * np.exp(-t / .04)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / .11) * 1.0 + _bp(rng.standard_normal(n), 1500, 5000) * _env(n, .0005, .004) * .2


def snap(rng):
    n = int(.18 * SR)
    x = np.zeros(n)
    for k, d in enumerate((0, .009, .019)):
        s = int(d * SR)
        m = n - s
        x[s:] += _bp(rng.standard_normal(m), 1200, 6000) * _env(m, .0005, .02 if k < 2 else .07)
    return x * .6


def shaker(rng, acc=1.0):
    n = int(.05 * SR)
    return _bp(rng.standard_normal(n), 6000, 14000) * _env(n, .004, .02) * .25 * acc


def rim(rng):
    n = int(.06 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1700 * t) * .5 + _bp(rng.standard_normal(n), 2000, 7000)) * _env(n, .0005, .012) * .35


def bass(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 2 * f * t)
    env = np.minimum(1, t / .015) * np.minimum(1, (dur - t) / .08) * (0.75 + .25 * np.exp(-t / .3))
    return np.tanh(x * 1.3) * env * .5


def pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + i) + .3 * np.sin(2 * np.pi * f * 1.004 * t) for i, f in enumerate(freqs))
    env = np.minimum(1, t / .5) * np.minimum(1, (dur - t) / .5)
    return _lp(x * env, 1800) * .06


def music(total, drop, gap_start):
    rng = np.random.default_rng(4)
    out = np.zeros(int((total + 1) * SR))
    t0 = drop - round(drop / BAR) * BAR  # the reveal lands on a downbeat
    gap = (gap_start, drop)  # the black "gap" frame: the music stops
    # part A: D minor, curious. i - VI - III - VII
    prog_a = [(50, [62, 65, 69, 72]), (46, [58, 62, 65, 69]), (53, [60, 65, 69, 72]), (48, [60, 64, 67, 72])]
    # part B: D major, settled. I - V - vi - IV
    prog_b = [(50, [62, 66, 69, 74]), (45, [61, 64, 69, 73]), (47, [62, 66, 71, 74]), (43, [62, 67, 71, 74])]
    bar_i = 0
    t = t0
    while t < total:
        b_part = t >= drop - 1e-6
        root, ch = (prog_b if b_part else prog_a)[bar_i % 4]
        in_gap = gap[0] - .05 <= t < gap[1] - .05
        if not in_gap:
            # plucked ostinato in eighths (A: sparse pattern, B: fuller and up an octave on the top)
            pat = [0, 2, 1, 3, 2, 1, 3, 2] if b_part else [0, None, 2, 1, None, 3, 2, None]
            for k, p in enumerate(pat):
                tt = t + k * BEAT / 2
                if p is None or gap[0] <= tt < gap[1] or tt >= total - .3:
                    continue
                note = ch[p] + (12 if b_part and k % 4 == 3 else 0)
                place(out, pluck(hz(note), .5, 1.0 if b_part else .7), tt, .16 if b_part else .14)
            for k in range(2 if not b_part else 4):  # bass
                tt = t + k * (BAR / (2 if not b_part else 4))
                if tt < gap[0] or tt >= gap[1]:
                    place(out, bass(hz(root - 12), BAR / (2 if not b_part else 4) * .9), tt, .55 if b_part else .4)
            # percussion
            for k in range(16):
                tt = t + k * BEAT / 4
                if gap[0] <= tt < gap[1] or tt >= total - .2:
                    continue
                if b_part or k % 2 == 0:
                    place(out, shaker(rng, 1.0 if k % 4 == 2 else .55), tt, .9 if b_part else .6)
                if not b_part and k in (4, 12):
                    place(out, rim(rng), tt, .9)
                if not b_part and k in (0, 8):
                    place(out, kick(rng), tt, .32)
                if b_part and k in (0, 8, 10):
                    place(out, kick(rng), tt, .5 if k != 10 else .3)
                if b_part and k in (4, 12):
                    place(out, snap(rng), tt, .42)
            if b_part:
                place(out, pad([hz(n) for n in ch[:3]], BAR + .4), t, 1.0)
        t += BAR
        bar_i += 1
    # riser into the reveal, and a soft sub hit on it
    n = int((gap[1] - gap[0]) * SR)
    rs = _bp(rng.standard_normal(n), 800, 6000) * np.linspace(0, 1, n) ** 2.5 * .18
    place(out, rs, gap[0])
    nn = int(1.2 * SR)
    tt = np.arange(nn) / SR
    place(out, np.sin(2 * np.pi * 42 * tt) * np.exp(-tt / .4) * .6, drop)
    # final chord rings out under the end card
    end = [62, 66, 69, 74]
    for k, m in enumerate(end):
        place(out, pluck(hz(m), 1.6), total - 1.6 + k * .04, .18)
    fade = np.ones(len(out))
    fs = int((total - 1.2) * SR)
    fade[fs:] = np.linspace(1, 0, len(out) - fs)
    return out * fade


# ---------- foley ----------
def ping(rng):
    n = int(.35 * SR)
    t = np.arange(n) / SR
    a = np.sin(2 * np.pi * 1318.5 * t) * _env(n, .002, .08)
    b = np.zeros(n)
    s = int(.07 * SR)
    b[s:] = np.sin(2 * np.pi * 1760 * t[: n - s]) * _env(n - s, .002, .12)
    return (a + b) * .22


def click(rng):
    n = int(.04 * SR)
    return _bp(rng.standard_normal(n), 2500, 9000) * _env(n, .0003, .006) * .7


def key(rng):
    return P.tap(rng, .07, body=900 + rng.random() * 300) * .6


def whoosh(rng, dur=.35):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return _bp(x, 400, 4000) * e * .35


def rip(rng):
    a = P.tape_rip(rng, .45)
    b = P.paper_slide(rng, .3)
    out = np.zeros(max(len(a), len(b)))
    out[: len(a)] += a * 1.3
    out[: len(b)] += b * .6
    return out


def hit(rng):
    n = int(.25 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (80 - 25 * t) * t) * _env(n, .002, .07) * .6 + _bp(rng.standard_normal(n), 300, 2500) * _env(n, .001, .02) * .3


def foley(events, total):
    rng = np.random.default_rng(9)
    out = np.zeros(int((total + 1) * SR))
    make = {"slide": lambda: P.paper_slide(rng), "drop": lambda: P.tap(rng), "tape": lambda: P.tape_rip(rng),
            "draw": lambda: P.marker(rng, .45), "ping": lambda: ping(rng), "click": lambda: click(rng), "key": lambda: key(rng),
            "whoosh": lambda: whoosh(rng), "rip": lambda: rip(rng), "hit": lambda: hit(rng)}
    level = {"slide": .55, "drop": .5, "tape": .6, "draw": .9, "ping": .8, "click": .8, "key": .7, "whoosh": .6, "rip": .9, "hit": .9}
    last = {}
    for ev in events:
        k = ev["k"]
        if ev["t"] - last.get(k, -9) < .09:  # never stack the same sound: keep it sparse
            continue
        last[k] = ev["t"]
        place(out, make[k](), ev["t"], level[k] * ev.get("g", 1.0))
    return out


def punch_voice(x):
    """Mature narration: a warm, even broadcast voice rather than a hyped one."""
    tmp_in, tmp_out = os.path.join(OUT, "vo_dry.wav"), os.path.join(OUT, "vo_punch.wav")
    sf.write(tmp_in, x.astype(np.float32), SR)
    # broadcast narration (female): warm body, cleared mud, gentle presence, light compression, de-essed, a hint of room
    chain = ("highpass=f=90,equalizer=f=210:t=q:w=1:g=2,equalizer=f=420:t=q:w=1.2:g=-2,equalizer=f=3800:t=q:w=1.4:g=1.5,"
             "equalizer=f=11000:t=h:w=5000:g=1.5,deesser=i=0.5,acompressor=threshold=-22dB:ratio=3:attack=8:release=140:makeup=4:knee=4,"
             "aecho=1.0:0.5:23|37:0.07|0.05,alimiter=limit=0.95:level=0")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp_in, "-af", chain, tmp_out], check=True)
    y, _ = sf.read(tmp_out, dtype="float32")
    y = y[: len(x)]
    return y / (np.max(np.abs(y)) or 1) * np.max(np.abs(x)) * 1.0


def main():
    cues = json.load(open(os.path.join(OUT, "cues.json")))
    total = cues["total"]
    n = int(total * SR)
    vo = np.zeros(n + SR)
    for i, t in enumerate(cues["vo_at"]):
        x, sr = sf.read(os.path.join(OUT, "vo", f"line{i}.wav"), dtype="float32")
        place(vo, resample_poly(x, SR, sr), t)
    vo = punch_voice(vo)
    mus = music(total, cues["drop"], cues["gap"])[: len(vo)]
    fx = foley(cues["sfx"], total)[: len(vo)]
    # duck the music under the voice
    env = _lp(np.abs(vo), 6)
    env = env / (env.max() or 1)
    duck = 1 - .5 * np.clip(env * 4, 0, 1)
    mix = vo * 1.0 + mus * duck * .5 + fx * .3
    mix = mix[:n]
    ad = os.path.join(OUT, "project", "assets", "audio")
    os.makedirs(ad, exist_ok=True)
    raw = os.path.join(OUT, "mix_raw.wav")
    sf.write(raw, mix / (np.max(np.abs(mix)) or 1) * .7, SR)
    sf.write(os.path.join(OUT, "music_only.wav"), mus[:n] / (np.max(np.abs(mus)) or 1) * .7, SR)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=0",
                    "-ar", "48000", os.path.join(ad, "mix.wav")], check=True)
    print("mix", os.path.join(ad, "mix.wav"))


if __name__ == "__main__":
    main()
