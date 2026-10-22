"use client";
import Link from "next/link";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { BAYS, BAY_ANGLES } from "@/lib/content";
import { gsap, hasFinePointer, prefersReducedMotion, ScrollTrigger } from "@/lib/gsap";
import { HoursLamp } from "./HoursLamp";
import { SplitHeading } from "./Split";
import { Turntable, turntableMath } from "./Turntable";

const START = 3; // Leads
const DWELL = 4.6; // seconds per bay on the tour
const NS = "http://www.w3.org/2000/svg";

export function Hero() {
  const root = useRef<HTMLElement>(null);
  const consoleBody = useRef<HTMLDivElement>(null);
  const bar = useRef<HTMLElement>(null);
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const angle = useRef(BAY_ANGLES[START]);
  const activeRef = useRef(START);
  const firstRender = useRef(true);

  const [active, setActive] = useState(START);
  const [shown, setShown] = useState(START);
  const [auto, setAuto] = useState(false);
  const [ready, setReady] = useState(false);
  const [visible, setVisible] = useState(true);
  const [motion, setMotion] = useState(false);

  const svg = () => root.current?.querySelector<SVGSVGElement>("#tt-hero") ?? null;

  const select = useCallback((i: number, user = false) => {
    const next = (i + BAYS.length) % BAYS.length;
    activeRef.current = next;
    setActive(next);
    if (user) setAuto(false);
  }, []);

  // Turn the bridge the short way round, then swap the console copy.
  useEffect(() => {
    if (firstRender.current) { firstRender.current = false; return; }
    const s = svg();
    const bridge = s?.querySelector(".tt-bridge");
    const target = turntableMath.nearest(angle.current, BAY_ANGLES[active]);
    const travel = Math.abs(target - angle.current);
    angle.current = target;
    if (!bridge) return;
    if (prefersReducedMotion()) {
      gsap.set(bridge, { rotation: target, svgOrigin: "0 0" });
      setShown(active);
      return;
    }
    gsap.to(bridge, { rotation: target, svgOrigin: "0 0", duration: 0.7 + travel / 150, ease: "power3.inOut", overwrite: true });
    const lamp = s?.querySelectorAll(".tt-bay")[active]?.querySelector(".tt-baylamp");
    if (lamp) gsap.fromTo(lamp, { scale: 0.4 }, { scale: 1, duration: 0.8, ease: "elastic.out(1, 0.35)", delay: 0.3 + travel / 300 });
    const parts = consoleBody.current?.querySelectorAll("[data-swap]");
    if (parts?.length) {
      gsap.to(parts, { y: -8, opacity: 0, duration: 0.18, ease: "power2.in", stagger: 0.02, overwrite: true, onComplete: () => setShown(active) });
    } else setShown(active);
  }, [active]);

  useLayoutEffect(() => {
    if (prefersReducedMotion()) return;
    const parts = consoleBody.current?.querySelectorAll("[data-swap]");
    if (parts?.length && ready) gsap.fromTo(parts, { y: 12, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "power3.out", stagger: 0.04 });
  }, [shown]); // eslint-disable-line react-hooks/exhaustive-deps

  // The tour: a progress bar fills, then the next bay is chosen.
  useEffect(() => {
    if (!bar.current) return;
    if (!auto || !ready || !visible) {
      gsap.to(bar.current, { scaleX: 0, duration: 0.3, overwrite: true });
      return;
    }
    const t = gsap.fromTo(bar.current, { scaleX: 0 }, { scaleX: 1, duration: DWELL, ease: "none", overwrite: true, onComplete: () => select(activeRef.current + 1) });
    const onVis = () => (document.hidden ? t.pause() : t.resume());
    document.addEventListener("visibilitychange", onVis);
    return () => { t.kill(); document.removeEventListener("visibilitychange", onVis); };
  }, [auto, ready, visible, active, select]);

  // Load sequence, work packets, tilt and parallax.
  useEffect(() => {
    const s = svg();
    const section = root.current;
    if (!s || !section) return;
    const bridge = s.querySelector<SVGGElement>(".tt-bridge")!;
    const loco = s.querySelector<SVGGElement>(".tt-loco")!;
    bridge.removeAttribute("transform");
    loco.removeAttribute("transform");
    gsap.set(bridge, { rotation: angle.current, svgOrigin: "0 0" });
    gsap.set(loco, { y: -168 });

    const vis = ScrollTrigger.create({ trigger: s, start: "top bottom", end: "bottom top", onToggle: (st) => setVisible(st.isActive) });
    if (prefersReducedMotion()) {
      setReady(true);
      return () => vis.kill();
    }
    setMotion(true);
    const fine = hasFinePointer();
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ delay: 0.1, onComplete: () => { setReady(true); setAuto(true); } });
      tl.from(s.querySelectorAll(".tt-house, .tt-houseline, .tt-div"), { opacity: 0, duration: 0.9, ease: "power2.out" }, 0)
        .from(s.querySelectorAll(".tt-pit, .tt-ring, .tt-pitwall"), { scale: 0.86, opacity: 0, svgOrigin: "0 0", duration: 1.1, ease: "expo.out", stagger: 0.05 }, 0.05)
        .from(s.querySelectorAll(".tt-bay"), { opacity: 0, duration: 0.6, stagger: 0.05 }, 0.25)
        .from(bridge, { rotation: angle.current - 200, svgOrigin: "0 0", duration: 2, ease: "power3.inOut" }, 0.1)
        .from(s.querySelectorAll(".tt-label, .tt-lead-label, .tt-scale"), { opacity: 0, y: 8, duration: 0.6, stagger: 0.04 }, 0.8)
        .from(s.querySelector(".tt-lead"), { opacity: 0, duration: 0.8 }, 0.4)
        .from(section.querySelectorAll("h1 .w"), { yPercent: 115, duration: 1.05, ease: "expo.out", stagger: 0.045 }, 0.05)
        .from(section.querySelectorAll(".hero-copy .status, .hero-copy .lede, .hero-actions"), { y: 22, opacity: 0, duration: 0.9, ease: "power3.out", stagger: 0.08 }, 0.35)
        .from(section.querySelector(".console"), { y: 40, opacity: 0, duration: 1, ease: "expo.out" }, 0.6)
        .from(section.querySelector(".tt-caption"), { opacity: 0, duration: 0.6 }, 1.2);
      gsap.to(s.querySelector(".tt-loco-glow"), { scale: 1.9, opacity: 0, svgOrigin: "0 -96", duration: 1.6, repeat: -1, ease: "power2.out" });
      const fig = section.querySelector(".tt-figure");
      if (fig) gsap.to(fig, { yPercent: 8, ease: "none", scrollTrigger: { trigger: section, start: "top top", end: "bottom top", scrub: true } });
    }, section);

    // Work packets: signal lamps run up the lead track and into the selected bay.
    const layer = s.querySelector(".tt-packets")!;
    let alive = true;
    const spawn = () => {
      if (!alive) return;
      if (!document.hidden && vis.isActive) {
        const c = document.createElementNS(NS, "circle");
        c.setAttribute("r", "5.5");
        c.setAttribute("cx", "0");
        c.setAttribute("cy", "420");
        c.setAttribute("class", "tt-packet");
        layer.appendChild(c);
        const a = BAY_ANGLES[activeRef.current];
        const [bx, by] = turntableMath.P(a, 252);
        const [mx, my] = turntableMath.P(a, 150);
        gsap.timeline({ onComplete: () => c.remove() })
          .fromTo(c, { opacity: 0 }, { attr: { cy: 152 }, opacity: 1, duration: 1.1, ease: "none" })
          .to(c, { attr: { cx: 0, cy: 0 }, duration: 0.55, ease: "none" })
          .to(c, { attr: { cx: mx, cy: my }, duration: 0.55, ease: "none" })
          .to(c, { attr: { cx: bx, cy: by }, opacity: 0, duration: 0.6, ease: "power1.in" });
      }
      gsap.delayedCall(1.15, spawn);
    };
    const first = gsap.delayedCall(2.2, spawn);

    // A gentle 3D tilt that follows the pointer.
    const fig = section.querySelector<HTMLElement>("[data-tilt]");
    const stage = fig?.querySelector<HTMLElement>(".tt-stage");
    let onMove: ((e: PointerEvent) => void) | null = null;
    let onLeave: (() => void) | null = null;
    if (fig && stage && fine) {
      stage.style.transition = "none";
      const rx = gsap.quickTo(stage, "rotationX", { duration: 0.8, ease: "power3.out" });
      const ry = gsap.quickTo(stage, "rotationY", { duration: 0.8, ease: "power3.out" });
      onMove = (e) => {
        const r = fig.getBoundingClientRect();
        ry(((e.clientX - r.left) / r.width - 0.5) * 9);
        rx(-((e.clientY - r.top) / r.height - 0.5) * 7);
      };
      onLeave = () => { rx(0); ry(0); };
      fig.addEventListener("pointermove", onMove);
      fig.addEventListener("pointerleave", onLeave);
    }

    return () => {
      alive = false;
      first.kill();
      gsap.killTweensOf(spawn);
      layer.replaceChildren();
      if (fig && onMove && onLeave) { fig.removeEventListener("pointermove", onMove); fig.removeEventListener("pointerleave", onLeave); }
      vis.kill();
      ctx.revert();
    };
  }, []);

  const onTabKey = (e: React.KeyboardEvent) => {
    const map: Record<string, number> = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
    let next: number | null = null;
    if (e.key in map) next = activeRef.current + map[e.key];
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = BAYS.length - 1;
    if (next === null) return;
    e.preventDefault();
    const i = (next + BAYS.length) % BAYS.length;
    select(i, true);
    tabs.current[i]?.focus();
  };

  const bay = BAYS[shown];
  return (
    <section className="hero" ref={root}>
      <div className="wrap hero-grid">
        <div className="hero-copy">
          <HoursLamp />
          <SplitHeading as="h1" className="h1" text="We automate the work that slows you down." />
          <p className="lede">From the factory floor to the front office, Round House finds where your team loses hours, builds the systems that win them back, and keeps those systems running.</p>
          <div className="hero-actions">
            <Link className="btn" href="/contact#book" data-magnetic=""><span className="lamp" aria-hidden="true" />Book a 30-minute call</Link>
            <Link className="ulink" href="/services#steps">See prices</Link>
          </div>
        </div>
        <div className="hero-draw">
          <figure className="tt-figure" data-tilt="">
            <div className="tt-stage">
              <Turntable
                id="tt-hero"
                active={active}
                title="A railroad turntable with eight bays: Onboarding, Documents, Inbox, Leads, CRM, Reporting, Content and Website."
                bridgeAngle={BAY_ANGLES[START]}
                onBayClick={(i) => select(i, true)}
              />
            </div>
            <figcaption className="tt-caption"><span>Pick a bay to see what we automate there.</span><span>Drawing RH-01, plan view, rev D</span></figcaption>
          </figure>
        </div>
        <div className="hero-panel">
          <div className="console">
            <div className="console-tabs" role="tablist" aria-label="Bays">
              {BAYS.map((b, i) => (
                <button
                  key={b.name}
                  ref={(el) => { tabs.current[i] = el; }}
                  className="console-tab"
                  role="tab"
                  type="button"
                  id={`bay-tab-${i}`}
                  aria-controls="bay-panel"
                  aria-selected={i === active}
                  tabIndex={i === active ? 0 : -1}
                  onClick={() => select(i, true)}
                  onKeyDown={onTabKey}
                >
                  {b.name}
                </button>
              ))}
            </div>
            <div className="console-body" id="bay-panel" role="tabpanel" aria-labelledby={`bay-tab-${active}`} aria-live="polite" ref={consoleBody}>
              <div className="console-head">
                <h2 className="console-name" data-swap="">{bay.name}</h2>
                <span className="console-price" data-swap="">Typical build {bay.price}</span>
              </div>
              <p className="console-desc" data-swap="">{bay.desc}</p>
              <p className="console-proof" data-swap="">
                <span>{bay.proofLabel}</span>
                <span dangerouslySetInnerHTML={{ __html: bay.proof }} />
              </p>
            </div>
            <div className="console-foot">
              <Link className="ulink" href="/services#build">All build prices</Link>
              {motion && (
                <button className="console-auto" type="button" aria-pressed={auto} onClick={() => setAuto((a) => !a)}>
                  <span>{auto ? "Touring the bays. Pause" : "Tour paused. Resume"}</span>
                  <span className="bar" aria-hidden="true"><i ref={bar} /></span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
