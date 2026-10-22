"use client";

import * as React from "react";

import { site } from "@/content/site";
import { cn } from "@/lib/utils";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** Whether it is inside US Eastern business hours now, and when they next open if not. */
function hoursNow(now = new Date()): { open: true } | { open: false; reopens: string } {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: site.hours.timeZone,
    weekday: "short",
    hour: "numeric",
    hourCycle: "h23",
  }).formatToParts(now);
  const day = DAYS.indexOf(parts.find((p) => p.type === "weekday")?.value ?? "");
  const hour = Number(parts.find((p) => p.type === "hour")?.value ?? -1);
  const weekday = day >= 1 && day <= 5;
  if (weekday && hour >= site.hours.open && hour < site.hours.close) return { open: true };
  if (weekday && hour < site.hours.open) return { open: false, reopens: "at 9am ET" };
  // After hours on Mon–Thu reopens tomorrow; Friday evening and weekends reopen Monday.
  if (day >= 1 && day <= 4) return { open: false, reopens: "tomorrow at 9am ET" };
  return { open: false, reopens: "Monday at 9am ET" };
}

/**
 * The server renders the plain hours. After hydration the line says whether we are open
 * right now, so it never claims "open" from a stale static page.
 */
export function HoursStatus({ className }: { className?: string }) {
  const [state, setState] = React.useState<ReturnType<typeof hoursNow> | null>(null);
  const open = state?.open ?? null;

  React.useEffect(() => {
    const tick = () => setState(hoursNow());
    tick();
    const t = window.setInterval(tick, 60_000);
    return () => window.clearInterval(t);
  }, []);

  return (
    <p className={cn("t-small inline-flex items-center gap-2", open ? "text-run" : "text-steel", className)}>
      <span
        aria-hidden="true"
        className={cn("size-2 rounded-full", open ? "bg-run" : "border border-steel bg-transparent")}
      />
      {open === null && <>Calls {site.hours.label}</>}
      {open === true && <>Taking calls now, until 6pm ET</>}
      {state && !state.open && (
        <>
          Back {state.reopens}. Calls {site.hours.label}
        </>
      )}
    </p>
  );
}
