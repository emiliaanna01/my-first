import type { Metadata } from "next";
import Link from "next/link";

import { SectionHead, SpecSheet, usTerms } from "@/components/blocks";
import { LogoMark } from "@/components/logo";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "About",
  description:
    "Why we are called Round House, the principles we work by, and how we handle hours, contracts and data security for US clients.",
  alternates: { canonical: "/about" },
};

const principles = [
  { name: "Outcome before tool", detail: "We start from the hours, the response time or the revenue you want to change. The software comes second." },
  { name: "Measure before and after", detail: "A baseline goes in writing before we build, so the result is a number, not an opinion." },
  { name: "Build in your stack", detail: "We use the CRM, accounts and tools you already pay for wherever we can, so nothing new has to be adopted." },
  { name: "Leave it documented", detail: "Every system ships with a runbook and a training session. Your team can own it without us." },
];

const security = [
  "Least-privilege access through your own accounts, never shared passwords",
  "MFA required on every account we use",
  "Client data is never used to train AI models",
  "AI providers that delete your data after each request, where they offer it",
  "Data stays in your systems. We do not copy it to ours",
  "Access removed and confirmed in writing at handover",
];

const roles = [
  { role: "Systems lead", detail: "Runs the audit, maps your processes and owns the roadmap. Your main contact from first call to handover." },
  { role: "Automation engineer", detail: "Builds and tests the integrations, agents and dashboards, and writes the runbooks." },
  { role: "Brand and web designer", detail: "Designs the identity, website and collateral, so what customers see matches how you operate." },
];

export default function AboutPage() {
  return (
    <>
      <section aria-labelledby="page-title" className="shell drafting">
        <div className="grid-12 relative gap-y-10 pt-14 pb-16 md:pt-20 md:pb-24">
          <div className="col-span-4 md:col-span-8">
            <h1 id="page-title" className="t-h1 max-w-[16ch]">
              Named after the building that keeps engines running
            </h1>
          </div>
          <div className="col-span-4 grid gap-5 md:col-span-6 md:col-start-1">
            <p className="t-lead">
              A roundhouse is where a railroad services its locomotives. Engines roll onto a turntable, get turned to the
              right bay, are inspected and repaired, and go back out on the right track.
            </p>
            <p className="max-w-[56ch]">
              That is the job we do for a business. Work comes in, we find where it stalls, rebuild the part that slows it
              down and keep it running. The same thinking applies to a quoting process on a shop floor and to a lead form
              on a website, which is why we do both.
            </p>
          </div>
          <div className="col-span-4 hidden md:col-span-4 md:col-start-9 md:block">
            <LogoMark className="ml-auto w-full max-w-[300px]" hub="plain" />
          </div>
        </div>
      </section>

      <section aria-labelledby="principles-title" className="border-t border-rule bg-panel">
        <div className="shell section-pad">
          <SectionHead id="principles-title" title="How we work" />
          <ul className="mt-12 grid border-b border-ink md:mt-16 md:grid-cols-2 md:gap-x-6">
            {principles.map((p) => (
              <li key={p.name} className="border-t border-ink py-6">
                <h3 className="t-h3">{p.name}</h3>
                <p className="mt-2 max-w-[46ch] text-steel">{p.detail}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section id="terms" aria-labelledby="terms-title" className="border-t border-rule">
        <div className="shell section-pad grid-12 gap-y-12">
          <div className="col-span-4 md:col-span-5">
            <h2 id="terms-title" className="t-h2 max-w-[14ch]">
              Hours, contracts and data
            </h2>
            <p className="t-lead mt-5 max-w-[36ch]">
              What your procurement, legal or IT team will want to know before you sign.
            </p>
          </div>
          <div className="col-span-4 md:col-span-7">
            <SpecSheet rows={usTerms} />
            <h3 className="t-h3 mt-14">Security practices</h3>
            <ul className="mt-4 border-b border-ink">
              {security.map((s) => (
                <li key={s} className="border-t border-rule py-3.5">
                  {s}
                </li>
              ))}
            </ul>
            <p className="t-small mt-5 text-steel">
              Need a security questionnaire completed or a DPA signed? We do both as part of onboarding.
            </p>
          </div>
        </div>
      </section>

      <section aria-labelledby="team-title" className="border-t border-rule bg-panel">
        <div className="shell section-pad">
          <SectionHead
            id="team-title"
            title="Who you work with"
            intro="A small senior team. The people on your first call are the people who build your system."
          />
          <dl className="mt-12 grid border-b border-ink md:mt-16 md:grid-cols-3 md:gap-x-6">
            {roles.map((r) => (
              <div key={r.role} className="border-t border-ink py-6">
                <dt className="t-h3">{r.role}</dt>
                <dd className="mt-2 max-w-[38ch] text-steel">{r.detail}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-12">
            <Button asChild size="lg">
              <Link href="/contact#book">Book a 30-minute call</Link>
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}
