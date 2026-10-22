# Replace before launch

Everything here is a stand-in. The site works with it, but none of it is real yet.

| What | Where | Now | Replace with |
|---|---|---|---|
| Contact email | `src/content/site.ts` → `email` | `hello@roundhouse.studio` | Your real inbox |
| Booking link | `src/content/site.ts` → `bookingUrl` | `https://cal.com/roundhouse/intro` | Your Cal.com / Calendly link for a 30-minute call |
| Contact form backend | Vercel env var `NEXT_PUBLIC_FORM_ENDPOINT` | unset, so the form opens a pre-filled email | A Formspree, Basin or similar endpoint URL; the form then posts JSON to it |
| Site URL | Vercel env var `NEXT_PUBLIC_SITE_URL` | `https://round-house.vercel.app` | Your final domain, for canonical URLs, sitemap and Open Graph |
| Hours | `src/content/site.ts` → `hours` | 9am–6pm ET, Mon–Fri | The US hours you actually cover |
| Case studies | `src/content/work.ts` | Four sample engagements, labelled as samples on every page | Real client results (problem, what you built, measured figures, cost, payback) |
| Prices | `src/content/services.ts` | Proposed ranges from DESIGN.md §6 | Your own ranges |
| Team | `src/app/about/page.tsx` → `roles` | Three roles, no names | Names, photos and a line each. The critique flagged "who am I hiring?" as the biggest missing trust signal |

When the last sample case study is replaced, remove the `SampleNote` / `SampleTag` uses in
`src/app/page.tsx`, `src/app/work/[slug]/page.tsx` and the note on `src/app/work/page.tsx`.
