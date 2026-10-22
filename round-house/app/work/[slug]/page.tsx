import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CtaBand, SampleNote, SecHead } from "@/components/Blocks";
import { SplitHeading } from "@/components/Split";
import { CASES, type BeforeAfter } from "@/lib/content";

type Params = { slug: string };

export function generateStaticParams(): Params[] {
  return CASES.map((c) => ({ slug: c.slug }));
}
export const dynamicParams = false;

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const c = CASES.find((x) => x.slug === slug);
  if (!c) return {};
  return { title: c.client, description: `${c.title} ${c.summary}`, alternates: { canonical: `/work/${c.slug}` } };
}

function Bars({ b }: { b?: BeforeAfter }) {
  if (!b) return null;
  const max = Math.max(b.before, b.after);
  const w = (v: number) => `${((v / max) * 100).toFixed(2)}%`;
  return (
    <div className="ba" aria-hidden="true">
      <div className="ba-row"><span>Before</span><span className="ba-track"><span className="ba-fill" data-bar="" style={{ ["--w" as string]: w(b.before) }} /></span><b>{b.bl}</b></div>
      <div className="ba-row after"><span>After</span><span className="ba-track"><span className="ba-fill" data-bar="" style={{ ["--w" as string]: w(b.after) }} /></span><b>{b.al}</b></div>
    </div>
  );
}

export default async function CasePage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const idx = CASES.findIndex((x) => x.slug === slug);
  if (idx < 0) notFound();
  const c = CASES[idx];
  const next = CASES[(idx + 1) % CASES.length];
  return (
    <>
      <main id="main" className="site-main">
        <section className="page-hero case-hero">
          <div className="wrap">
            <nav className="crumbs" aria-label="Breadcrumb"><Link href="/work">Work</Link><span aria-hidden="true">/</span><span>{c.client}</span></nav>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {c.steps.map((s) => <span key={s} className="chip">{s}</span>)}
              <span className="chip">Sample engagement</span>
            </div>
            <SplitHeading as="h1" text={c.title} />
            <p className="lede">{c.summary}</p>
            <dl className="facts">
              <div><dt>Client</dt><dd>{c.client}</dd></div>
              <div><dt>Size and place</dt><dd>{c.where}</dd></div>
              <div><dt>Timeline</dt><dd>{c.timeline}</dd></div>
              <div><dt>Investment</dt><dd>{c.investment}</dd></div>
              <div><dt>Payback</dt><dd>{c.payback}</dd></div>
            </dl>
          </div>
        </section>

        <section className="section band-dark on-dark" aria-labelledby="res-title">
          <div className="wrap">
            <SecHead id="res-title" title="What changed"><SampleNote /></SecHead>
            <div className="results">
              {c.results.map((r) => (
                <div key={r.cap} className="result">
                  <span className="result-num" data-count="">{r.num}</span>
                  <p className="result-cap">{r.cap}</p>
                  <Bars b={r.ba} />
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="section" aria-labelledby="sit-title">
          <div className="wrap prose-grid">
            <h2 className="h2" id="sit-title">The situation</h2>
            <div className="prose">{c.situation.map((p) => <p key={p}>{p}</p>)}</div>
          </div>
        </section>

        <section className="section band-alt" aria-labelledby="built-title">
          <div className="wrap">
            <SecHead id="built-title" title="What we built"><p className="lede">Each part hands its work to the next, in this order.</p></SecHead>
            <ol className="flow" data-flow="">
              {c.built.map(([n, d], i) => (
                <li key={n} className="flow-step"><span className="fs-n">{i + 1}</span><h3>{n}</h3><p>{d}</p></li>
              ))}
            </ol>
          </div>
        </section>

        <section className="section" aria-labelledby="run-title">
          <div className="wrap prose-grid">
            <h2 className="h2" id="run-title">{c.runningLabel}</h2>
            <div style={{ display: "grid", gap: 28 }}>
              <p className="prose">{c.running}</p>
              <div style={{ display: "grid", gap: 12 }}>
                <p className="kicker">Tools</p>
                <div className="tools">{c.tools.map((t) => <span key={t} className="chip">{t}</span>)}</div>
              </div>
            </div>
          </div>
        </section>

        <section className="section--tight" style={{ paddingTop: 0 }}>
          <div className="wrap">
            <Link className="next-case" href={`/work/${next.slug}`}>
              <span className="nc-lab">Next case study</span>
              <span className="nc-title">{next.title}</span>
              <span className="small" style={{ color: "inherit", opacity: 0.75 }}>{next.client}, {next.where}</span>
            </Link>
          </div>
        </section>
      </main>
      <CtaBand />
    </>
  );
}
