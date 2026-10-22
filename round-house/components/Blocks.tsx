import Link from "next/link";
import { STEPS, TERMS, type CaseStudy } from "@/lib/content";
import { CopyEmail } from "./CopyEmail";
import { Icon } from "./Icon";
import { Mark } from "./Mark";
import { SplitHeading } from "./Split";

export function SampleNote() {
  return (
    <p className="sample-note">
      <b>Sample engagement.</b> Illustrative figures. Published client studies replace these as clients approve.
    </p>
  );
}

export function CtaBand() {
  return (
    <section className="cta-band band-dark on-dark" aria-labelledby="cta-title">
      <Mark className="cta-mark" />
      <div className="wrap">
        <SplitHeading as="h2" id="cta-title" text="Bring us the work that slows you down." />
        <div className="cta-row">
          <Link className="btn" href="/contact#book" data-magnetic="">
            <span className="lamp" aria-hidden="true" />Book a 30-minute call
          </Link>
          <CopyEmail />
        </div>
        <p className="small">Calls 9am–6pm ET, Monday to Friday. Happy to sign your NDA before we see anything sensitive.</p>
      </div>
    </section>
  );
}

export function CaseCard({ c, desc = false, as: H = "h3", count = true, hidden }: { c: CaseStudy; desc?: boolean; as?: "h2" | "h3"; count?: boolean; hidden?: boolean }) {
  return (
    <Link className="case-card on-dark" href={`/work/${c.slug}`} data-steps={c.steps.join(" ")} data-spot="" hidden={hidden}>
      <div className="cc-top">
        <span><strong>{c.client}</strong><br />{c.where}</span>
        <span className="cc-steps">{c.steps.map((s) => <span key={s} className="chip">{s}</span>)}</span>
      </div>
      <H>{c.title}</H>
      {desc ? <p className="cc-desc">{c.summary}</p> : <span />}
      <div style={{ display: "grid", gap: 18 }}>
        <div className="cc-metric">
          <span className="cc-num" data-count={count ? "" : undefined}>{c.metric}</span>
          <span className="cc-cap">{c.metricCap}</span>
        </div>
        <div className="cc-foot">
          <span><b>Investment</b> {c.investment}</span>
          <span><b>Payback</b> {c.payback}</span>
        </div>
      </div>
    </Link>
  );
}

/** Diagnose, Build and Run as stations on a track. The motion layer drives the engine along it. */
export function Stations() {
  return (
    <div className="track-wrap" data-track="">
      <div className="rail" aria-hidden="true">
        <div className="rail-bed" />
        <div className="rail-fill" />
        <div className="rail-loco" />
      </div>
      <ol className="stations">
        {STEPS.map((s, i) => (
          <li key={s.key} className="station" data-station="">
            <span className="station-node" aria-hidden="true" />
            <span className="station-step">Step {i + 1} of 3</span>
            <h3>{s.name}</h3>
            <p>{s.desc}</p>
            <p className="station-price">{s.price}</p>
            <p className="station-terms">{s.terms}</p>
            <Link className="ulink" href={`/services#${s.key}`}>What {s.name.toLowerCase()} includes</Link>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function TermsList() {
  return (
    <dl className="terms">
      {TERMS.map((t) => (
        <div key={t.name} className="term">
          <dt><Icon name={t.icon} />{t.name}</dt>
          <dd>{t.text}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SecHead({ title, id, children, split = true }: { title: string; id: string; children?: React.ReactNode; split?: boolean }) {
  return (
    <div className={`sec-head${children ? " sec-head--split" : ""}`}>
      {split ? <SplitHeading as="h2" className="h2" id={id} text={title} /> : <h2 className="h2" id={id}>{title}</h2>}
      {children ? <div className="sec-head-side">{children}</div> : null}
    </div>
  );
}
