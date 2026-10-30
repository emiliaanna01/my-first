# Vox-style paper-collage shorts: the playbook

This is how every film in this kit was made: *The Great Molasses Flood*, *The Biggest World Cup Ever*,
*The One-Dollar Camera* and *Caught by the Taxman*. Follow it in order. Same style, different content every time.

Output: a 35–48 s vertical documentary (1080×1920, 30 fps, −14 LUFS) built from real archive photos, halftone
paper cut-outs, ransom-note numbers, typed documents, maps, a narrator, captions, a custom score and foley.
Nothing is rented: no video model, no image model, no credits.

---

## 0. What is in the kit

| Path | What it is |
|---|---|
| `skill/papercut/` | The engine and its `SKILL.md` (install as a Claude Code skill) |
| `skill/papercut/engine/looks.py` | Six art directions (classic, noir, riso, blueprint, pastel, tabloid) |
| `skill/papercut/engine/fetch.py` | Rate-limit-proof Wikimedia photo fetcher with a shared cache |
| `templates/story_template.json` | A blank film, every beat kind shown once |
| `templates/sfx_design_template.py` | Score + foley generator to copy into each film |
| `films/*/` | The four finished films: `story.json`, `sfx_design.py`, `CREDITS.txt` |
| `NEW_CHAT_PROMPT.md` | Paste this into a new chat to start |

## 1. Install (once per machine or container)

Needs Python 3.10+, Node 18+, FFmpeg (with rubberband), curl, git.

```bash
mkdir -p .claude/skills && cp -r skill/papercut .claude/skills/papercut
cd .claude/skills/papercut && ./setup.sh
```

`setup.sh` makes `.venv`, installs the Python libraries, downloads the Kokoro voice model (~330 MB) to
`~/.papercut/kokoro`, and fetches the map data and the animation library into `engine/data`. If jsDelivr is
blocked it takes the same files from the npm registry automatically.

Network the pipeline uses: `commons.wikimedia.org` and `upload.wikimedia.org` (photos), `github.com` (models),
`registry.npmjs.org`, `pypi.org`. In a locked-down cloud environment add the two Wikimedia hosts to the allowed
domains. Hugging Face is optional (exact caption timing); without it captions are spaced evenly per line, which is
close enough for 1–3 s lines.

Paths below: `P=.claude/skills/papercut`, `PY=$P/.venv/bin/python`.

## 2. The workflow for one film

Make one folder per film (`films/<slug>/`) and run every command from inside it.

### Step 1 — Pick the story and the angle
- A true story with a turn in it: a reversal, an absurd cause, a hidden person, a number nobody expects.
- Check that photos exist **before** committing: run `search` (step 3) on the main person/object first.
- Decide the five variety choices now (section 3): look, hook form, story shape, scene mix, ending.

### Step 2 — Facts
- Every date, name and number needs **two independent sources**. Search; don't trust one page.
- Where sources disagree, **write around it**: "around 1914", "about seven and a half years", "more than $600,000",
  or leave the detail out entirely. Never invent a quote: use the documented wording or none.
- Watch for fake/prediction pages on recent events; ignore an outlier that contradicts everything else.
- Keep the source URLs; they go in the final message and the video description.

### Step 3 — Photos
```bash
$PY $P/engine/papercut.py search "Al Capone 1930" sheet_capone.png              # public domain / CC0
$PY $P/engine/papercut.py search "Ferran Torres" sheet_ft.png --allow-by          # also CC BY / BY-SA (credit!)
```
Search several angles (the person, the place, the object, the newspaper of the day, adverts, documents).
Open the contact sheets and **pick by looking**, not by title. Aim for **4–7 photos**.

Then download them before building, in the background:
```bash
$PY $P/engine/papercut.py fetch story.json --wait 2400
```
`fetch` waits as long as Wikimedia asks (it reads Retry-After), keeps going past a slow photo, caches every
download in `~/.papercut/cache`, and prints what is still missing. Run it again later to resume. If a photo will
not come, the person can save it as `photos/<key>.jpg` and it is used as-is. Only then replace that beat with a
type-only beat (number, document, timeline) that stays factual.

Photo rules learned the hard way:
- People and objects: `"cut": true` (background removed). Face well lit; crop tight with `"crop": [l,t,r,b]`.
- Scenes, rooms, ships, buildings: `"cut": false` (a taped print).
- Documents, newspapers, ads, maps: `"cut": false, "dots": false`.
- **Dim or busy photos: `"dots": false`** plus `"contrast": 1.1–1.25`. Halftone turns them into mush.
- Never caption a photo as something it is not. If no true photo exists, use another beat kind.

### Step 4 — Script (`story.json`)
Copy `templates/story_template.json`. Rules:
- **10–12 beats, 35–47 s.** One sentence (or half of one) per beat, one visual idea per beat.
- **Beat 1 is a spoken hook** in the viewer's voice over the opening picture. Rotate the form:
  "What if I told you…", "Do you know what happened…", "How did a…", or a bold claim.
- Ground it fast in beat 2 (a date and a place, a map, a number).
- **The last beat pays off the hook** (a callback, not a summary).
- Calm documentary sentences. Write amounts the way they should be spoken ("two point three million gallons");
  years can stay as digits ("1931"), the voice reads them correctly. Split names it mispronounces ("Round House").
- Labels 1–3 words, uppercase; tags are short typed captions; `stamp_on` names the spoken word the stamp lands on.
- Numbers that would wrap badly as ransom letters: shorten (`"2.3 MILLION"`, `"$600K+"`, `"250,000"`).

### Step 5 — Build, look, fix
```bash
$PY $P/engine/papercut.py make story.json          # photos → cut-outs, voice, animation, sound
```
1. Open `pieces.jpg`: every cut-out on one sheet. Mush → `dots: false`; bad cut → re-crop or `cut: false`.
2. Read the beat end times and snapshot every beat:
   ```bash
   T=$(python3 -c "import json;t=json.load(open('project/assets/audio/timing.json'))['timing'];print(','.join(f\"{x['start']+x['dur']-.15:.1f}\" for x in t))")
   $PY $P/engine/papercut.py snap story.json $T            # → snaps/contact-sheet-*.jpg
   ```
3. Check every frame (section 5) and fix `story.json`; `make` again (voice and cut-outs are cached).
4. If the voice runs over ~47 s, tighten two or three lines without dropping facts.

### Step 6 — Sound design (every film gets its own)
Copy `templates/sfx_design.py` into the film folder and write a score + foley that fits the subject:
- **Score**: replace papercut's tense bed with something made for this story (music-box waltz for the camera,
  noir jazz for Capone, stadium crowd for football, papercut's bed + effects for the disaster).
- **Foley on words**: each effect is placed on the spoken word it belongs to, using the word times in
  `project/assets/audio/timing.json` (`w(beat, "word")`). Examples used: tank groan + burst, syrup wave,
  steel creak, newspaper rustle, gavel, coins, shutter + film wind, flashbulb, cell-door clang, whistle,
  goal roar, clapping. Sparse: 5–10 moments per film, not one per beat.
- Then:
  ```bash
  $PY sfx_design.py                                  # writes score.wav (float, not normalised)
  # in story.json: "music": "score.wav", "music_gain": 0.22–0.3, "sfx_gain": 0.38–0.45
  $PY $P/engine/papercut.py make story.json
  ```
- Check levels: speech alone ≈ −16 dB RMS; effect moments 1–3 dB louder at most (the measuring snippet is in the
  template). The voice must never be covered.

### Step 7 — Render and deliver
```bash
$PY $P/engine/papercut.py make story.json --render     # <slug>.mp4 (large master)
f=<slug>.mp4
M=$(ffmpeg -hide_banner -i $f -af loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
I=$(echo "$M" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -y -i $f -c:v libx264 -crf 22 -preset slow -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.5:LRA=9:$I:linear=true" -ar 48000 -c:a aac -b:a 192k -movflags +faststart <slug>_social.mp4
```
The two-pass loudnorm matters: the renderer changes loudness, so always measure the rendered file and correct it.
Deliver `<slug>_social.mp4` (25–45 MB), the photo credits from `CREDITS.txt` (they go in the description), and
the list of sources. Say plainly what was left out or substituted and why.

## 3. Make every film different (the style stays, the film changes)

Before writing, choose, and never repeat the previous film's choice:

1. **Look** (`"look"` in story.json):

   | look | stock | suits | used for |
   |---|---|---|---|
   | `classic` | mustard, red, teal, navy, kraft | mid-century history | Molasses Flood, World Cup |
   | `noir` | black, greys, cream, one red | crime, scandal, disaster | Capone |
   | `riso` | fluoro pink, blue, yellow on off-white | culture, music, youth, sport | – |
   | `blueprint` | navies, blues, safety orange | science, tech, space | – |
   | `pastel` | sage, blush, butter, terracotta; serif labels | gentle stories, objects, places | Brownie |
   | `tabloid` | black, white, yellow, red | sport, records, money | – |

2. **Hook form**: what if I told you / do you know what happened / how did / a bold claim.
3. **Shape**: chronological, countdown, then-vs-now, myth-vs-fact, one object followed through time, a chase.
4. **Scene mix**: at least five beat kinds, at least four photo beats, no kind more than three times.
   `gallery` when several photos tell one beat; `bars` for any comparison of amounts; `duo` for two people.
5. **Voice**: `af_heart` (warm US female, best quality, the default the person liked), `bf_emma` (British female,
   used for the Brownie film). Male voices exist (`am_michael`, `bm_lewis`, `bm_george`) but are lower quality.
   Use `"lang": "en-gb"` with British voices.
6. **Score**: a new one per film (section 2, step 6).
7. **Ending**: the hook's payoff; a twist, callback, number or quote, not always a timeline to TODAY.

## 4. Beat kinds (story.json reference)

Every beat: `say`, `kind`, optional `bg`, `scraps`, `burst` (+`burst_color`), `transition`, `label`, `tag`,
`stamp` (+`stamp_on`, `stamp_size`).

| kind | fields | use for |
|---|---|---|
| `hero` | `hero`, `circle` | a person or object, big cut-out |
| `photo` | `photo` | a scene, newspaper, document photo (taped print) |
| `duo` | `left`, `right`, `string` | two people, a connection (red string) |
| `gallery` | `photos` (2–4), `captions` | several photos at once, dealt as taped prints |
| `number` | `number`, `sub`, `hero` | a date, an amount, a count, a verdict (ransom letters) |
| `bars` | `bars: [[name, value]…]`, `values`, `unit`, `active` | comparing amounts (torn-paper bar chart) |
| `document` | `head`, `lines`, `redact`, `mark` | typed records, rulings, lists, ledgers |
| `timeline` | `dates`, `active`, `hero` | a span of years, before/after |
| `quote` | `quote`, `by`, `hero` | a real, sourced quote |
| `map` | `map: {country \| highlight[], pin: [lon, lat], place, sea}` | where it happened |

`bg` names (mustard, red, teal, navy, newsprint, kraft, cream, pink, olive, ink) are the look's stock, not fixed
colours. Leave `bg` out to use the look's own order.

## 5. Checking frames: the pitfalls already met

- Photo turned to noise → `dots: false`, raise `contrast`.
- Number wraps as "2,300" / ",000" → shorten the number.
- Stamp invisible: on a grey map, or the same colour as the card → drop it or move it (the engine already switches
  to cream ink on an accent-coloured card, and keeps accent ink on document paper).
- Marker `circle` lands off the face on cut-outs → remove it.
- A snapshot that looks blank is often a paper wipe mid-transition: snapshot a little earlier.
- Captions sit low; nothing important should sit under them.
- A front page whose headline contradicts the narration (early casualty counts) → don't use it next to the fact.
- Pastel and riso: check every key element stands out from the card behind it.
- The renderer's `check` prints contrast warnings for small decorative text; look at the frames, not the count.

## 6. Engine changes made in this project (already in `skill/papercut`)

- `looks.py`: six looks; `bg`, ransom tiles, stamps, caption highlight, label font and transition rhythm per look.
- New beat kinds `gallery` and `bars`.
- `fetch.py`: honours Retry-After, batched lookups, shared cache, upload.wikimedia.org fallback, standard-width
  previews, `papercut.py fetch` command, `photos/` drop folder.
- Stamps on documents land on the paper; active timeline date stays visible on an accent card.
- `SKILL.md`: hook rule, photo workflow, make-every-film-different checklist.
