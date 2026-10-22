import type { Metadata } from "next";
import Link from "next/link";
import { CtaBand, SecHead, TermsList } from "@/components/Blocks";
import { Icon } from "@/components/Icon";
import { SplitHeading } from "@/components/Split";
import { Story } from "@/components/Story";
import { PRINCIPLES, ROLES, SECURITY } from "@/lib/content";

export const metadata: Metadata = {
  title: "About",
  description: "Why we are called Round House, the principles we work by, and how we handle hours, contracts and data security for US clients.",
  alternates: { canonical: "/about" },
};

export default function About() {
  return (
    <>
      <main id="main" className="site-main">
        <section className="page-hero">
          <div className="wrap page-hero-grid">
            <SplitHeading as="h1" className="h1" text="Named after the building that keeps engines running" />
            <div style={{ display: "grid", gap: 16 }}>
              <p className="lede">A roundhouse is where a railroad services its locomotives. Engines roll onto a turntable, get turned to the right bay, are inspected and repaired, and go back out on the right track.</p>
              <p className="lede">That is the job we do for a business. The same thinking applies to a quoting process on a shop floor and to a lead form on a website, which is why we do both.</p>
            </div>
          </div>
        </section>

        <Story />

        <section className="section band-dark on-dark" aria-labelledby="how-title">
          <div className="wrap">
            <SecHead id="how-title" title="How we work" />
            <div className="principles">
              {PRINCIPLES.map(([h, p]) => <div key={h} className="principle"><h3>{h}</h3><p>{p}</p></div>)}
            </div>
          </div>
        </section>

        <section className="section" id="terms" aria-labelledby="terms-title">
          <div className="wrap">
            <SecHead id="terms-title" title="Hours, contracts and data">
              <p className="lede">What your procurement, legal or IT team will want to know before you sign.</p>
            </SecHead>
            <TermsList />
            <div className="faq-grid" style={{ marginTop: "clamp(56px,7vw,96px)" }}>
              <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
                <h3 className="h3">Security practices</h3>
                <p className="small" style={{ maxWidth: "34ch" }}>Need a security questionnaire completed or a DPA signed? We do both as part of onboarding.</p>
              </div>
              <ul className="checklist" data-checklist="">
                {SECURITY.map((s) => (
                  <li key={s}>
                    <svg viewBox="0 0 24 24" aria-hidden="true"><rect className="ck-box" x="1" y="1" width="22" height="22" rx="6" /><path className="ck-path" d="M7 12.5l3.2 3.2L17.2 8.6" /></svg>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section className="section band-alt" aria-labelledby="who-title">
          <div className="wrap">
            <SecHead id="who-title" title="Who you work with">
              <p className="lede">A small senior team. The people on your first call are the people who build your system.</p>
            </SecHead>
            <div className="roles">
              {ROLES.map(([ic, h, p]) => (
                <div key={h} className="role"><span className="role-ic"><Icon name={ic} /></span><h3>{h}</h3><p>{p}</p></div>
              ))}
            </div>
            <div style={{ marginTop: 32 }}><Link className="btn" href="/contact#book">Book a 30-minute call</Link></div>
          </div>
        </section>
      </main>
      <CtaBand />
    </>
  );
}
