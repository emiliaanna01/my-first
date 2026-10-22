"use client";

import * as React from "react";
import Link from "next/link";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

import { bays } from "@/content/services";

gsap.registerPlugin(useGSAP);

// Plan-view geometry, in SVG user units. Angles are degrees, clockwise from +x (SVG convention).
const CX = 360;
const CY = 400;
const PIT = 54; // turntable radius
const R1 = 170; // inner wall of the roundhouse
const R2 = 244; // outer wall
const A0 = 192;
const A1 = 348;
const STEP = (A1 - A0) / (bays.length - 1);
const ENTRY = 90; // the lead-in track comes from straight below
const START = bays.findIndex((b) => b.id === "leads");

const f = (n: number) => +n.toFixed(2);
const pt = (r: number, deg: number) => {
  const a = (deg * Math.PI) / 180;
  return [f(CX + r * Math.cos(a)), f(CY + r * Math.sin(a))] as const;
};
const sector = (r1: number, r2: number, from: number, to: number) => {
  const [ax, ay] = pt(r2, from);
  const [bx, by] = pt(r2, to);
  const [cx, cy] = pt(r1, to);
  const [dx, dy] = pt(r1, from);
  return `M${ax} ${ay}A${r2} ${r2} 0 0 1 ${bx} ${by}L${cx} ${cy}A${r1} ${r1} 0 0 0 ${dx} ${dy}Z`;
};
const angleOf = (i: number) => A0 + i * STEP;

const geometry = bays.map((bay, i) => {
  const a = angleOf(i);
  const cos = Math.cos((a * Math.PI) / 180);
  const [t1x, t1y] = pt(PIT + 3, a);
  const [t2x, t2y] = pt(R2 - 12, a);
  const [lx, ly] = pt(R2 + 22, a);
  return {
    ...bay,
    angle: a,
    stall: sector(R1, R2, a - STEP / 2, a + STEP / 2),
    track: [t1x, t1y, t2x, t2y] as const,
    label: { x: lx, y: ly, anchor: (Math.abs(cos) < 0.1 ? "middle" : cos < 0 ? "end" : "start") as "middle" | "end" | "start" },
  };
});

const building = sector(R1, R2, A0 - STEP / 2, A1 + STEP / 2);
const wall = (() => {
  const [ax, ay] = pt(R2 + 7, A0 - STEP / 2);
  const [bx, by] = pt(R2 + 7, A1 + STEP / 2);
  return `M${ax} ${ay}A${R2 + 7} ${R2 + 7} 0 0 1 ${bx} ${by}`;
})();

export function Roundhouse() {
  const root = React.useRef<HTMLDivElement>(null);
  const bridge = React.useRef<SVGGElement>(null);
  const intro = React.useRef<gsap.core.Timeline | null>(null);
  const [active, setActive] = React.useState<number | null>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      const origin = `${CX} ${CY}`;

      mm.add("(prefers-reduced-motion: no-preference)", () => {
        // The one orchestrated moment: the drawing inks itself in, then the turntable
        // swings from the entry track to the Leads bay.
        gsap.set(bridge.current, { rotation: ENTRY, svgOrigin: origin });
        const tl = gsap.timeline({ delay: 0.25, onComplete: () => setActive(START) });
        tl.to(".rh-draw", { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut", stagger: 0.025 })
          .to(".rh-fade", { opacity: 1, duration: 0.45, ease: "power1.out", stagger: 0.02 }, "-=0.45")
          .to(bridge.current, { rotation: angleOf(START), svgOrigin: origin, duration: 1, ease: "power3.inOut" }, "-=0.1");
        intro.current = tl;
      });

      mm.add("(prefers-reduced-motion: reduce)", () => {
        gsap.set(bridge.current, { rotation: angleOf(START), svgOrigin: origin });
        setActive(START);
      });

      // Bay changes run from event handlers, outside this context; stop them on unmount too.
      const el = bridge.current;
      return () => gsap.killTweensOf(el);
    },
    { scope: root },
  );

  function select(i: number) {
    intro.current?.progress(1).kill();
    intro.current = null;
    setActive(i);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    gsap.to(bridge.current, {
      rotation: angleOf(i),
      svgOrigin: `${CX} ${CY}`,
      duration: reduce ? 0 : 0.6,
      ease: "power3.out",
      overwrite: true,
    });
  }

  const step = (dir: 1 | -1) => select(((active ?? START) + dir + bays.length) % bays.length);
  const current = active === null ? null : bays[active];

  return (
    <div ref={root} className="relative">
      <svg
        viewBox="-90 40 900 420"
        className="rh-armed block h-auto w-full overflow-visible"
        role="group"
        aria-label="Roundhouse diagram: work comes in on one track and the turntable routes it to one of eight bays"
      >
        {/* Building, outer wall, lead-in track and pit: the line work that draws in on load. */}
        <path d={building} pathLength={1} className="rh-draw" fill="none" stroke="var(--ink)" strokeWidth={1.5} />
        <path d={wall} pathLength={1} className="rh-draw" fill="none" stroke="var(--ink)" strokeWidth={1} />
        <line x1={CX} y1={CY + PIT} x2={CX} y2={470} pathLength={1} className="rh-draw" stroke="var(--ink)" strokeWidth={2.5} />

        {geometry.map((g, i) => {
          const pressed = active === i;
          return (
            <g
              key={g.id}
              className="rh-bay"
              role="button"
              tabIndex={0}
              aria-pressed={pressed}
              aria-label={`${g.name}: ${g.outcome}`}
              onClick={() => select(i)}
              onPointerEnter={(e) => e.pointerType === "mouse" && select(i)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  select(i);
                }
              }}
            >
              <path d={g.stall} className="rh-stall rh-fade" stroke="var(--ink)" strokeWidth={1} />
              <path d={g.stall} className="rh-focus" fill="none" />
              <line
                x1={g.track[0]}
                y1={g.track[1]}
                x2={g.track[2]}
                y2={g.track[3]}
                pathLength={1}
                className="rh-track rh-draw"
                strokeWidth={1.5}
              />
              <text
                x={g.label.x}
                y={g.label.y}
                textAnchor={g.label.anchor}
                dominantBaseline="middle"
                className="rh-label rh-fade text-[34px] md:text-[23px]"
              >
                {g.name}
              </text>
            </g>
          );
        })}

        {/* Turntable pit and its bridge. The bridge starts lined up with the entry track. */}
        <circle cx={CX} cy={CY} r={PIT} pathLength={1} className="rh-draw" fill="var(--plant)" stroke="var(--ink)" strokeWidth={2} />
        <g ref={bridge} transform={`rotate(${ENTRY} ${CX} ${CY})`}>
          <rect x={CX - PIT + 4} y={CY - 10} width={PIT * 2 - 8} height={20} fill="var(--panel)" stroke="var(--ink)" strokeWidth={1.5} />
          <line x1={CX - PIT + 4} y1={CY - 4.5} x2={CX + PIT - 4} y2={CY - 4.5} stroke="var(--ink)" strokeWidth={1.5} />
          <line x1={CX - PIT + 4} y1={CY + 4.5} x2={CX + PIT - 4} y2={CY + 4.5} stroke="var(--ink)" strokeWidth={1.5} />
          <rect x={CX + PIT - 17} y={CY - 7} width={11} height={14} fill="var(--signal)" stroke="var(--ink)" strokeWidth={1} />
        </g>
      </svg>

      <div className="mt-6 flex items-start gap-4 border-t border-ink pt-4 md:mt-2">
        <p className="min-h-[3.2em] flex-1 text-[17px] leading-snug" aria-live="polite">
          {current ? (
            <>
              <strong className="font-semibold">{current.name}.</strong> {current.outcome}{" "}
              <Link href="/services#build" className="whitespace-nowrap underline underline-offset-4 hover:decoration-2">
                How we build it
              </Link>
            </>
          ) : (
            <span className="text-steel">Pick a bay to see what we automate there.</span>
          )}
        </p>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() => step(-1)}
            className="grid size-11 place-items-center rounded-sm border border-ink transition-colors hover:bg-ink hover:text-plant"
            aria-label="Previous bay"
          >
            <svg viewBox="0 0 16 16" className="size-4" aria-hidden="true">
              <path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" strokeWidth={1.8} />
            </svg>
          </button>
          <button
            type="button"
            onClick={() => step(1)}
            className="grid size-11 place-items-center rounded-sm border border-ink transition-colors hover:bg-ink hover:text-plant"
            aria-label="Next bay"
          >
            <svg viewBox="0 0 16 16" className="size-4" aria-hidden="true">
              <path d="m6 3 5 5-5 5" fill="none" stroke="currentColor" strokeWidth={1.8} />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
