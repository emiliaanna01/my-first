---
name: motion-reel
description: Make short motion-design reels (15–50 s, usually 9:16) built entirely in code — no camera footage needed — in three proven looks: (1) neon glass product promo on pure black (Apple-reveal × synthwave), (2) paper-and-ink kinetic explainer with one loud accent colour, hand-drawn scribbles, a cursor and animated charts, (3) editorial cut-out collage with 3D wooden-mannequin poses on a soft gradient and condensed type. Voice-over, synthesized score and sound design, −14 LUFS, MP4 + editable HTML. Use when the user asks for a promo / launch film / motion graphics reel / kinetic typography / explainer / "visual essay" / product video from a script or website, or sends a reference reel of that kind. Not for archival history documentaries (use documentary-reel) or talking-head footage edits (use it-reelsmaker).
---

# Motion reel

Proven on: "Control reel" (20 s neon promo), "You'll forget this tomorrow" (19.6 s forgetting-curve explainer),
"Be bored on purpose" (48 s editorial collage). Everything is drawn on a 2D canvas, rendered frame by frame in headless Chromium.

## The user's standing preferences (follow these every time)
- **Plan first.** Send a beat sheet (4–8 timed beats: shot, on-screen words, sound cue) and wait for "go"/"approved" before building.
- **Ask for exactly what you need**, as a short list, with copy-paste prompts if they must generate anything. Check every upload and say keep / redo and why.
- **Text in the centre hooks** — big, centred, mixed sizes, one loud accent word; never overlapping lines (check stills for this).
- **Voice: female.** Use the saved narrator in `voices/` (or the user's ElevenLabs MP3). Not Samara, not a flat male TTS.
- **Sound makes it alive:** music clearly audible (ride it down only under spoken lines), a whoosh/hit/pop/click on every cut and reveal.
- Always deliver **MP4 + editable HTML**, commit and push, then summarise briefly. "Just answer" means a short answer, no work.

## 1 · Read the brief or reference
- From a script: cut it to 4–6 ideas, five-word lines, lead with the sharpest line, numbers get their own shot.
- From a reference reel: sample frames (`ffmpeg -vf fps=1`), cut rhythm (`select='gt(scene,0.3)'`), loudness (`ebur128`), voice pitch; note palette, type, transitions, how text animates. Match the feel, never copy it.
- The only two things to ask if missing: **duration** and **aspect ratio** (9:16 1080×1920 · 1:1 · 16:9).

## 2 · Pick a look and copy its template (`templates/`)
| Look | Template | Signature |
|---|---|---|
| **Neon glass promo** | `neon-promo/reel.html` | Pure black; light is the subject; dark matte glass panels with lit edges; neon hue travelling cyan → violet → magenta (or around the brand colour); typing whose last letter flashes; shockwaves, rings, glass icon tiles, phone UI, big stat slamming in with bloom; hard cuts, push-ins; motion blur via shutter samples. Fonts: Inter Display, Instrument Serif italic accents, JetBrains Mono. |
| **Paper explainer** | `paper-explainer/reel.html` (+ `audio.py`, `vo.py`) | Warm paper bg, black ink, ONE loud accent (#FF4A1C) for key words/numbers, white cards with thick outlines, scribbled ellipses, strike-throughs, a blue cursor that clicks, clock, animated line chart with zoom, bookmark "save this" end. Pattern interrupt where music stops. |
| **Editorial collage** | `editorial-collage/` (reel + `sprites/` 3D studio) | Lavender radial gradient, grayscale/duotone cut-outs of wooden mannequin poses rendered in three.js (`sprites/studio.html` → `shoot.cjs` → `post.py`), violet cast shadows, condensed navy type typed in, white orbit/scribble lines, pixel speech bubbles, mosaic entrances. |
Every template has an **EDIT ME** block at the top (palette, copy, timing, BEATS, CUES) — change that first, then the scene functions.

## 3 · Voice-over and timing
- `pip install kokoro-onnx`; model files `kokoro-v1.0.onnx` + `voices-v1.0.bin` from github.com/thewh1teagle/kokoro-onnx/releases.
- Saved narrator: `voices/narrator_female.npy` (Kokoro 70 % bf_emma + 30 % af_kore, en-gb, speed 0.97) — `voices/speak.py` for single lines.
- For scripts: write `vo.py` CLIPS (id, text, pause after) like the templates; then `scripts/words.py <vo_dir> vo.json` → word onsets.
  Key every visual off the voice: `W("clip", n)` / `T.name` = when word n is spoken. Pauses ~0.2 s, longer only on punchlines.

## 4 · Build, check, render
```bash
python3 scripts/build.py motion/<slug>/src/reel.html exports/<slug>.html [soundtrack.m4a]   # inlines subset fonts (+ VO, sprites, audio)
node scripts/render.cjs exports/<slug>.html --stills /tmp/st 0.5,2,4,…      # one still per beat; contact-sheet with scripts/sheet.py; look, fix, repeat
node scripts/render.cjs exports/<slug>.html out/silent.mp4 6               # 6 = motion-blur samples (3 for heavy scenes)
```
(The editorial template has its own `build.py` that also inlines the sprite cut-outs and VO timings.)
Check stills for: overlapping text, text off-safe-area (keep 90 px margins on 9:16), illegible contrast, empty beats, a hook that isn't readable in 0.5 s.

## 5 · Sound (`audio/` — all generated, no samples)
- `music.py`: synth score (e.g. dark synthwave 120 BPM D minor for the neon look; lighter plucks/marimba for paper; soft pads for editorial). **Drops and stops land on picture cuts**; one pattern-interrupt silence.
- `sfx.py` + `dsp.py`: boom, whoosh, mech_click, pop, glitch, tink, chime, riser, reverse_swell, power_down, glass_swipe… placed on the `CUES` list in the HTML.
  Optional richer bank: earshot (`pip install soxr pyloudnorm && pip install --no-deps -e earshot`; `earshot sfx render whoosh_fast/crisp -o x.wav`) — place each sound so its **peak** lands on the frame.
- `mix.py`: `LEVEL` / `DUCK` at the top; prints voice clarity per line. Keep every line ≥ ~8 dB above the bed in 300–4000 Hz, but keep the music present between lines (the user wants it audible).
- Master: `ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.2:LRA=11 -c:a aac -b:a 192k soundtrack.m4a`, mux with `-c:v copy -shortest -movflags +faststart`, rebuild the HTML with the soundtrack so it plays in sync.

## 6 · Refining (plain-language notes → change)
"beat 3 too fast" → stretch that beat only · "make it pop" → stronger glow/bloom, more colour movement · "too busy" → fewer objects, longer holds ·
"colder/warmer" → shift the palette arc · "laggy" → fix the easing · brand hex → set `brand.hero`, palette rebuilds around it · "different opening" → swap shot 1.
Re-render only what changed; re-send MP4 + HTML.

## Files in this skill
- `scripts/render.cjs` (stills / MP4 with motion-blur samples), `scripts/build.py` (subset-font inliner), `scripts/words.py`, `scripts/sheet.py`
- `audio/` dsp · music · sfx · mix · vo (Kokoro) — the control-reel sound pipeline
- `templates/neon-promo`, `templates/paper-explainer`, `templates/editorial-collage` (+ 3D mannequin sprite studio)
- `voices/` saved female narrator · `motion-promo-guide.md` the user-facing guide (what to say, ratios, durations, troubleshooting)
- Project layout when used: `motion/<slug>/src/reel.html`, `motion/audio/` (copy `audio/` there — templates import `../audio`), `exports/`
