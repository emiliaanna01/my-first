"""Noir score and foley for the Capone film -> score.wav.

A slow minor jazz bed (walking upright bass, brushed swing ride, muted piano chords) and crime-file foley placed on
their words: a flashbulb on the mugshot, ledger pages, a gavel on the verdict, a cell door at Alcatraz.
Times come from project/assets/audio/timing.json. Run after `papercut.py make`, then run `make` again.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "papercut", "engine"))
from sfx import SR, _bp, _env, _lp, tap  # noqa: E402

rng = np.random.default_rng(1931)


def tt(d):
    return np.arange(int(d * SR)) / SR


def place(buf, x, t, g=1.0):
    s = max(0, int(t * SR))
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s] * g


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def upright(f, d=.5):
    """Plucked upright bass: round fundamental, thumpy attack, quick decay."""
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .08)
    return np.tanh(1.4 * x) * np.exp(-t / .28) * np.minimum(1, t / .004)


def ride(acc=1.0):
    n = int(.35 * SR)
    return _bp(rng.standard_normal(n), 5000, 12000) * _env(n, .001, .12) * .12 * acc


def brush(d=.25):
    n = int(d * SR)
    return _bp(rng.standard_normal(n), 1500, 7000) * np.sin(np.linspace(0, np.pi, n)) * .05


def piano(notes, d=1.6):
    """Muted piano chord: soft hammer, felt-damped partials."""
    t = tt(d)
    x = sum(np.sin(2 * np.pi * hz(m) * t) + .3 * np.sin(2 * np.pi * 2 * hz(m) * t) * np.exp(-t / .2) for m in notes)
    return _lp(x, 2200) * np.exp(-t / .7) * np.minimum(1, t / .006) * .09


def jazz(total, bpm=78):
    """Am7 - Dm7 - E7 - Am7, walking bass in quarters, swung ride, chords on 2 and 4 (comped)."""
    beat = 60 / bpm
    prog = [("A", [45, 48, 52, 55], [57, 60, 64, 67]), ("D", [50, 53, 57, 60], [62, 65, 69, 72]),
            ("E", [52, 56, 59, 62], [64, 68, 71, 74]), ("A", [45, 47, 48, 52], [57, 60, 64, 67])]
    out = np.zeros(int((total + 2) * SR))
    t, k = 0.0, 0
    while t < total - .3:
        _, walk, chord = prog[k % 4]
        for j in range(4):
            tb = t + j * beat
            place(out, upright(hz(walk[j] - 12)), tb, .55)
            place(out, ride(1.0 if j % 2 else .7), tb, 1)
            place(out, ride(.5), tb + beat * 2 / 3, 1)  # swung skip note
            place(out, brush(), tb, 1)
        place(out, piano(chord[:3]), t + beat, 1)
        place(out, piano(chord[1:]), t + 3 * beat + beat * 2 / 3, .8)
        t += 4 * beat
        k += 1
    fade = np.ones(len(out))
    fs = int((total - 1.5) * SR)
    fade[fs:] = np.linspace(1, 0, len(out) - fs)
    fade[: int(1.2 * SR)] = np.linspace(0, 1, int(1.2 * SR))
    return out * fade


def flashbulb():
    """Magnesium flash: a pop, a fizz, the whine of the charge."""
    t = tt(.6)
    pop = _bp(rng.standard_normal(len(t)), 800, 6000) * np.exp(-t / .02)
    fizz = _bp(rng.standard_normal(len(t)), 3000, 9000) * np.exp(-t / .2) * .3
    whine = np.sin(2 * np.pi * (3200 + 1800 * t) * t) * np.exp(-t / .25) * .05
    return (pop + fizz + whine) * .9


def page():
    n = int(.35 * SR)
    x = _bp(rng.standard_normal(n), 1500, 8000) * np.sin(np.linspace(0, np.pi, n)) ** 2
    return x * (.6 + .4 * np.abs(_lp(rng.standard_normal(n), 30)) * 5) * .25


def gavel():
    return tap(rng, .25, body=300) * 1.7 + tap(rng, .25, body=620) * .6


def cell_door():
    """A heavy steel door: a slam, a long metallic ring, the lock bolt."""
    t = tt(2.4)
    slam = np.sin(2 * np.pi * (70 - 20 * t) * t) * np.exp(-t / .18) * 1.1
    ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dd) for f, a, dd in [(183, .5, .9), (467, .35, .7), (811, .25, .5), (1290, .15, .35)])
    clang = _bp(rng.standard_normal(len(t)), 500, 4000) * np.exp(-t / .05) * .8
    out = slam + ring * .6 + clang
    bolt = tap(rng, .12, body=900) * .8
    place(out, bolt, .55)
    return out * .8


def main():
    d = json.load(open(os.path.join(HERE, "project", "assets", "audio", "timing.json")))
    total, words = d["total"], d["words"]

    def w(beat, word):
        return next(x["s"] for x in words[beat] if x["w"].strip(".,:;?!…'\"").lower() == word)

    fx = np.zeros(int((total + 3) * SR))
    place(fx, flashbulb(), w(0, "gangster") - .1, 1.0)
    for k in range(3):
        place(fx, page(), d["timing"][5]["start"] + k * .3, 1.0)
    place(fx, gavel(), w(6, "guilty"), 1.1)
    place(fx, gavel(), w(6, "guilty") + .22, .8)
    place(fx, cell_door(), w(8, "alcatraz"), 1.0)
    place(fx, flashbulb(), w(10, "taxes") - .05, .8)
    music = jazz(total)
    out = music + fx[: len(music)] * .9
    sf.write(os.path.join(HERE, "score.wav"), out.astype(np.float32), SR, subtype="FLOAT")
    print("score.wav", round(len(out) / SR, 1), "s")


if __name__ == "__main__":
    main()
