import Link from "next/link";
import { EMAIL, NAV, SITE } from "@/lib/content";
import { EasternClock, HoursLamp } from "./HoursLamp";
import { FootWord } from "./FootWord";

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="wrap">
        <div className="foot-grid">
          <div style={{ display: "grid", gap: 16, alignContent: "start", justifyItems: "start" }}>
            <p style={{ maxWidth: "30ch", color: "var(--ink-2)" }}>We automate the work that slows US businesses down, from the factory floor to the front office.</p>
            <HoursLamp />
          </div>
          <div style={{ display: "grid", gap: 32 }}>
            <nav className="foot-nav" aria-label="Footer">
              <Link href="/">Home</Link>
              {NAV.map((n) => <Link key={n.key} href={n.href}>{n.label}</Link>)}
            </nav>
            <dl className="foot-facts">
              <div><dt>Studio</dt><dd>Round House</dd></div>
              <div><dt>Hours</dt><dd>9am–6pm ET, Monday to Friday</dd></div>
              <div><dt>Contact</dt><dd>{EMAIL}</dd></div>
              <div><dt>Contracts</dt><dd>Mutual NDA, MSA and fixed-price SOW</dd></div>
              <div><dt>Updated</dt><dd>{SITE.revision}</dd></div>
            </dl>
          </div>
        </div>
        <FootWord text="Round House" />
        <div className="foot-base">
          <span>© 2026 Round House. Case studies marked as samples are illustrative.</span>
          <EasternClock />
        </div>
      </div>
    </footer>
  );
}
