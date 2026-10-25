#!/usr/bin/env python3
"""Voice-over for the 'Forgetting curve' reel (Kokoro TTS, local).
usage: python3 motion/forget/vo.py <kokoro_model_dir> <out_dir>
Writes one wav per clip and vo.json with back-to-back timings (gap after each clip)."""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

# (id, text, pause after in seconds)
CLIPS = [
    ("hook",    "You'll forget most of this video by tomorrow.", 0.22),
    ("notyou",  "It's not you.", 0.08),
    ("brain",   "It's your brain.", 0.20),
    ("day",     "Within a day,", 0.06),
    ("lose",    "you can lose up to sixty-seven percent of what you learn.", 0.22),
    ("curve",   "It's called the forgetting curve.", 0.24),
    ("fix",     "The fix?", 0.14),
    ("review",  "Review right before you'd forget.", 0.20),
    ("d1",      "Day one.", 0.10),
    ("d3",      "Day three.", 0.10),
    ("d7",      "Day seven.", 0.20),
    ("flat",    "Each review flattens the curve.", 0.26),
    ("save",    "Save this...", 0.10),
    ("cta",     "so you don't forget it.", 0.0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1600] if len(i) else x

def main(model_dir, out_dir, voice="af_heart", speed=1.1):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    t, meta = 0.12, []
    for cid, text, gap in CLIPS:
        s, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
        s = trim(s)
        path = f"{out_dir}/{cid}.wav"
        sf.write(path, s, sr)
        d = len(s) / sr
        meta.append({"id": cid, "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"{cid:<7} {t:6.2f}  {d:4.2f}s  {text}")
        t += d + gap
    print(f"total {t:.2f}s")
    json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
