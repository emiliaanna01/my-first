"use client";

import * as React from "react";
import Link from "next/link";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

import type { Tier } from "@/content/services";
import { cn } from "@/lib/utils";

gsap.registerPlugin(useGSAP, ScrollTrigger);

/**
 * Diagnose → Build → Run as one railway line with three stations. This is a real sequence,
 * so the numbering is honest. The rail draws itself as the section scrolls into view; with
 * reduced motion it is simply there.
 */
export function TrackLine({ tiers, linkPrefix = "/services" }: { tiers: Tier[]; linkPrefix?: string }) {
  const root = React.useRef<HTMLOListElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference) and (min-width: 768px)", () => {
        gsap.fromTo(
          ".tl-rail",
          { scaleX: 0 },
          {
            scaleX: 1,
            ease: "none",
            scrollTrigger: { trigger: root.current, start: "top 85%", end: "top 40%", scrub: 0.6 },
          },
        );
        gsap.utils.toArray<HTMLElement>(".tl-stop").forEach((stop, i) => {
          gsap.fromTo(
            stop,
            { backgroundColor: "#e8ebe9" },
            {
              backgroundColor: i === 0 ? "#ffc21a" : "#f6f7f6",
              scrollTrigger: {
                trigger: root.current,
                start: `top ${85 - i * 20}%`,
                toggleActions: "play none none reverse",
              },
              duration: 0.2,
            },
          );
        });
      });
    },
    { scope: root },
  );

  return (
    <ol ref={root} className="relative grid gap-10 md:grid-cols-3 md:gap-6 md:pt-12">
      <span
        aria-hidden="true"
        className="tl-rail absolute top-[13px] left-[13px] hidden h-0.5 w-[calc(100%-13px)] origin-left bg-ink md:block"
      />
      {tiers.map((t, i) => (
        <li key={t.id} className="relative pl-12 md:pl-0">
          <span
            aria-hidden="true"
            className={cn(
              "tl-stop absolute top-0.5 left-0 size-7 rounded-full border-2 border-ink md:-top-12",
              i === 0 ? "bg-signal" : "bg-panel",
            )}
          />
          {i < tiers.length - 1 && (
            <span aria-hidden="true" className="absolute top-8 bottom-[-40px] left-[13px] w-0.5 bg-ink md:hidden" />
          )}
          <h3 className="t-h3">
            <span className="tnum">{t.step}.</span> {t.name}
          </h3>
          <p className="mt-2 max-w-[34ch] text-steel">{t.summary}</p>
          <p className="wide tnum mt-5 text-xl font-bold">{t.price}</p>
          <p className="t-small mt-1 max-w-[30ch] text-steel">{t.priceNote}</p>
          <Link
            href={`${linkPrefix}#${t.id}`}
            className="mt-4 inline-flex min-h-11 items-center font-semibold underline underline-offset-4 hover:decoration-2"
          >
            What {t.name.toLowerCase()} includes
          </Link>
        </li>
      ))}
    </ol>
  );
}
