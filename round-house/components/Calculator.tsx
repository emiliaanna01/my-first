"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { gsap, prefersReducedMotion } from "@/lib/gsap";

const WEEKS = 48;
type Key = "people" | "hours" | "rate" | "share" | "build";
const FIELDS: { key: Key; label: string; min: number; max: number; step: number; hint?: string; fmt: (v: number) => string }[] = [
  { key: "people", label: "People doing this work", min: 1, max: 60, step: 1, fmt: (v) => String(v) },
  { key: "hours", label: "Hours each loses per week", min: 1, max: 20, step: 1, hint: "Re-keying, chasing, waiting, copy-paste.", fmt: (v) => `${v} h` },
  { key: "rate", label: "Loaded cost per hour", min: 20, max: 150, step: 5, fmt: (v) => `$${v}` },
  { key: "share", label: "Share we can automate", min: 20, max: 90, step: 5, hint: "Most builds take 40–70% of a process off people.", fmt: (v) => `${v}%` },
  { key: "build", label: "Build price", min: 4000, max: 40000, step: 1000, fmt: (v) => money(v) },
];
const money = (v: number) => "$" + Math.round(v).toLocaleString("en-US");

/** Smoothly tweens a displayed number toward its target. */
function useTweened(value: number) {
  const [shown, setShown] = useState(value);
  const obj = useRef({ v: value });
  useEffect(() => {
    if (prefersReducedMotion()) { obj.current.v = value; setShown(value); return; }
    const t = gsap.to(obj.current, { v: value, duration: 0.6, ease: "power3.out", onUpdate: () => setShown(obj.current.v) });
    return () => { t.kill(); };
  }, [value]);
  return shown;
}

export function Calculator() {
  const [v, setV] = useState<Record<Key, number>>({ people: 6, hours: 5, rate: 45, share: 60, build: 16000 });
  const hours = v.people * v.hours * WEEKS * (v.share / 100);
  const value = hours * v.rate;
  const months = v.build / (value / 12);
  const shownHours = useTweened(hours);
  const shownValue = useTweened(value);
  const payback = months < 1 ? "under 1 month" : months > 24 ? "over 24 months" : `${months.toFixed(1)} months`;

  return (
    <div className="calc on-dark">
      <div className="calc-inputs">
        <div style={{ display: "grid", gap: 14 }}>
          <h2 className="h2" id="calc-title">What would the hours be worth?</h2>
          <p className="lede" style={{ color: "var(--on-brunswick-2)" }}>Move the sliders to match one slow process in your business. The audit replaces this estimate with measured numbers.</p>
        </div>
        {FIELDS.map((f) => (
          <div className="field-range" key={f.key}>
            <div className="fr-top">
              <label htmlFor={`c-${f.key}`}>{f.label}</label>
              <output htmlFor={`c-${f.key}`}>{f.fmt(v[f.key])}</output>
            </div>
            <input
              id={`c-${f.key}`}
              type="range"
              min={f.min}
              max={f.max}
              step={f.step}
              value={v[f.key]}
              style={{ ["--fill" as string]: `${((v[f.key] - f.min) / (f.max - f.min)) * 100}%` }}
              onChange={(e) => setV((s) => ({ ...s, [f.key]: Number(e.target.value) }))}
            />
            {f.hint && <span className="hint">{f.hint}</span>}
          </div>
        ))}
      </div>
      <div className="calc-out" aria-live="polite">
        <div className="row"><span className="lab">Hours back each year</span><span className="val num">{Math.round(shownHours).toLocaleString("en-US")}</span></div>
        <div className="row"><span className="lab">What those hours cost you today</span><span className="val num signal">{money(shownValue)}</span></div>
        <div className="row pay">
          <span className="lab">Build pays for itself in</span>
          <span className="val num">{payback}</span>
          <div className="payback-bar" aria-hidden="true">
            <i style={{ width: `${Math.min(100, (months / 24) * 100).toFixed(1)}%`, background: months <= 12 ? undefined : "var(--stop)" }} />
          </div>
          <div className="payback-scale" aria-hidden="true"><span>0</span><span>6 mo</span><span>12 mo</span><span>18 mo</span><span>24 mo</span></div>
        </div>
        <p className="calc-note">Uses {WEEKS} working weeks a year. An estimate from your inputs, not a quote.</p>
        <Link className="btn" href="/contact#book" style={{ justifySelf: "start" }}>Check it on a call</Link>
      </div>
    </div>
  );
}
