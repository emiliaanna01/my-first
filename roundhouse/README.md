# RoundHouse reel (30 s, 1080×1920)

Paper-collage explainer built on the papercut engine (`.claude/skills/papercut`, run its `setup.sh` first).
Everything on screen is drawn in code; no stock photos are used. "Your Brand" / "yourbrand.com" are placeholders for a viewer's business.

```bash
PY=../.claude/skills/papercut/.venv/bin/python
$PY vo.py        # voice lines (Kokoro, af_heart) -> out/vo/
$PY build.py     # scenes, captions, sound cues -> out/project/, out/cues.json
$PY audio.py     # score (104 BPM), foley, voice mix -> out/project/assets/audio/mix.wav
npx hyperframes snapshot out/project --at 2,8,14 -o out/snaps   # check frames
npx hyperframes render out/project -o ../exports/roundhouse_v1.mp4 -q delivery
```

The renderer raises loudness by ~2 LU, so finish with a two-pass `loudnorm` (I=-14, TP=-1.5, `linear=true`)
on the rendered file. `exports/roundhouse_v1_social.mp4` is that file re-encoded at CRF 21 for upload.

Timing: voice line start times are `VO_AT` in `build.py`; every scene is placed around them.
Swap `wordmark()` in `build.py` for the real RoundHouse logo when you have it.
