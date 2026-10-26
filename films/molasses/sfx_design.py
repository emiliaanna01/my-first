"""Story sound design for The Great Molasses Flood -> score.wav (papercut's bed + designed effects).

story.json points "music" at score.wav, so papercut mixes it under the voice (with its own paper foley on top).
Every effect is synthesised here and placed on the word it belongs to (times from project/assets/audio/timing.json).
Run after `papercut.py make` has made the voice, then run `make` again.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "papercut", "engine"))
from sfx import SR, _bp, _env, _lp, bed, tap  # noqa: E402

rng = np.random.default_rng(1919)


def tt(d):
    return np.arange(int(d * SR)) / SR


def hp(x, f):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)


def place(buf, x, t, g=1.0):
    s = max(0, int(t * SR))
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s] * g


# ---------- sounds ----------
def groan(d=1.1):
    """A steel tank straining: two detuned low tones bending down, with a slow rattle."""
    t = tt(d)
    f = 95 - 30 * (t / d) ** 1.5
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sign(np.sin(ph)) * .4 + np.sin(ph * 1.013) + .5 * np.sin(ph * 2.02)
    x = _lp(x, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t))
    return x * np.minimum(1, t / (d * .8)) ** 2 * .5


def burst():
    """The tank giving way: crack, deep boom, rivets popping, then debris."""
    t = tt(2.4)
    boom = np.sin(2 * np.pi * (48 - 14 * t) * t) * np.exp(-t / .7)
    crack = _bp(rng.standard_normal(len(t)), 300, 4000) * np.exp(-t / .08)
    out = boom * 1.1 + crack * .9
    for k in range(9):  # rivets
        s = int((.05 + k * .045 + rng.random() * .02) * SR)
        n = int(.05 * SR)
        out[s:s + n] += (_bp(rng.standard_normal(n), 1800, 7000) * _env(n, .0003, .01) + np.sin(2 * np.pi * 1400 * tt(.05)) * _env(n, .0005, .015) * .4)[: len(out) - s] * .7
    rub = _lp(rng.standard_normal(len(t)), 500) * np.exp(-t / .9) * .6  # debris rumble
    return out + rub


def wave(d=3.2):
    """A slow, heavy wave: thick low rush with syrupy gloops in it."""
    t = tt(d)
    body = _lp(rng.standard_normal(len(t)), 350) * 2.2 + _bp(rng.standard_normal(len(t)), 300, 1400) * .5
    env = np.minimum(1, t / .5) * np.exp(-np.maximum(0, t - 1.2) / 1.1)
    out = body * env
    for _ in range(14):  # gloops: low pitched blips sliding up
        s = rng.random() * (d - .4)
        n = int(.14 * SR)
        f0 = 70 + rng.random() * 90
        g = np.sin(2 * np.pi * np.cumsum(f0 + 260 * tt(.14)) / SR) * _env(n, .01, .05)
        place(out, g * .45 * np.interp(s, [0, 1.2, d], [.6, 1, .3]), s)
    return out * .8


def crunch(d=.6):
    """Timber and brick giving way."""
    t = tt(d)
    x = np.zeros(len(t))
    for _ in range(40):
        s = int(rng.random() * (d - .05) * SR)
        n = int(.03 * SR)
        x[s:s + n] += _bp(rng.standard_normal(n), 200, 2500) * _env(n, .001, .01) * rng.random()
    return (x + _lp(rng.standard_normal(len(t)), 300) * .5) * np.exp(-t / (d * .6))


def creak(d=.9):
    """Steel bending: a rough, slowly sliding resonance."""
    t = tt(d)
    f = 180 + 120 * np.sin(np.pi * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    grit = (rng.random(len(t)) < 0.08) * 1.0
    x = np.sin(ph) * _lp(grit, 400) * 6 + np.sin(ph * 2.7) * .2
    return _bp(x, 120, 2500) * np.sin(np.pi * t / d) * .7


def clang(d=1.6):
    """A struck girder: inharmonic partials, long ring."""
    t = tt(d)
    parts = [(220, 1), (563, .6), (1012, .4), (1580, .25), (2390, .12)]
    return sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / (d * .35 / (1 + f / 1500))) for f, a in parts) * .35


def toll(d=3.0):
    """A low, sombre hit with a soft bell overtone."""
    t = tt(d)
    sub = np.sin(2 * np.pi * 41 * t) * np.exp(-t / .9)
    bell = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dd) for f, a, dd in [(196, .3, 1.6), (392, .15, 1.1), (494, .08, .9)])
    return sub * .9 + bell * .6


def rustle(d=.55):
    """Newsprint: crisp crinkle bursts."""
    t = tt(d)
    x = np.zeros(len(t))
    for _ in range(60):
        s = int(rng.random() * (d - .03) * SR)
        n = int(.012 * SR)
        x[s:s + n] += hp(rng.standard_normal(n), 2500) * rng.random()
    return x * np.sin(np.pi * t / d) * .5


def snap_paper():
    n = int(.12 * SR)
    return hp(rng.standard_normal(n), 1500) * _env(n, .001, .03) * 1.2


def scrub(n_strokes=6, every=.36):
    """Stiff brooms on cobblestones."""
    out = np.zeros(int((n_strokes * every + .4) * SR))
    for k in range(n_strokes):
        d = .26
        t = tt(d)
        x = _bp(rng.standard_normal(len(t)), 2500, 9000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 40 * t)))
        place(out, x * np.sin(np.pi * t / d) ** 1.5 * .45, k * every + rng.normal(0, .02))
    return out


def lapping(d=2.4):
    """Harbour water against stone."""
    t = tt(d)
    x = _lp(rng.standard_normal(len(t)), 700) * (0.4 + 0.6 * np.abs(np.sin(np.pi * t / .8)) ** 3)
    x += _bp(rng.standard_normal(len(t)), 900, 3000) * .15 * np.abs(np.sin(np.pi * t / .8)) ** 6
    return x * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .6) * .9


def gavel():
    """A wooden knock: hard click plus a short hollow body."""
    return tap(rng, .2, body=310) * 1.6 + tap(rng, .2, body=620) * .6


def coins(n=7):
    out = np.zeros(int(.9 * SR))
    for k in range(n):
        d = .3
        t = tt(d)
        f = 3200 + rng.random() * 1800
        x = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 1.47 * t)) * np.exp(-t / .06)
        place(out, x * .25, k * .09 + rng.random() * .04)
    return out


def shimmer(d=2.2):
    """Something sweet in the air: soft rising chimes."""
    out = np.zeros(int(d * SR))
    for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        t = tt(d - k * .18)
        place(out, np.sin(2 * np.pi * f * t) * np.exp(-t / .9) * np.minimum(1, t / .02) * .12, k * .18)
    return out


def main():
    d = json.load(open(os.path.join(HERE, "project", "assets", "audio", "timing.json")))
    total, words = d["total"], d["words"]

    def w(beat, word):
        return next(x["s"] for x in words[beat] if x["w"].strip(".,:;").lower() == word)

    fx = np.zeros(int((total + 3) * SR))
    place(fx, groan(1.1), w(1, "street") - .4, .9)            # the tank strains...
    place(fx, burst(), w(1, "bursts"), 1.0)                     # ...and gives way
    place(fx, wave(3.4), w(3, "wave") - .25, 1.0)               # the wave
    place(fx, crunch(.6), w(4, "crushes"), .9)
    place(fx, creak(.9), w(4, "twists"), 1.0)
    place(fx, clang(1.6), w(4, "steel"), .8)
    place(fx, toll(3.0), w(5, "twenty-one") - .05, .9)          # the dead
    place(fx, rustle(.55), d["timing"][6]["start"] - .05, .9)   # newspaper
    place(fx, snap_paper(), w(6, "front-page"), .8)
    place(fx, scrub(6, .36), w(7, "workers"), 1.0)
    place(fx, lapping(2.2), d["timing"][8]["start"] - .1, 1.0)  # the harbour
    place(fx, gavel(), w(9, "court"), 1.0)
    place(fx, gavel(), w(9, "court") + .2, .8)
    place(fx, coins(7), w(10, "thousand"), 1.0)
    place(fx, shimmer(2.2), w(11, "sweet") - .1, 1.0)
    # the score is papercut's bed with the effects on top; papercut scales it by music_gain (0.22)
    score = bed(total, bpm=72)[: len(fx)]
    # not normalised: the bed keeps exactly the level papercut gives it, the effects sit just under the voice
    out = score + fx[: len(score)] * .8
    sf.write(os.path.join(HERE, "score.wav"), out.astype(np.float32), SR, subtype="FLOAT")
    print("score.wav", round(len(out) / SR, 1), "s, bed peak", round(float(np.max(np.abs(score))), 3), "fx peak", round(float(np.max(np.abs(fx * .8))), 3))


if __name__ == "__main__":
    main()
