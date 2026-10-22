"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { site } from "@/content/site";

/** The closing call to action. Left out on /contact, which already is that page. */
export function FooterCta() {
  const pathname = usePathname();
  if (pathname === "/contact") return <div className="col-span-4 md:col-span-6" />;

  return (
    <div className="col-span-4 md:col-span-6">
      <p className="t-h2 max-w-[14ch]">Bring us the work that slows you down.</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/contact#book"
          className="inline-flex min-h-12 items-center rounded-sm bg-signal px-[22px] font-semibold text-ink transition-colors hover:bg-signal-press"
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
  );
}
