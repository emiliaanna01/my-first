#!/usr/bin/env python3
"""Voice-over for 'Be bored on purpose' (Kokoro TTS, local).
usage: python3 motion/bored/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

# (id, text, pause after)
CLIPS = [
    ("desk",     "Your best ideas don't arrive at your desk.", 0.55),
    ("shower",   "They show up in the shower.", 0.25),
    ("walk",     "On a walk.", 0.25),
    ("queue",    "Standing in a queue.", 0.45),
    ("places",   "Places where nothing is asking for your attention.", 0.45),
    ("coinc",    "That's not a coincidence.", 0.55),
    ("wander",   "When your mind has nothing to do, it starts to wander.", 0.40),
    ("links",    "It links old memories to new problems.", 0.30),
    ("plays",    "It rehearses. It plays.", 0.50),
    ("dmn",      "Neuroscientists call it the default mode network.", 0.40),
    ("bored",    "You'd call it... being bored.", 0.65),
    ("barely",   "But we barely let it happen anymore.", 0.40),
    ("screen",   "Every empty second has a screen waiting to fill it.", 0.45),
    ("bus",      "The bus stop.", 0.20),
    ("lift",     "The elevator.", 0.20),
    ("kettle",   "The kettle.", 0.55),
    ("traded",   "We traded boredom for stimulation,", 0.20),
    ("lost",     "and quietly lost the space where ideas grow.", 0.60),
    ("pocket",   "So next time you're waiting, leave the phone in your pocket.", 0.50),
    ("purpose",  "Be bored on purpose.", 0.60),
    ("start",    "That's where the good ideas start.", 0.0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, voice="af_heart", speed=0.98):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    t, meta = 0.35, []
    for cid, text, gap in CLIPS:
        s, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
        s = trim(s); path = f"{out_dir}/{cid}.wav"; sf.write(path, s, sr)
        d = len(s) / sr
        meta.append({"id": cid, "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"{cid:<8} {t:6.2f}  {d:4.2f}s  {text}")
        t += d + gap
    print(f"total {t:.2f}s")
    json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
