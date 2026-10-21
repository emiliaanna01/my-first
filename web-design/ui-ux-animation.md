# UI/UX and animation rules

A one-page summary of what the installed skills enforce. The full rule sets live in
`.claude/skills/ui-ux-pro-max/references/quick-reference.md`, `.claude/skills/impeccable/`,
`.claude/skills/frontend-design/SKILL.md` and the `gsap-*` skills.

## Layout and typography
- One job per page and one primary action per screen; everything else is visually quieter.
- 4 or 8 px spacing scale; consistent section padding; max text width about 65-75 characters.
- At most two font families. A clear scale (e.g. 14 / 16 / 20 / 28 / 40 / 56) with tight line-height
  on headings (1.1-1.2) and relaxed body (1.5-1.7).
- Design phone width first: no horizontal scroll, 16 px side gutter, tap targets at least 44 px.

## Colour
- Define tokens once (`--bg`, `--surface`, `--text`, `--muted`, `--accent`, `--border`) and use
  only tokens in components. Provide a dark theme by redefining the same tokens.
- Text contrast at least 4.5:1 (3:1 for large text and UI boundaries). Never signal state by colour
  alone: pair it with an icon, label or shape. (Same rule as alarm colours on an HMI.)
- One accent colour used sparingly reads as deliberate; five reads as generic.

## Avoid the "AI-generated" look
Purple-to-blue gradients on everything, glassmorphism cards on a gradient, emoji as icons,
centred everything, identical three-card feature rows, Inter + default shadows everywhere.
`impeccable detect` flags most of these automatically.

## Motion
- Motion explains something: where an element came from, what changed, what to look at next.
- Durations: 150-250 ms for UI feedback (hover, press, toggle), 300-600 ms for entrances,
  longer only for scroll-driven storytelling.
- Animate `transform` and `opacity` only; never `width`, `height`, `top`, `left` (layout thrash).
- Ease out for entrances (`power2.out` / `power3.out`), ease in-out for moves; avoid linear except
  for continuous loops like marquees.
- Stagger lists by 40-80 ms. Reveal on scroll once; don't re-animate every time it re-enters.
- **Always** honour `prefers-reduced-motion`: show the final state, no parallax, no autoplay.
- Content must be visible with JavaScript off; animation is an enhancement.

GSAP patterns (see the `gsap-scrolltrigger` and `gsap-performance` skills):
```js
gsap.registerPlugin(ScrollTrigger);
const mm = gsap.matchMedia();
mm.add("(prefers-reduced-motion: no-preference)", () => {
  gsap.utils.toArray(".reveal").forEach((el) =>
    gsap.from(el, { y: 24, autoAlpha: 0, duration: 0.6, ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 85%", once: true } }));
});
```
In React use `useGSAP()` from `@gsap/react` so animations clean up on unmount.

## Review checklist before shipping
1. Screenshots at 1440 px and 390 px (`node web-design/bin/shoot.cjs ...`), light and dark.
2. `/impeccable critique` (design) and `/impeccable audit` (accessibility, performance).
3. `web-quality-audit` skill: Core Web Vitals, accessibility, SEO, best practices.
4. Keyboard only: every control reachable, visible focus ring, logical order.
5. Reduced motion on: nothing moves that doesn't need to, nothing is hidden.
