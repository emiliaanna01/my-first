# Web design toolkit

Everything from the *Claude Code Website Tools Guide* that can live in a repo, installed and
ready: design skills, UI/UX data, animation skills, quality audits, browser/MCP tooling, and the
inspiration and component sources to feed them.

```
.claude/skills/        25 skills Claude loads automatically in this repo (see table below)
.mcp.json              MCP servers: Context7, Playwright, Chrome DevTools, shadcn
web-design/
  README.md            this file: what's installed and the workflow
  inspiration.md       design inspiration sites and how to brief Claude with them
  components.md        component libraries and code sources, with install commands
  ui-ux-animation.md   UI/UX rules, motion rules, and the review checklist
  setup.sh             re-install / update every skill from upstream, optional extras
  bin/                 MCP launchers + shoot.cjs (screenshots at desktop and phone width)
  references/          drop 3-5 screenshots of sites you like here before a new design
  starter/             a working demo page (tokens, dark mode, GSAP ScrollTrigger)
```

## Installed skills (`.claude/skills/`)

| Skill | Source | Use it for |
|---|---|---|
| `frontend-design` | anthropics/skills | Deliberate font, colour and layout direction instead of generic AI styling |
| `web-artifacts-builder` | anthropics/skills | Multi-component React + Tailwind + shadcn pages |
| `theme-factory` | anthropics/skills | 10 preset font/colour themes to apply to anything |
| `canvas-design` | anthropics/skills | Posters, hero visuals, static art |
| `brand-guidelines` | anthropics/skills | Applying a brand's colours and type consistently |
| `webapp-testing` | anthropics/skills | Claude tests the local site with Playwright and screenshots it |
| `ui-ux-pro-max` | nextlevelbuilder/ui-ux-pro-max-skill | 79 styles, 192 palettes, 74 font pairings, 119 UX rules, GSAP presets, 22 stacks |
| `design-system` | nextlevelbuilder/ui-ux-pro-max-skill | Token architecture (primitive → semantic → component) |
| `ui-styling` | nextlevelbuilder/ui-ux-pro-max-skill | shadcn/ui + Tailwind styling, canvas visuals |
| `impeccable` | pbakaus/impeccable | `/impeccable critique`, `audit`, `polish`, `typeset`, `colorize`, `layout`, `animate`, `live` |
| `shadcn` | shadcn-ui/ui | Finding, installing and customising shadcn/ui components correctly |
| `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-plugins`, `gsap-react`, `gsap-frameworks`, `gsap-utils`, `gsap-performance` | greensock/gsap-skills | Animation: tweens, timelines, scroll effects, React/Vue/Svelte, 60fps |
| `web-quality-audit`, `performance`, `core-web-vitals`, `accessibility`, `seo`, `best-practices` | addyosmani/web-quality-skills | Lighthouse-style audits and fixes |

Skills trigger on their own when a request matches, or ask by name: *"use ui-ux-pro-max to pick a
palette for an industrial SCADA dashboard"*, *"/impeccable critique web-design/starter"*.

Quick checks without Claude:
```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "industrial monitoring dashboard" --design-system
.claude/skills/impeccable/scripts/impeccable detect web-design/starter   # 61 anti-pattern rules
```

## MCP servers (`.mcp.json`)

| Server | What it gives Claude | Status in Claude cloud sessions |
|---|---|---|
| `context7` | Current, version-specific docs (Next.js, Tailwind, GSAP...) | Reachable once `context7.com` is allowed, but the shared anonymous quota runs out fast: set `CONTEXT7_API_KEY` (free key from context7.com/dashboard) |
| `playwright` | Real browser: click, type, screenshot, console, network | Chromium refuses to start as root without `--no-sandbox`; works locally. In the cloud, use `webapp-testing` or `bin/shoot.cjs` |
| `chrome-devtools` | Lighthouse, performance traces, console, network (usage stats off) | Same root/sandbox limit as Playwright; works locally |
| `shadcn` | Search and install shadcn components from registries | Works |
| `parallel-search` | Web search and page reading, no key | Needs `search.parallel.ai` allowed in the environment's network settings |
| `magic-21st` | 21st.dev Magic: search 10,000+ React/Tailwind components, generate new ones | Needs a key from 21st.dev/mcp stored as the environment variable `TWENTY_FIRST_API_KEY`, and `21st.dev` allowed in network settings |

Claude asks once to approve project MCP servers the first time it opens this repo.

### Setting these up when you only use claude.ai/code (no terminal)
Everything is configured by files in this repo, so there's nothing to type. What's left is in
the cloud environment's settings (environment menu in the session's title bar → **Edit**), and
it applies from the next new session:
- **Network access → Allowed domains:** add `context7.com`, `mcp.context7.com`, `search.parallel.ai`,
  `21st.dev` (keep *Allow package managers* ticked). Steps: https://code.claude.com/docs/en/cloud-environments#network-access
- **Environment variables:** `TWENTY_FIRST_API_KEY=<your 21st.dev key>` (and optionally
  `CONTEXT7_API_KEY=<free key from context7.com/dashboard>`, which Context7 needs in practice). Never paste keys into the chat.
  (`magic-21st` runs with `NODE_USE_ENV_PROXY=1` so Node's fetch goes through the cloud proxy.)
- **Vercel** needs a login, so connect it at https://claude.ai/customize/connectors instead of here.

On your own PC, the terminal equivalents are `claude mcp add ...` / `npx @21st-dev/cli@latest init --client claude`.

## Plugins (`.claude/settings.json`)
**Superpowers** (brainstorm → plan → TDD → review workflow) is enabled for this repo in
`.claude/settings.json`, so every Claude Code session on it loads the plugin automatically. Anthropic's
example skills and the GSAP skills are already copied into `.claude/skills/`, so they need no plugin.
In an interactive terminal session the same thing is `/plugin install superpowers@claude-plugins-official`.

## Workflow for a new site

1. **Brief.** Write `CLAUDE.md` / `spec.md` for the site: audience, pages, one job per page, tone.
2. **References.** Put 3-5 screenshots in `web-design/references/` (see `inspiration.md`).
   Text-only requests are what produce generic pages.
3. **Direction.** Ask for a design system first: *"use ui-ux-pro-max and frontend-design to propose
   style, palette, fonts and spacing from these references; write DESIGN.md"*.
4. **Build.** Plain HTML for one page; Next.js + Tailwind + shadcn for anything bigger
   (`components.md`). Motion with the GSAP skills, following `ui-ux-animation.md`.
5. **Check.** `node web-design/bin/shoot.cjs <url-or-file>` for desktop + phone screenshots,
   `/impeccable critique` and `/impeccable audit`, then `web-quality-audit`.
6. **Ship.** Push to GitHub, connect Vercel / Netlify / Cloudflare Pages (or GitHub Pages for
   static sites) for deploys on every push.

## Keeping it current
```bash
web-design/setup.sh            # re-pulls every skill from upstream into .claude/skills
web-design/setup.sh --extras   # also installs uipro-cli and the Impeccable CLI globally
```
