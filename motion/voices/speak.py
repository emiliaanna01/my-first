#!/usr/bin/env python3
"""The saved narrator: a calm British female documentary voice (Kokoro TTS, 70% bf_emma + 30% af_kore),
stored as its exact style vector in narrator_female.npy so it sounds identical every time.
Settings used in "The Man Who Never Was": speed 0.97, British English, pitch about 173 Hz.

usage: python3 motion/voices/speak.py <kokoro_model_dir> "Text to say." out.wav [speed]
The model files (kokoro-v1.0.onnx, voices-v1.0.bin) come from the kokoro-onnx GitHub releases:
https://github.com/thewh1teagle/kokoro-onnx/releases  (pip install kokoro-onnx)
For a whole script with pauses and word timings, see motion/mincemeat/vo.py (same voice)."""
import os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "narrator_female.npy"))

def speak(model_dir, text, out, speed=0.97):
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    s, sr = k.create(text, voice=VOICE, speed=float(speed), lang="en-gb")
    sf.write(out, s, sr); print(f"wrote {out} ({len(s) / sr:.2f} s)")

if __name__ == "__main__":
    speak(*sys.argv[1:5])
