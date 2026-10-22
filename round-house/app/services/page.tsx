import type { Metadata } from "next";
import Link from "next/link";
import { Calculator } from "@/components/Calculator";
import { CtaBand, SecHead, Stations } from "@/components/Blocks";
import { Faq } from "@/components/Faq";
import { SplitHeading } from "@/components/Split";
import { Subnav } from "@/components/Subnav";
import { BUILD, DIAGNOSE, FAQ, PLANS, PRACTICES, RUN, STEPS, type Row, type Step } from "@/lib/content";

export const metadata: Metadata = {
  title: "Services and prices",
  description: "Audits, automation, AI agents, CRM migration, brand and websites for US businesses. Three steps, Diagnose, Build and Run, with published price ranges.",
  alternates: { canonical: "/services" },
};

function StepAside({ s, i }: { s: Step; i: number }) {
  return (
    <div className="step-aside">
      <span className="step-n">Step {i + 1} of 3</span>
      <h2 className="h2">{s.name}</h2>
      <p className="lede">{s.desc}</p>
      <p className="big-price">{s.price}</p>
      <p className="station-terms">{s.terms}</p>
      <p className="outcome">{s.outcome}</p>
    </div>
  );
}

function Rows({ rows, plan = false }: { rows: Row[]; plan?: boolean }) {
  return (
    <>
      {rows.map(([n, d, p]) => (
        <tr key={n}>
          <td><span className="svc">{n}</span><span className="desc">{d}</span></td>
          <td className="price">{plan ? <span className="price-tag">{p}</span> : p}</td>
        </tr>
      ))}
    </>
  );
}

const SUBNAV: [string, string][] = [["steps", "Overview"], ["diagnose", "Diagnose"], ["build", "Build"], ["run", "Run"], ["retainers", "Retainers"], ["payback", "Payback"], ["practices", "Practices"], ["faq", "Questions"]];

export default function Services() {
  return (
    <>
      <main id="main" className="site-main">
        <section className="page-hero">
          <div className="wrap page-hero-grid">
            <SplitHeading as="h1" className="h1" text="Services and prices" />
            <p className="lede">Three steps. Pay for an audit, build what it recommends at a fixed price, then keep it running on a monthly plan. Every price on this page is a real range, not a starting bid.</p>
          </div>
        </section>
        <Subnav items={SUBNAV} />

        <section className="section" id="steps" aria-labelledby="steps-title">
          <div className="wrap">
            <SecHead id="steps-title" title="The three steps and their prices" />
            <Stations />
          </div>
        </section>

        <section className="section band-alt" id="diagnose" aria-label="Diagnose">
          <div className="wrap step-block">
            <StepAside s={STEPS[0]} i={0} />
            <div style={{ minWidth: 0, overflowX: "auto" }}>
              <table className="pricelist">
                <caption className="sr-only">What Diagnose includes, with prices</caption>
                <thead><tr><th scope="col">Service</th><th scope="col" className="price">Typical price</th></tr></thead>
                <tbody><Rows rows={DIAGNOSE} /></tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="section" id="build" aria-label="Build">
          <div className="wrap step-block">
            <StepAside s={STEPS[1]} i={1} />
            <div style={{ minWidth: 0, overflowX: "auto" }}>
              <table className="pricelist">
                <caption className="sr-only">What Build includes, with prices</caption>
                <thead><tr><th scope="col">Service</th><th scope="col" className="price">Typical price</th></tr></thead>
                {BUILD.map((g) => (
                  <tbody key={g.group}>
                    <tr className="group"><th colSpan={2} scope="colgroup">{g.group}</th></tr>
                    <Rows rows={g.rows} />
                  </tbody>
                ))}
              </table>
            </div>
          </div>
        </section>

        <section className="section band-alt" id="run" aria-label="Run">
          <div className="wrap step-block">
            <StepAside s={STEPS[2]} i={2} />
            <div style={{ minWidth: 0, overflowX: "auto" }}>
              <table className="pricelist">
                <caption className="sr-only">What Run includes, with prices</caption>
                <thead><tr><th scope="col">Service</th><th scope="col" className="price">Plan</th></tr></thead>
                <tbody><Rows rows={RUN} plan /></tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="section" id="retainers" aria-labelledby="ret-title">
          <div className="wrap">
            <SecHead id="ret-title" title="Run retainers">
              <p className="lede">Pick the level of support that matches how much you automate. Month to month after the first three months. Prices per month.</p>
            </SecHead>
            <div className="plans">
              {PLANS.map((p) => (
                <article key={p.name} className={`plan${p.pick ? " plan--pick" : ""}`}>
                  {p.pick && <span className="plan-flag">Most clients pick this</span>}
                  <h3>{p.name}</h3>
                  <p className="plan-price">{p.price}<small>/mo</small></p>
                  <p className="plan-best">Best for: {p.best.charAt(0).toLowerCase() + p.best.slice(1)}</p>
                  <ul>{p.items.map((i) => <li key={i}>{i}</li>)}</ul>
                  <Link className={`btn${p.pick ? "" : " btn--ghost"}`} href="/contact?interest=run" style={{ justifySelf: "start" }}>Ask about {p.name}</Link>
                </article>
              ))}
            </div>
            <div className="plans-foot">
              <p className="small">Need a named automation lead with more hours? Fractional plans start at $6,000 a month.</p>
              <Link className="ulink" href="/contact?interest=run">Ask about a retainer</Link>
            </div>
          </div>
        </section>

        <section className="section--tight" id="payback" aria-labelledby="calc-title">
          <div className="wrap"><Calculator /></div>
        </section>

        <section className="section" id="practices" aria-labelledby="prac-title">
          <div className="wrap">
            <SecHead id="prac-title" title="Six practices, one team">
              <p className="lede">Every step draws on the same people, so the audit, the build and the brand never get lost between agencies.</p>
            </SecHead>
            <div className="pgrid">
              {PRACTICES.map((p) => (
                <div key={p.name} className="pcell">
                  <h3>{p.name}</h3>
                  <p>{p.desc}</p>
                  <ul>{p.items.map((i) => <li key={i}>{i}</li>)}</ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="section band-alt" id="faq" aria-labelledby="faq-title">
          <div className="wrap faq-grid">
            <div style={{ display: "grid", gap: 18, alignContent: "start", justifyItems: "start" }}>
              <h2 className="h2" id="faq-title">Questions buyers ask us</h2>
              <p className="lede">Still unsure? Ask on a call. We answer straight, including when we are not the right fit.</p>
            </div>
            <Faq items={FAQ} />
          </div>
        </section>
      </main>
      <CtaBand />
    </>
  );
}
