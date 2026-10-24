# Reel audio

All audio is generated locally. There are no samples or stock tracks.

| File | What it makes |
| --- | --- |
| `vo.py` | Voice-over lines (Kokoro TTS, voice `af_heart`) and `vo.json` with each line's cue time |
| `music.py` | Background score: dark synthwave, 120 BPM, D minor. Drops and stops sit on the picture cuts |
| `sfx.py` | Sound design: every effect is synthesized and placed on the film's cue points |
| `mix.py` | Mixes voice, effects and score, ducks the bed under the voice, and prints a clarity report |
| `dsp.py` | Shared synthesis helpers |

Rebuild:

```sh
python3 motion/audio/vo.py <kokoro_model_dir> <vo_dir>          # kokoro-v1.0.onnx + voices-v1.0.bin
python3 motion/audio/mix.py <vo_dir> mix.wav
ffmpeg -i exports/control-reel.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1:LRA=11" -c:a aac -b:a 256k -movflags +faststart -shortest exports/control-reel-vo.mp4
ffmpeg -i exports/control-reel-vo.mp4 -vn -c:a copy motion/audio/soundtrack.m4a
python3 motion/build.py motion/src/control-reel.html exports/control-reel.html motion/audio/soundtrack.m4a
```

Change balance with `LEVEL` and `DUCK` at the top of `mix.py`.
