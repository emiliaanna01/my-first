#!/usr/bin/env python3
"""Voice-over for '<your film> — EDIT CLIPS below' (Kokoro TTS, local).
usage: python3 motion/<slug>/vo.py <kokoro_model_dir> <out_dir> [voice] [speed]
voice is a Kokoro voice name or a blend like "bf_emma:.7+af_kore:.3" (calm British female narrator)."""
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

# (id, text, pause after). Short sentences, a beat every 1.5-2 s like the reference.
CLIPS = [
    ("hook",     "In the spring of nineteen forty-three, a dead man lied to Hitler.", 0.30),
    ("believed", "And Hitler believed him.", 0.55),
    ("sicily",   "The Allies need Sicily. The Germans know it.", 0.35),
    ("london",   "So in London, two intelligence officers plan the unthinkable.", 0.45),
    ("body",     "They find a body.", 0.55),
    ("drifter",  "A Welsh drifter, Glin-dur Michael.", 0.40),
    ("newlife",  "They give him a new life.", 0.30),
    ("martin",   "Major William Martin, Royal Marines.", 0.40),
    ("pam",      "A fiancée called Pam. Love letters. Theatre tickets. A bill for the ring.", 0.40),
    ("greece",   "And a briefcase of secret letters, pointing at Greece.", 0.50),
    ("april",    "On the thirtieth of April, a submarine releases him off the coast of Spain.", 0.40),
    ("fisher",   "A fisherman finds him.", 0.40),
    ("copy",     "Spanish officers let German spies copy the letters.", 0.35),
    ("panzer",   "Hitler moves a panzer division to Greece.", 0.45),
    ("july",     "In July, the Allies land on Sicily.", 0.50),
    ("message",  "A message reaches Churchill: Mincemeat swallowed. Rod, line and sinker.", 0.60),
    ("grave",    "In Huelva, his grave still carries the false name.", 0.35),
    ("beneath",  "Beneath it, the real one.", 0.55),
    ("never",    "Glin-dur Michael. The man who never was.", 0.0),
]

def trim(x, thr=0.008):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 1800] if len(i) else x

def main(model_dir, out_dir, voice="saved", speed=0.97):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    speed = float(speed)
    if voice == "saved": voice = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "narrator_female.npy"))   # copy voices/narrator_female.npy here
    elif ":" in voice: voice = sum(k.get_voice_style(n) * float(w) for n, w in (p.split(":") for p in voice.split("+")))
    t, meta = 0.15, []
    for cid, text, gap in CLIPS:
        s, sr = k.create(text, voice=voice, speed=speed, lang="en-gb")
        s = trim(s); path = f"{out_dir}/{cid}.wav"; sf.write(path, s, sr)
        d = len(s) / sr
        meta.append({"id": cid, "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"{cid:<9} {t:6.2f}  {d:4.2f}s  {text}")
        t += d + gap
    print(f"total {t:.2f}s")
    json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:5])
