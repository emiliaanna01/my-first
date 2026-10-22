# Round House launch film

A ~59 s website launch + "how it works" film for Round House, built from the site itself
(`site/index.html`, the uploaded file) in HyperFrames, with cursor moves, clicks and sound design.

| Path | What it is |
|---|---|
| `film/renders/roundhouse-launch.mp4` | The rendered film (1920×1080, 30 fps, stereo) |
| `film/SPEC.md` | The director's brief: every shot with its frames, colours, eases and sounds |
| `film/REVIEW.md` | What was checked, what was only measured, what is weakest |
| `film/build/build.py` | Generates every scene from the site's own DOM and the sound cues; re-run after edits |
| `film/compositions/s1-s7.html` | The seven scenes (generated) |
| `film/assets/` | Site CSS and fonts (extracted from the upload), the spheres clip, Mixkit music and SFX |
| `dom/`, `cap/` | Snapshots of the site's sections and 2× reference screenshots |

Rebuild and render:
```bash
cd launch/film
python3 build/build.py                         # regenerate scenes + index from the site DOM
npx --prefix ../../motion hyperframes check    # lint, layout, motion, contrast, craft
npx --prefix ../../motion hyperframes preview --background   # Studio preview to edit by hand
npx --prefix ../../motion hyperframes render -q looks -o renders/roundhouse-launch.mp4
```

## The skills you need for website launch videos

Out of the 73 installed skills and 5 plugins, these are the ones that matter for this kind of film.
Everything below is free.

**Core, used for this film**
| Skill | Why |
|---|---|
| `hyperframes` (plugin) | The render contract, launch/explainer structure, story, spec, motion and review rules. Read first. |
| `hyperframes-cli` | `init`, `check`, `snapshot --review`, `audio`, `render`, `preview` |
| `hyperframes-registry` | ~450 ready blocks: cursors (`oversized-cursor`, `press-ripple`, `cursor-zoom-follow`), transitions, kinetic type |
| `media-use` | Music, SFX, voiceover and logos for HyperFrames; says what is free |
| `video-shotcraft` (plugin) | 104 launch-video shot recipes + 149 free Mixkit SFX and 5 music beds (used for this film's sound) |
| `playwright-recording` | Capture real pages, states and interactions (used to capture the site and the WebGL spheres) |
| `gsap-timeline`, `gsap-core` | Sequencing, eases and staggers inside each scene |
| `lottie-motion-design` | Timing/easing/choreography principles for UI motion |
| `orkas-video-craft` | Craft checklist: hooks, pacing, type safe zones, captions, audio mix, pre-publish review |

**Add when the film needs it**
| Skill | When |
|---|---|
| `synthetic-ui-demo` | Rebuild app screens from source and drive them with a scripted cursor (Remotion) |
| `remotion-best-practices`, `remotion-render` | If you prefer Remotion (React) over HyperFrames |
| `remotion-to-hyperframes` | Port Remotion/Motion Canvas work into HyperFrames |
| `figma` (plugin) | Pull frames/logos from Figma (connect via `/mcp`) |
| `ffmpeg` | Cut-downs: 15 s teaser, 9:16 vertical, GIF for Product Hunt |
| `it-reelsmaker` | Vertical Reels/Shorts version with subtitles |
| `elevenlabs` / `heygen-video` | Voiceover / presenter (paid credits; ElevenLabs has a free tier) |
| `skill-inspector` | Check any new skill pack before installing it |

Not needed for launch films: the Manim skills (math explainers), Orkas `stage-*` (needs Orkas' own CLI),
`ltx2`, `qwen-edit`, `runpod`, `ideogram4` (AI generation, paid GPU/API).

## Credits
Music: "House Vibez" by Lily J (Mixkit Stock Music Free License). Sound effects: Mixkit Sound Effects Free License,
via video-shotcraft's bundled library. A few base files in that library have no recorded source URL
(see `assets/audio` ATTRIBUTION in video-shotcraft); the ones used here (`pop.mp3`, `riser-cine.mp3`) should be
re-checked before paid commercial use.
