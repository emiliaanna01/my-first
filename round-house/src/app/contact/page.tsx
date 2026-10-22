import type { Metadata } from "next";

import { ContactForm } from "@/components/contact-form";
import { HoursStatus } from "@/components/hours-status";
import { Button } from "@/components/ui/button";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: "Contact",
  description: "Book a 30-minute call or tell us what slows your team down. We reply within one business day, 9am–6pm ET.",
  alternates: { canonical: "/contact" },
};

const next = [
  { name: "We reply within one business day", detail: "With a few questions, or a time for a call." },
  { name: "A 30-minute call", detail: "We learn how the work moves today. No pitch deck." },
  { name: "A written proposal", detail: "Scope, fixed price and timeline within three business days. Usually it starts with an audit." },
];

export default function ContactPage() {
  return (
    <section aria-labelledby="page-title" className="shell">
      <div className="grid-12 relative gap-y-14 pt-14 pb-24 md:pt-20 md:pb-32">
        <div className="col-span-4 md:col-span-12">
          <h1 id="page-title" className="t-h1 max-w-[18ch]">
            Tell us what slows your team down
          </h1>
          <p className="t-lead mt-6 max-w-[50ch]">
            Book a call if you would rather talk it through, or send the details and we will come back with questions.
          </p>
        </div>

        <div className="col-span-4 md:col-span-7">
          <div className="border-t border-ink bg-plant pt-8">
            <h2 className="t-h3 mb-6">Send the details</h2>
            <ContactForm />
          </div>
        </div>

        <aside className="col-span-4 md:col-span-4 md:col-start-9" aria-label="Other ways to reach us">
          <div className="border-t border-ink bg-plant pt-8">
            <h2 className="t-h3">Book a call</h2>
            <p className="mt-2 text-steel">30 minutes, by video or phone, at a time that suits you.</p>
            <Button asChild className="mt-5 w-full sm:w-auto">
              <a href={site.bookingUrl}>Book a 30-minute call</a>
            </Button>
            <HoursStatus className="mt-5" />

            <h2 className="t-h3 mt-12">Email</h2>
            <p className="mt-2">
              <a className="underline underline-offset-4 hover:decoration-2" href={`mailto:${site.email}`}>
                {site.email}
              </a>
            </p>
            <p className="t-small mt-2 text-steel">Happy to sign your NDA before we see anything sensitive.</p>

            <h2 className="t-h3 mt-12">What happens next</h2>
            <ol className="mt-4 border-b border-ink">
              {next.map((s, i) => (
                <li key={s.name} className="grid grid-cols-[2rem_1fr] border-t border-rule py-4">
                  <span className="tnum font-bold">{i + 1}.</span>
                  <span>
                    <span className="block font-semibold">{s.name}</span>
                    <span className="block text-steel">{s.detail}</span>
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </aside>
      </div>
    </section>
  );
}
