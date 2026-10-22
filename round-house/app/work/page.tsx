import type { Metadata } from "next";
import { CtaBand } from "@/components/Blocks";
import { Icon } from "@/components/Icon";
import { SplitHeading } from "@/components/Split";
import { WorkList } from "@/components/WorkList";

export const metadata: Metadata = {
  title: "Work",
  description: "Case studies in automation, AI agents, CRM and web for US field services, manufacturing, logistics and healthcare, each with measured results.",
  alternates: { canonical: "/work" },
};

export default function Work() {
  return (
    <>
      <main id="main" className="site-main">
        <section className="page-hero">
          <div className="wrap page-hero-grid">
            <SplitHeading as="h1" className="h1" text="Work, measured" />
            <p className="lede">Each study starts with the baseline we measured, then what we built and what changed. Filter by the step of the engagement.</p>
          </div>
        </section>
        <section className="section--tight" style={{ paddingTop: 0 }}>
          <div className="wrap">
            <p className="notice"><Icon name="info" /><span>These four are sample engagements. They show the kind of work we do and how we report results, and the figures are illustrative. Published client studies replace them as clients approve.</span></p>
            <WorkList />
          </div>
        </section>
      </main>
      <CtaBand />
    </>
  );
}
