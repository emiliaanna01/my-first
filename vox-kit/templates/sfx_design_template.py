"""Score and foley for one papercut film -> score.wav. Copy into the film folder and rewrite for the story.

Pattern used by every film in this kit:
  1. build the voice first (`papercut.py make story.json`) so project/assets/audio/timing.json has word times;
  2. write a score that suits the subject (here: a soft minor pulse; swap in a waltz, jazz, crowd, ... );
  3. place 5-10 effects on the exact words they belong to with w(beat_index, "word");
  4. save score.wav unnormalised (float), set "music": "score.wav", "music_gain" 0.22-0.3, "sfx_gain" 0.38-0.45
     in story.json, and run `make` again. papercut mixes it under the voice and adds its own paper foley.
Run with the skill's Python:  .claude/skills/papercut/.venv/bin/python sfx_design.py
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
# papercut's synth helpers: SR (48 kHz), band-pass, envelope, low-pass, a wooden/paper tap, its tension bed
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "skills", "papercut", "engine"))
from sfx import SR, _bp, _env, _lp, bed, tap  # noqa: E402

rng = np.random.default_rng(1)


def tt(d):
    return np.arange(int(d * SR)) / SR


def place(buf, x, t, g=1.0):
    s = max(0, int(t * SR))
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s] * g


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------- score: replace this with one made for the story ----------
def pluck(f, d=1.2):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / .1)) * np.exp(-t / .5) * np.minimum(1, t / .003)


def score(total, bpm=84):
    """A quiet minor pulse: plucked arpeggio over a soft bass; fades in and out."""
    beat = 60 / bpm
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [52, 56, 59]]  # Am F C E
    out = np.zeros(int((total + 2) * SR))
    t, k = 0.0, 0
    while t < total - .3:
        ch = prog[k % 4]
        place(out, pluck(hz(ch[0] - 12), 2.0), t, .35)
        for j, n in enumerate([0, 1, 2, 1]):
            place(out, pluck(hz(ch[n] + 12)), t + j * beat, .12)
        t += 4 * beat
        k += 1
    fade = np.ones(len(out))
    fade[: int(SR)] = np.linspace(0, 1, int(SR))
    fs = int((total - 1.5) * SR)
    fade[fs:] = np.linspace(1, 0, len(out) - fs)
    return out * fade
    # or papercut's own tension bed: return bed(total, bpm=72)


# ---------- foley: small synthesised sounds ----------
def thud():
    t = tt(.6)
    return np.sin(2 * np.pi * (60 - 20 * t) * t) * np.exp(-t / .2) + _bp(rng.standard_normal(len(t)), 200, 2000) * np.exp(-t / .03) * .4


def whoosh(d=.5):
    n = int(d * SR)
    return _bp(rng.standard_normal(n), 400, 4000) * np.sin(np.linspace(0, np.pi, n)) ** 2 * .4


def chime(d=1.5):
    t = tt(d)
    return sum(np.sin(2 * np.pi * f * t) * np.exp(-t / .6) for f in (1046.5, 1568.0)) * .1


def click():
    n = int(.04 * SR)
    return _bp(rng.standard_normal(n), 2500, 9000) * _env(n, .0003, .006) * .8


def main():
    d = json.load(open(os.path.join(HERE, "project", "assets", "audio", "timing.json")))
    total, words = d["total"], d["words"]

    def w(beat, word):
        """When `word` is spoken in beat `beat` (0-based). Punctuation is ignored."""
        return next(x["s"] for x in words[beat] if x["w"].strip(".,:;?!…'\"").lower() == word)

    fx = np.zeros(int((total + 3) * SR))
    # place each effect on its word, e.g.:
    # place(fx, thud(), w(0, "jailed"), 1.0)
    # place(fx, whoosh(), d["timing"][3]["start"] - .1, .8)     # at the start of beat 3
    # place(fx, chime(), w(10, "taxes"), 1.0)
    music = score(total)
    out = music + fx[: len(music)] * .9
    sf.write(os.path.join(HERE, "score.wav"), out.astype(np.float32), SR, subtype="FLOAT")
    print("score.wav", round(len(out) / SR, 1), "s")


if __name__ == "__main__":
    main()

# Level check after `make` (speech alone ≈ -16 dB, effect moments at most 1-3 dB louder):
#   python -c "import soundfile as sf,numpy as np;x,sr=sf.read('project/assets/audio/mix.wav');x=x.mean(1) if x.ndim>1 else x;
#   db=lambda a,b:20*np.log10(np.sqrt((x[int(a*sr):int(b*sr)]**2).mean()));print(db(8.6,11.6),db(7.6,8.4))"
