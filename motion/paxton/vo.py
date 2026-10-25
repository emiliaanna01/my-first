#!/usr/bin/env python3
"""Voice-over for 'The leaf and the Crystal Palace' (Kokoro TTS, local).
usage: python3 motion/paxton/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

CLIPS = [
    ("girl",     "In eighteen forty-nine, a little girl stood on a leaf.", 0.45),
    ("held1",    "It held her.", 0.70),
    ("lily",     "The leaf belonged to a giant Amazon water lily.", 0.35),
    ("father",   "And the man who grew it was her father, Joseph Paxton.", 0.25),
    ("gardener", "A gardener. The first to make it bloom in England.", 0.60),
    ("over",     "Turn the leaf over, and you see why it's so strong.", 0.35),
    ("ribs",     "Ribs. Spreading the weight in every direction.", 0.75),
    ("london",   "A year later, London had a problem.", 0.35),
    ("expo",     "It was hosting the Great Exhibition, and needed a building.", 0.35),
    ("designs",  "Two hundred and forty-five designs had been submitted.", 0.25),
    ("rejected", "Every one was rejected.", 0.65),
    ("meeting",  "So in a railway meeting, Paxton picked up a pen...", 0.20),
    ("sketch",   "and sketched an idea on blotting paper.", 0.55),
    ("likeleaf", "A building made like that leaf.", 0.35),
    ("parts",    "Iron ribs. Glass panes. Every part made in a factory.", 0.60),
    ("warned",   "Experts warned it would collapse.", 0.30),
    ("soldiers", "So soldiers marched across the galleries to test it.", 0.55),
    ("held2",    "It held.", 0.80),
    ("opened",   "On the first of May, eighteen fifty-one, the Crystal Palace opened.", 0.35),
    ("panes",    "Nearly three hundred thousand panes of glass.", 0.25),
    ("visitors", "Six million visitors.", 0.75),
    ("since",    "Every glass building since owes something to that leaf.", 0.0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, voice="af_heart", speed=0.94):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    t, meta = 0.6, []
    for cid, text, gap in CLIPS:
        s, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
        s = trim(s); path = f"{out_dir}/{cid}.wav"; sf.write(path, s, sr)
        d = len(s) / sr
        meta.append({"id": cid, "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"{cid:<9} {t:6.2f}  {d:4.2f}s  {text}")
        t += d + gap
    print(f"total {t:.2f}s")
    json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
