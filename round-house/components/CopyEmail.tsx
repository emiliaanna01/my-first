"use client";
import { useRef, useState } from "react";
import { EMAIL } from "@/lib/content";

/** Shows the address as selectable text and copies it on click. */
export function CopyEmail({ light = false }: { light?: boolean }) {
  const [label, setLabel] = useState<"Copy" | "Copied" | "Selected">("Copy");
  const addr = useRef<HTMLSpanElement>(null);
  const timer = useRef<number | undefined>(undefined);
  const done = (l: "Copied" | "Selected") => {
    setLabel(l);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setLabel("Copy"), 2200);
  };
  const select = () => {
    if (!addr.current) return;
    const r = document.createRange();
    r.selectNodeContents(addr.current);
    const s = window.getSelection();
    s?.removeAllRanges();
    s?.addRange(r);
    done("Selected");
  };
  const copy = () => {
    try {
      navigator.clipboard.writeText(EMAIL).then(() => done("Copied"), select);
    } catch {
      select();
    }
  };
  return (
    <button className={`copy-email${light ? " copy-email--light" : ""}${label === "Copied" ? " is-copied" : ""}`} type="button" onClick={copy}>
      <span className="addr" ref={addr}>{EMAIL}</span>
      <span className="tag" aria-live="polite">{label}</span>
    </button>
  );
}
