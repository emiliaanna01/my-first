"use client";
import type Lenis from "lenis";
import { prefersReducedMotion } from "./gsap";

let lenis: Lenis | null = null;
export const setLenis = (l: Lenis | null) => { lenis = l; };
export const getLenis = () => lenis;

export function headerOffset() {
  const h = document.querySelector<HTMLElement>(".site-header");
  const sub = document.querySelector<HTMLElement>(".subnav-wrap");
  return (h ? h.offsetHeight : 68) + (sub ? sub.offsetHeight : 0) + 24;
}

export function scrollToEl(el: HTMLElement | null, immediate = false) {
  if (!el) return;
  if (lenis) {
    lenis.scrollTo(el, { offset: -headerOffset(), immediate, duration: 1.3, force: true });
    return;
  }
  const y = el.getBoundingClientRect().top + window.scrollY - headerOffset();
  window.scrollTo({ top: y, behavior: immediate || prefersReducedMotion() ? "auto" : "smooth" });
}

export function scrollToTop(immediate = true) {
  if (lenis) lenis.scrollTo(0, { immediate, force: true });
  window.scrollTo(0, 0);
}
