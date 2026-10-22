import type { Metadata } from "next";
import { ContactForm } from "@/components/ContactForm";
import { CopyEmail } from "@/components/CopyEmail";
import { HoursLamp } from "@/components/HoursLamp";
import { Icon } from "@/components/Icon";
import { SplitHeading } from "@/components/Split";
import { CAL } from "@/lib/content";

export const metadata: Metadata = {
  title: "Contact",
  description: "Book a 30-minute call or tell us what slows your team down. We reply within one business day, 9am–6pm ET.",
  alternates: { canonical: "/contact" },
};

export default function Contact() {
  return (
    <main id="main" className="site-main">
      <section className="page-hero">
        <div className="wrap page-hero-grid">
          <SplitHeading as="h1" className="h1" text="Tell us what slows your team down" />
          <p className="lede">Book a call if you would rather talk it through, or send the details and we will come back with questions.</p>
        </div>
      </section>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="wrap contact-grid">
          <div className="contact-side">
            <div className="book-card band-dark on-dark" id="book">
              <h2>Book a call</h2>
              <p style={{ color: "var(--on-brunswick-2)" }}>30 minutes, by video or phone, at a time that suits you. No pitch deck.</p>
              <a className="btn" href={CAL} target="_blank" rel="noopener noreferrer" data-magnetic="">Pick a time for the call <Icon name="out" size={16} /></a>
              <HoursLamp style={{ background: "rgba(255,255,255,0.08)", boxShadow: "none", color: "var(--on-brunswick-2)" }} />
            </div>
            <div className="mini-card">
              <h2>Email</h2>
              <CopyEmail light />
              <p className="small">Happy to sign your NDA before we see anything sensitive.</p>
            </div>
            <div className="mini-card">
              <h2>What happens next</h2>
              <ol className="next-steps" style={{ width: "100%" }}>
                <li><span className="n">1</span><span><b>We reply within one business day</b><span>With a few questions, or a time for a call.</span></span></li>
                <li><span className="n">2</span><span><b>A 30-minute call</b><span>We learn how the work moves today.</span></span></li>
                <li><span className="n">3</span><span><b>A written proposal</b><span>Scope, fixed price and timeline within three business days. Usually it starts with an audit.</span></span></li>
              </ol>
            </div>
          </div>
          <div className="form-card"><ContactForm /></div>
        </div>
      </section>
    </main>
  );
}
