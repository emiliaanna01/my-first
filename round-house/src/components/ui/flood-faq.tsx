"use client";

/*
 * FAQ accordion where opening a question floods its row with ink from the left, and the
 * question inverts exactly where the edge passes (a paper-coloured copy of the row is clipped
 * in step). Closing wipes the ink out to the right.
 *
 * Adapted from "Slit Type FAQ" by kedhareswer on 21st.dev
 * (https://21st.dev/@kedhareswer/components/slit-type-faq), restyled to Round House tokens:
 * sentence-case Archivo instead of the slit capitals, 2px corners, no ticker or chips.
 * Kept from the original: aria-expanded/aria-controls buttons, ↑ ↓ Home End between questions,
 * single-open behaviour, #hash deep links and the reduced-motion handling.
 */

import * as React from "react";

export type FaqItem = { question: string; answer: string; id?: string };

function slugify(s: string): string {
  return (
    s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 64) || "question"
  );
}

function nextFocus(key: string, i: number, n: number): number {
  if (!n) return -1;
  if (key === "ArrowDown") return (i + 1) % n;
  if (key === "ArrowUp") return (i - 1 + n) % n;
  if (key === "Home") return 0;
  if (key === "End") return n - 1;
  return -1;
}

const css = `
.ff { --ff-in: 400ms; --ff-out: 280ms; --ff-ease: cubic-bezier(0.76, 0, 0.24, 1); --ff-ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --p: var(--plant); --k: var(--ink); --o: var(--plant); --ff-gutter: 16px; position: relative; }
@media (min-width: 768px) { .ff { --ff-gutter: 24px; } }
.ff-list { margin: 0; padding: 0; list-style: none; border-bottom: 1px solid var(--k); }
.ff-item { position: relative; border-top: 1px solid var(--k); }
.ff-fill { position: absolute; top: -1px; bottom: 0; left: calc(var(--ff-gutter) * -1); right: calc(var(--ff-gutter) * -1);
  background: var(--k); clip-path: inset(0 100% 0 0); pointer-events: none; }
.ff-item[data-state="open"] .ff-fill { clip-path: inset(0 0 0 0); transition: clip-path var(--ff-in) var(--ff-ease); }
.ff-item[data-state="closing"] .ff-fill { clip-path: inset(0 0 0 100%); transition: clip-path var(--ff-out) var(--ff-ease); }
.ff-h { margin: 0; font: inherit; }
.ff-btn { position: relative; display: block; width: 100%; appearance: none; border: 0; margin: 0; padding: 0; background: none;
  color: var(--k); font: inherit; text-align: left; cursor: pointer; -webkit-tap-highlight-color: transparent; }
.ff-btn:focus-visible { outline: none; }
.ff-btn::after { content: ""; position: absolute; top: 5px; bottom: 5px; left: calc(var(--ff-gutter) * -0.5); right: calc(var(--ff-gutter) * -0.5);
  box-shadow: inset 0 0 0 2px var(--k); opacity: 0; pointer-events: none; }
.ff-item[data-state="open"] .ff-btn::after { box-shadow: inset 0 0 0 2px var(--signal); }
.ff-btn:focus-visible::after { opacity: 1; }
.ff-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 20px; min-height: 64px;
  padding: 18px 0; font-size: clamp(1.125rem, 1rem + 0.6vw, 1.5rem); font-weight: 650; line-height: 1.2; letter-spacing: -0.01em; text-wrap: balance; }
.ff-row--inv { position: absolute; inset: 0 calc(var(--ff-gutter) * -1); padding-inline: var(--ff-gutter); color: var(--o);
  clip-path: inset(0 100% 0 0); pointer-events: none; }
.ff-item[data-state="open"] .ff-row--inv { clip-path: inset(0 0 0 0); transition: clip-path var(--ff-in) var(--ff-ease); }
.ff-item[data-state="closing"] .ff-row--inv { clip-path: inset(0 0 0 100%); transition: clip-path var(--ff-out) var(--ff-ease); }
.ff-label { display: block; transition: transform 240ms var(--ff-ease-out); }
.ff-cell { position: relative; display: grid; place-items: center; width: 44px; height: 44px; }
.ff-cell::before { content: ""; position: absolute; inset: 0; background: var(--k); clip-path: inset(0 100% 0 0); transition: clip-path 220ms var(--ff-ease-out); }
.ff-row--inv .ff-cell::before { display: none; }
.ff-plus { position: relative; width: 22px; height: 22px; overflow: visible; transition: transform 280ms var(--ff-ease-out), color 160ms ease; }
.ff-row--inv .ff-plus { color: var(--signal); }
.ff-item[data-state="open"] .ff-plus { transform: rotate(135deg); transition-duration: var(--ff-in); }
@media (hover: hover) and (pointer: fine) {
  .ff-btn:hover .ff-label { transform: translateX(0.3em); }
  .ff-item[data-state="closed"] .ff-btn:hover .ff-cell::before { clip-path: inset(0 0 0 0); }
  .ff-item[data-state="closed"] .ff-btn:hover .ff-plus { color: var(--o); }
}
.ff-panel { position: relative; display: grid; grid-template-rows: 0fr; transition: grid-template-rows 240ms var(--ff-ease-out); }
.ff-item[data-state="open"] .ff-panel { grid-template-rows: 1fr; transition: grid-template-rows 360ms var(--ff-ease-out); }
.ff-panel-in { overflow: hidden; min-height: 0; }
.ff-item[data-state="closed"] .ff-panel-in { visibility: hidden; }
.ff-answer { padding: 0 0 28px; color: var(--o); }
@media (min-width: 768px) { .ff-answer { padding-left: calc((100% + 24px) / 9 * 3); } }
.ff-text { max-width: 60ch; font-size: 1.0625rem; line-height: 1.55; margin: 0; }
@media (prefers-reduced-motion: reduce) {
  .ff-fill, .ff-row--inv, .ff-panel, .ff-plus, .ff-label, .ff-cell::before,
  .ff-item[data-state] .ff-fill, .ff-item[data-state] .ff-row--inv, .ff-item[data-state] .ff-panel { transition: none !important; }
  .ff-btn:hover .ff-label { transform: none !important; }
}
`;

function PlusIcon() {
  return (
    <span className="ff-cell" aria-hidden="true">
      <svg className="ff-plus" viewBox="0 0 32 32" fill="none">
        <path d="M16 1v30M1 16h30" stroke="currentColor" strokeWidth="2.5" />
      </svg>
    </span>
  );
}

export default function FloodFaq({ items, defaultOpen = 0 }: { items: FaqItem[]; defaultOpen?: number | null }) {
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const btnRefs = React.useRef([] as (HTMLButtonElement | null)[]);
  const timers = React.useRef({} as Record<string, number>);
  const ids = React.useMemo(() => items.map((it) => it.id ?? "faq-" + slugify(it.question)), [items]);

  const [open, setOpen] = React.useState<string[]>(() =>
    defaultOpen === null || !ids[defaultOpen] ? [] : [ids[defaultOpen]],
  );
  const [closing, setClosing] = React.useState<string[]>([]);
  const openRef = React.useRef(open);
  React.useEffect(() => {
    openRef.current = open;
  }, [open]);

  const reduced = React.useCallback(
    () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  // A question that closes wipes its ink out to the right before it is put away. Both state
  // updates land in the same render, so the ink never blinks.
  const changeOpen = React.useCallback(
    (next: string[]) => {
      const closed = openRef.current.filter((id) => !next.includes(id));
      openRef.current = next;
      setOpen(next);
      if (!closed.length || reduced()) return;
      setClosing((cur) => [...cur.filter((c) => !closed.includes(c) && !next.includes(c)), ...closed]);
      for (const id of closed) {
        window.clearTimeout(timers.current[id]);
        timers.current[id] = window.setTimeout(() => setClosing((cur) => cur.filter((c) => c !== id)), 300);
      }
    },
    [reduced],
  );

  // A #hash naming a question opens it and brings it into view.
  React.useEffect(() => {
    const fromHash = () => {
      const h = decodeURIComponent(location.hash.replace(/^#/, ""));
      if (!h || !ids.includes(h)) return;
      changeOpen([h]);
      const i = ids.indexOf(h);
      window.setTimeout(
        () => btnRefs.current[i]?.scrollIntoView({ block: "center", behavior: reduced() ? "auto" : "smooth" }),
        60,
      );
    };
    fromHash();
    window.addEventListener("hashchange", fromHash);
    return () => window.removeEventListener("hashchange", fromHash);
  }, [ids, reduced, changeOpen]);

  React.useEffect(() => {
    const t = timers.current;
    return () => Object.values(t).forEach((h) => window.clearTimeout(h));
  }, []);

  const toggle = (id: string) => changeOpen(open.includes(id) ? [] : [id]);

  return (
    <div className="ff">
      <style>{css}</style>
      <ul className="ff-list">
        {items.map((it, i) => {
          const id = ids[i];
          const isOpen = open.includes(id);
          const state = isOpen ? "open" : closing.includes(id) ? "closing" : "closed";
          const btnId = uid + "-b-" + i;
          const panelId = uid + "-p-" + i;
          const row = (inv: boolean) => (
            <span className={"ff-row" + (inv ? " ff-row--inv" : "")} aria-hidden={inv ? "true" : undefined}>
              <span className="ff-label">{it.question}</span>
              <PlusIcon />
            </span>
          );
          return (
            <li key={id} id={id} className="ff-item" data-state={state}>
              <span className="ff-fill" aria-hidden="true" />
              <h3 className="ff-h">
                <button
                  ref={(el) => {
                    btnRefs.current[i] = el;
                  }}
                  id={btnId}
                  type="button"
                  className="ff-btn"
                  aria-expanded={isOpen}
                  aria-controls={panelId}
                  onClick={() => toggle(id)}
                  onKeyDown={(e) => {
                    const to = nextFocus(e.key, i, items.length);
                    if (to < 0) return;
                    e.preventDefault();
                    btnRefs.current[to]?.focus();
                  }}
                >
                  {row(false)}
                  {row(true)}
                </button>
              </h3>
              <div className="ff-panel" id={panelId} role="region" aria-labelledby={btnId}>
                <div className="ff-panel-in">
                  <div className="ff-answer">
                    <p className="ff-text">{it.answer}</p>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
