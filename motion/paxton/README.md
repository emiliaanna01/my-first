# The leaf and the Crystal Palace (≈66 s historical short)

A true story (Joseph Paxton, the *Victoria regia* leaf and the Crystal Palace, 1849–51), told as an animated 1850s periodical: engraved plates, albumen photographs, Victorian silhouettes, teal label strips and paper texture.

| Path | What it does |
| --- | --- |
| `vo.py` / `vo.json` | Voice-over clips (Kokoro TTS) and their timings, which the on-screen text keys off |
| `studio/studio.html` | 3D period studio (three.js): lily leaves, glasshouse, lily tank, meeting table, Hyde Park, iron frame, gallery, Crystal Palace, glass towers |
| `studio/shoot.cjs` | Renders each shot twice: a lit pass and a material-id pass (`studio/raw/`) |
| `studio/post.py` | Turns renders into engravings (hatching, contours, hand-tinted teal glass and walnut wood) or albumen prints (`studio/cut/`) |
| `src/paxton-reel.html` | The film: scenes, silhouette rig, teal strips, engraved water, blotting-paper sketch, crossfades |
| `build.py` | Inlines fonts, plates, timings (and soundtrack) into one self-contained HTML |
| `audio.py` | Documentary score, period sound design and voice mix; reports voice clarity |

## Sources for the story

- Paxton first flowered *Victoria regia* in England at Chatsworth in November 1849; the *Illustrated London News* showed his daughter Annie standing on a leaf.
- The Great Exhibition Building Committee received 245 designs in 1850 and accepted none of them.
- Paxton's first sketch was drawn on blotting paper during a Midland Railway meeting in Derby on 11 June 1850 (now held by the V&A).
- George Airy warned that the building could fail, and Royal Sappers and Miners load-tested a section of the galleries.
- The building opened on 1 May 1851, with about 293,000 panes of glass, and had more than six million visitors.
