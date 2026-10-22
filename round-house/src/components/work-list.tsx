"use client";

import * as React from "react";

import { CaseRow } from "@/components/blocks";
import type { CaseStudy } from "@/content/work";
import { cn } from "@/lib/utils";

const filters = ["All", "Diagnose", "Build", "Run"] as const;

export function WorkList({ studies }: { studies: CaseStudy[] }) {
  const [filter, setFilter] = React.useState<(typeof filters)[number]>("All");
  const shown = filter === "All" ? studies : studies.filter((s) => s.tiers.includes(filter));

  return (
    <>
      <div role="group" aria-label="Filter case studies by step" className="flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f}
            type="button"
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
            className={cn(
              "inline-flex min-h-11 items-center rounded-sm border border-ink px-4 text-[15px] font-semibold transition-colors",
              filter === f ? "bg-ink text-plant" : "hover:bg-ink/5",
            )}
          >
            {f}
          </button>
        ))}
      </div>
      <p className="t-small mt-4 text-steel" aria-live="polite">
        {filter === "All" ? `${studies.length} case studies` : `${shown.length} of ${studies.length} include ${filter}`}
      </p>
      <ul className="mt-8 border-b border-ink">
        {shown.map((s) => (
          <CaseRow key={s.slug} study={s} headingLevel="h2" />
        ))}
      </ul>
    </>
  );
}
