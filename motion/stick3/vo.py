#!/usr/bin/env python3
"""Voice-over for the "one dollar, billionaire confidence" stick-figure reel: a four-voice cast (Kokoro), lines grouped by scene.
Writes one WAV per scene (its lines joined by short pauses) plus vo.json with each scene's start; lines.json keeps every
line's speaker and start for the mix.
usage: python3 motion/stick3/vo.py <kokoro_model_dir> <out_dir>"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

CAST = {  # speaker: (voice blend, speed, lang)
    "NARRATOR": ([("am_michael", .6), ("am_onyx", .4)], 1.0, "en-us"),      # deep, deadpan
    "RED": ([("am_puck", .6), ("am_eric", .4)], 1.12, "en-us"),             # fast, cocky
    "WHITE": ([("am_liam", .6), ("am_adam", .4)], 1.0, "en-us"),            # flat, unimpressed
    "WAITER": ([("bm_george", .7), ("bm_lewis", .3)], .95, "en-gb"),        # posh British
}
SCENES = [   # [(speaker, line)], pause after the scene
    ([("NARRATOR", "This is what happens when you have one dollar... but billionaire confidence.")], .45),
    ([("RED", "Bro, money doesn't impress me anymore."), ("WHITE", "You borrowed five bucks yesterday.")], .35),
    ([("RED", "That's called leveraging assets.")], .45),
    ([("NARRATOR", "So he walks into a fancy restaurant.")], .35),
    ([("RED", "Your finest sparkling water, please."), ("WAITER", "That'll be twelve dollars.")], .3),
    ([("RED", "Twelve?! Does it come with the ocean?!")], .45),
    ([("NARRATOR", "His card gets declined."), ("WHITE", "Where's your Lamborghini now?")], .35),
    ([("RED", "Funny you mention that..."), ("RED", "Can you lend me fifty bucks for parking?"), ("WHITE", "You don't even have a car!!")], 0),
]
GAP = .3

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    style = {c: sum(k.get_voice_style(n) * w for n, w in mix) for c, (mix, _, _) in CAST.items()}
    t, meta, lines = .3, [], []
    for i, (ls, gap) in enumerate(SCENES):
        parts, lt = [], t
        for j, (who, text) in enumerate(ls):
            _, sp, lang = CAST[who]
            s, sr = k.create(text, voice=style[who], speed=sp, lang=lang); s = trim(s); s = s / (np.abs(s).max() + 1e-9) * .8
            lines.append({"scene": i + 1, "who": who, "text": text, "t": round(lt, 3), "dur": round(len(s) / sr, 3)})
            parts.append(s); lt += len(s) / sr
            if j < len(ls) - 1: parts.append(np.zeros(int(GAP * sr))); lt += GAP
        x = np.concatenate(parts); d = len(x) / sr; path = f"{out_dir}/S{i + 1:02d}.wav"; sf.write(path, x, sr)
        text = " ".join(l for _, l in ls)
        meta.append({"id": f"S{i + 1:02d}", "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"S{i + 1:02d} {t:6.2f} {d:4.2f}s  {text[:70]}"); t += d + gap
    print(f"total {t:.2f}s")
    json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1); json.dump(lines, open(f"{out_dir}/lines.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
