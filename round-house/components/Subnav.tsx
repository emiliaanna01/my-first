"use client";
import { useEffect, useRef, useState } from "react";
import { headerOffset, scrollToEl } from "@/lib/scroll";

/** A sticky "on this page" menu that tracks the section in view. */
export function Subnav({ items }: { items: [id: string, label: string][] }) {
  const nav = useRef<HTMLElement>(null);
  const pill = useRef<HTMLSpanElement>(null);
  const links = useRef<(HTMLAnchorElement | null)[]>([]);
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    const pick = () => {
      const line = headerOffset() + 40;
      let idx = 0;
      items.forEach(([id], i) => {
        const s = document.getElementById(id);
        if (s && s.getBoundingClientRect().top <= line) idx = i;
      });
      setCurrent(idx);
    };
    window.addEventListener("scroll", pick, { passive: true });
    pick();
    return () => window.removeEventListener("scroll", pick);
  }, [items]);

  useEffect(() => {
    const place = () => {
      const a = links.current[current];
      const n = nav.current;
      if (!a || !n || !pill.current) return;
      pill.current.style.left = `${a.offsetLeft}px`;
      pill.current.style.width = `${a.offsetWidth}px`;
      n.scrollTo({ left: Math.max(0, a.offsetLeft - n.clientWidth / 2 + a.offsetWidth / 2), behavior: "smooth" });
    };
    place();
    window.addEventListener("resize", place);
    document.fonts?.ready.then(place);
    return () => window.removeEventListener("resize", place);
  }, [current]);

  return (
    <div className="subnav-wrap">
      <div className="wrap">
        <nav className="subnav" aria-label="On this page" ref={nav}>
          <span className="subnav-pill" aria-hidden="true" ref={pill} />
          {items.map(([id, label], i) => (
            <a
              key={id}
              href={`#${id}`}
              ref={(el) => { links.current[i] = el; }}
              className={i === current ? "is-active" : undefined}
              aria-current={i === current ? "location" : undefined}
              onClick={(e) => {
                e.preventDefault();
                scrollToEl(document.getElementById(id));
                history.replaceState(history.state, "", `#${id}`);
              }}
            >
              {label}
            </a>
          ))}
        </nav>
      </div>
    </div>
  );
}
