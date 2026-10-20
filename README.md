# my-first: short-form video editing toolkit

CPU-only tools for turning a raw talking-head clip into a styled 9:16 Short
(warm background, word-by-word captions, glowing titles).

## Setup
```bash
./setup.sh                       # venv, models, fonts (idempotent)
source ~/.venvs/video/bin/activate
```

## Tools
| Step | Command | Engine |
|---|---|---|
| Cut silences / dead air | `auto-editor IN.mp4 --margin 0.15s -o cut.mp4` | auto-editor |
| Replace background | `python tools/matte.py cut.mp4 room.jpg matted.mp4` | RobustVideoMatting (ONNX), ~4 fps at 1080x1920 |
| Captions + titles | `python tools/captions.py matted.mp4 subs.ass --title "Level One@9-11"` | Parakeet TDT 0.6B (English, word timestamps) |
| Burn in | `ffmpeg -i matted.mp4 -vf ass=subs.ass -c:a copy final.mp4` | ffmpeg + libass |

Also installed for upcoming effects: MediaPipe (hand tracking for the energy-orb
VFX, face detection for auto punch-in zooms, hair/body segmentation), rembg
(BiRefNet stills), Whisper-small ONNX (non-English speech).
