# Design inspiration sites

Every design-focused source in the guide gives the same advice: **show Claude 3-5 screenshots of
sites you like** instead of describing the look in words.

| Site | Best for | Cost |
|---|---|---|
| [Dribbble](https://dribbble.com) | Design shots, mood boards, single components, colour ideas | Free |
| [Awwwards](https://www.awwwards.com) | Award-winning sites; motion and scroll-driven storytelling | Free |
| [Godly](https://godly.website) | Curated modern website designs, many with video previews | Free |
| [Land-book](https://land-book.com) | Landing page gallery, filterable by industry and style | Free |
| [Mobbin](https://mobbin.com) | Real app and web UI screenshots, whole user flows | Free tier |
| [Pinterest](https://www.pinterest.com) | Saving visual references into boards | Free |

Also useful for motion and components: [21st.dev](https://21st.dev), [Magic UI](https://magicui.design),
[CodePen](https://codepen.io) (see `components.md`).

Good starting searches for automation / industrial work: Land-book → *SaaS*, *Technology*;
Awwwards → *Industrial*, *Engineering*; Dribbble → *SCADA dashboard*, *HMI*, *IoT dashboard*;
Mobbin → *dashboard*, *data table*, *settings*.

## How to brief Claude with references

1. Save screenshots into `web-design/references/<project>/` (full page or the part you like).
   To grab a page yourself:
   ```bash
   node web-design/bin/shoot.cjs https://example.com web-design/references/<project>/example
   ```
   (writes `example-desktop.png` and `example-mobile.png`)
2. Say what to take from each one, not just "make it like this":
   > Use `references/plant-ops/`: take the **type scale and whitespace** from 1, the **dark
   > palette and data-card style** from 2, the **hero layout** from 3. Ignore their copy and logos.
3. Ask for the design system first (palette, fonts, spacing, radius, motion) and approve it
   before any page is built.

Use references for direction only. Never copy a site's logos, copy, illustrations or brand.
