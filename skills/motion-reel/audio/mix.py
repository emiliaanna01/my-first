#!/usr/bin/env python3
"""Mix voice-over + sound design + score for the control reel.

usage: python3 motion/audio/mix.py <vo_dir> <out_wav> [--stems <dir>]
Loudness-normalise the result to -14 LUFS with ffmpeg afterwards (see README in this folder).
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(__file__))
from dsp import N, SR, convolve, hp, ir, pan  # noqa: E402
from music import score  # noqa: E402
from sfx import design  # noqa: E402

LEVEL = {"vo": 1.0, "sfx": 0.74, "music": 0.4}
DUCK = {"sfx": 0.6, "music": 0.62}   # how far each bus dips while the voice speaks


def voice(vo_dir):
    vo = np.zeros((N, 2))
    for m in json.load(open(f"{vo_dir}/vo.json")):
        x, sr = sf.read(m["file"])
        x = x.mean(1) if x.ndim > 1 else x
        if sr != SR:
            x = signal.resample_poly(x, SR, sr)
        x = hp(x, 90)
        x = x / (np.abs(x).max() + 1e-9) * 0.8
        a = int(m["t"] * SR)
        b = min(N, a + len(x))
        vo[a:b] += pan(x[: b - a])
    return vo + convolve(vo, ir(0.6, 1.0, 5000)) * 0.35


def duck_curve(vo):
    lvl = np.abs(vo).max(1)
    k = int(0.03 * SR)
    e = np.convolve(lvl, np.ones(k) / k, "same")
    e = signal.sosfiltfilt(signal.butter(1, 5, "lowpass", fs=SR, output="sos"), e)
    return np.clip(e / (e.max() + 1e-9) * 3, 0, 1)


def main(vo_dir, out, stems=None):
    vo = voice(vo_dir)
    sfx = design()
    music, _ = score()
    d = duck_curve(vo)[:, None]
    buses = {
        "vo": vo * LEVEL["vo"],
        "sfx": sfx * LEVEL["sfx"] * (1 - DUCK["sfx"] * d),
        "music": music / (np.abs(music).max() + 1e-9) * LEVEL["music"] * (1 - DUCK["music"] * d),
    }
    mix = sum(buses.values())
    fade = np.ones(N)
    k = int(0.3 * SR)
    fade[-k:] = np.linspace(1, 0, k) ** 1.5
    mix = mix * fade[:, None]
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.25) * 0.9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    if stems:
        os.makedirs(stems, exist_ok=True)
        for name, x in buses.items():
            sf.write(f"{stems}/{name}.wav", x.astype(np.float32), SR, subtype="FLOAT")

    # voice clarity report: speech-band level of VO vs everything else, per line
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    v = signal.sosfilt(sos, buses["vo"].mean(1))
    rest = signal.sosfilt(sos, (buses["sfx"] + buses["music"]).mean(1))
    for m in json.load(open(f"{vo_dir}/vo.json")):
        a, b = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        r = lambda x: np.sqrt(np.mean(x[a:b] ** 2)) + 1e-9
        print(f"{m['t']:6.2f}s  {m['text']:<32} voice over bed: {20 * np.log10(r(v) / r(rest)):5.1f} dB")
    print("wrote", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    stems = args[args.index("--stems") + 1] if "--stems" in args else None
    main(args[0], args[1], stems)
