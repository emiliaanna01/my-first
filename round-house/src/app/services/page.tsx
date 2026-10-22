import type { Metadata } from "next";
import Link from "next/link";

import { SectionHead } from "@/components/blocks";
import { TrackLine } from "@/components/track-line";
import { Button } from "@/components/ui/button";
import FloodFaq from "@/components/ui/flood-faq";
import { faqs } from "@/content/faq";
import { practices, retainers, tiers } from "@/content/services";

export const metadata: Metadata = {
  title: "Services and prices",
  description:
    "Audits, automation, AI agents, CRM migration, brand and websites for US businesses. Three steps, Diagnose, Build and Run, with published price ranges.",
  alternates: { canonical: "/services" },
};

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faqs.map((f) => ({
    "@type": "Question",
    name: f.question,
    acceptedAnswer: { "@type": "Answer", text: f.answer },
  })),
};

export default function ServicesPage() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />

      <section aria-labelledby="page-title" className="shell drafting">
        <div className="grid-12 relative pt-14 pb-16 md:pt-20 md:pb-24">
          <div className="col-span-4 md:col-span-9">
            <h1 id="page-title" className="t-h1 max-w-[16ch]">
              Services and prices
            </h1>
            <p className="t-lead mt-6 max-w-[52ch]">
              Three steps. Pay for an audit, build what it recommends at a fixed price, then keep it running on a monthly
              plan. Every price on this page is a real range, not a starting bid.
            </p>
            <nav aria-label="On this page" className="mt-8">
              <ul className="flex flex-wrap gap-x-6 gap-y-1">
                {[...tiers.map((t) => ({ href: `#${t.id}`, label: t.name })), { href: "#retainers", label: "Retainers" }, { href: "#practices", label: "Practices" }, { href: "#faq", label: "Questions" }].map(
                  (l) => (
                    <li key={l.href}>
                      <a href={l.href} className="inline-flex min-h-11 items-center font-semibold underline underline-offset-4 hover:decoration-2">
                        {l.label}
                      </a>
                    </li>
                  ),
                )}
              </ul>
            </nav>
          </div>
        </div>
      </section>

      <section id="pricing" aria-label="The three steps" className="border-t border-rule bg-panel">
        <div className="shell py-16 md:py-20">
          <TrackLine tiers={tiers} linkPrefix="" />
        </div>
      </section>

      {tiers.map((t) => (
        <section key={t.id} id={t.id} aria-labelledby={`${t.id}-title`} className="border-t border-rule">
          <div className="shell section-pad grid-12 gap-y-10">
            <div className="col-span-4 md:col-span-4">
              <div className="md:sticky md:top-28">
                <p className="t-small text-steel">
                  Step <span className="tnum">{t.step}</span> of 3
                </p>
                <h2 id={`${t.id}-title`} className="t-h2 mt-2">
                  {t.name}
                </h2>
                <p className="mt-4 max-w-[36ch]">{t.summary}</p>
                <p className="wide tnum mt-6 text-[1.75rem] leading-tight font-bold">{t.price}</p>
                <p className="t-small mt-1 max-w-[32ch] text-steel">{t.priceNote}</p>
                <p className="mt-6 max-w-[36ch] border-l-[3px] border-signal pl-4">{t.outcome}</p>
              </div>
            </div>
            <div className="col-span-4 md:col-span-8">
              <table className="w-full border-collapse text-left">
                <caption className="sr-only">What {t.name} includes, with prices</caption>
                <thead>
                  <tr className="border-b border-ink">
                    <th scope="col" className="t-small pb-3 font-semibold text-steel">
                      Service
                    </th>
                    <th scope="col" className="t-small hidden pb-3 text-right font-semibold text-steel sm:table-cell">
                      {t.id === "run" ? "Included in" : "Typical price"}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {t.items.map((item) => (
                    <tr key={item.name} className="border-b border-rule align-top">
                      <th scope="row" className="py-5 pr-6 font-normal">
                        <span className="block font-semibold">{item.name}</span>
                        <span className="mt-1 block max-w-[54ch] text-steel">{item.detail}</span>
                        <span className="wide tnum mt-2 block font-bold sm:hidden">{item.price ?? "Retainer"}</span>
                      </th>
                      <td className="wide tnum hidden py-5 text-right font-bold whitespace-nowrap sm:table-cell">
                        {item.price ?? "Retainer"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      ))}

      <section id="retainers" aria-labelledby="retainers-title" className="border-t border-rule bg-panel">
        <div className="shell section-pad">
          <SectionHead
            id="retainers-title"
            title="Run retainers"
            intro="Pick the level of support that matches how much you automate. Month to month after the first three months. Prices per month."
          />
          <div className="mt-12 overflow-x-auto md:mt-16">
            <table className="w-full min-w-[640px] border-collapse text-left">
              <caption className="sr-only">Run retainer plans compared</caption>
              <thead>
                <tr>
                  <td className="w-1/4" />
                  {retainers.map((r) => (
                    <th key={r.name} scope="col" className="border-b border-ink pb-5 align-bottom">
                      <span className="t-h3 block">{r.name}</span>
                      <span className="wide tnum mt-2 block text-[2rem] leading-none font-[760]">
                        {r.price}
                        <span className="text-base font-semibold text-steel"> /mo</span>
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-rule align-top">
                  <th scope="row" className="py-5 pr-6 font-semibold">
                    Best for
                  </th>
                  {retainers.map((r) => (
                    <td key={r.name} className="py-5 pr-6 text-steel">
                      {r.for}
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-ink align-top">
                  <th scope="row" className="py-5 pr-6 font-semibold">
                    Includes
                  </th>
                  {retainers.map((r) => (
                    <td key={r.name} className="py-5 pr-6">
                      <ul className="grid gap-2">
                        {r.includes.map((line) => (
                          <li key={line} className="max-w-[30ch]">
                            {line}
                          </li>
                        ))}
                      </ul>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Button asChild>
              <Link href="/contact?interest=run">Ask about a retainer</Link>
            </Button>
            <p className="t-small text-steel">Need a named automation lead with more hours? Fractional plans start at $6,000 a month.</p>
          </div>
        </div>
      </section>

      <section id="practices" aria-labelledby="practices-title" className="border-t border-rule">
        <div className="shell section-pad">
          <SectionHead
            id="practices-title"
            title="Six practices, one team"
            intro="Every step draws on the same people, so the audit, the build and the brand never get lost between agencies."
          />
          <ul className="mt-12 grid border-b border-ink md:mt-16 md:grid-cols-3 md:gap-x-6">
            {practices.map((p) => (
              <li key={p.name} className="border-t border-ink py-6 md:pr-4">
                <h3 className="t-h3">{p.name}</h3>
                <p className="mt-2">{p.line}</p>
                <ul className="t-small mt-3 grid gap-1 text-steel">
                  {p.examples.map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section id="faq" aria-labelledby="faq-title" className="border-t border-rule bg-panel">
        <div className="shell section-pad">
          <SectionHead id="faq-title" title="Questions buyers ask us" />
          <div className="mt-12 md:mt-16">
            <FloodFaq items={faqs} />
          </div>
        </div>
      </section>
    </>
  );
}
