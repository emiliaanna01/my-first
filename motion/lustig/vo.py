#!/usr/bin/env python3
"""Voice-over for the Jimmy Hoffa reel: British female storyteller (Kokoro 80% bf_emma + 20% bf_isabella), one line per clip.
Clip i starts when line i starts, so each clip lasts exactly as long as its line plus the pause after it.
usage: python3 motion/lustig/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

# (text, pause after). Fact fixes vs the draft: call time ~2:15 (AP), missing report filed the next day (July 31).
LINES = [
    ("July thirtieth, nineteen seventy-five.", .35), ("Machus Red Fox restaurant,", .12), ("Bloomfield Township, Michigan.", .4),
    ("A man in his sixties", .08), ("parks a green Pontiac", .1), ("and walks inside.", .35),
    ("He is Jimmy Hoffa,", .12), ("the former president of the Teamsters union.", .4),
    ("He has come for a two o'clock meeting", .08), ("with two men,", .12), ("Anthony Giacalone and Anthony Provenzano.", .4),
    ("Neither man is there.", .45),
    ("Around two fifteen, Hoffa phones his wife.", .15), ("He tells her Giacalone has not shown up.", .45),
    ("Hoffa had left federal prison in nineteen seventy-one,", .1), ("after President Nixon cut his sentence.", .35),
    ("Because of the terms of his release,", .1), ("he could not return to union leadership until nineteen eighty.", .45),
    ("Around two forty-five, a witness sees him", .08), ("standing in the parking lot.", .35),
    ("Then he is gone.", .7),
    ("The next day, his family reports him missing.", .3), ("His car is still in the lot.", .4),
    ("The FBI searches for decades,", .1), ("through farms, fields, and driveways.", .4),
    ("Hoffa is declared legally dead in nineteen eighty-two.", .5),
    ("They found his car.", .55), ("They never found Jimmy Hoffa.", 0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, speed=1.07):
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
