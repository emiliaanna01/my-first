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

## IT Reelsmaker plugin
`it-reelsmaker.json` points the plugin at this project; `reels/` is its Remotion project (ReelKit).
Its default transcriber (faster-whisper) needs Hugging Face, which this environment blocks, so transcripts come
from Parakeet instead:
```bash
python <plugin>/scripts/transcribe.py audio edit/<id> <source>       # prints the 16 kHz WAV path
python tools/asr.py edit/<id>/audio16k-<stem>.wav edit/<id>/transcripts/<stem>.json --source <source>
python <plugin>/scripts/transcribe.py check edit/<id>/transcripts/<stem>.json
```

## Web design toolkit
`web-design/` holds the website-building setup: 25 design, UI/UX, animation (GSAP) and quality skills
in `.claude/skills/`, MCP servers in `.mcp.json`, inspiration and component guides, a screenshot
tool and a starter page. Start with `web-design/README.md`.

## Pass & Play Chess
`chess-2p/` is an offline two-player chess app for Android (chess.com-style board, clocks with
increment, all draw rules). Build the APK with `chess-2p/build-apk.sh`; see `chess-2p/README.md`.
