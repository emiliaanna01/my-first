#!/usr/bin/env python3
"""Voice-over for the D.B. Cooper stick-figure reel: British male narrator (Kokoro 60% bm_george + 40% bm_lewis).
One entry per scene (a scene may hold several sentences, joined by short pauses). Scene i starts when its line starts.
usage: python3 motion/stick2/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

SCENES = [   # (sentences, pause after the scene)
    (["He hijacked a plane.", "Collected two hundred thousand dollars.", "Then jumped into the darkness."], .7),
    (["The FBI searched for decades...", "but never found him."], .8),
    (["November twenty-fourth, nineteen seventy-one.", "A man calling himself Dan Cooper boards a flight from Portland to Seattle."], .5),
    (["He orders a drink, then quietly hands a flight attendant a note."], .5),
    (["He claims there's a bomb in his briefcase."], .6),
    (["His demands?", "Two hundred thousand dollars... and four parachutes."], .6),
    (["The plane lands.", "All thirty-six passengers are released.", "Cooper gets his money."], .5),
    (["But he's not finished.", "The plane takes off again."], .5),
    (["Shortly after eight that night, Cooper parachutes from the rear of the aircraft into the darkness."], .9),
    (["He disappears."], 1.3),
    (["Nine years later, a boy discovers five thousand eight hundred dollars of the ransom money near the Columbia River."], .5),
    (["But no confirmed trace of Cooper himself."], .7),
    (["In twenty sixteen, the FBI redirects its investigation resources elsewhere."], .7),
    (["Did Cooper survive?", "Or did the wilderness claim him?"], .9),
    (["To this day... nobody knows."], 0),
]
INNER = .25

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, speed=1.06):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    voice = k.get_voice_style("bm_george") * .6 + k.get_voice_style("bm_lewis") * .4
    t, meta = .3, []
    for i, (sents, gap) in enumerate(SCENES):
        parts = []
        for j, s_ in enumerate(sents):
            s, sr = k.create(s_, voice=voice, speed=float(speed), lang="en-gb"); parts.append(trim(s))
            if j < len(sents) - 1: parts.append(np.zeros(int(INNER * sr)))
        x = np.concatenate(parts); d = len(x) / sr; path = f"{out_dir}/S{i + 1:02d}.wav"; sf.write(path, x, sr)
        text = " ".join(sents)
        meta.append({"id": f"S{i + 1:02d}", "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"S{i + 1:02d} {t:6.2f} {d:4.2f}s  {text[:70]}"); t += d + gap
    print(f"total {t:.2f}s"); json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
