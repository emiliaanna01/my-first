"use client";
import Lenis from "lenis";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { gsap, hasFinePointer, inViewport, prefersReducedMotion, ScrollTrigger } from "@/lib/gsap";
import { scrollToEl, scrollToTop, setLenis } from "@/lib/scroll";

/* The site-wide motion layer. One instance lives in the root layout.
   - Global: inertial scroll (Lenis) and the curtain that covers route changes.
   - Per page: headline reveals, scroll reveals, count-ups, the Diagnose/Build/Run track,
     magnetic buttons, card spotlights and a few drawn details. Everything created for a
     page is torn down when the route changes. */

export function SiteMotion() {
  const pathname = usePathname();
  const router = useRouter();
  const nav = useRef<{ pending: boolean; hash: string; failsafe?: number }>({ pending: false, hash: "" });

  // ---------- Global: smooth scroll and route curtain ----------
  useEffect(() => {
    const reduced = prefersReducedMotion();
    let lenis: Lenis | null = null;
    let raf: ((t: number) => void) | null = null;
    if (!reduced) {
      lenis = new Lenis({ duration: 1.1, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), smoothWheel: true });
      setLenis(lenis);
      lenis.on("scroll", ScrollTrigger.update);
      raf = (t) => lenis?.raf(t * 1000);
      gsap.ticker.add(raf);
      gsap.ticker.lagSmoothing(0);
    }

    const curtain = document.querySelector<HTMLElement>(".curtain");
    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      if ((a.target && a.target !== "_self") || a.hasAttribute("download")) return;
      const href = a.getAttribute("href") || "";
      if (href.startsWith("mailto:") || href.startsWith("tel:")) return;
      let url: URL;
      try { url = new URL(a.href); } catch { return; }
      if (url.origin !== location.origin || url.pathname.startsWith("/api/")) return;

      if (url.pathname === location.pathname) {
        if (url.search !== location.search) return; // a different view of this page: let Next handle it
        e.preventDefault();
        if (url.hash) {
          const t = document.getElementById(decodeURIComponent(url.hash.slice(1)));
          if (t) { scrollToEl(t); history.replaceState(history.state, "", url.hash); }
        } else if (lenis) lenis.scrollTo(0, { duration: 1.2 });
        else window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
        return;
      }
      if (reduced || !curtain) return; // plain client navigation

      e.preventDefault();
      nav.current = { pending: true, hash: url.hash };
      const rot = curtain.querySelector(".bm-rot");
      gsap.set(curtain, { yPercent: 100, visibility: "visible" });
      if (rot) gsap.fromTo(rot, { rotation: 0, svgOrigin: "20 20" }, { rotation: 90, svgOrigin: "20 20", duration: 0.7, ease: "power3.inOut" });
      gsap.to(curtain, {
        yPercent: 0, duration: 0.6, ease: "power4.inOut",
        onComplete: () => router.push(url.pathname + url.search + url.hash, { scroll: false }),
      });
      window.clearTimeout(nav.current.failsafe);
      nav.current.failsafe = window.setTimeout(() => lift(curtain), 6000);
    };
    document.addEventListener("click", onClick, true);
    return () => {
      document.removeEventListener("click", onClick, true);
      if (raf) gsap.ticker.remove(raf);
      lenis?.destroy();
      setLenis(null);
    };
  }, [router]);

  // ---------- Per page ----------
  useEffect(() => {
    const curtain = document.querySelector<HTMLElement>(".curtain");
    const arrived = nav.current.pending;
    if (arrived) scrollToTop(true);
    const teardown = initPage(arrived);

    const hash = arrived ? nav.current.hash : window.location.hash;
    let hashTimer: number | undefined;
    if (hash) {
      hashTimer = window.setTimeout(() => {
        const t = document.getElementById(decodeURIComponent(hash.slice(1)));
        if (!t) return;
        scrollToEl(t, true);
        if (t.id === "book" && !prefersReducedMotion()) {
          gsap.fromTo(t, { boxShadow: "0 0 0 0 rgba(245,183,0,0.6)" }, { boxShadow: "0 0 0 18px rgba(245,183,0,0)", duration: 1.4, ease: "power2.out", repeat: 1, delay: 0.5 });
        }
      }, arrived ? 60 : 250);
    }
    if (arrived && curtain) {
      window.clearTimeout(nav.current.failsafe);
      lift(curtain);
    }
    nav.current.pending = false;
    const refresh = window.setTimeout(() => ScrollTrigger.refresh(), 400);
    return () => {
      window.clearTimeout(refresh);
      window.clearTimeout(hashTimer);
      teardown();
    };
  }, [pathname]);

  return null;
}

function lift(curtain: HTMLElement) {
  const rot = curtain.querySelector(".bm-rot");
  if (rot) gsap.to(rot, { rotation: 180, svgOrigin: "20 20", duration: 0.8, ease: "power3.out" });
  gsap.to(curtain, {
    yPercent: -100, duration: 0.8, ease: "power4.inOut", delay: 0.1, overwrite: true,
    onComplete: () => { gsap.set(curtain, { yPercent: 100, visibility: "hidden" }); },
  });
}

function initPage(arrived: boolean): () => void {
  const reduced = prefersReducedMotion();
  const fine = hasFinePointer();
  const offs: (() => void)[] = [];
  const on = <K extends keyof HTMLElementEventMap>(el: HTMLElement, ev: K, fn: (e: HTMLElementEventMap[K]) => void) => {
    el.addEventListener(ev, fn as EventListener);
    offs.push(() => el.removeEventListener(ev, fn as EventListener));
  };
  const $$ = <T extends Element = HTMLElement>(s: string, root: ParentNode = document) => Array.from(root.querySelectorAll<T>(s) as NodeListOf<T>);
  const main = document.getElementById("main") ?? document.body;

  const ctx = gsap.context(() => {
    // Diagnose → Build → Run: the engine runs along the rail as you scroll.
    $$("[data-track]", main).forEach((wrap) => {
      const rail = wrap.querySelector<HTMLElement>(".rail");
      const stations = $$("[data-station]", wrap);
      if (!rail) return;
      if (reduced) {
        rail.style.setProperty("--p", "1");
        stations.forEach((s) => s.classList.add("is-reached"));
        return;
      }
      let marks: number[] = [];
      const measure = () => {
        const r = rail.getBoundingClientRect();
        const horiz = r.width > r.height;
        marks = stations.map((s) => {
          const n = s.querySelector(".station-node")!.getBoundingClientRect();
          return horiz ? (n.left + n.width - r.left) / r.width : (n.top + n.height - r.top) / r.height;
        });
      };
      ScrollTrigger.create({
        trigger: wrap, start: "top 78%", end: "bottom 55%", scrub: 0.6, onRefresh: measure,
        onUpdate: (self) => {
          const p = self.progress;
          rail.style.setProperty("--p", p.toFixed(4));
          stations.forEach((s, i) => s.classList.toggle("is-reached", p >= Math.max(0.02, (marks[i] ?? 0) - 0.02)));
        },
      });
      measure();
    });

    if (reduced) return;

    // Headlines rise in word by word (the home hero runs its own sequence).
    $$("[data-split]", main.parentElement ?? document).forEach((el) => {
      if (el.closest(".hero")) return;
      const words = $$(".w", el);
      if (inViewport(el)) {
        gsap.from(words, { yPercent: 115, duration: 1.05, ease: "expo.out", stagger: 0.045, delay: arrived ? 0.45 : 0.1 });
      } else {
        gsap.set(words, { yPercent: 115 });
        ScrollTrigger.create({ trigger: el, start: "top 88%", once: true, onEnter: () => { gsap.to(words, { yPercent: 0, duration: 1, ease: "expo.out", stagger: 0.04 }); } });
      }
    });

    // Supporting copy in an inner-page hero.
    const intro = $$(".page-hero .lede, .page-hero .crumbs, .page-hero .chip, .page-hero .facts", main);
    if (intro.length) gsap.from(intro, { y: 24, opacity: 0, duration: 0.9, ease: "power3.out", stagger: 0.06, delay: arrived ? 0.6 : 0.3 });

    // Blocks below the fold slide up as they arrive. Anything already on screen stays put.
    const sel = [
      ".sec-head-side", ".metric", ".prow", ".term", ".plan", ".pcell", ".principle", ".role", ".result",
      ".case-rail .case-card", ".metrics-foot", ".plans-foot", ".pricelist tbody tr", ".step-aside > *",
      ".faq details", ".calc", ".prose", ".mini-card", ".book-card", ".form-card", ".next-case", ".notice",
      ".practices-intro > *", ".cases-rail-head > *", ".tools", ".facts > div", ".checklist li", ".story-step",
    ].join(",");
    const els = $$(sel, main).filter((el) => !inViewport(el) && !el.closest(".hero"));
    if (els.length) {
      gsap.set(els, { y: 36, opacity: 0 });
      ScrollTrigger.batch(els, {
        start: "top 90%", once: true,
        onEnter: (batch) => { gsap.to(batch, { y: 0, opacity: 1, duration: 0.9, ease: "power3.out", stagger: 0.07, overwrite: true }); },
      });
    }

    // Numbers count up to their value when they come into view.
    $$("[data-count]", main).forEach((el) => {
      const raw = el.textContent?.trim() ?? "";
      const m = raw.match(/^([^\d]*)(\d[\d,]*(?:\.\d+)?)(.*)$/);
      if (!m) return;
      const [, pre, num, post] = m;
      const target = parseFloat(num.replace(/,/g, ""));
      const dec = (num.split(".")[1] || "").length;
      const fmt = (v: number) => pre + v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + post;
      const o = { v: 0 };
      ScrollTrigger.create({
        trigger: el, start: "top 92%", once: true,
        onEnter: () => {
          el.textContent = fmt(0);
          gsap.to(o, { v: target, duration: 1.6, ease: "power3.out", onUpdate: () => { el.textContent = fmt(o.v); }, onComplete: () => { el.textContent = raw; } });
        },
      });
    });

    // The big turntable behind the closing call to action turns as you scroll past.
    const band = main.parentElement?.querySelector<HTMLElement>(".cta-band");
    const bandRot = band?.querySelector(".cta-mark .bm-rot");
    if (band && bandRot) {
      gsap.fromTo(bandRot, { rotation: -70, svgOrigin: "20 20" }, { rotation: 50, svgOrigin: "20 20", ease: "none", scrollTrigger: { trigger: band, start: "top bottom", end: "bottom top", scrub: 0.8 } });
    }

    // About: the security checklist ticks itself.
    const list = main.querySelector("[data-checklist]");
    if (list) {
      const paths = $$<SVGPathElement>(".ck-path", list);
      gsap.set(paths, { strokeDasharray: 20, strokeDashoffset: 20 });
      ScrollTrigger.create({ trigger: list, start: "top 85%", once: true, onEnter: () => { gsap.to(paths, { strokeDashoffset: 0, duration: 0.6, ease: "power2.out", stagger: 0.12, delay: 0.3 }); } });
    }

    // Case studies: before/after bars grow, and the build flow lights up in order.
    $$("[data-bar]", main).forEach((bar) => {
      gsap.set(bar, { scaleX: 0, transformOrigin: "left center" });
      ScrollTrigger.create({ trigger: bar, start: "top 92%", once: true, onEnter: () => { gsap.to(bar, { scaleX: 1, duration: 1.4, ease: "expo.out", delay: bar.closest(".after") ? 0.25 : 0 }); } });
    });
    const flow = main.querySelector<HTMLElement>("[data-flow]");
    if (flow) {
      const steps = $$(".flow-step", flow);
      ScrollTrigger.create({
        trigger: flow, start: "top 75%", end: "bottom 45%", scrub: true,
        onUpdate: (self) => steps.forEach((s, i) => s.classList.toggle("is-lit", self.progress >= (i + 0.35) / steps.length || (i === 0 && self.progress > 0.02))),
      });
    }
  }, main.parentElement ?? document.body);

  // Buttons lean toward the pointer; dark cards carry a soft lamp under it.
  if (!reduced && fine) {
    $$("[data-magnetic]").forEach((el) => {
      const xTo = gsap.quickTo(el, "x", { duration: 0.5, ease: "power3.out" });
      const yTo = gsap.quickTo(el, "y", { duration: 0.5, ease: "power3.out" });
      on(el, "pointermove", (e) => {
        const r = el.getBoundingClientRect();
        xTo((e.clientX - (r.left + r.width / 2)) * 0.22);
        yTo((e.clientY - (r.top + r.height / 2)) * 0.32);
      });
      on(el, "pointerleave", () => { gsap.to(el, { x: 0, y: 0, duration: 0.9, ease: "elastic.out(1, 0.4)" }); });
      offs.push(() => gsap.set(el, { clearProps: "transform" }));
    });
  }
  if (fine) {
    $$("[data-spot]").forEach((el) => {
      on(el, "pointermove", (e) => {
        const r = el.getBoundingClientRect();
        el.style.setProperty("--mx", `${e.clientX - r.left}px`);
        el.style.setProperty("--my", `${e.clientY - r.top}px`);
      });
    });
  }

  return () => {
    offs.forEach((f) => f());
    ctx.revert();
  };
}
