"use client";
import { useRef } from "react";
import { gsap, prefersReducedMotion } from "@/lib/gsap";

/** Native details elements with an animated open and close. */
export function Faq({ items }: { items: [string, string][] }) {
  const busy = useRef(false);
  const toggle = (e: React.MouseEvent<HTMLElement>) => {
    if (prefersReducedMotion()) return;
    e.preventDefault();
    if (busy.current) return;
    const d = e.currentTarget.parentElement as HTMLDetailsElement;
    const ans = d.querySelector<HTMLElement>(".answer")!;
    busy.current = true;
    if (d.open) {
      gsap.to(ans, { height: 0, duration: 0.45, ease: "power3.inOut", onComplete: () => { d.open = false; gsap.set(ans, { clearProps: "height" }); busy.current = false; } });
    } else {
      d.open = true;
      gsap.fromTo(ans, { height: 0 }, { height: ans.scrollHeight, duration: 0.55, ease: "power3.out", onComplete: () => { gsap.set(ans, { clearProps: "height" }); busy.current = false; } });
      gsap.fromTo(ans.querySelector("p"), { y: 10, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, delay: 0.1 });
    }
  };
  return (
    <div className="faq">
      {items.map(([q, a], i) => (
        <details key={i} id={`faq-${i}`}>
          <summary onClick={toggle}>{q}<span className="plus" aria-hidden="true" /></summary>
          <div className="answer"><p>{a}</p></div>
        </details>
      ))}
    </div>
  );
}
