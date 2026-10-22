# Motion Design & Video Launch with Claude: Resource List

The tools, skills, connectors (MCP), GitHub repos and other sources that YouTube motion-design videos
recommend, filtered to what **Claude can use**: Claude Code skills and plugins, MCP servers, Claude Design,
and the free apps Claude can drive or hand files to.

Compiled 2026-10-22 from about 110 YouTube videos (vidIQ search: "Claude Code Remotion", "motion design tools
2026", "product launch video", "free motion design software", "free After Effects plugins", "HyperFrames"),
plus the repos and pages those videos link to. YouTube has far more motion-design videos than any one list can
cover, so this is a representative sample of current (2025-2026) videos ranked by reach. It is not every video
on YouTube.

**Installed in this repo:** see `motion/README.md` (skills, plugins, frameworks) and `motion/MCP.md` (connectors).

**Legend:** 🆓 free / open source · 💲 freemium (free tier or trial) · 💰 paid · ⭐ most recommended across videos

---

## 1. The core Claude motion stack (start here)

| Tool | Cost | What it does with Claude | Install / link |
|---|---|---|---|
| ⭐ **Remotion** + official agent skill | 🆓 for individuals and small teams (companies may need a license) | React-based video framework. Claude writes the scenes as React components and Remotion renders the MP4. This is the stack nearly every "Claude motion graphics" video uses. | `npx create-video@latest`, then `npx skills add remotion-dev/skills` · https://www.remotion.dev · https://github.com/remotion-dev/skills |
| ⭐ **HyperFrames** (HeyGen) | 🆓 Apache-2.0 | HTML/CSS/GSAP to deterministic MP4. Built for agents, ships ~21 skills, and includes a `/product-launch-video` workflow. Videos call it the simpler Remotion alternative. | https://github.com/heygen-com/hyperframes · https://hyperframes.heygen.com |
| ⭐ **Claude Design** | Included with a Claude plan | Prompt-to-animation with no code: design system, templates, screenshot recreation, transcript/SRT-synced graphics, MP4 export. | https://claude.ai/design |
| **GSAP skills** (official) | 🆓 MIT | Teach Claude timelines, ScrollTrigger and React patterns. Used inside both Remotion and HyperFrames. | `npx skills add greensock/gsap-skills` (already installed here as `gsap-*`) |
| **Remotion "CLAUDE.md" gist** (Thariq S.) | 🆓 | The original Remotion instructions file that several tutorials paste into Claude Code. | https://gist.github.com/ThariqS/3d446e7c7aa9eb94f468194deb73028f |
| **Remotion prompt gallery** | 🆓 | Copy-paste prompts and examples. | https://www.remotion.dev/prompts |

## 2. Claude skills & plugins for motion / video (GitHub)

| Repo | Cost | Why it's useful | Install |
|---|---|---|---|
| ⭐ **Vincentwei1021/video-shotcraft** | 🆓 Apache-2.0 | Turns Claude Code into a product-promo studio: 104+ shot recipe cards, 161 styles/motion previews, beat-sync, 149 SFX, page-capture scripts. Built for **launch videos**. | `npx skills add Vincentwei1021/video-shotcraft` |
| ⭐ **frankxai/awesome-motion-design-agent-skills** | 🆓 CC0 | Curated index of GSAP, Motion, Remotion, Lottie and Rive skills, plus 5 own skills (e.g. `web-motion-auditor`). Installs as a Claude Code plugin or a Claude.ai skill zip. | `/plugin marketplace add frankxai/awesome-motion-design-agent-skills` |
| **LottieFiles/motion-design-skill** | 🆓 MIT | Motion-design principles (easing, timing, choreography) for Lottie/dotLottie output. | `npx skills add LottieFiles/motion-design-skill` |
| **digitalsamba/claude-code-video-toolkit** | 🆓 | Full project template: Remotion + ElevenLabs + FFmpeg + Playwright skills, `/video`, `/record-demo`, `/brand` commands. | https://github.com/digitalsamba/claude-code-video-toolkit |
| **wilwaldon/Claude-Code-Video-Toolkit** | 🆓 | Curated list of video skills and MCP servers (Remotion, Manim, screen recording, clipping, FFmpeg). | https://github.com/wilwaldon/Claude-Code-Video-Toolkit |
| **product-launch-motion** | 🆓 MIT | Claude Code skill: website URL to a 60 fps launch video with music, SFX and motion blur (needs Playwright and ffmpeg). | Listed in the frankxai index |
| **haidrrrry/claude-remotion-skill** | 🆓 | Springs, staggered choreography, color grade, film grain, Ken Burns, word-synced captions, sound design. | https://github.com/haidrrrry/claude-remotion-skill |
| **wshuyi/remotion-video-skill** | 🆓 | Remotion skill with free Edge-TTS voiceover and scene-based auto timing. | `cp -r remotion-video ~/.claude/skills/` |
| **heygen-com/skills** | 💲 (HeyGen API for avatars) | HeyGen for Agents: avatar + script + video from Claude Code. | https://github.com/heygen-com/skills |
| **NousResearch/hermes-agent** HyperFrames skill | 🆓 | HyperFrames skill for the Hermes agent. | `optional-skills/creative/hyperframes` |
| **tonbistudio/hyperframes-prompts** | 🆓 | Prompts and research doc from a 5-build HyperFrames test (deck to video, website to promo, repo to explainer). | https://github.com/tonbistudio/hyperframes-prompts |
| **Yusuke710/manim-skill** | 🆓 | Manim (3Blue1Brown-style math/diagram animation) skill. | `/plugin marketplace add Yusuke710/manim-skill` |
| **HarleyCoops/Math-To-Manim** | 🆓 | 55+ Manim examples plus a Claude plugin. | `claude --plugin-dir ./Math-To-Manim/skill` |
| **Orkas-AI/Orkas-VideoStudio** | 🆓 MIT | 14-skill video pack driven by `plan.json`. | see repo |
| **vercel-labs/skills** (skills CLI) | 🆓 MIT | The `npx skills add …` installer most of the above use. | https://github.com/vercel-labs/skills |
| **NVIDIA/SkillSpector** | 🆓 Apache-2.0 | Scan skill packs before installing them. | see repo |

> **Already in this repo/session:** `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-plugins`,
> `gsap-react`, `it-reelsmaker` (vertical Reels/Shorts with Remotion), `frontend-design`, `impeccable`,
> `canvas-design`, `theme-factory`. See `web-design/README.md`.

## 3. Free MCP connectors Claude can drive

| Connector | Cost | What Claude can do | Link |
|---|---|---|---|
| ⭐ **AE Motion MCP** (After Effects) | 🆓 MIT (needs After Effects) | 77 tools: create comps, layers, keyframes, expressions, masks, 3D camera, audio sync, render in a **live AE project**. | https://github.com/dha-aa/ae-motion |
| ⭐ **Blender MCP** (ahujasid) | 🆓 | Control Blender: build scenes, materials, animation, render. | https://github.com/ahujasid/blender-mcp |
| **Blender MCP** (6xvl) | 🆓 | ~270 tools: model, rig, animate, UV, render, export. | https://github.com/6xvl/blender-mcp |
| **Blender MCP read-only** (MakerSully) | 🆓 | Safe inspection of scenes and animations, no edits. | https://github.com/MakerSully/blender-mcp |
| **Manim MCP server** | 🆓 | Claude sends scene code and gets an MP4 back. | via the wilwaldon toolkit |
| **Figma MCP** | 💲 (free Figma plan works) | Pull frames/SVGs for UI animation (videos export UI from Figma as SVG, then animate in Remotion). | Figma Dev Mode MCP |
| **Playwright MCP** | 🆓 | Capture real product pages/screens for launch videos. | already in `.mcp.json` |
| **Context7** | 🆓 | Current Remotion/GSAP/Three.js docs inside Claude. | already connected |
| **21st.dev Magic** | 💲 | UI components plus a video-block editor (`video_*` tools). | already connected |
| **vidIQ for Claude** | 💲 | YouTube research, titles, thumbnails, upload, motion graphics, voiceover. Used to research this list. | already connected |
| **Higgsfield MCP** | 💲 (free credits) | Claude to Seedance/"Vibe Motion" AI video. Very common in 2026 videos, but credit-based. | https://higgsfield.ai/mcp |
| **ElevenLabs MCP** | 💲 (free tier) | Voiceover / SFX for explainers. | ElevenLabs |
| **Canva connector** | 💲 | Social cut-downs and thumbnails. (Failed to connect in this session.) | Claude connectors |

## 4. Free / freemium motion design apps (from the videos)

**Code-based (Claude writes the code)**
- 🆓 **Remotion**, 🆓 **HyperFrames**: see section 1
- 🆓 **Motion Canvas**: TypeScript animation with an editor, MIT. https://github.com/motion-canvas/motion-canvas
- 🆓 **Revideo**: Motion Canvas fork aimed at rendering via API
- 🆓 **Manim Community**: math/diagram animation in Python
- 🆓 **Three.js**, **Lottie (lottie-web / dotLottie)**: used inside Remotion ("Remotion + GSAP / Three.js / Lottie" breakdown by Andy Lo)
- 🆓 **Theatre.js**: keyframe editor for web/Three.js scenes
- 🆓 **FFmpeg**: final encode, cut-downs, GIFs (already set up in this repo)

**Visual tools**
- 💲 **Figma Motion**: timeline, presets, keyframes, easing, "Animate with Agents" (official 8-min tutorial; TD Sunshine deep dive)
- 💲 **Jitter**: Figma-to-motion. A free 1-hour SaaS explainer masterclass uses only Figma + Jitter.
- 🆓 **Blender**: 3D product shots and logo reveals; pairs with Blender MCP
- 💲 **Rive**: interactive/state-machine animation
- 💲 **Spline**: web 3D
- 💲 **Lottie Creator** (LottieFiles)
- 🆓 **Cavalry** (free tier), 🆓 **Synfig Studio**, 🆓 **Natron** (compositing), 🆓 **Kdenlive**, 🆓 **DaVinci Resolve** (Fusion for motion)
- 💰 **Apple Motion**, 💰 **After Effects 2026** (new native 3D, SBSAR materials, shadows)
- 💲 Mobile: **Alight Motion**, **CapCut**, **Node Video**
- 💲 AI prompt-to-motion: **Raylight** (connects to Claude), **Hera**, **ChatCut**, **Motionfly** (Product Hunt videos), **Luma Agents**

## 5. Free After Effects plugins & scripts (for the AE Motion MCP route)

Recommended in Gavin Herman's "26 AE Plugins 2026", Plainly's "12 Free AE Plugins", After Effects Basics, Alyousfi and Jake In Motion:

| Plugin / script | Use | Link |
|---|---|---|
| Motion Tools Classic | Anchor, align, ease, shift layers | https://motiondesign.school/products/motion-tools-classic |
| Code Runner 2 | One-button scripts, expressions, eases | Jake In Motion (jkinmo.com) |
| Void, BeatGrid, Soupcan | Null/guide, beat markers, utilities | https://battleaxe.co |
| FX Console | Quick effect search | https://www.videocopilot.net |
| VC Orb, VC Reflect, Color Vibrance | 3D spheres, reflections, color | https://www.videocopilot.net/products/ae22/ |
| EaseCopy | Copy easing between keyframes | https://aescripts.com/easecopy/ |
| Dojo Shifter 2 | Offset layers in time | https://creativedojo.net |
| Copy Pasta | Fast copy/paste of properties | https://www.pluginplay.app |
| TrimPack | Trim-path animation controls | https://olaolayuan.gumroad.com/l/trimpack |
| Presetify | Text animation presets | https://kuldeepmp4.gumroad.com/l/presetify |
| Odometer | Number count-ups | https://aescripts.com/odometer/ |
| 3D Extruder | Fake depth on text/shapes | motionnations.com |
| Animation Composer 3 | Free preset library | https://misterhorse.com/animation-composer |
| EDITKIT (EaseIt / AlignIt / QuickIt) | Easing, alignment, loops | https://zickfx.com/editkit |
| AEViewer | Asset browser | aescripts.com |
| Plainly Expressions Library | 150+ copy-paste expressions, text rigs | https://www.plainlyvideos.com/after-effects-expressions-library |

## 6. Free assets (music, SFX, footage, fonts, 3D, Lottie)

From Ben Marriott's "47 Free Resources for Motion Designers" and the launch-video tutorials:

- **Audio:** Mixkit (music + SFX, free commercial license, also bundled in video-shotcraft), Uppbeat (free with license codes), Adobe Audition SFX library, YouTube Audio Library, Pixabay Music
- **Footage / images:** Pexels, Unsplash, Pixabay, NASA, Library of Congress free-to-use
- **Lottie:** https://lottiefiles.com/free-animations
- **3D models:** CGTrader free, Free3D, 3D Sky, Dimensiva, Poly Haven; Adobe Substance community materials (free SBSAR)
- **Freebies/tools:** Battle Axe freebies, Ordinary Folk "Play", Happy Toolbox, Effectatron
- **UI to animate:** Figma Community files (dashboards, app kits), Mobbin, Dribbble for references
- **Inspiration:** Ben Marriott "Best Motion Design of 2026", Pinterest (screenshot reference → Claude recreates the style), Instagram motion accounts, Vimeo staff picks

## 7. Product launch video playbook (what the videos agree on)

**Workflow with Claude (from Sanji Nai-Chien, kaye.creatives, Esther, Zinho Automates, Snapper AI):**
1. **Storyboard first.** Write a scene-by-scene shot list. Sanji's test showed the storyboard decides whether the AI output works.
2. **Brand system:** fonts, colors and logo in a `DESIGN.md` or Claude Design system; export UI from Figma as **SVG**.
3. **Capture real UI:** Playwright screenshots/recordings of the product (video-shotcraft and product-launch-motion automate this).
4. **Build:** Remotion or HyperFrames at 1920×1080 / 60 fps (plus a 1080×1920 cut for Reels/Shorts with `it-reelsmaker`).
5. **Iterate with one-sentence fixes:** preview in Remotion Studio or HyperFrames preview before rendering.
6. **Sound:** beat-synced cuts plus SFX (whooshes and clicks on every UI action). Videos call this the biggest "pro" signal.
7. **Render:** export MP4 (and transparent ProRes/WebM for overlays to drop into Resolve, Premiere or Final Cut).

**Launch-video rules of thumb:**
- Hook in the first 3–5 s; the video must **work without sound** (captions/on-screen text).
- Product Hunt gallery video: **45–60 s**; gallery images 1270×760; logo 240×240; tagline ≤ 60 chars.
- Make cut-downs: 6–15 s teaser loop / GIF, 30 s ad, 60 s full, 9:16 vertical.
- Popular styles: SaaS UI animation (Zelios, Motion Swell, PING Studio examples), Apple-style clean product motion, Vox-style explainers, 3D product ad.
- **Distribution:** Product Hunt (launch checklists: getlaunchlist.com, motionfly.co, Product Hunt's own 200-tip checklist), X/Twitter, LinkedIn, Indie Hackers, relevant Discord/Slack, YouTube Shorts, Instagram Reels, TikTok. Warm up 2–4 weeks beforehand and keep a 100+ waitlist.

## 8. Key YouTube videos (sample, by topic)

**Claude + Remotion**
- Zinho Automates: *Create Motion Graphics with Claude Code + Remotion* (`MAhkbZHcbLA`); *Vox-style* (`LiQPU7_5v68`); *FREE Motion Graphics with Claude + JavaScript* (`RSe268YFglA`)
- Roboverse: *Claude Code Can Now Automate Your Videos (Remotion + Opus 5.5)* (`6_rCyryA6hg`)
- The David Shutt: *Claude & DaVinci Resolve 20* (`IZflKWRMhNI`)
- Pouya Eti: *Claude Code + Remotion = FREE Motion Graphics (No Subscription)* (`kXmY6yQa5q4`)
- Andy Lo: *Everything Claude Code + Remotion Can Do (GSAP, Three.js, Lottie)* (`OX80FZjHJ7o`); *Professional Motion Graphics, no editing* (`xAUifztpib8`)
- Snapper AI: *Remotion Agent Skill Tutorial* (`EwKCAgt4aKI`)
- Artificial Quotient: *Remotion beginner tutorial* (`kuDzysXdUsY`)
- RandomAI: *Opus 5.5 Vox-Style Motion Graphics* (`uIHJvUVaB34`)
- Esther: *Claude Code + Remotion, No After Effects (SaaS UI animation)* (`5lCoz9QSxhY`)
- Mike: *Claude Code Can Make Videos Now* (`sWQMAl8uf90`)

**Claude Design / HyperFrames**
- Kevin Stratvert: *How to Create Motion Graphics with Claude AI* (`ZE9URNHaP5M`)
- Paul J Lipsky: *Stunning Motion Graphics With Claude Design* (`lxmrK4RCWQQ`)
- Sanji Nai-Chien: *Motion Graphics Without Plugins: The New Claude Method* (`9XvKyoz6Nmo`)
- CharliMarieTV: *Creative Director tries Claude Design for a real product launch* (`LpLs1QXdb2g`)
- Selling With Nas: *FREE AI Videos with Claude + Hyperframes* (`3sEuuAk-lYc`)
- RoboNuggets: *Hyperframes V2* (`4E2I_NJkzhI`)
- Tonbi's AI Garage: *Hermes Agent + HyperFrames* (`1IsskexiCSw`)
- Productive Dude: *Claude + HeyGen automated videos* (`GnoJaaIHXWU`)

**Launch videos**
- Sanji Nai-Chien: *$880/Day Motion Graphics Skill*: a full SaaS launch video with storyboard, Figma SVG and 60 fps (`D5qpBbEWTxo`)
- kaye.creatives: *Insane Motion Graphics with Opus 5.5*: a launch intro from scratch (`AsvN_feasyY`)
- Higgsfield AI: *Claude Opus 5.5 + Higgsfield*: launch video, 3D ad, AE/Blender export (`5HYYXYYCrL4`)
- Ahmed Alsayad: *SaaS Motion Graphics in 60 Minutes (Figma + Jitter, free)* (`pbFpqYPbg1o`)
- Joseph: *How to Edit Viral SaaS Animations 2026* (`zWbLfFA9l8s`)
- NaughtyyJuan: *Ultimate Apple Style Animation Guide* (`5j4HmfgPCDI`)
- Zakaria HQ: *Apple Style UI Ad in After Effects*, 1-hour masterclass (`Zfx5oL3pPmk`)
- Examples: Zelios (`WA9TNC6r3hU`, `SgmuplXU2iY`, `aSte18D2_YE`), Motion Swell (`y0DMsRT2U1U`), PING Studio (`o1DLUZm3eqg`)

**Craft & industry**
- Somrat Dutta: *If You ONLY Watch One Motion Design Video…* (5-stage roadmap) (`CF2xAa8Wujg`)
- Ben Marriott: *Best Motion Design of 2026* (`ylXeuDp_8XM`); *47 Free Resources* (`7ocRNV7hLIQ`)
- Jake In Motion: *Higgsfield AI Motion Designer: I Tested the Claims* (`QLZNiwaKqWg`), a critical take
- School of Motion: *The Uncomfortable Truth about AI and Motion Design* (`HhhMgtD2J_0`)
- Figma: *Learn Figma Motion in 8 minutes* (`wpGI6BmhbJU`)
- Justin Serran: *After Effects 2026 3D Workflow* (`lrnsxp-lwac`)

Watch any of these at `https://www.youtube.com/watch?v=<id>`.

---

### Recommended free Claude setup (one-time)
```bash
npx create-video@latest                        # Remotion project
npx skills add remotion-dev/skills             # official Remotion skill
npx skills add greensock/gsap-skills           # GSAP
npx skills add Vincentwei1021/video-shotcraft  # launch/promo shot recipes
npx skills add LottieFiles/motion-design-skill # motion principles
# optional: HyperFrames (github.com/heygen-com/hyperframes), Blender MCP, AE Motion MCP
```
Caveats: Remotion needs a paid company license above its small-team threshold. Higgsfield, HeyGen, ElevenLabs
and Canva are credit/freemium. Star counts and features come from the linked pages as of October 2026.
Check each repo before installing it (SkillSpector can help).
