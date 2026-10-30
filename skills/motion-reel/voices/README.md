# Saved voices

## narrator_female — the voice from "The Man Who Never Was" (Operation Mincemeat reel)
- Calm British female documentary narrator.
- Kokoro TTS blend: **70% `bf_emma` + 30% `af_kore`**, British English, **speed 0.97**.
- Measured pitch about 173 Hz (range 141–217 Hz), close to the Turing reference narrator (about 164 Hz).
- Exact voice saved as `narrator_female.npy`, so it is identical in every future reel.
- Write names phonetically when needed (e.g. "Glyndwr" -> "Glin-dur").

Quick use: `python3 motion/voices/speak.py <kokoro_model_dir> "Your line." out.wav`
Full scripts with pauses + word timings: copy `motion/mincemeat/vo.py` (it uses this same blend and speed).
