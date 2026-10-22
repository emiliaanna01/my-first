import Link from "next/link";

import { Wordmark } from "@/components/logo";
import { nav, site } from "@/content/site";

/** Styled as the title block in the corner of an engineering drawing. */
export function SiteFooter() {
  return (
    <footer className="on-ink bg-ink text-plant">
      <div className="shell pt-16 pb-10 md:pt-20">
        <div className="grid-12 gap-y-10">
          <div className="col-span-4 md:col-span-6">
            <p className="t-h2 max-w-[14ch]">Bring us the work that slows you down.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/contact"
                className="inline-flex min-h-12 items-center rounded-sm bg-signal px-[22px] font-semibold text-ink transition-colors hover:bg-[#f0b400]"
              >
                Book a 30-minute call
              </Link>
              <a
                href={`mailto:${site.email}`}
                className="inline-flex min-h-12 items-center rounded-sm border border-plant px-[22px] font-semibold transition-colors hover:bg-plant hover:text-ink"
              >
                Email us
              </a>
            </div>
          </div>
          <nav aria-label="Footer" className="col-span-4 md:col-span-3 md:col-start-10">
            <ul className="grid gap-1">
              {[{ href: "/", label: "Home" }, ...nav].map((item) => (
                <li key={item.href}>
                  <Link href={item.href} className="inline-flex min-h-10 items-center text-plant/85 hover:text-plant hover:underline underline-offset-4">
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <dl className="mt-16 grid grid-cols-1 border border-ink-rule sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1.2fr_1fr_0.8fr]">
          <div className="border-b border-ink-rule p-4 sm:col-span-2 lg:col-span-1 lg:border-r lg:border-b-0">
            <dt className="text-xs font-medium text-ink-muted">Studio</dt>
            <dd className="mt-2">
              <Wordmark tone="plant" />
            </dd>
          </div>
          <div className="border-b border-ink-rule p-4 sm:border-r lg:border-b-0">
            <dt className="text-xs font-medium text-ink-muted">Hours</dt>
            <dd className="mt-1 text-[15px]">{site.hours.label}</dd>
          </div>
          <div className="border-b border-ink-rule p-4 lg:border-r lg:border-b-0">
            <dt className="text-xs font-medium text-ink-muted">Contact</dt>
            <dd className="mt-1 text-[15px]">
              <a href={`mailto:${site.email}`} className="underline-offset-4 hover:underline">
                {site.email}
              </a>
            </dd>
          </div>
          <div className="border-b border-ink-rule p-4 sm:border-r sm:border-b-0 lg:border-r">
            <dt className="text-xs font-medium text-ink-muted">Contracts</dt>
            <dd className="mt-1 text-[15px]">Mutual NDA, MSA and fixed-price SOW</dd>
          </div>
          <div className="p-4">
            <dt className="text-xs font-medium text-ink-muted">Rev.</dt>
            <dd className="mt-1 text-[15px] tnum">C, {site.updated}</dd>
          </div>
        </dl>
        <p className="mt-6 text-xs text-ink-muted">© 2026 Round House. Case studies marked as samples are illustrative.</p>
      </div>
    </footer>
  );
}
