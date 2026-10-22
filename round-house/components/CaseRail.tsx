"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { CASES } from "@/lib/content";
import { prefersReducedMotion } from "@/lib/gsap";
import { CaseCard, SampleNote } from "./Blocks";
import { Icon } from "./Icon";
import { SplitHeading } from "./Split";

/** Selected work: a horizontal rail with arrow buttons, keyboard control and mouse drag. */
export function CaseRail() {
  const rail = useRef<HTMLDivElement>(null);
  const [atStart, setAtStart] = useState(true);
  const [atEnd, setAtEnd] = useState(false);
  const drag = useRef<{ x: number; left: number } | null>(null);
  const moved = useRef(false);

  const step = () => {
    const c = rail.current?.firstElementChild as HTMLElement | null;
    return c ? c.getBoundingClientRect().width + 20 : 400;
  };
  const by = (dir: 1 | -1) => rail.current?.scrollBy({ left: dir * step(), behavior: prefersReducedMotion() ? "auto" : "smooth" });

  useEffect(() => {
    const r = rail.current;
    if (!r) return;
    const update = () => {
      setAtStart(r.scrollLeft <= 2);
      setAtEnd(r.scrollLeft >= r.scrollWidth - r.clientWidth - 2);
    };
    const move = (e: PointerEvent) => {
      if (!drag.current) return;
      const dx = e.clientX - drag.current.x;
      if (!moved.current && Math.abs(dx) > 6) { moved.current = true; r.classList.add("is-dragging"); }
      if (moved.current) r.scrollLeft = drag.current.left - dx;
    };
    const up = () => {
      if (!drag.current) return;
      drag.current = null;
      if (moved.current) {
        r.classList.remove("is-dragging");
        const s = step();
        r.scrollTo({ left: Math.round(r.scrollLeft / s) * s, behavior: "smooth" });
      }
    };
    r.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    update();
    return () => {
      r.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
  }, []);

  return (
    <section className="section" aria-labelledby="work-title">
      <div className="wrap">
        <div className="cases-rail-head">
          <div style={{ display: "grid", gap: 16 }}>
            <SplitHeading as="h2" className="h2" id="work-title" text="Selected work" />
            <p className="lede">Field services, fabrication, logistics and healthcare. The problem, what we built and what changed.</p>
          </div>
          <div style={{ display: "flex", gap: 20, alignItems: "center", flexWrap: "wrap" }}>
            <Link className="ulink" href="/work">All case studies</Link>
            <div className="rail-ctrls">
              <button className="icon-btn" type="button" aria-label="Previous case study" disabled={atStart} onClick={() => by(-1)}><Icon name="arrowL" /></button>
              <button className="icon-btn" type="button" aria-label="Next case study" disabled={atEnd} onClick={() => by(1)}><Icon name="arrowR" /></button>
            </div>
          </div>
        </div>
        <div
          className="case-rail"
          ref={rail}
          tabIndex={0}
          role="region"
          aria-label="Case studies"
          onKeyDown={(e) => {
            if (e.key === "ArrowRight") { e.preventDefault(); by(1); }
            if (e.key === "ArrowLeft") { e.preventDefault(); by(-1); }
          }}
          onPointerDown={(e) => {
            if (e.pointerType !== "mouse" || e.button !== 0) return;
            drag.current = { x: e.clientX, left: e.currentTarget.scrollLeft };
            moved.current = false;
          }}
          onClickCapture={(e) => { if (moved.current) { e.preventDefault(); e.stopPropagation(); moved.current = false; } }}
        >
          {CASES.map((c) => <CaseCard key={c.slug} c={c} />)}
        </div>
        <div style={{ marginTop: 20 }}><SampleNote /></div>
      </div>
    </section>
  );
}
