"use client";
import { useEffect, useRef } from "react";
import { gsap, hasFinePointer, prefersReducedMotion, ScrollTrigger } from "@/lib/gsap";

/** The closing wordmark: sized to fill the column exactly, letters rise in on first sight. */
export function FootWord({ text }: { text: string }) {
  const el = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    const word = el.current;
    if (!word) return;
    const letters = Array.from(word.children) as HTMLElement[];
    const fit = () => {
      word.style.fontSize = "100px";
      const gap = parseFloat(getComputedStyle(word).columnGap || "0") || 0;
      const inner = letters.reduce((w, c) => w + c.getBoundingClientRect().width, 0) + gap * (letters.length - 1);
      if (inner > 0) word.style.fontSize = `${Math.floor(((100 * word.clientWidth) / inner) * 0.995)}px`;
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(word);
    document.fonts?.ready.then(() => { fit(); ScrollTrigger.refresh(); });
    if (prefersReducedMotion()) return () => ro.disconnect();
    const ctx = gsap.context(() => {
      gsap.set(letters, { yPercent: 105 });
      ScrollTrigger.create({
        trigger: word, start: "top 98%", once: true,
        onEnter: () => { gsap.to(letters, { yPercent: 0, duration: 1.2, ease: "expo.out", stagger: 0.035 }); },
      });
    });
    const hop = (e: Event) => {
      const l = e.currentTarget as HTMLElement;
      if (gsap.isTweening(l)) return;
      gsap.to(l, { yPercent: -10, duration: 0.25, ease: "power2.out", yoyo: true, repeat: 1 });
    };
    if (hasFinePointer()) letters.forEach((l) => l.addEventListener("mouseenter", hop));
    return () => {
      ro.disconnect();
      letters.forEach((l) => l.removeEventListener("mouseenter", hop));
      ctx.revert();
    };
  }, []);
  return (
    <p className="foot-word" aria-hidden="true" ref={el}>
      {text.split("").map((c, i) => (
        <span key={i} className="fw-letter">{c === " " ? " " : c}</span>
      ))}
    </p>
  );
}
