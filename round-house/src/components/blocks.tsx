import Link from "next/link";

import type { CaseStudy } from "@/content/work";
import { cn } from "@/lib/utils";

export function SampleTag({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border border-rule bg-panel px-2 py-0.5 text-[13px] font-semibold text-steel",
        className,
      )}
    >
      Sample engagement
    </span>
  );
}

/** Section opener: heading in columns 1–7, optional intro, optional action on the right. */
export function SectionHead({
  id,
  title,
  intro,
  action,
  className,
}: {
  id?: string;
  title: string;
  intro?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("grid-12 items-end gap-y-6", className)}>
      <div className="col-span-4 md:col-span-8">
        <h2 id={id} className="t-h2 max-w-[20ch]">
          {title}
        </h2>
        {intro && <p className="t-lead mt-5 max-w-[56ch]">{intro}</p>}
      </div>
      {action && <div className="col-span-4 md:col-span-4 md:justify-self-end">{action}</div>}
    </div>
  );
}

export function TextLink({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) {
  return (
    <Link
      href={href}
      className={cn("inline-flex min-h-11 items-center font-semibold underline underline-offset-4 hover:decoration-2", className)}
    >
      {children}
    </Link>
  );
}

/** A result figure. The signal bar marks it as a result, per the colour rule. */
export function Figure({ value, label, className }: { value: string; label: string; className?: string }) {
  return (
    <div className={className}>
      <p className="t-figure">
        <span className="border-b-[6px] border-signal pb-1">{value}</span>
      </p>
      <p className="mt-4 max-w-[28ch] text-[16px] text-steel">{label}</p>
    </div>
  );
}

export function CaseRow({ study, headingLevel = "h3" }: { study: CaseStudy; headingLevel?: "h2" | "h3" }) {
  const H = headingLevel;
  const lead = study.figures[0];
  return (
    <li className="group relative border-t border-ink">
      <div className="grid-12 gap-y-4 py-8 md:py-10">
        <div className="col-span-4 md:col-span-3">
          <p className="font-semibold">{study.client}</p>
          <p className="t-small mt-1 text-steel">{study.location}</p>
          <p className="t-small mt-3 text-steel">{study.tiers.join(", ")}</p>
        </div>
        <div className="col-span-4 md:col-span-6">
          <H className="t-h3 max-w-[30ch] text-[1.5rem] md:text-[1.75rem]">
            <Link
              href={`/work/${study.slug}`}
              className="after:absolute after:inset-0 group-hover:underline group-hover:decoration-2 group-hover:underline-offset-4 focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:outline-ink focus-visible:after:-outline-offset-2"
            >
              {study.headline}
            </Link>
          </H>
          <p className="mt-3 max-w-[52ch] text-steel">{study.summary}</p>
          <SampleTag className="mt-4" />
        </div>
        <div className="col-span-4 md:col-span-3 md:text-right">
          <p className="wide tnum text-[2.5rem] leading-none font-[760] tracking-[-0.02em]">{lead.value}</p>
          <p className="t-small mt-2 text-steel md:ml-auto md:max-w-[22ch]">{lead.label}</p>
        </div>
      </div>
    </li>
  );
}

export function SpecSheet({ rows, className }: { rows: { term: string; detail: React.ReactNode }[]; className?: string }) {
  return (
    <dl className={cn("border-b border-ink", className)}>
      {rows.map((r) => (
        <div key={r.term} className="grid gap-1 border-t border-ink py-5 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] md:gap-6">
          <dt className="font-semibold">{r.term}</dt>
          <dd className="max-w-[60ch] text-steel">{r.detail}</dd>
        </div>
      ))}
    </dl>
  );
}

export const usTerms = [
  { term: "Hours", detail: "9am–6pm Eastern, Monday to Friday. Replies within one business day, faster on a retainer." },
  { term: "Contracts", detail: "Mutual NDA before discovery. Every project runs on a master services agreement and a fixed-price statement of work." },
  { term: "Pricing", detail: "Published ranges for every service. The audit fee is credited to your build if you go ahead within 60 days." },
  {
    term: "Data security",
    detail:
      "We work inside your accounts with the least access the job needs, require MFA, never train models on your data, and remove our access at handover.",
  },
  { term: "Ownership", detail: "You own the code, automations, prompts and documentation. Nothing is locked to a platform we control." },
  { term: "Measurement", detail: "We record a baseline before we build and report hours saved, response times and revenue influenced against it." },
];
