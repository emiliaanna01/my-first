---
name: documentary-reel
description: Make an original 55–70 s vertical (9:16, 1080×1920) archival-history documentary reel in the style of golden-sepia "mystery documentary" Shorts — AI-generated period stills and 5 s clips, cut-outs pasted over scenes, documents that type themselves, condensed serif captions built word by word on the voice, a slow diagonal light beam with dust, film grain, a narrator, a beat-cut music track and code-made sound effects, mixed to −14 LUFS. Delivers an MP4 and an editable HTML. Use when the user asks for a history/documentary/"forgotten inventor"/"secret operation" reel, a video "like my reference" that is archival or documentary, or gives a reference reel of that kind. Not for talking-head edits (use it-reelsmaker) or stick-figure/cartoon explainers.
---

# Documentary reel

Proven on: "The Man Who Never Was" (Operation Mincemeat, 60.7 s) and "The Woman Who Cleared the Glass" (Mary Anderson).
Everything renders on CPU in a canvas page driven by headless Chromium; no paid APIs.

## 0 · Ground rules (learned the hard way)
- **Two phases. Plan first, build only after the user says "approved"/"start".** Phase 1 = analysis, story, verified facts, script, storyboard, asset prompts. No rendering before approval.
- The user generates images/clips in **Gemini / ChatGPT**; you give exact prompts, check every upload, and say clearly what to redo and why.
- **Images sent in the middle of your turn are shown but NOT saved to disk.** If they don't appear under the uploads/images folder, ask the user to re-send them in a new message.
- Never invent faces of real people; the anonymous dead/real subjects are shown through documents and objects. Paraphrase documents; add a small "dramatised reconstructions" line on the end card.
- Leave disputed facts out of the script (ages, exact numbers) or flag them.
- Commit and push after every meaningful step; keep exports < 50 MB if possible (GitHub warns above that).

## 1 · Analyse the reference (Phase 1)
```bash
R=reference.mp4; ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$R"
ffmpeg -i "$R" -vf "fps=1,scale=270:-1" frames/f%03d.png          # then contact-sheet them (scripts/sheet.py)
ffmpeg -i "$R" -filter:v "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep -o "pts_time:[0-9.]*"   # cut rhythm
ffmpeg -i "$R" -af ebur128 -f null - 2>&1 | grep -A1 Integrated     # loudness (target the same, usually −14)
```
Zoom into specific seconds at 4 fps when the user points at a moment ("the head moving at 2 s", "the submarine at 14 s").
Note: grade, light, layering, typography, how text builds, cut rhythm, voice pitch (librosa.pyin), music tempo.

**The style this skill reproduces** (from the Turing reference):
- One golden-sepia duotone over everything (black → olive-brown → tobacco → antique gold → beige); green only for "the lie".
- A wide diagonal window beam with floating dust; dark edges, bright centres; grain; gentle flicker; gate weave; dust specks.
- Large faded "ghost" portrait behind a sharp cut-out; prints and documents dropped at slight angles; hand-drawn circles/lines.
- "Living portrait" (AI-animated still: eyes lift to camera) for the hook; real-looking newsreel clips; hands writing/circling.
- Condensed serif (Instrument Serif regular/italic), phrases built word by word with mixed sizes, gold italic key words, cream on dark, ink on paper; positions vary (top / beside a face / lower third). Big dates in Gloock.
- ~1.5–4 s shots, longer holds on portraits; cuts, dissolves through shadow, match cuts.

## 2 · Story, facts, script
- Pick one verifiable story with an arc: shocking hook → context → character → complication → discovery → consequence → revelation.
- Verify with WebSearch (several sources); list verified facts + sources; mark disputes.
- 115–145 words for ~60 s. Short sentences. No "Did you know". Hook in the first line. Write years as words ("nineteen forty-three") and hard names phonetically ("Glin-dur") for TTS.

## 3 · Storyboard + asset prompts (end Phase 1 here)
For every shot: time, VO line, on-screen text, visual, asset, layers, light, camera, animation, transition, SFX, music cue, purpose.
Asset naming: `P#` people, `B#` 9:16 scenes, `K#` cut-outs (plain light-grey bg), `D#` blank paper/tickets, `C#` Gemini 5–10 s clips.

Prompt rules to give the user:
- Paste once at the start of the chat: *"Every image must look like an authentic 1943 archival photograph: monochrome warm sepia, deep shadows, soft window light from the upper left, realistic film grain, slightly soft focus, documentary photography. Never put any text, letters, numbers or watermarks in the images."*
- Scenes: vertical 9:16. Cut-outs: shape of the object (landscape 3:2 for vehicles), plain light-grey bg, margin around the object, no shadow.
- **Paper/telegrams/headstones must be blank** — you type the text in code (AI writes garbage text).
- Recurring character: generate P1 first, then attach it as reference for every other shot of him.
- Clips (Gemini image-to-video): new chat per clip, **never press "Extend"** (it re-uses earlier scenes), "camera static" unless stated, "no text, no music". For a hand writing on paper, first composite the paper onto the desk yourself (rembg) and send that frame.
- Priority clips: living portrait (eyes rise), newsreel street, hand circling a map, hand underlining paper.

Check each upload: resolution, AI text, extra fingers, wrong uniforms/period details, glitches; with clips run scene detection and trim jumps:
```bash
ffmpeg -i C8.mp4 -filter:v "select='gt(scene,0.2)',showinfo" -f null - 2>&1 | grep -o "pts_time:[0-9.]*"
```

## 4 · Build (Phase 2) — project layout
```
motion/<slug>/images/   user stills (P1.jpg, B1.jpg, K1.webp, D1.webp …)
motion/<slug>/video/    user clips (C1.mp4 …)
motion/<slug>/src/reel.html   ← copy template/reel.html and rewrite the SCENES block
motion/<slug>/{prep.py, vo.py, build.py, audio.py, dsp.py, narrator_female.npy}   ← from template/ + scripts/ + voices/
motion/render.cjs       ← scripts/render.cjs (shared)
```
1. **Grade + cut-outs**: edit the `PLATES`/cutout lists in `prep.py`, run it → `layers/*.webp` + `grade.cube`.
   Crop photo-print borders (~5.5 % x / 3.5 % y); paint out AI glitches with cv2.inpaint; cut subjects with rembg (`u2net_human_seg` for people, `isnet-general-use` for objects).
2. **Clips** → graded VP9 webm (and a small copy for the HTML):
   ```bash
   ffmpeg -i video/C1.mp4 [-ss A -t D] -an -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,lut3d=grade.cube,fps=30,format=yuv420p" \
     -c:v libvpx-vp9 -crf 30 -b:v 0 -g 6 -row-mt 1 -cpu-used 4 clips/C1.webm      # -g 6 = fast exact seeking
   ffmpeg -i clips/C1.webm -vf scale=540:960 -c:v libvpx-vp9 -crf 40 -b:v 0 -g 6 -an clips_lo/C1.webm
   ```
   `.gitignore` the big `clips/` and `render.html`.
3. **Voice-over** (saved narrator = Kokoro 70 % bf_emma + 30 % af_kore, en-gb, speed 0.97, style vector in `voices/narrator_female.npy`):
   `pip install kokoro-onnx`; model files `kokoro-v1.0.onnx` + `voices-v1.0.bin` from github.com/thewh1teagle/kokoro-onnx/releases.
   Edit `CLIPS` in `vo.py` (one entry per line with the pause after it), then
   `python3 motion/<slug>/vo.py <model_dir> <out_dir>` and `python3 scripts/words.py <out_dir> motion/<slug>/vo.json`.
   If the user supplies an ElevenLabs MP3 instead: `scripts/vo_el.py` splits it on pauses, speeds it (rubberband, formants kept) and re-paces it.
   Reference pace ≈ 0.2 s gaps between lines, longer only on dramatic beats.
4. **Scenes** in `src/reel.html` — every time is relative to a spoken word: `at("clip", wordIndex, offset)`.
   Helpers: `cover` (image/video Ken Burns), `place` (cut-out/print with shadow), `drop` (document lands), `beam`, `shade`,
   `phrase` (word-by-word mixed-size caption with scrim), `hero` (big date + light leak), `label`, `typed` (typewriter text, `hl` green marker),
   `hand` (handwriting), `arrow` (dashed hand-drawn arrow), `sheet` (aged paper with contents), `engrave` (text carved into stone),
   per-scene `clip: t => ["C1", sourceTime]`, `xin` = dissolve through shadow. Global: grain, vignette, flicker, film damage, gate weave.
   **Never put two phrases at the same height at the same time** — give the second line its own y (this was the one bug the user caught).
5. **Check stills before the full render**:
   ```bash
   python3 motion/<slug>/build.py render
   node motion/render.cjs motion/<slug>/render.html --stills /tmp/st 1.2,3,5.2,…   # one per shot
   python3 scripts/sheet.py /tmp/st /tmp/sheet_ 7      # contact sheets; look at them, fix, repeat
   ```
   Look for: borders showing, text over faces/bright skies, overlapping lines, typed text off the paper, cut-out placement.
6. **Full render** (~15 min for 60 s): `node motion/render.cjs motion/<slug>/render.html out/video.mp4 1`
   (render.cjs launches Chromium with `--allow-file-access-from-files` and awaits `REEL.renderFrame` so clips seek frame-accurately).

## 5 · Sound
- **Music**: a licensed track (Pixabay etc.) cut on its beat grid into pieces: quiet intro under the hook → hard drop to silence on the shock line → loud section re-entering so its strongest onset lands on the climax → the track's own fade under the ending. Beat-track with librosa; crossfade 40–800 ms.
- Breath dips (−8…−12 dB, 0.3 s) right before punchline words; total silence before the big hit.
- **Level** (the user wants music clearly present): music bus ≈ 0.6 of peak, voice-ducking only ~40 %, then **ride the music down only under lines where it masks the voice** so every line is ≥ ~8.5 dB above the music in the 300–4000 Hz band. Normalise the music *before* the ride. Aim: music between lines ~6.5 dB under the voice (same as the reference). Print per-line margins (vs music, vs sfx) and fix the worst.
- **Effects** from earshot (`pip install --no-deps -e earshot` + `soxr pyloudnorm`; `earshot sfx list` / `earshot sfx render ID -o x.wav [--dur --pitch]`; cache renders to disk): whoosh on cuts, low hits on reveals/dates, paper swipes + desk knocks on documents, typing runs, shutters with flashes, latch clicks, riser into the quote, reverse swells into names, sub-sink under the end card. Place each so its **peak** lands on the frame. Plus filtered-noise beds (underwater, sea, wind, engine) and CC0 recordings (Wikimedia downloads work; Freesound blocks bots — don't try to get around it).
- Master: `ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.2:LRA=11 -c:a aac -b:a 192k soundtrack.m4a`.

## 6 · Deliver
```bash
ffmpeg -i video.mp4 -i soundtrack.m4a -map 0:v -map 1:a -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart exports/<slug>-reel.mp4
python3 motion/<slug>/build.py exports/<slug>-reel.html motion/<slug>/soundtrack.m4a     # self-contained, small clips embedded
```
Sample 10 frames of the final MP4 into a contact sheet and look before sending. Send both files, then summarise: what follows the reference, sound choices, measured loudness, and honest caveats (reconstructions, unverified details, file size).

## Files in this skill
- `scripts/render.cjs` — headless-Chromium frame renderer (stills or MP4 via ffmpeg)
- `scripts/words.py` — word onset estimation for VO clips; `scripts/vo_el.py` — re-pace a recorded narration
- `scripts/dsp.py` — synthesis/mix helpers (noise, filters, envelopes, reverb, pan); `scripts/sheet.py` — contact sheets
- `template/reel.html` — the full Operation Mincemeat reel (scene system + player) to copy and rewrite
- `template/prep.py`, `vo.py`, `build.py`, `audio.py` — the matching pipeline (edit the lists at the top)
- `voices/narrator_female.npy` + `voices/speak.py` — the saved female narrator
