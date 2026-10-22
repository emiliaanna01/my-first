import type { Metadata } from "next";

import { WorkList } from "@/components/work-list";
import { caseStudies } from "@/content/work";

export const metadata: Metadata = {
  title: "Work",
  description:
    "Case studies in automation, AI agents, CRM and web for US field services, manufacturing, logistics and healthcare, each with measured results.",
  alternates: { canonical: "/work" },
};

export default function WorkPage() {
  return (
    <>
      <section aria-labelledby="page-title" className="shell drafting">
        <div className="grid-12 relative pt-14 pb-14 md:pt-20 md:pb-20">
          <div className="col-span-4 md:col-span-9">
            <h1 id="page-title" className="t-h1 max-w-[16ch]">
              Work, measured
            </h1>
            <p className="t-lead mt-6 max-w-[54ch]">
              Each study starts with the baseline we measured, then what we built and what changed. Filter by the step of
              the engagement.
            </p>
            <p className="mt-6 max-w-[60ch] border-l-[3px] border-rule pl-4 text-[16px] text-steel">
              These four are sample engagements. They show the kind of work we do and how we report results, and the
              figures are illustrative. Published client studies replace them as clients approve.
            </p>
          </div>
        </div>
      </section>
      <section aria-label="Case studies" className="border-t border-rule">
        <div className="shell pt-10 pb-24 md:pt-14 md:pb-32">
          <WorkList studies={caseStudies} />
        </div>
      </section>
    </>
  );
}
