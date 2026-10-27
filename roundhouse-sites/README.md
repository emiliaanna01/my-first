# RoundHouse website concepts

Eleven static, front-end-only websites for RoundHouse. Each one takes on the whole look and feel of a
world-leading site (navigation, hero, components, type, colour and footer), filled with RoundHouse's
own content from `round-house/lib/content.ts`: services, published prices, Diagnose → Build → Run,
retainers, sample case studies, security terms and an enquiry form.

Open `index.html` for the gallery, or any folder's `index.html` directly. No build step: plain HTML,
CSS and a little vanilla JavaScript per page, with fonts from Google Fonts.

| Folder | Modelled on | Signature pieces |
|---|---|---|
| `01-uber` | Uber | Black top bar, inputs-first hero with a price estimator, grey suggestion cards |
| `02-stripe` | Stripe | Animated skewed gradient, product mockups, dark code band, stat columns |
| `03-apple` | Apple | Global nav and product nav, stacked product tiles, plan comparison, footnoted footer |
| `04-linear` | Linear | Dark canvas, gradient type, tilted app screenshot, 1.0/2.0/3.0 chapters |
| `05-vercel` | Vercel | Geist, prism hero, crosshair grid, go-live log, light/dark theme switch |
| `06-notion` | Notion | Line drawings, tabbed workspace mockup, pale cards |
| `07-airbnb` | Airbnb | Pill search that filters, listing cards, listing modal with reserve card |
| `08-accenture` | Accenture | Black and purple, 3D spheres, numbered featured carousel |
| `09-ibm` | IBM (Carbon) | Masthead, light Plex leadspace, tiles, tabs, accordion, data table |
| `10-mailchimp` | Mailchimp | Yellow hero, serif headlines, journey-builder flow, plan toggle |
| `11-tokens-studio` | Tokens Studio | Header that shrinks into a floating bar, 3D tokens that pop and drift (GSAP + Lenis), process stepper, stacked colour panels, portfolio with case dialogs, client reviews, pricing toggle |

## Notes

- Brand marks are RoundHouse's own simple marks. No reference site's logo, imagery or copy is used.
- Enquiry forms validate and then prepare a ready-to-send message for hello@roundhouse.studio; they
  don't post anywhere. Wire them to Formspree, Resend or similar before launch.
- Case-study figures are the labelled sample engagements, and logo-row company names are
  placeholders. Replace both with real clients before launch (see `round-house/PLACEHOLDERS.md`).
- `thumbs/` holds the gallery screenshots.
