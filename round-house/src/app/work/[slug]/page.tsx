import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Figure, SampleTag } from "@/components/blocks";
import { Button } from "@/components/ui/button";
import { caseStudies, getCaseStudy } from "@/content/work";

export function generateStaticParams() {
  return caseStudies.map((c) => ({ slug: c.slug }));
}

export async function generateMetadata({ params }: PageProps<"/work/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const study = getCaseStudy(slug);
  if (!study) return {};
  return {
    title: study.headline,
    description: `${study.summary} Sample engagement: ${study.client}, ${study.location}.`,
    alternates: { canonical: `/work/${study.slug}` },
  };
}

export default async function CaseStudyPage({ params }: PageProps<"/work/[slug]">) {
  const { slug } = await params;
  const study = getCaseStudy(slug);
  if (!study) notFound();

  const index = caseStudies.indexOf(study);
  const next = caseStudies[(index + 1) % caseStudies.length];

  return (
    <article>
      <header className="shell drafting">
        <div className="grid-12 relative pt-10 pb-14 md:pt-14 md:pb-20">
          <nav aria-label="Breadcrumb" className="col-span-4 md:col-span-12">
            <ol className="t-small flex gap-2 text-steel">
              <li>
                <Link href="/work" className="underline underline-offset-4 hover:text-ink">
                  Work
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li aria-current="page" className="text-ink">
                {study.client}
              </li>
            </ol>
          </nav>
          <div className="col-span-4 mt-10 md:col-span-10 md:mt-14">
            <SampleTag />
            <h1 className="t-h1 mt-5 max-w-[20ch]">{study.headline}</h1>
            <p className="t-lead mt-6 max-w-[52ch]">{study.summary}</p>
          </div>
          <dl className="col-span-4 mt-10 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-ink pt-5 md:col-span-12 md:grid-cols-4">
            <div>
              <dt className="t-small text-steel">Client</dt>
              <dd className="mt-1 font-semibold">{study.client}</dd>
            </div>
            <div>
              <dt className="t-small text-steel">Where</dt>
              <dd className="mt-1 font-semibold">{study.location}</dd>
            </div>
            <div>
              <dt className="t-small text-steel">Steps</dt>
              <dd className="mt-1 font-semibold">{study.tiers.join(", ")}</dd>
            </div>
            <div>
              <dt className="t-small text-steel">Timeline</dt>
              <dd className="mt-1 font-semibold">{study.timeline}</dd>
            </div>
          </dl>
        </div>
      </header>

      <section aria-labelledby="results" className="border-t border-rule bg-panel">
        <div className="shell py-16 md:py-20">
          <h2 id="results" className="sr-only">
            Results
          </h2>
          <ul className="grid gap-12 md:grid-cols-3 md:gap-6">
            {study.figures.map((f) => (
              <li key={f.label}>
                <Figure value={f.value} label={f.label} />
              </li>
            ))}
          </ul>
          <p className="t-small mt-10 text-steel">Figures are illustrative for this sample engagement.</p>
        </div>
      </section>

      <section aria-labelledby="situation" className="border-t border-rule">
        <div className="shell section-pad grid-12 gap-y-6">
          <h2 id="situation" className="t-h2 col-span-4 md:col-span-4">
            The situation
          </h2>
          <div className="col-span-4 grid gap-5 md:col-span-7 md:col-start-6">
            {study.situation.map((p) => (
              <p key={p.slice(0, 24)} className="max-w-[62ch] text-[1.125rem]">
                {p}
              </p>
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="built" className="border-t border-rule">
        <div className="shell section-pad grid-12 gap-y-8">
          <h2 id="built" className="t-h2 col-span-4 md:col-span-4">
            What we built
          </h2>
          <dl className="col-span-4 border-b border-ink md:col-span-7 md:col-start-6">
            {study.built.map((b) => (
              <div key={b.name} className="border-t border-ink py-5">
                <dt className="font-semibold">{b.name}</dt>
                <dd className="mt-1 max-w-[58ch] text-steel">{b.detail}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section aria-labelledby="running" className="border-t border-rule bg-panel">
        <div className="shell section-pad grid-12 gap-y-8">
          <h2 id="running" className="t-h2 col-span-4 md:col-span-4">
            Running it
          </h2>
          <div className="col-span-4 md:col-span-7 md:col-start-6">
            <p className="max-w-[58ch] text-[1.125rem]">{study.running}</p>
            <p className="t-small mt-8 text-steel">Tools in this build</p>
            <ul className="mt-3 flex flex-wrap gap-2">
              {study.stack.map((s) => (
                <li key={s} className="rounded-sm border border-rule bg-plant px-3 py-1.5 text-[15px]">
                  {s}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <nav aria-label="More work" className="border-t border-rule">
        <div className="shell flex flex-col gap-8 py-14 md:flex-row md:items-end md:justify-between md:py-20">
          <div>
            <p className="t-small text-steel">Next case study</p>
            <Link href={`/work/${next.slug}`} className="t-h3 mt-2 block max-w-[34ch] underline-offset-4 hover:underline">
              {next.headline}
            </Link>
          </div>
          <Button asChild size="lg">
            <Link href="/contact">Talk about a project like this</Link>
          </Button>
        </div>
      </nav>
    </article>
  );
}
