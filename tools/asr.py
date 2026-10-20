"""Word-level English speech recognition on CPU: NVIDIA Parakeet TDT 0.6B via sherpa-onnx.

As a script, writes an IT Reelsmaker transcript (used instead of faster-whisper, whose models live on Hugging Face):
  python tools/asr.py WAV16K OUT.json [--source NAME]
Get WAV16K from: python <reelsmaker>/scripts/transcribe.py audio edit/<id> <source>
"""
import argparse, json, os, subprocess, tempfile
import numpy as np, sherpa_onnx

M = os.path.expanduser("~/.cache/video-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/")
CHUNK = 16000 * 30  # 30 s chunks keep memory flat on long videos


def load_audio(path):
    with tempfile.NamedTemporaryFile(suffix=".f32") as f:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", f.name],
                       check=True)
        return np.fromfile(f.name, np.float32)


def transcribe(path):
    """-> [[word, start, end], ...] in seconds. A word lasts until the next one starts (max 0.8 s)."""
    audio = load_audio(path)
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx", joiner=M + "joiner.int8.onnx",
        tokens=M + "tokens.txt", model_type="nemo_transducer", num_threads=os.cpu_count())
    words = []
    for off in range(0, len(audio), CHUNK):
        s = rec.create_stream()
        s.accept_waveform(16000, audio[off:off + CHUNK])
        rec.decode_stream(s)
        for tok, t in zip(s.result.tokens, s.result.timestamps):
            t += off / 16000
            if tok.startswith(" ") or not words:
                words.append([tok.strip(), t, t])
            else:
                words[-1][0] += tok
                words[-1][2] = t
    words = [w for w in words if w[0]]
    for i, w in enumerate(words):
        nxt = words[i + 1][1] if i + 1 < len(words) else w[2] + 0.5
        w[2] = min(nxt, max(w[2] + 0.08, w[1] + 0.12), w[1] + 0.8)
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav"); ap.add_argument("out"); ap.add_argument("--source")
    a = ap.parse_args()
    words = transcribe(a.wav)
    doc = {"language_code": "en", "text": " ".join(w[0] for w in words),
           "words": [{"text": w, "start": round(s, 3), "end": round(e, 3), "type": "word"} for w, s, e in words],
           "source": a.source or os.path.basename(a.wav), "model": "parakeet-tdt-0.6b-v2 int8 (sherpa-onnx)",
           "timeline": "video", "audio_offset": 0.0}
    with open(a.out, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"{a.out}: {len(words)} words")


if __name__ == "__main__":
    main()
