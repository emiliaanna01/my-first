"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { EMAIL, NAV } from "@/lib/content";
import { gsap, prefersReducedMotion } from "@/lib/gsap";
import { getLenis } from "@/lib/scroll";
import { Mark } from "./Mark";

const isActive = (pathname: string, href: string) => pathname === href || pathname.startsWith(href + "/");

export function Header() {
  const pathname = usePathname();
  const header = useRef<HTMLElement>(null);
  const nav = useRef<HTMLElement>(null);
  const pill = useRef<HTMLSpanElement>(null);
  const bar = useRef<HTMLSpanElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const brandRot = useRef(0);
  const [open, setOpen] = useState(false);

  // Hide on the way down, show on the way up, and fill the progress rail.
  useEffect(() => {
    const el = header.current;
    if (!el) return;
    let lastY = window.scrollY;
    const onScroll = () => {
      const y = window.scrollY;
      el.classList.toggle("is-scrolled", y > 8);
      const menuOpen = document.documentElement.classList.contains("menu-open");
      if (y > 420 && y > lastY + 2 && !menuOpen) {
        el.classList.add("is-hidden");
        document.documentElement.classList.add("header-hidden");
      } else if (y < lastY - 2 || y < 420) {
        el.classList.remove("is-hidden");
        document.documentElement.classList.remove("header-hidden");
      }
      lastY = y;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (bar.current) bar.current.style.transform = `scaleX(${max > 0 ? Math.min(1, y / max) : 0})`;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // The pill rests under the current section and follows the pointer.
  const place = useCallback((link: HTMLElement | null) => {
    const p = pill.current;
    if (!p) return;
    if (!link) { p.style.opacity = "0"; return; }
    p.style.left = `${link.offsetLeft}px`;
    p.style.width = `${link.offsetWidth}px`;
    p.style.opacity = "1";
  }, []);
  const current = useCallback(() => nav.current?.querySelector<HTMLElement>(".nav-link[aria-current='page']") ?? null, []);
  useEffect(() => {
    place(current());
    const onResize = () => place(current());
    window.addEventListener("resize", onResize);
    document.fonts?.ready.then(onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [pathname, place, current]);

  // Mobile menu
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("menu-open", open);
    const lenis = getLenis();
    if (open) {
      lenis?.stop();
      if (!prefersReducedMotion() && menu.current) {
        gsap.fromTo(menu.current.querySelectorAll("nav a, .btn, .small"), { y: 48, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: "expo.out", stagger: 0.05, delay: 0.15 });
      }
    } else lenis?.start();
  }, [open]);
  useEffect(() => { setOpen(false); }, [pathname]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    const onResize = () => { if (window.innerWidth >= 900) setOpen(false); };
    window.addEventListener("keydown", onKey);
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("keydown", onKey); window.removeEventListener("resize", onResize); };
  }, []);

  const spinBrand = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (prefersReducedMotion()) return;
    const rot = e.currentTarget.querySelector(".bm-rot");
    brandRot.current += 90;
    if (rot) gsap.to(rot, { rotation: brandRot.current, svgOrigin: "20 20", duration: 0.9, ease: "back.out(1.6)" });
  };

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="site-header" ref={header}>
        <div className="wrap">
          <Link className="brand" href="/" aria-label="Round House, home" onMouseEnter={spinBrand}>
            <Mark />
            <span>Round House</span>
          </Link>
          <nav className="nav" aria-label="Main" ref={nav} onMouseLeave={() => place(current())}>
            <span className="nav-pill" aria-hidden="true" ref={pill} />
            {NAV.map((n) => (
              <Link
                key={n.key}
                className="nav-link"
                href={n.href}
                aria-current={isActive(pathname, n.href) ? "page" : undefined}
                onMouseEnter={(e) => place(e.currentTarget)}
                onFocus={(e) => place(e.currentTarget)}
              >
                {n.label}
              </Link>
            ))}
          </nav>
          <Link className="btn btn--sm header-cta" href="/contact#book" data-magnetic="">Book a call</Link>
          <button
            className="menu-btn"
            type="button"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((o) => !o)}
          >
            <span />
            <span />
          </button>
        </div>
        <span className="scroll-progress" aria-hidden="true" ref={bar} />
      </header>
      <div className="mobile-menu on-dark" id="mobile-menu" aria-hidden={!open} ref={menu} inert={!open}>
        <nav aria-label="Mobile">
          {[{ href: "/", label: "Home", key: "home" }, ...NAV].map((n) => (
            <Link key={n.key} href={n.href} aria-current={(n.href === "/" ? pathname === "/" : isActive(pathname, n.href)) ? "page" : undefined}>
              {n.label}
            </Link>
          ))}
        </nav>
        <div style={{ display: "grid", gap: 14, justifyItems: "start" }}>
          <Link className="btn" href="/contact#book">Book a 30-minute call</Link>
          <p className="small">Calls 9am–6pm ET, Monday to Friday. {EMAIL}</p>
        </div>
      </div>
    </>
  );
}
