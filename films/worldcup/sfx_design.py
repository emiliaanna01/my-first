"""Stadium sound design for the 2026 World Cup final film -> score.wav (papercut's bed + crowd, whistles, drums).

story.json points "music" at score.wav. Every sound is synthesised and placed on its word, using the voice
timings in project/assets/audio/timing.json. Run after `papercut.py make`, then run `make` again.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "papercut", "engine"))
from sfx import SR, _bp, _env, _lp, bed  # noqa: E402

rng = np.random.default_rng(2026)


def tt(d):
    return np.arange(int(d * SR)) / SR


def place(buf, x, t, g=1.0):
    s = max(0, int(t * SR))
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s] * g


def crowd(d, energy=0.5):
    """A stadium crowd: thousands of voices as band-limited noise with a slow, uneven swell."""
    t = tt(d)
    swell = 0.6 + 0.4 * _lp(rng.standard_normal(len(t)), 1.5) * 8
    voices = _bp(rng.standard_normal(len(t)), 250, 2500) * (0.5 + 0.5 * np.clip(swell, 0, 2))
    air = _bp(rng.standard_normal(len(t)), 2500, 7000) * .25 * energy
    return (voices * (0.5 + energy) + air) * .35


def roar(d=3.0):
    """A goal: the crowd erupts, peaks, then settles."""
    t = tt(d)
    env = np.minimum(1, t / .35) ** 1.5 * np.exp(-np.maximum(0, t - .8) / 1.4)
    return crowd(d, 1.0) * env * 3.2


def applause(d=2.5, density=900):
    out = np.zeros(int(d * SR))
    for _ in range(int(density * d)):
        n = int(.012 * SR)
        place(out, _bp(rng.standard_normal(n), 900, 6000) * _env(n, .0005, .004) * rng.random() * .5, rng.random() * (d - .02))
    t = tt(d)
    return out * np.minimum(1, t / .3) * np.minimum(1, (d - t) / .8)


def clap_rhythm(d=2.6, bpm=120):
    """Fans clapping in time, urging the team on."""
    out = np.zeros(int(d * SR))
    beat = 60 / bpm
    for k in range(int(d / beat)):
        place(out, applause(.12, 2500) * 2.2, k * beat)
    return out


def whistle(d=.35):
    """A referee's pea whistle: a high tone with a fast trill and some breath."""
    t = tt(d)
    f = 3050 + 160 * np.sign(np.sin(2 * np.pi * 26 * t)) * (0.6 + 0.4 * rng.random())
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + .3 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    breath = _bp(rng.standard_normal(len(t)), 2500, 6000) * .25
    env = np.minimum(1, t / .015) * np.minimum(1, (d - t) / .04)
    return (tone + breath) * env * .25


def whistles(pattern):
    """A sequence like [(.2, .1), (.2, .1), (.8, 0)]: (blast length, gap after)."""
    out = np.zeros(int((sum(a + b for a, b in pattern) + .1) * SR))
    t = 0.0
    for a, b in pattern:
        place(out, whistle(a), t)
        t += a + b
    return out


def drum(d=.6):
    """A stadium bass drum (bombo)."""
    t = tt(d)
    body = np.sin(2 * np.pi * (70 - 25 * t) * t) * np.exp(-t / .18)
    skin = _bp(rng.standard_normal(len(t)), 150, 1200) * np.exp(-t / .03)
    return body * 1.1 + skin * .5


def kick():
    """Boot on ball."""
    t = tt(.25)
    return np.sin(2 * np.pi * (140 - 200 * t) * t) * np.exp(-t / .04) + _bp(rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t / .006) * .6


def main():
    d = json.load(open(os.path.join(HERE, "project", "assets", "audio", "timing.json")))
    total, words = d["total"], d["words"]

    def w(beat, word):
        return next(x["s"] for x in words[beat] if x["w"].strip(".,:;").lower() == word)

    fx = np.zeros(int((total + 3) * SR))
    # under everything: a distant stadium, swelling where the story does
    amb = crowd(total + 2, .3)
    lvl = np.full(len(amb), .45)
    for a, b, g in [(d["timing"][3]["start"], w(3, "1994") + .6, .9), (d["timing"][5]["start"], w(8, "spain") + 3.0, 1.0),
                    (w(11, "spain"), total + 1, .9)]:
        lvl[int(a * SR):int(b * SR)] = g
    place(fx, amb * _lp(lvl, 2), 0)
    # the format and the matchup land on the drum
    place(fx, drum(), w(1, "forty-eight"), .9)
    place(fx, drum(), w(1, "teams"), .9)
    place(fx, applause(1.8), w(3, "record"), .8)
    place(fx, drum(), w(4, "spain"), 1.0)
    place(fx, drum(), w(4, "argentina"), 1.0)
    # ninety minutes, no goals: the half-time-style whistle into extra time
    place(fx, whistles([(.18, .12), (.6, 0)]), w(5, "goals") + .25, 1.0)
    # the goal
    place(fx, kick(), w(6, "torres") + .25, 1.0)
    place(fx, roar(3.0), w(6, "scores"), 1.0)
    # Argentina push: clapping in time
    place(fx, clap_rhythm(2.6, 120), d["timing"][7]["start"], .9)
    # full time: short, short, long
    place(fx, whistles([(.18, .12), (.18, .12), (.85, 0)]), w(8, "spain") - .15, 1.1)
    place(fx, roar(3.4), w(8, "one-nil") + .2, 1.0)
    place(fx, applause(2.6), w(8, "one-nil") + .5, .8)
    # 2030: the drums again and a last cheer
    place(fx, drum(), w(11, "2030"), .9)
    place(fx, roar(2.4), w(11, "spain"), .8)
    score = bed(total, bpm=84)[: len(fx)]
    out = score + fx[: len(score)] * .8
    sf.write(os.path.join(HERE, "score.wav"), out.astype(np.float32), SR, subtype="FLOAT")
    print("score.wav", round(len(out) / SR, 1), "s, fx peak", round(float(np.max(np.abs(fx * .8))), 3))


if __name__ == "__main__":
    main()
