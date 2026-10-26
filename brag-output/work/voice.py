"""Narration for the RoundHouse video: Kokoro TTS (sherpa-onnx), one clip per scene, placed on the beat grid.

Usage: python voice.py MODEL_DIR OUT_DIR
Writes OUT_DIR/line_NN.wav and OUT_DIR/voice.wav (48 kHz mono, full video length) plus timing.json.
"""
import json
import os
import sys

import numpy as np
import sherpa_onnx
import soundfile as sf

MODEL, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))  # holds lex/: the model lexicon plus extra-lexicon.txt
SR_OUT = 48000
LENGTH = 54.0
VOICE = 3      # af_heart
SPEED = 1.0

# (start in seconds, scene end in seconds, line). Starts sit just after a cut, on or near a beat.
# Lines add to the picture instead of reading the on-screen text.
LINES = [
    (0.5, 4.0, "Every business starts with a good idea."),
    (4.5, 9.0, "Meet Roundhouse, an independent studio for brands, websites, and automation."),
    (9.5, 14.0, "We connect how customers see you, with how your team gets the work done."),
    (14.5, 21.0, "So every inquiry gets the right next step, from a real person."),
    (21.5, 27.0, "Details get checked, someone follows up, and nothing slips through."),
    (27.5, 33.0, "Your team finds answers in your own approved documents, with sources."),
    (33.5, 38.0, "And your brand and website show your value at a glance."),
    (38.5, 44.0, "Imagine what your team could do with the hours repetitive work takes today."),
    (44.5, 48.0, "Understand it. Build it. Keep it useful."),
    (48.5, 53.5, "What would you like to make better? Tell Roundhouse about your project."),
]

cfg = sherpa_onnx.OfflineTtsConfig(
    model=sherpa_onnx.OfflineTtsModelConfig(
        kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
            model=f"{MODEL}/model.onnx", voices=f"{MODEL}/voices.bin", tokens=f"{MODEL}/tokens.txt",
            data_dir=f"{MODEL}/espeak-ng-data", lexicon=f"{HERE}/lex/lexicon-us-en.txt", lang="en-us",
        ),
        num_threads=4,
    ),
)
tts = sherpa_onnx.OfflineTts(cfg)


def resample(x, sr_in, sr_out):
    n = int(round(len(x) * sr_out / sr_in))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(idx[0] - 240, 0): idx[-1] + 2400] if len(idx) else x


track = np.zeros(int(LENGTH * SR_OUT))
timing = []
for i, (start, end, text) in enumerate(LINES):
    speed = SPEED
    for _ in range(4):  # speed up slightly if a line overruns its scene
        a = tts.generate(text, sid=VOICE, speed=speed)
        x = trim(resample(np.asarray(a.samples), a.sample_rate, SR_OUT))
        dur = len(x) / SR_OUT
        if start + dur <= end - 0.15:
            break
        speed *= 1.06
    sf.write(f"{OUT}/line_{i:02d}.wav", x, SR_OUT)
    s = int(start * SR_OUT)
    seg = x[: len(track) - s]
    track[s:s + len(seg)] += seg
    timing.append({"i": i, "start": start, "end": round(start + dur, 2), "scene_end": end, "speed": round(speed, 3), "text": text})
    print(f"{i:02d} {start:5.1f}-{start + dur:5.2f} (scene ends {end}) speed {speed:.2f}  {text}")

track /= np.max(np.abs(track)) * 1.12
sf.write(f"{OUT}/voice.wav", track, SR_OUT)
json.dump(timing, open(f"{OUT}/timing.json", "w"), indent=1)
