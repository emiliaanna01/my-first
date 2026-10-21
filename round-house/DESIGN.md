# Round House: design direction

Status: **proposal, awaiting approval.** Nothing is built yet. The style tile in
`design/style-tile.html` shows the tokens below on screen.

## 1. Brief, restated

| | |
|---|---|
| **Who we sell to** | US small and mid-sized businesses (10–250 staff): field services, manufacturing and fabrication, logistics, professional services, multi-location clinics. Buyers are owners, COOs and ops managers, not marketers. |
| **What they buy** | Outcomes in three tiers: **Diagnose** (paid audit + roadmap) → **Build** (automation, AI agent, CRM, brand/web project) → **Run** (monthly retainer: maintenance, optimization, reporting). |
| **Positioning line** | "From the factory floor to the front office, we automate the work that slows you down." |
| **Personality** | Engineer-grade reliability, modern and approachable. Precise, calm, outcome-driven. No AI hype: no glowing brains, no purple gradients. |
| **Trust signals** | ROI case studies with numbers, clear price ranges, US-hours availability, contracts and NDAs, data-security practices. |
| **Job of the site** | Get a qualified buyer to book a 30-minute call or start a paid audit. |

## 2. Research: five leading agency sites

Fetched with parallel-search (Oct 2026). The browser in this environment can't reach the sites
directly, so the visual notes come from Awwwards entries and site copy.

| Site | Recognition | What makes it strong | What we take | What we leave |
|---|---|---|---|---|
| **Immersive Garden** (Paris) | Awwwards Agency of the Year 2025; SOTD Jan 2025 | Two-colour palette (#000 / #C2C2C2): restraint makes the work the colour. Every project gets one line of *what it did*, not a list of deliverables. Signature interactions (bas-relief, rapid-scroll index, menu transition) are few and memorable. | Restraint: a tiny palette and one signature interaction. One-line case summaries. | Luxury-brand 3D/WebGL; it would slow pages and say "art studio", not "reliable operator". |
| **Locomotive** (Montréal) | Multiple SOTD, 15 years running | Strong, quirky voice. "From strategy to deployment and maintenance, we're the one-stop shop": it sells the full lifecycle, which is our Diagnose → Build → Run. Featured work first, nav kept to Work / Agency / Careers / Let's talk. | Lifecycle framing; a short nav; "Let's talk" always visible. | Emoji-heavy humour; wrong tone for COOs. |
| **basement.studio** (Buenos Aires → SF clients) | Awwwards SOTD + Developer Awards; made the Geist typeface with Vercel | A remote studio selling to US clients, which is our exact model. Case studies lead with the business result ("sold out inventory in hours"). Services are grouped as four clear practices, each with 2–4 concrete deliverables. Separate emails for hello and sales. | Result-first case headlines; practices with concrete deliverables; a clear US-client model. | Swagger ("making cool shit") would undercut "engineer-grade". |
| **Noomo Agency** (LA) | Awwwards Site of the Year 2023 | Contact form asks for **budget in USD bands** up front, which qualifies leads and signals price transparency. Awards are listed as evidence, with year and project. | Budget bands on the contact form; evidence presented as data with dates. | Heavy 3D transitions; glass cards. |
| **Instrument** (Portland) | Campaign US Design Studio of the Year 2026 | Calm US-corporate clarity. Work filterable by discipline (brand / marketing / product). Services: "We make brands, products, websites, and campaigns" says everything in one sentence. | Filter case studies by tier/discipline; a one-sentence services summary. | Its big-brand portfolio scale; we'll use honest, labelled sample studies until real ones exist. |

**Common thread:** each site is strong because of *one* distinctive idea carried with discipline
(a palette, a voice, a signature interaction), plus result-first proof. None of them relies on
decoration. Their weakness for our buyer: none shows prices, availability hours or security
practices. **That gap is our edge.** We can be as crafted as them and more transparent.

## 3. Concept: the roundhouse

A **roundhouse** is the building where railroads service locomotives: engines roll onto a
central **turntable**, get rotated to the right bay, inspected, repaired and sent back out on the
right track. That is exactly the offer: work comes in, we route it, rebuild it and keep it
running.

So the brand's signature is a **plan-view schematic of a roundhouse**: a turntable in the
middle, radial tracks fanning out to bays, drawn like a control-system diagram. Each bay is a
business process (Leads, Quotes, Inbox, CRM, Reporting, Onboarding, Brand, Web). It is the logo,
the hero, and the visual grammar for diagrams across the site.

Second idea, from your own field: **high-performance HMI (ISA-101) colour discipline.** Control
room screens stay grey so that colour only ever means something: an alarm, a running state, an
action. The site does the same. It is calm graphite on plant-grey, and **Signal Yellow appears
only where a visitor can act or where a result lives.** That is the "strong, confident accent"
from your brief, given a rule.

## 4. Tokens

### Colour

| Token | Hex | Role | Contrast |
|---|---|---|---|
| `--plant` | `#E8EBE9` | Page background: control-room grey, slightly green-cool (not cream) | — |
| `--panel` | `#F6F7F6` | Raised surfaces, form fields, table rows | — |
| `--ink` | `#151A1E` | Text, schematic strokes, dark sections | 14.6 : 1 on plant |
| `--steel` | `#4F5A63` | Secondary text, captions | 5.9 : 1 on plant |
| `--rule` | `#BCC3C2` | Grid lines, dividers, inactive tracks | decorative only |
| `--signal` | `#FFC21A` | **Action and result only:** primary buttons, active bay, result figures' highlight | ink on signal 10.8 : 1 |
| `--run` | `#186B3C` | State only: "Online now (9–6 ET)", "Running" status dots | 5.5 : 1 on plant |

Rule: if `--signal` appears and you can neither click it nor read a result in it, remove it.
Dark sections (footer, final CTA) invert to ink background with plant text; signal stays the same.

### Type: Archivo, one family, two widths

[Archivo](https://fonts.google.com/specimen/Archivo) (Omnibus-Type) is a grotesque designed for
technical and industrial use, with a variable **width** axis (62–125) as well as weight. Width
gives the contrast instead of a second family:

| Role | Setting | Size (desktop / phone) |
|---|---|---|
| Display (H1) | wdth 118, wght 760, tracking −0.025em, line-height 0.98 | 88 / 44px |
| H2 | wdth 112, wght 700, tracking −0.02em | 52 / 32px |
| H3 | wdth 100, wght 650 | 24 / 20px |
| Body | wdth 100, wght 400, line-height 1.55, max 68ch | 18 / 17px |
| Small / captions | wdth 100, wght 500 | 14px |
| Figures (results, prices) | wdth 118, wght 760, `tabular-nums` | 64 / 40px |

Scale ratio ≈ 1.333 (perfect fourth). Sentence case everywhere: no all-caps eyebrows, no
monospace "data" labels, no arrows glued to button text.

### Layout

- 12-column grid, 1280px max content width, 24px gutters (16px phone). In the hero the column
  lines are visible, like a drafting sheet. Elsewhere the grid is felt, not drawn.
- **Left-aligned** throughout. Headlines hang on column 1; body copy sits in columns 1–7.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 72, 112, 160px. Section padding 112px desktop / 72px phone.
- Radius: **2px** on inputs and buttons (machined, not pill), **0** on sections. One radius,
  purposefully small; cards aren't the structuring device.
- No drop shadows. Elevation is shown with `--panel` vs `--plant` and a 1px `--rule` line.

### Structural devices (each carries information)

- **Track line:** Diagnose → Build → Run drawn as one railway line with three stations. Used only
  where the content really is a sequence, so the numbering is honest.
- **Spec sheet tables** for pricing, deliverables and security practices: rows, not cards.
- **Drawing title block** as the footer: the engineering-drawing corner box, here holding
  contact, US hours, location, NDA note and "Rev." date. It's the kind of detail a buyer from
  manufacturing recognises.
- "Sample engagement" tag on every case study until real ones replace them.

### Motion (GSAP + ScrollTrigger via `useGSAP`)

One orchestrated moment, two responsive ones:

1. **Hero load (the signature):** the schematic draws itself (tracks stroke in ~900ms), the
   turntable bridge swings to the "Leads" bay and that bay fills signal yellow. Then it stops.
2. **On interaction:** hovering or focusing a bay label rotates the bridge to it and shows the
   one-line outcome for that process. Keyboard-accessible; it's a real list of buttons.
3. **On scroll, once:** the Diagnose → Build → Run track line draws between stations as the
   section enters (scrubbed, 0.6s ease-out).

No fade-up on every section and no hover lift on cards. `prefers-reduced-motion: reduce` renders
the final state immediately (bridge pointing at Leads, track lines drawn) via `gsap.matchMedia()`.

## 5. Pages

| Page | One job | Key sections |
|---|---|---|
| **Home** | Make the offer clear in 10 seconds, prove it, get the click | Hero + turntable · three result figures (sample) · Diagnose → Build → Run track with price ranges · what we build (outcome-first index) · selected work · trust spec sheet · CTA |
| **Services** | Let a buyer self-select a tier and see the price | Three tiers in depth with deliverables and ranges · the six practices (business analysis, automation, AI agents & integrated systems, brand identity & social, websites, UI/UX) · Run retainer table: Starter / Growth / Scale · FAQ |
| **Work** | Prove ROI with numbers | Filter by Diagnose / Build / Run · 4 sample case studies, each with its own page: situation, what we built, result figures, stack |
| **About** | Earn trust in how we operate | The roundhouse idea · how we work with US clients (hours, contracts, NDAs, data security) · principles · who you work with (roles) |
| **Contact** | Turn intent into a booked call | Short form with budget bands in USD and tier interest · "Book a 30-min call" · email · hours · what happens next (3 steps) |

## 6. Proposed prices (edit before launch)

| Tier | Offer | Range |
|---|---|---|
| Diagnose | Automation & AI readiness audit + 90-day roadmap | $2,500 – $6,000 · fee credited to your build within 60 days |
| Diagnose | Single audit (tool-spend, funnel, brand/website, data readiness, AI policy starter) | from $1,500 |
| Build | Landing page / microsite | $4,000 – $9,000 |
| Build | Automation or AI-agent project (speed-to-lead, documents, inbox, onboarding, knowledge assistant) | $8,000 – $35,000 |
| Build | CRM setup & migration (HubSpot, GoHighLevel, Pipedrive) | $6,000 – $20,000 |
| Build | Brand identity + website | $12,000 – $40,000 |
| Run | Starter / Growth / Scale retainer | $1,800 / $4,200 / $8,500 per month |
| Run | Fractional automation lead (20 h/month) | from $6,000 per month |

## 7. Placeholders to replace

Listed in `PLACEHOLDERS.md` when the build lands: email (`hello@roundhouse.studio`), booking link,
city/time zone (site says 9am–6pm ET), contact-form endpoint, the four sample case studies, prices.

## 8. Self-review against generic defaults

| Axis | First instinct | Why it was generic | Changed to |
|---|---|---|---|
| Palette | ui-ux-pro-max returned navy #0F172A + trust blue #0369A1 | It's the default for every B2B site; nothing about Round House | Plant grey + graphite + Signal Yellow, with the HMI "colour means something" rule |
| Accent | Safety orange (database "industrial" pick) | The construction/industrial cliché, and close to the warm-clay tell | Signal yellow: floor-marking and rail-signal vernacular, rarely used by agencies, high contrast with ink |
| Type | Plus Jakarta Sans / Space Grotesk / Inter + JetBrains Mono for "data" | Overused; mono labels are a generated-page tell | Archivo with its width axis: one industrial family, contrast via width |
| Layout | Bento grid of service cards | The SaaS-card kit | Spec-sheet rows, a track-line sequence, a drawing title block |
| Hero | Big number + small label + gradient | The default treatment | The roundhouse schematic, which is the brand's own concept and doubles as navigation into services |
| Dark theme | Near-black page with one bright accent | Tell #2 | Light page; dark only for footer and final CTA |

## 9. Tech plan

- Next.js (App Router, static export where possible) + Tailwind CSS v4 + shadcn/ui (Button,
  Input, Textarea, Select, Accordion, Tabs). Tokens above mapped to shadcn CSS variables.
- 21st.dev Magic components where they fit (likely the FAQ accordion and the contact form
  layout), restyled to these tokens.
- GSAP 3 + `@gsap/react` `useGSAP`, ScrollTrigger; `gsap.matchMedia()` for reduced motion.
- `next/font/google` for Archivo (variable, `wdth` axis), self-hosted at build.
- Contact form: posts to `NEXT_PUBLIC_FORM_ENDPOINT` (Formspree or similar) when set; until then
  it opens a pre-filled email, so no message is silently lost.
- Light theme only for v1 (dark sections inside it). A full dark mode can follow.
- Lives in `round-house/` in this repo; Vercel project root = `round-house`.
