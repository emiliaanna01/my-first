#!/usr/bin/env python3
"""Voice-over for 'Mary Anderson and the windshield wiper' (Kokoro TTS, local).
usage: python3 motion/anderson/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

# (id, text, pause after). Short sentences, a beat every 1.5-2 s like the reference.
CLIPS = [
    ("hook",     "What if I told you...", 0.18),
    ("hook2",    "the windshield wiper was invented by a woman riding a streetcar?", 0.55),
    ("ny",       "New York, nineteen-oh-two.", 0.25),
    ("crawl",    "A streetcar crawls through the sleet.", 0.25),
    ("cantsee",  "The driver can't see the road.", 0.40),
    ("only",     "So he does the only thing he can.", 0.15),
    ("opens",    "He opens the window, and leans into the storm.", 0.45),
    ("watch",    "One passenger can't stop watching.", 0.30),
    ("name",     "Her name is Mary Anderson.", 0.15),
    ("visiting", "She's visiting from Alabama.", 0.30),
    ("engineer", "She isn't an engineer.", 0.35),
    ("follows",  "But the problem follows her home.", 0.30),
    ("sketch",   "She sketches an idea.", 0.30),
    ("lever",    "A lever inside the car.", 0.12),
    ("blade",    "A rubber blade outside.", 0.30),
    ("turn",     "One turn of the handle...", 0.10),
    ("clear",    "and the glass is clear.", 0.45),
    ("patent",   "In nineteen-oh-three, she's granted a patent.", 0.25),
    ("sell",     "Then she tries to sell it.", 0.25),
    ("canada",   "A company in Canada tells her it isn't worth making.", 0.30),
    ("nobody",   "Nobody buys it.", 0.45),
    ("expire",   "Her patent runs out in nineteen-twenty,", 0.10),
    ("roads",    "just as cars are filling the roads.", 0.25),
    ("standard", "Within a few years, wipers are standard.", 0.30),
    ("profit",   "She never profits from it.", 0.55),
    ("every",    "But every time yours sweeps the rain away...", 0.15),
    ("still",    "that's her idea, still moving.", 0.0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, voice="af_heart", speed=1.0):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    t, meta = 0.15, []
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
