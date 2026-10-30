#!/usr/bin/env python3
"""Generate voice-over lines with Kokoro TTS (local, offline).
usage: python3 motion/audio/vo.py <model_dir> <out_dir> [voice]"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

# (cue seconds, text). Spelling is phonetic where the brand name needs it.
LINES = [
    (0.12, "One fault... stops everything."),
    (2.42, "Alarms."),
    (3.52, "Delays."),
    (4.62, "Guesswork."),
    (6.20, "See every signal."),
    (8.15, "Live."),
    (10.05, "Forty percent less downtime."),
    (13.62, "Control it... from anywhere."),
    (17.45, "Halsin."),
    (18.45, "Book a demo."),
]

def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(0, idx[0] - 240): idx[-1] + 2400] if len(idx) else x

def main(model_dir, out_dir, voice="af_heart"):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    meta = []
    for i, (t, text) in enumerate(LINES):
        samples, sr = k.create(text, voice=voice, speed=1.0, lang="en-us")
        samples = trim(samples)
        path = f"{out_dir}/vo_{i:02d}.wav"
        sf.write(path, samples, sr)
        meta.append({"t": t, "text": text, "file": path, "dur": round(len(samples) / sr, 3), "sr": sr})
        print(f"{t:6.2f}s  {len(samples)/sr:5.2f}s  {text}")
    json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:])
