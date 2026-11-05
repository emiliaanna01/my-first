#!/usr/bin/env python3
"""Voice-over for the stick-figure money reel: friendly relaxed male (Kokoro 60% am_liam + 40% am_michael), one line per scene.
usage: python3 motion/stick/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

LINES = [   # (text, pause after) — scene i starts when line i starts
    ("Your salary just hit your account. You're rich!", .45),
    ("Well... for about five minutes.", 1.5),
    ("First comes rent.", .75),
    ("Then groceries, bills, subscriptions, and that daily coffee you swear doesn't count.", .45),
    ("Suddenly, your bank balance looks like a horror movie.", .5),
    ("Here's the real problem: your money has jobs before you even get paid.", .5),
    ("So next payday, pay yourself first.", .4),
    ("Save a little, budget the rest, and stop wondering where it all went.", 0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, speed=1.08):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    voice = k.get_voice_style("am_liam") * .6 + k.get_voice_style("am_michael") * .4
    t, meta = .3, []
    for i, (text, gap) in enumerate(LINES):
        s, sr = k.create(text, voice=voice, speed=float(speed), lang="en-us"); s = trim(s); d = len(s) / sr
        path = f"{out_dir}/S{i + 1:02d}.wav"; sf.write(path, s, sr)
        meta.append({"id": f"S{i + 1:02d}", "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"S{i + 1:02d} {t:6.2f} {d:4.2f}s  {text}"); t += d + gap
    print(f"total {t:.2f}s"); json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
