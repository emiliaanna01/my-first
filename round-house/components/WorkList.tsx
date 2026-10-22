"use client";
import { useLayoutEffect, useRef, useState } from "react";
import { CASES } from "@/lib/content";
import { Flip, gsap, prefersReducedMotion, ScrollTrigger } from "@/lib/gsap";
import { CaseCard } from "./Blocks";

const FILTERS = ["All", "Diagnose", "Build", "Run"] as const;
type Filter = (typeof FILTERS)[number];
const matches = (f: Filter, steps: string[]) => f === "All" || steps.includes(f);

/** Case studies filtered by engagement step; the grid reflows with a FLIP animation. */
export function WorkList() {
  const [filter, setFilter] = useState<Filter>("All");
  const list = useRef<HTMLDivElement>(null);
  const pending = useRef<{ state: Flip.FlipState; entering: Element[]; leaving: Element[] } | null>(null);
  const busy = useRef(false);

  const cards = () => Array.from(list.current?.querySelectorAll<HTMLElement>(".case-card") ?? []);

  const apply = (f: Filter) => {
    if (busy.current || f === filter) return;
    if (prefersReducedMotion()) return setFilter(f);
    busy.current = true;
    const all = cards();
    const leaving = all.filter((c) => !c.hidden && !matches(f, c.dataset.steps!.split(" ")));
    const staying = all.filter((c) => !c.hidden && matches(f, c.dataset.steps!.split(" ")));
    const entering = all.filter((c) => c.hidden && matches(f, c.dataset.steps!.split(" ")));
    gsap.to(leaving, {
      opacity: 0, scale: 0.96, duration: leaving.length ? 0.25 : 0, ease: "power2.in",
      onComplete: () => {
        pending.current = { state: Flip.getState(staying), entering, leaving };
        setFilter(f);
      },
    });
  };

  useLayoutEffect(() => {
    const p = pending.current;
    if (!p) return;
    pending.current = null;
    gsap.set(p.leaving, { clearProps: "opacity,transform" });
    Flip.from(p.state, { duration: 0.65, ease: "power3.inOut" });
    if (p.entering.length) {
      gsap.fromTo(p.entering, { opacity: 0, scale: 0.96, y: 20 }, { opacity: 1, scale: 1, y: 0, duration: 0.6, ease: "power3.out", stagger: 0.06, delay: 0.15, clearProps: "transform", onComplete: () => { busy.current = false; } });
    } else gsap.delayedCall(0.7, () => { busy.current = false; });
    gsap.delayedCall(0.8, () => ScrollTrigger.refresh());
  }, [filter]);

  const n = CASES.filter((c) => matches(filter, c.steps)).length;
  return (
    <>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "center", justifyContent: "space-between", marginTop: 40 }}>
        <div className="filters" role="group" aria-label="Filter by step">
          {FILTERS.map((f) => (
            <button key={f} className="filter-btn" type="button" aria-pressed={f === filter} onClick={() => apply(f)}>{f}</button>
          ))}
        </div>
        <p className="filter-count" aria-live="polite">{n} case {n === 1 ? "study" : "studies"}</p>
      </div>
      <div className="work-list" ref={list}>
        {CASES.map((c) => (
          <CaseCard key={c.slug} c={c} desc as="h2" count={false} hidden={!matches(filter, c.steps)} />
        ))}
      </div>
    </>
  );
}
