# Be bored on purpose (48 s visual essay)

An editorial cutout-collage reel: lavender gradient, grayscale and lavender cutouts, typed condensed type.

| Path | What it does |
| --- | --- |
| `vo.py` / `vo.json` | Voice-over clips (Kokoro TTS) and their timings; the reel's text timing keys off these |
| `sprites/studio.html` | 3D studio (three.js): wooden mannequin poses and props, rendered on transparent backgrounds |
| `sprites/shoot.cjs` | Renders every studio shot to `sprites/raw/` |
| `sprites/post.py` | Grades the raw renders into cutouts (`sprites/cut/*.webp`): duotone, contrast, film grain, trim |
| `src/bored-reel.html` | The animation: scenes, typed text, orbit lines, pixel bubbles, mosaic entrances |
| `build.py` | Inlines fonts, cutouts, timings (and soundtrack) into one self-contained HTML |
| `audio.py` | Score, sound design and voice mix; prints voice clarity per line |

Rebuild:

```sh
cd motion/bored/sprites && npm install three@0.147.0 @fontsource/barlow-condensed@5.0.13
node shoot.cjs && python3 post.py raw cut && cd ../../..
python3 motion/bored/build.py exports/bored-reel.html
node motion/render.cjs exports/bored-reel.html exports/bored-reel-silent.mp4 3
python3 motion/bored/audio.py <vo_dir> mix.wav     # vo_dir from vo.py (needs the Kokoro model files)
```
