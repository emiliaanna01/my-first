"use client";

import * as React from "react";

import { site } from "@/content/site";
import { cn } from "@/lib/utils";

/** True when it is currently inside US Eastern business hours. */
function isOpenNow(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: site.hours.timeZone,
    weekday: "short",
    hour: "numeric",
    hourCycle: "h23",
  }).formatToParts(now);
  const weekday = parts.find((p) => p.type === "weekday")?.value ?? "";
  const hour = Number(parts.find((p) => p.type === "hour")?.value ?? -1);
  return !["Sat", "Sun"].includes(weekday) && hour >= site.hours.open && hour < site.hours.close;
}

/**
 * The server renders the plain hours. After hydration the line says whether we are open
 * right now, so it never claims "open" from a stale static page.
 */
export function HoursStatus({ className }: { className?: string }) {
  const [open, setOpen] = React.useState<boolean | null>(null);

  React.useEffect(() => {
    const tick = () => setOpen(isOpenNow());
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
      {open === false && <>Back at 9am ET. Calls {site.hours.label}</>}
    </p>
  );
}
