# Replace before launch

Everything here is a stand-in. The site works with it, but none of it is real yet.

| What | Where | Now | Replace with |
|---|---|---|---|
| Contact email | `lib/content.ts` → `EMAIL` | `hello@roundhouse.studio` | Your real inbox |
| Booking link | `lib/content.ts` → `CAL` | `https://cal.com/roundhouse/intro` | Your Cal.com / Calendly link for a 30-minute call |
| Contact form delivery | Vercel env vars (see README) | unset, so the form gives the visitor a ready-to-send copy | `FORM_ENDPOINT`, or the three Resend variables |
| Site URL | Vercel env var `NEXT_PUBLIC_SITE_URL` | `https://round-house.vercel.app` | Your final domain |
| Hours | `lib/content.ts`, `lib/hours.ts` | 9am–6pm ET, Mon–Fri | The US hours you actually cover |
| Case studies | `lib/content.ts` → `CASES` | Four sample engagements, labelled as samples on every page | Real client results (problem, what you built, measured figures, cost, payback) |
| Prices | `lib/content.ts` → `DIAGNOSE`, `BUILD`, `RUN`, `PLANS` | Proposed ranges | Your own ranges |
| Team | `app/about/page.tsx` | Three roles, no names | Names, photos and a line each |

When the last sample case study is replaced, remove the sample notes on the home, Work and case-study pages.
