# Component libraries and code sources

| Source | What it is | How to use it here |
|---|---|---|
| [shadcn/ui](https://ui.shadcn.com) | The most common React component library in the tutorials. You own the code (copied into your project), built on Radix/Base UI + Tailwind | `shadcn` skill + `shadcn` MCP are installed. `npx shadcn@latest init`, then `npx shadcn@latest add button card dialog` |
| [21st.dev](https://21st.dev) | Community React/Tailwind components: scroll effects, animated buttons, heroes, pricing tables | Copy the install command from a component page (`npx shadcn@latest add "https://21st.dev/r/..."`), or add the Magic MCP (`npx @21st-dev/cli@latest init --client claude`, key from 21st.dev/mcp) and ask in plain language. There is no `/ui` command any more |
| [Magic UI](https://magicui.design) | Animated components (marquees, number tickers, bento grids, shimmer buttons) | Installs through the shadcn CLI: copy the `npx shadcn@latest add ...` command from the component page |
| [CodePen](https://codepen.io) | Public snippets for effects | Paste the pen URL or code and ask Claude to port it into the project's tokens and respect reduced motion |
| [GSAP](https://gsap.com) | Animation engine, fully free including all plugins (ScrollTrigger, SplitText, Flip, MorphSVG...) | 8 `gsap-*` skills installed. `npm i gsap` or CDN `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js` (+ `ScrollTrigger.min.js`); `web-design/starter/vendor/` has local copies |

## Frameworks

| Project size | Stack | Start |
|---|---|---|
| One page, portfolio, landing page | Plain HTML + CSS (+ GSAP) | Copy `web-design/starter/` |
| Multi-page marketing site | Astro or Next.js + Tailwind | `npm create astro@latest` / `npx create-next-app@latest --tailwind` |
| App, dashboard, logged-in UI | Next.js + Tailwind + shadcn/ui | `npx create-next-app@latest --tailwind && npx shadcn@latest init` |

For dashboards (HMI-style status, trends, alarms) also read the `dataviz` guidance and the
`ui-ux-pro-max` chart data: `python3 .claude/skills/ui-ux-pro-max/scripts/search.py "real-time trend" --domain chart`.

## Rules when pulling components in

- Restyle every imported component to the project's tokens; don't ship three different button styles.
- Check the licence (shadcn, Magic UI free tier, 21st.dev community components are MIT or similar;
  "Pro" templates are not).
- Animated components must honour `prefers-reduced-motion`.
