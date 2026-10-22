import Link from "next/link";

import { CaseRow, Figure, SampleTag, SectionHead, SpecSheet, TextLink, usTerms } from "@/components/blocks";
import { HoursStatus } from "@/components/hours-status";
import { Roundhouse } from "@/components/roundhouse";
import { TrackLine } from "@/components/track-line";
import { Button } from "@/components/ui/button";
import { practices, tiers } from "@/content/services";
import { site } from "@/content/site";
import { caseStudies } from "@/content/work";

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  name: site.name,
  url: site.url,
  description: site.description,
  email: site.email,
  areaServed: { "@type": "Country", name: "United States" },
  openingHoursSpecification: {
    "@type": "OpeningHoursSpecification",
    dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    opens: "09:00",
    closes: "18:00",
  },
  priceRange: "$1,500–$40,000",
};

export default function Home() {
  const headlineFigures = caseStudies.slice(0, 3).map((c) => ({ ...c.figures[0], client: c.client }));

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      {/* Hero: the positioning line, and the roundhouse that routes work to the right bay. */}
      <section aria-labelledby="hero-title" className="shell drafting">
        <div className="grid-12 relative gap-y-12 pt-14 pb-20 md:pt-20 md:pb-28">
          <div className="col-span-4 self-center md:col-span-10 lg:col-span-6">
            <h1 id="hero-title" className="t-display max-w-[11ch]">
              We automate the work that slows you down.
            </h1>
            <p className="t-lead mt-7 max-w-[40ch]">
              From the factory floor to the front office, Round House finds where your team loses hours, builds the
              systems that win them back, and keeps those systems running.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/contact">Book a 30-minute call</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/services#pricing">See prices</Link>
              </Button>
            </div>
            <HoursStatus className="mt-7" />
          </div>
          <div className="col-span-4 md:col-span-10 md:col-start-2 lg:col-span-6 lg:col-start-7 lg:pl-4">
            <Roundhouse />
          </div>
        </div>
      </section>

      {/* Proof first: numbers, the way a COO reads them. */}
      <section aria-labelledby="results-title" className="border-t border-rule bg-panel">
        <div className="shell section-pad">
          <SectionHead
            id="results-title"
            title="Measured in hours, not hype."
            intro="Every engagement starts with a baseline, so the result is a number you can check. These are sample engagements that show how we report."
            action={<TextLink href="/work">See the case studies</TextLink>}
          />
          <ul className="mt-14 grid gap-12 md:mt-20 md:grid-cols-3 md:gap-6">
            {headlineFigures.map((f) => (
              <li key={f.client}>
                <Figure value={f.value} label={`${f.label}. ${f.client}.`} />
                <SampleTag className="mt-4" />
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* The offer, as a sequence with prices. */}
      <section aria-labelledby="how-title" className="border-t border-rule">
        <div className="shell section-pad">
          <SectionHead
            id="how-title"
            title="Start with a paid audit. Then decide."
            intro="We sell outcomes in three steps, with prices on the page. The audit fee comes off the build if you go ahead within 60 days, so the first step carries little risk."
          />
          <div className="mt-14 md:mt-20">
            <TrackLine tiers={tiers} />
          </div>
        </div>
      </section>

      {/* What we build, as an index rather than a grid of cards. */}
      <section aria-labelledby="build-title" className="border-t border-rule bg-panel">
        <div className="shell section-pad">
          <SectionHead
            id="build-title"
            title="One team for the systems and the shop window."
            intro="Most agencies do either the automation or the brand. We do both, so the website that captures the lead and the system that answers it are built to work together."
            action={<TextLink href="/services">All services and prices</TextLink>}
          />
          <ul className="mt-14 grid border-b border-ink md:mt-20 md:grid-cols-2 md:gap-x-6">
            {practices.map((p) => (
              <li key={p.name} className="border-t border-ink py-6">
                <h3 className="t-h3">{p.name}</h3>
                <p className="mt-2 max-w-[44ch]">{p.line}</p>
                <p className="t-small mt-3 text-steel">{p.examples.join(", ")}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section aria-labelledby="work-title" className="border-t border-rule">
        <div className="shell section-pad">
          <SectionHead
            id="work-title"
            title="Selected work"
            intro="Field services, fabrication, logistics and healthcare. The problem, what we built and what changed."
            action={<TextLink href="/work">All case studies</TextLink>}
          />
          <ul className="mt-12 border-b border-ink md:mt-16">
            {caseStudies.map((c) => (
              <CaseRow key={c.slug} study={c} />
            ))}
          </ul>
        </div>
      </section>

      <section aria-labelledby="terms-title" className="border-t border-rule bg-panel">
        <div className="shell section-pad grid-12 gap-y-12">
          <div className="col-span-4 md:col-span-5">
            <h2 id="terms-title" className="t-h2 max-w-[14ch]">
              How we work with US teams
            </h2>
            <p className="t-lead mt-5 max-w-[36ch]">
              The terms a procurement or IT review will ask about, answered before the first call.
            </p>
            <TextLink href="/about#terms" className="mt-6">
              More on security and contracts
            </TextLink>
          </div>
          <div className="col-span-4 md:col-span-7">
            <SpecSheet rows={usTerms} />
          </div>
        </div>
      </section>
    </>
  );
}
