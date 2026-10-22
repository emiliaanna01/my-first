"use client";
import { useEffect, useState, type CSSProperties } from "react";
import { easternNow, officeStatus } from "@/lib/hours";

const RESTING = "Calls 9am–6pm ET, Monday to Friday";

/** A status pill that shows whether the office is open right now in New York. */
export function HoursLamp({ style }: { style?: CSSProperties }) {
  const [state, setState] = useState<{ open: boolean; text: string } | null>(null);
  useEffect(() => {
    const tick = () => setState(officeStatus());
    tick();
    const id = window.setInterval(tick, 30000);
    return () => window.clearInterval(id);
  }, []);
  return (
    <p className="status" data-open={state ? String(state.open) : undefined} style={style}>
      <span className="dot" aria-hidden="true" />
      <span>{state ? state.text : RESTING}</span>
    </p>
  );
}

export function EasternClock() {
  const [time, setTime] = useState("");
  useEffect(() => {
    const tick = () => setTime(easternNow().time);
    tick();
    const id = window.setInterval(tick, 30000);
    return () => window.clearInterval(id);
  }, []);
  return <span>{time ? `New York ${time} ET` : ""}</span>;
}
