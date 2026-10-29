"""Score and camera foley for The One-Dollar Camera -> score.wav.

A music-box waltz (3/4) instead of papercut's tense bed, plus shutter clicks and film-winding ratchets placed on their
words (times from project/assets/audio/timing.json). story.json points "music" at score.wav.
Run after `papercut.py make` has made the voice, then run `make` again.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "papercut", "engine"))
from sfx import SR, _bp, _env  # noqa: E402

rng = np.random.default_rng(1900)


def tt(d):
    return np.arange(int(d * SR)) / SR


def place(buf, x, t, g=1.0):
    s = max(0, int(t * SR))
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s] * g


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def tine(f, d=1.4):
    """A music-box tine: bright attack, inharmonic shimmer, long soft decay."""
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / .15) + .2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / .05)
    return x * np.exp(-t / .55) * np.minimum(1, t / .002)


def waltz(total, bpm=96):
    """C major music box: I - vi - IV - V, melody on beat one, chord tines on two and three."""
    beat = 60 / bpm
    bar = 3 * beat
    prog = [(60, [64, 67, 72]), (57, [64, 69, 72]), (53, [65, 69, 72]), (55, [62, 67, 71])]
    melody = [76, 74, 72, 74, 76, 76, 77, 74, 72, 71, 72, 79]
    out = np.zeros(int((total + 2) * SR))
    k = 0
    t = 0.0
    while t < total - .5:
        root, ch = prog[k % 4]
        place(out, tine(hz(root + 12), 1.2), t, .35)
        place(out, tine(hz(melody[k % len(melody)] + 12), 1.6), t, .5)
        for j in (1, 2):
            for n in ch[:2]:
                place(out, tine(hz(n + 12), .8), t + j * beat, .18)
        t += bar
        k += 1
    n = len(out)
    fade = np.ones(n)
    fs = int((total - 1.5) * SR)
    fade[fs:] = np.linspace(1, 0, n - fs)
    fade[: int(SR)] = np.linspace(0, 1, int(SR))
    return out * fade * .5


def shutter():
    """A box-camera shutter: a sprung lever clack, the blade, a small spring ring."""
    out = np.zeros(int(.35 * SR))
    for dt, g, lo, hi in ((0, 1.0, 1500, 7000), (.045, .7, 2500, 9000)):
        n = int(.04 * SR)
        place(out, _bp(rng.standard_normal(n), lo, hi) * _env(n, .0003, .006) * g, dt)
    t = tt(.3)
    place(out, np.sin(2 * np.pi * 2350 * t) * np.exp(-t / .05) * .12, .045)
    return out


def wind(n=9, rate=22):
    """The film-advance ratchet."""
    out = np.zeros(int((n / rate + .2) * SR))
    for k in range(n):
        m = int(.02 * SR)
        place(out, _bp(rng.standard_normal(m), 2000, 6000) * _env(m, .0002, .004) * (.5 + .3 * rng.random()), k / rate + rng.normal(0, .004))
    return out


def ding():
    t = tt(1.2)
    return (np.sin(2 * np.pi * 2093 * t) + .4 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t / .4) * .25


def main():
    d = json.load(open(os.path.join(HERE, "project", "assets", "audio", "timing.json")))
    total, words = d["total"], d["words"]

    def w(beat, word):
        return next(x["s"] for x in words[beat] if x["w"].strip(".,:;?").lower() == word)

    fx = np.zeros(int((total + 3) * SR))
    for beat, word in [(0, "mirror"), (1, "brownie"), (8, "snapshot"), (10, "box")]:
        place(fx, shutter(), w(beat, word), 1.0)
        place(fx, wind(), w(beat, word) + .45, .8)
    place(fx, ding(), w(4, "one"), 1.0)
    music = waltz(total)
    out = music + fx[: len(music)] * .9
    sf.write(os.path.join(HERE, "score.wav"), out.astype(np.float32), SR, subtype="FLOAT")
    print("score.wav", round(len(out) / SR, 1), "s")


if __name__ == "__main__":
    main()
