import Link from "next/link";
import { CaseRail } from "@/components/CaseRail";
import { CtaBand, SampleNote, SecHead, Stations, TermsList } from "@/components/Blocks";
import { Hero } from "@/components/Hero";
import { PRACTICES, TOOLS } from "@/lib/content";

export default function Home() {
  return (
    <>
      <main id="main" className="site-main">
        <Hero />

        <section className="section band-alt" aria-labelledby="proof-title">
          <div className="wrap">
            <SecHead id="proof-title" title="Measured in hours, not hype.">
              <p className="lede">Every engagement starts with a baseline, so the result is a number you can check, and every case study shows what it cost.</p>
            </SecHead>
            <div className="metrics">
              <div className="metric"><span className="metric-num" data-count="">+38%</span><p><strong>Booked service calls</strong> in the first quarter. Regional HVAC and plumbing company.</p></div>
              <div className="metric"><span className="metric-num" data-count="">2.1×</span><p><strong>Quotes sent per week</strong> by the same two estimators. Metal fabrication shop.</p></div>
              <div className="metric"><span className="metric-num" data-count="">26 h</span><p><strong>Accounts-payable time</strong> returned each week. Third-party logistics provider.</p></div>
            </div>
            <div className="metrics-foot"><SampleNote /><Link className="ulink" href="/work">See the case studies</Link></div>
          </div>
        </section>

        <section className="section" id="pricing" aria-labelledby="steps-title">
          <div className="wrap">
            <SecHead id="steps-title" title="Start with a paid audit. Then decide.">
              <p className="lede">We sell outcomes in three steps, with prices on the page. The audit fee comes off the build if you go ahead within 60 days, so the first step carries little risk.</p>
            </SecHead>
            <Stations />
          </div>
        </section>

        <section className="section band-alt" aria-labelledby="practices-title">
          <div className="wrap practices-grid">
            <div className="practices-intro">
              <h2 className="h2" id="practices-title">One team for the systems and the shop window.</h2>
              <p className="lede">Most agencies do either the automation or the brand. We do both, so the website that captures the lead and the system that answers it are built to work together.</p>
              <Link className="ulink" href="/services">All services and prices</Link>
            </div>
            <div className="plist">
              {PRACTICES.map((p) => (
                <Link key={p.name} className="prow" href="/services#practices">
                  <h3><span className="plamp" aria-hidden="true" />{p.name}</h3>
                  <div>
                    <p>{p.desc}</p>
                    <ul>{p.items.map((i) => <li key={i} className="chip">{i}</li>)}</ul>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <CaseRail />

        <section className="section--tight" aria-label="Tools we work with">
          <div className="marquee">
            <div className="marquee-track">
              {[...TOOLS, ...TOOLS].map((t, i) => <span key={i} aria-hidden={i >= TOOLS.length ? true : undefined}>{t}</span>)}
            </div>
          </div>
        </section>

        <section className="section" aria-labelledby="terms-title">
          <div className="wrap">
            <SecHead id="terms-title" title="How we work with US teams">
              <p className="lede">The terms a procurement or IT review will ask about, answered before the first call.</p>
              <Link className="ulink" href="/about#terms">More on security and contracts</Link>
            </SecHead>
            <TermsList />
          </div>
        </section>
      </main>
      <CtaBand />
    </>
  );
}
