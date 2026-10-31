#!/usr/bin/env python3
"""Voice-over for the Jimmy Hoffa reel: British female storyteller (Kokoro 80% bf_emma + 20% bf_isabella), one line per clip.
Clip i starts when line i starts, so each clip lasts exactly as long as its line plus the pause after it.
usage: python3 motion/lustig/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

# (text, pause after). Fact fixes vs the draft: call time ~2:15 (AP), missing report filed the next day (July 31).
LINES = [
    ("July thirtieth, nineteen seventy-five.", 1.05), ("Machus Red Fox restaurant,", 0.57), ("Bloomfield Township, Michigan.", 1.1),
    ("A man in his sixties", 0.53), ("parks a green Pontiac", 0.55), ("and walks inside.", 1.05),
    ("He is Jimmy Hoffa,", 0.57), ("the former president of the Teamsters union.", 1.1),
    ("He has come for a two o'clock meeting", 0.53), ("with two men,", 0.57), ("Anthony Giacalone and Anthony Provenzano.", 1.1),
    ("Neither man is there.", 1.15),
    ("Around two fifteen, Hoffa phones his wife.", 0.6), ("He tells her Giacalone has not shown up.", 1.15),
    ("Hoffa had left federal prison in nineteen seventy-one,", 0.55), ("after President Nixon cut his sentence.", 1.05),
    ("Because of the terms of his release,", 0.55), ("he could not return to union leadership until nineteen eighty.", 1.15),
    ("Around two forty-five, a witness sees him", 0.53), ("standing in the parking lot.", 1.05),
    ("Then he is gone.", 1.4),
    ("The next day, his family reports him missing.", 0.75), ("His car is still in the lot.", 1.1),
    ("The FBI searches for decades,", 0.55), ("through farms, fields, and driveways.", 1.1),
    ("Hoffa is declared legally dead in nineteen eighty-two.", 1.2),
    ("They found his car.", 1.25), ("They never found Jimmy Hoffa.", 0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, speed=0.98):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    voice = k.get_voice_style("bf_emma") * .8 + k.get_voice_style("bf_isabella") * .2
    t, meta = .25, []
    for i, (text, gap) in enumerate(LINES):
        s, sr = k.create(text, voice=voice, speed=float(speed), lang="en-gb"); s = trim(s); d = len(s) / sr
        path = f"{out_dir}/S{i + 1:02d}.wav"; sf.write(path, s, sr)
        meta.append({"id": f"S{i + 1:02d}", "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"S{i + 1:02d} {t:6.2f} {d:4.2f}s  {text}"); t += d + gap
    print(f"total {t:.2f}s"); json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
