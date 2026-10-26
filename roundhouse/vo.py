"""Voiceover: one Kokoro clip per line (trimmed), plus word timings from faster-whisper per clip.

Writes out/vo/line{i}.wav and out/vo/lines.json ([{text, dur, words: [{w, s, e}]}], times relative to the clip).
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".claude", "skills", "papercut", "engine"))
import voice  # noqa: E402  papercut's model lookup

# Michael: a steady, grown-up narrator. Read a touch slower, then lowered ~1 semitone (formants kept) for weight.
# Pauses between lines are set in build.py (GAPS), giving ~140 wpm overall like documentary narration.
VOICE, SPEED, PITCH = (("am_michael", 1.0),), .9, .94

# (what is shown in captions, what is spoken: "RoundHouse" is split so the voice says it as two words)
LINES = [
    "Your business has two sides.",
    "The side your customers see…",
    "and the side your team has to deal with.",
    "And when those two sides don't connect,",
    "things get harder than they need to be.",
    "That's the gap RoundHouse works on.",
    "Your brand.",
    "Your website.",
    "Your workflows.",
    "Designed to make the business easier to understand…",
    "and the work easier to do.",
    "What would you make work better?",
]


def spoken(t):
    return t.replace("RoundHouse", "Round House").replace("…", ",")


def main():
    from kokoro_onnx import Kokoro
    km = voice._models()
    k = Kokoro(os.path.join(km, "kokoro-v1.0.onnx"), os.path.join(km, "voices-v1.0.bin"))
    style = sum(k.get_voice_style(v) * w for v, w in VOICE)
    out = os.path.join(HERE, "out", "vo")
    os.makedirs(out, exist_ok=True)
    try:
        from faster_whisper import WhisperModel
        wm = WhisperModel("small", device="cpu", compute_type="int8")
    except Exception as e:
        print("whisper unavailable, even word timing:", type(e).__name__)
        wm = None
    from scipy.signal import resample_poly
    rows = []
    for i, line in enumerate(LINES):
        x, sr = k.create(spoken(line), voice=style, speed=SPEED, lang="en-us")
        x = np.asarray(x, np.float32)
        nz = np.where(np.abs(x) > 0.004)[0]
        x = x[max(0, nz[0] - int(0.01 * sr)): nz[-1] + int(0.04 * sr)]
        raw = os.path.join(out, f"line{i}_raw.wav")
        sf.write(raw, x, sr, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", f"rubberband=pitch={PITCH}:formant=preserved:transients=smooth",
                        os.path.join(out, f"line{i}.wav")], check=True)
        x, _ = sf.read(os.path.join(out, f"line{i}.wav"), dtype="float32")
        dur = len(x) / sr
        toks = line.split()
        heard = []
        if wm:
            segs, _ = wm.transcribe(resample_poly(x, 16000, sr).astype(np.float32), word_timestamps=True, language="en")
            heard = [w for s in segs for w in (s.words or [])]
        # map the script's own tokens onto whisper's clock by character position (spelling always matches the script)
        n = lambda t: len(re.sub(r"\W", "", t)) or 1
        total = sum(n(t) for t in toks)
        xs, ts, c = [0], [heard[0].start if heard else 0.0], 0
        for w in heard:
            c += n(w.word)
            xs.append(c)
            ts.append(w.end)
        if not heard:
            xs, ts = [0, total], [0.0, dur]
        scale = xs[-1] / total
        cur, words = 0, []
        for t in toks:
            s = float(np.interp(cur * scale, xs, ts))
            e = float(np.interp((cur + n(t)) * scale, xs, ts))
            words.append({"w": t, "s": round(s, 3), "e": round(max(e, s + 0.08), 3)})
            cur += n(t)
        rows.append({"text": line, "dur": round(dur, 3), "words": words})
        print(f"{i:2d} {dur:5.2f}s  {line}")
    json.dump({"sr": sr, "lines": rows}, open(os.path.join(out, "lines.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
