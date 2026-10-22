import { ImageResponse } from "next/og";

export const alt = "Round House: we automate the work that slows you down";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 72, background: "#1c4332", color: "#e9efe9" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18, fontSize: 34, fontWeight: 700 }}>
          <div style={{ width: 40, height: 40, borderRadius: 40, border: "4px solid #e9efe9", display: "flex", alignItems: "flex-start", justifyContent: "center" }}>
            <div style={{ width: 8, height: 18, marginTop: 4, background: "#f5b700", borderRadius: 2 }} />
          </div>
          Round House
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ fontSize: 92, fontWeight: 800, lineHeight: 0.95, letterSpacing: -2, maxWidth: 960 }}>We automate the work that slows you down.</div>
          <div style={{ fontSize: 30, color: "#b4c6ba" }}>Audits, automation, AI agents, CRM, brand and web. Prices on the page.</div>
        </div>
        <div style={{ display: "flex", gap: 14, alignItems: "center", fontSize: 26, color: "#f5b700", fontWeight: 700 }}>
          <div style={{ width: 14, height: 14, borderRadius: 14, background: "#f5b700" }} />
          Diagnose · Build · Run
        </div>
      </div>
    ),
    size,
  );
}
