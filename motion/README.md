# Motion toolkit

Everything from `docs/motion-design-claude-resources.md` that Claude can run, installed into this repo.

```bash
./motion/setup.sh          # npm frameworks, Manim venv, reference repos (idempotent)
FULL=1 ./motion/setup.sh   # also the 470 MB Math-To-Manim examples
```

## What loads by itself (committed in `.claude/`)

**Plugins** (`.claude/settings.json`, project scope)
| Plugin | Source | Gives Claude |
|---|---|---|
| `hyperframes@hyperframes` | heygen-com/hyperframes | HyperFrames skills: `hyperframes`, `-cli`, `-registry` (~450 blocks), `media-use`, `figma`, `slideshow`, `remotion-to-hyperframes` |
| `video-shotcraft@motion-extras` | Vincentwei1021/video-shotcraft (via `motion/marketplace`) | Launch/promo videos: 104 shot recipes, 161 styles, SFX, template |
| `motion-design-studio@frankx-motion` | frankxai/awesome-motion-design-agent-skills | `motion-director`, `web-motion-auditor`, `remotion-video-agent`, `generative-media-director`, `site-motion-excellence-director` |
| `manim-skill@manim-skill` | Yusuke710/manim-skill | Plan → code → render → iterate Manim videos |
| `figma@claude-plugins-official` | Anthropic marketplace | Figma MCP + Figma skills (sign in via `/mcp`) |

**Skills** (`.claude/skills/`, copied from their repos on 2026-10-22)
| From | Skills |
|---|---|
| remotion-dev/skills (official) | `remotion-best-practices` (router), `-create`, `-render`, `-studio`, `-captions`, `-markup`, `-maps`, `-multimedia`, `-interactivity`, `-saas`, `-docs`, `-upgrade` |
| LottieFiles/motion-design-skill | `lottie-motion-design` |
| haidrrrry/claude-remotion-skill | `remotion-motion-graphics` |
| wshuyi/remotion-video-skill | `remotion-video` (Edge-TTS voiceover) |
| digitalsamba/claude-code-video-toolkit | `remotion`, `ffmpeg`, `playwright-recording`, `synthetic-ui-demo`, `moviepy`, `elevenlabs`, `acestep`, `ltx2`, `qwen-edit`, `ideogram4`, `runpod` |
| adithya-s-k/manim_skill | `manim-composer`, `manimce-best-practices`, `manimgl-best-practices` |
| HarleyCoops/Math-To-Manim | `math-to-manim` |
| Orkas-AI/Orkas-VideoStudio | `orkas-*` (14 skills; the pipeline expects Orkas' `ovs` CLI) |
| heygen-com/skills | `heygen-avatar`, `heygen-video`, `heygen-translate` (need the HeyGen MCP or `HEYGEN_API_KEY`) |
| dha-aa/ae-motion | `run-ae-motion` |
| NVIDIA/SkillSpector | `skill-inspector`: review a skill pack before installing it |

Not copied: Orkas' and digitalsamba's `frontend-design` (one already exists) and digitalsamba's `remotion-official`
(same as `remotion-best-practices`). HeyGen's own marketplace file fails validation, so its skills were copied instead.
GSAP skills (`gsap-*`) were already here.

## What `setup.sh` installs
- **npm (`motion/node_modules`):** `hyperframes` CLI, `remotion` + `@remotion/cli`, Motion Canvas, Revideo, GSAP, Lottie (`lottie-web`, dotLottie), Three.js, `skills` CLI. Run with `npx --prefix motion <cli>`.
- **Python (`~/.venvs/manim`):** Manim Community + `mcp`. Run `~/.venvs/manim/bin/manim -ql scene.py Scene`.
- **Reference repos (`motion/vendor/`, gitignored):** Claude-Code-Video-Toolkit, hyperframes-prompts, claude-code-video-toolkit, awesome-motion-design-agent-skills, SkillSpector, ae-motion, blender-mcp, manim-mcp-server, motion-canvas, revideo.

## MCP connectors
See `motion/MCP.md`. Figma is installed. HeyGen, Higgsfield and ElevenLabs are one command each for you to run.
After Effects and Blender are desktop-only.

## Notes for this cloud environment
- `cdn.jsdelivr.net` is blocked here, so HyperFrames templates that load GSAP from the CDN fail to render. Copy
  `motion/node_modules/gsap/dist/gsap.min.js` next to `index.html` and point the `<script src>` at it (tested:
  the blank example then renders 1920×1080).
- Manim needs `libpango1.0-dev` (setup installs it); LaTeX for `MathTex` is not installed.
- Remotion needs a paid company license above its small-team threshold.
