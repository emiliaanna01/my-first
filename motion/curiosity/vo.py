#!/usr/bin/env python3
"""Voice-over for the curiosity / phone-addiction reel: calm deep male (Kokoro 60% am_michael + 40% am_onyx), one line per 6 s clip.
usage: python3 motion/curiosity/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

CLIP = 6.0 / 1.3     # clips play 1.3x faster: each scene is exactly 2 bars at 104 BPM
LEAD = 0.3      # each line starts right after the cut
LINES = [
    "You check your phone, and nothing new is there.",
    "Then you check it again anyway.",
    "You think you're checking because your phone is useful.",
    "You're really checking because your phone is unpredictable.",
    "Slot machines run on something called variable rewards.",
    "Sometimes you win. Sometimes you don't. You never know when.",
    "That uncertainty makes your brain crave the next check.",
    "Every notification is another pull of the lever.",
    "Your phone isn't addictive because it's useful.",
    "It's addictive because it's uncertain.",
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, speed=1.12):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    voice = k.get_voice_style("am_michael") * .6 + k.get_voice_style("am_onyx") * .4
    meta = []
    for i, text in enumerate(LINES):
        s, sr = k.create(text, voice=voice, speed=float(speed), lang="en-us"); s = trim(s)
        d = len(s) / sr; t = i * CLIP + LEAD
        if d > CLIP - LEAD - .15: t = i * CLIP + max(.12, (CLIP - d) / 2)    # long line: centre it in the clip
        path = f"{out_dir}/S{i + 1:02d}.wav"; sf.write(path, s, sr)
        meta.append({"id": f"S{i + 1:02d}", "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"S{i + 1:02d} {t:6.2f} {d:4.2f}s  {text}")
    json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
