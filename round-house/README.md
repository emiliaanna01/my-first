# Round House website (revision D)

Next.js 16 (App Router) marketing site for Round House. Every page is pre-rendered as static HTML;
the only server code is the contact form endpoint.

## Run it

```bash
npm install
npm run dev     # http://localhost:3000
npm run build && npm start
```

## Where things live

| What | Where |
| --- | --- |
| All copy, prices and case studies | `lib/content.ts` |
| Pages | `app/page.tsx`, `app/services`, `app/work`, `app/work/[slug]`, `app/about`, `app/contact` |
| Design tokens and styles | `app/globals.css` (colors, type, light and dark themes at the top) |
| Turntable drawing | `components/Turntable.tsx` |
| Home hero, bay console and tour | `components/Hero.tsx` |
| Site-wide motion (smooth scroll, route curtain, scroll reveals) | `components/SiteMotion.tsx` |
| Fonts (Big Shoulders and Hanken Grotesk, self-hosted by `next/font` at build time) | `app/layout.tsx` |

Motion uses GSAP 3 (ScrollTrigger, Flip) and Lenis. Everything respects `prefers-reduced-motion`,
and the content is fully readable with JavaScript off.

## Contact form

`/api/contact` validates the enquiry, then delivers it one of two ways, set in Vercel
(Project → Settings → Environment Variables):

**A form service.** Set `FORM_ENDPOINT` (or `NEXT_PUBLIC_FORM_ENDPOINT`) to a Formspree, Basin or similar
URL that accepts JSON.

**Email through [Resend](https://resend.com).** Set all three:

| Variable | Example |
| --- | --- |
| `RESEND_API_KEY` | `re_...` |
| `CONTACT_TO` | `hello@roundhouse.studio` |
| `CONTACT_FROM` | `Round House site <site@roundhouse.studio>` (a sender on a domain verified in Resend) |

Until they are set, the form still validates and then gives the visitor a ready-to-send copy of their
message with a mail-app link, so no enquiry is silently lost.

## Site address

Set `NEXT_PUBLIC_SITE_URL` to the final domain (for canonical URLs, the sitemap and link previews).
It defaults to `https://round-house.vercel.app`.

## Old URLs

`next.config.ts` redirects the `.html` URLs of the static prototype (`/services.html`,
`/case-hvac-speed-to-lead.html`, and so on) to the new routes.
