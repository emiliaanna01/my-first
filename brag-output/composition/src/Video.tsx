import React, { useEffect, useState } from "react";
import {
  AbsoluteFill, Audio, Easing, Img, Sequence, continueRender, delayRender,
  interpolate, staticFile, useCurrentFrame,
} from "remotion";

// 120 BPM at 30fps: one beat = 15 frames, one bar = 60 frames.
export const BEAT = 15;

const C = {
  paper: "#f7f7f2", ink: "#1d221e", muted: "#626a60", sage: "#7d8a67", lime: "#e0ed9b",
  line: "#d8ddd1", journey: "#e3e8cf", knowledge: "#e7e2f0", brand: "#e7dacb", dark: "#1f251f",
  plum: "#3f3550", brown: "#5e3a2a",
};
const HEAD = "'Inter Tight Variable', 'Inter Tight', Arial, sans-serif";
const BODY = "'DM Sans', Arial, sans-serif";
const ease = Easing.bezier(0.16, 0.84, 0.24, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Scene timeline (frames). `wipe` = the scene's colour arrives as a growing circle.
const SCENES = {
  hook: { from: 0, dur: 120, bg: C.paper },
  reveal: { from: 120, dur: 150, bg: C.paper },
  statement: { from: 270, dur: 150, bg: C.paper },
  journey: { from: 420, dur: 210, bg: C.journey, wipe: true },
  workflow: { from: 630, dur: 180, bg: C.journey },
  knowledge: { from: 810, dur: 180, bg: C.knowledge, wipe: true },
  brand: { from: 990, dur: 150, bg: C.brand, wipe: true },
  calc: { from: 1140, dur: 180, bg: C.dark, wipe: true },
  process: { from: 1320, dur: 120, bg: C.paper, wipe: true },
  cta: { from: 1440, dur: 180, bg: C.paper },
};
export const TOTAL = 1620;
export const CUTS = Object.values(SCENES).map((s) => s.from);

// ---------- helpers ----------
const prog = (f: number, start: number, dur = 18) => interpolate(f, [start, start + dur], [0, 1], { ...clamp, easing: ease });

const Rise: React.FC<{ f: number; at: number; dur?: number; y?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ f, at, dur = 20, y = 40, children, style }) => {
  const p = prog(f, at, dur);
  return <div style={{ opacity: p, transform: `translateY(${(1 - p) * y}px)`, ...style }}>{children}</div>;
};

// Words slide up out of a mask, one per `step` frames.
const Words: React.FC<{ text: string; f: number; at: number; step?: number; style?: React.CSSProperties; wordStyle?: (i: number) => React.CSSProperties }> = ({ text, f, at, step = 4, style, wordStyle }) => (
  <div style={{ display: "flex", flexWrap: "wrap", ...style }}>
    {text.split(" ").map((w, i) => {
      const p = prog(f, at + i * step, 22);
      return (
        <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: "0.12em", marginBottom: "-0.12em", marginRight: "0.22em" }}>
          <span style={{ display: "inline-block", transform: `translateY(${(1 - p) * 105}%)`, ...(wordStyle ? wordStyle(i) : {}) }}>{w}</span>
        </span>
      );
    })}
  </div>
);

const Eyebrow: React.FC<{ children: React.ReactNode; color?: string; style?: React.CSSProperties }> = ({ children, color = C.ink, style }) => (
  <div style={{ fontFamily: BODY, fontWeight: 500, fontSize: 20, letterSpacing: "0.1em", textTransform: "uppercase", color, display: "flex", alignItems: "center", gap: 14, ...style }}>
    <span style={{ width: 9, height: 9, borderRadius: 9, background: C.sage }} />
    {children}
  </div>
);

const headStyle = (size: number, color = C.ink): React.CSSProperties => ({
  fontFamily: HEAD, fontWeight: 550, fontSize: size, letterSpacing: "-0.058em", lineHeight: 1.0, color,
});

// Scene shell: background (optionally a round wipe), slow push-in, staggered exit.
const Scene: React.FC<{ s: { from: number; dur: number; bg: string; wipe?: boolean }; children: (f: number) => React.ReactNode; exit?: boolean }> = ({ s, children, exit = true }) => (
  <Sequence from={s.from} durationInFrames={s.dur + 24} layout="none">
    <SceneInner s={s} exit={exit}>{children}</SceneInner>
  </Sequence>
);
const SceneInner: React.FC<{ s: { dur: number; bg: string; wipe?: boolean }; exit: boolean; children: (f: number) => React.ReactNode }> = ({ s, exit, children }) => {
  const f = useCurrentFrame();
  const r = s.wipe ? interpolate(f, [0, 22], [0, 1180], { ...clamp, easing: Easing.bezier(0.6, 0, 0.2, 1) }) : 2000;
  const out = exit ? interpolate(f, [s.dur - 10, s.dur], [1, 0], clamp) : 1;
  const outY = exit ? interpolate(f, [s.dur - 10, s.dur], [0, -24], { ...clamp, easing: Easing.in(Easing.quad) }) : 0;
  const push = interpolate(f, [0, s.dur], [1, 1.035]);
  return (
    <AbsoluteFill style={{ background: s.bg, clipPath: s.wipe ? `circle(${r}px at 50% 50%)` : undefined }}>
      <AbsoluteFill style={{ opacity: out, transform: `translateY(${outY}px) scale(${push})` }}>{children(f)}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- the sphere cluster (rebuilt from the hero's 3D sculpture) ----------
const SPHERE_KIND = ["c", "k", "c", "w", "c", "c", "k", "c", "w", "c", "c", "k", "c", "w", "c", "c"];
const sphereBg = (k: string) =>
  k === "k"
    ? "radial-gradient(circle at 34% 28%, #ffffff 0%, #9a9c98 4%, #3a3d3a 18%, #141614 55%, #050605 100%)"
    : k === "w"
      ? "radial-gradient(circle at 34% 28%, #ffffff 0%, #fbfbf8 22%, #e7e7e1 62%, #c9c9c1 100%)"
      : "radial-gradient(circle at 34% 28%, #ffffff 0%, #f6f9df 14%, #e5ebb7 48%, #c8cf8f 86%, #b2b977 100%)";

const Spheres: React.FC<{ f: number; cx: number; cy: number; scale?: number; enterAt?: number }> = ({ f, cx, cy, scale = 1, enterAt = 0 }) => {
  const n = SPHERE_KIND.length;
  const theta = f * 0.012 + 0.6;
  const items = SPHERE_KIND.map((k, i) => {
    const a = (i / n) * Math.PI * 2 + Math.sin(f * 0.02 + i) * 0.05;
    const R = 230 + 30 * Math.sin(i * 2.1);
    const x0 = R * Math.cos(a), y0 = R * Math.sin(a) * 1.08, z0 = 60 * Math.sin(i * 1.7);
    const x = x0 * Math.cos(theta) + z0 * Math.sin(theta);
    const z = -x0 * Math.sin(theta) + z0 * Math.cos(theta);
    const bob = Math.sin(f * 0.05 + i * 0.8) * 8;
    const persp = 900 / (900 - z);
    const size = (96 + 40 * ((i * 7) % 5) / 4) * persp;
    const p = interpolate(f, [enterAt + i * 2, enterAt + i * 2 + 26], [0, 1], { ...clamp, easing: Easing.bezier(0.3, 1.5, 0.5, 1) });
    return { k, i, x: x * persp, y: y0 * persp + bob, z, size, p };
  }).sort((a, b) => a.z - b.z);
  return (
    <div style={{ position: "absolute", left: cx, top: cy, transform: `scale(${scale})` }}>
      <div style={{ position: "absolute", left: -330, top: 330, width: 660, height: 70, borderRadius: "50%", background: "radial-gradient(closest-side, rgba(29,34,30,0.16), rgba(29,34,30,0))", opacity: prog(f, enterAt, 30) }} />
      {items.map((s) => (
        <div key={s.i} style={{
          position: "absolute", left: s.x - s.size / 2, top: s.y - s.size / 2, width: s.size, height: s.size, borderRadius: "50%",
          background: sphereBg(s.k), transform: `scale(${s.p})`,
          boxShadow: `inset -${s.size * 0.06}px -${s.size * 0.08}px ${s.size * 0.18}px rgba(0,0,0,${s.k === "k" ? 0.5 : 0.12}), 0 ${s.size * 0.12}px ${s.size * 0.25}px rgba(29,34,30,0.12)`,
        }} />
      ))}
    </div>
  );
};

// ---------- scenes ----------
const Hook: React.FC<{ f: number }> = ({ f }) => {
  const hl = prog(f, 52, 22);
  return (
    <AbsoluteFill>
      <Spheres f={f + 120} cx={1530} cy={500} scale={0.92} enterAt={120 + 6} />
      <div style={{ position: "absolute", left: 140, top: 250 }}>
        <Words text="Good ideas." f={f} at={4} step={7} style={headStyle(220)} />
        <div style={{ display: "flex", marginTop: 6 }}>
          <Words text="Made" f={f} at={30} style={headStyle(220)} />
          <div style={{ position: "relative" }}>
            <div style={{ position: "absolute", left: -6, top: 150, height: 68, width: 372 * hl, background: C.lime }} />
            <Words text="real." f={f} at={39} style={{ ...headStyle(220), position: "relative" }} />
          </div>
        </div>
      </div>
      <Rise f={f} at={70} style={{ position: "absolute", left: 146, top: 820, fontFamily: BODY, fontSize: 30, color: C.muted }}>
        Brands, websites, and automated workflows for growing businesses.
      </Rise>
    </AbsoluteFill>
  );
};

const Reveal: React.FC<{ f: number }> = ({ f }) => {
  const chips = ["Brand identity", "Websites & UI/UX", "Automation & AI"];
  const dot = interpolate(f, [16, 30], [0, 1], { ...clamp, easing: Easing.bezier(0.3, 1.6, 0.5, 1) });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ display: "flex", alignItems: "baseline", ...headStyle(250), fontWeight: 720, letterSpacing: "-0.055em" }}>
        <Words text="roundhouse" f={f} at={0} />
        <span style={{ display: "inline-block", width: 52, height: 52, borderRadius: 52, background: C.sage, transform: `scale(${dot})`, marginLeft: -40 }} />
      </div>
      <Rise f={f} at={30} style={{ marginTop: 34 }}><Eyebrow style={{ fontSize: 26 }}>An independent digital agency.</Eyebrow></Rise>
      <div style={{ display: "flex", gap: 22, marginTop: 70 }}>
        {chips.map((c, i) => {
          const p = prog(f, 60 + i * BEAT, 18);
          return (
            <div key={c} style={{ opacity: p, transform: `translateY(${(1 - p) * 30}px) scale(${0.9 + 0.1 * p})`, fontFamily: BODY, fontSize: 32, color: C.ink, padding: "16px 34px", border: `1.5px solid ${C.line}`, borderRadius: 60, background: i === 2 ? C.lime : "#fbfbf7" }}>{c}</div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Statement: React.FC<{ f: number }> = ({ f }) => (
  <AbsoluteFill>
    <Rise f={f} at={0} style={{ position: "absolute", left: 140, top: 200 }}><Eyebrow>One business. Connected experiences.</Eyebrow></Rise>
    <div style={{ position: "absolute", left: 140, top: 290 }}>
      <Words text="How you show up." f={f} at={6} step={5} style={headStyle(150)} />
      <Words text="How the work gets done." f={f} at={36} step={5} style={{ ...headStyle(150, C.sage), marginTop: 8 }} />
    </div>
    <Rise f={f} at={70} style={{ position: "absolute", left: 146, top: 700, width: 1100, fontFamily: BODY, fontSize: 34, lineHeight: 1.5, color: C.muted }}>
      A customer visits your website, sends an inquiry, and waits for a reply. We help improve the experience on both sides.
    </Rise>
  </AbsoluteFill>
);

const Tags: React.FC<{ f: number; at: number; tags: string[]; color?: string }> = ({ f, at, tags, color = C.ink }) => (
  <div style={{ display: "flex", gap: 14, marginTop: 40 }}>
    {tags.map((t, i) => {
      const p = prog(f, at + i * 5, 16);
      return <div key={t} style={{ opacity: p, transform: `translateY(${(1 - p) * 16}px)`, fontFamily: BODY, fontSize: 24, color, padding: "10px 24px", border: `1.5px solid ${color}33`, borderRadius: 40 }}>{t}</div>;
    })}
  </div>
);

const CopyBlock: React.FC<{ f: number; eyebrow: string; title: string[]; body: string; tags: string[]; color?: string }> = ({ f, eyebrow, title, body, tags, color = C.ink }) => (
  <div style={{ position: "absolute", left: 130, top: 250, width: 980 }}>
    <Rise f={f} at={14}><Eyebrow color={color}>{eyebrow}</Eyebrow></Rise>
    <div style={{ marginTop: 34 }}>
      {title.map((t, i) => <Words key={i} text={t} f={f} at={20 + i * 12} step={4} style={headStyle(84, color)} />)}
    </div>
    <Rise f={f} at={52} style={{ marginTop: 34, fontFamily: BODY, fontSize: 30, lineHeight: 1.5, color: C.muted, width: 620 }}>{body}</Rise>
    <Tags f={f} at={66} tags={tags} color={color} />
  </div>
);

const Mock: React.FC<{ f: number; at: number; src: string; w: number; x: number; y: number; rot?: [number, number, number] }> = ({ f, at, src, w, x, y, rot = [6, -14, 2] }) => {
  const p = prog(f, at, 36);
  const drift = interpolate(f, [at, at + 220], [0, 1]);
  const rx = rot[0] * (1 + (1 - p) * 1.5), ry = rot[1] * (1 + (1 - p) * 1.8) + drift * 4, rz = rot[2];
  return (
    <div style={{ position: "absolute", left: x, top: y, perspective: 2400, opacity: p }}>
      <div style={{ transform: `translateX(${(1 - p) * 220}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg)`, transformStyle: "preserve-3d" }}>
        <Img src={staticFile(src)} style={{ width: w, display: "block", borderRadius: 14, boxShadow: "0 40px 90px rgba(29,34,30,0.18), 0 8px 20px rgba(29,34,30,0.08)" }} />
      </div>
    </div>
  );
};

const Journey: React.FC<{ f: number }> = ({ f }) => (
  <AbsoluteFill>
    <CopyBlock f={f} eyebrow="01 / Customer journey" title={["Give every inquiry", "a next step."]} body="Connect your forms, customer records, and follow-up tasks so your team can respond with the right information." tags={["Lead capture", "CRM", "Follow-up"]} />
    <Mock f={f} at={24} src="ui/lead.png" w={1000} x={860} y={300} />
  </AbsoluteFill>
);

const Icon: React.FC<{ kind: number; color: string }> = ({ kind, color }) => (
  <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    {kind === 0 && <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z" />}
    {kind === 1 && <path d="M12 3v4M12 17v4M3 12h4M17 12h4M12 7c.8 3 2 4.2 5 5-3 .8-4.2 2-5 5-.8-3-2-4.2-5-5 3-.8 4.2-2 5-5z" />}
    {kind === 2 && <path d="m5 12.5 4.5 4.5L19 7.5" />}
  </svg>
);

const Workflow: React.FC<{ f: number }> = ({ f }) => {
  const nodes = ["Inquiry received", "Details checked", "Follow-up assigned"];
  return (
    <AbsoluteFill>
      <Rise f={f} at={0} style={{ position: "absolute", left: 130, top: 150 }}><Eyebrow>See how the steps connect.</Eyebrow></Rise>
      <div style={{ position: "absolute", left: 130, top: 215 }}>
        <Words text="A smoother handoff" f={f} at={4} step={4} style={headStyle(120)} />
        <Words text="starts here." f={f} at={16} step={4} style={headStyle(120, C.sage)} />
      </div>
      <Rise f={f} at={20} y={60} style={{ position: "absolute", left: 130, top: 520, width: 1660, height: 330, background: "#f8f9f3", borderRadius: 34, border: `1.5px solid ${C.line}`, padding: "40px 48px", boxSizing: "border-box" }}>
        <div style={{ fontFamily: BODY, fontSize: 18, letterSpacing: "0.1em", color: C.sage }}>ILLUSTRATIVE WORKFLOW / 01 · LEAD RESPONSE</div>
        <div style={{ display: "flex", alignItems: "center", marginTop: 46 }}>
          {nodes.map((n, i) => {
            const on = prog(f, 45 + i * 2 * BEAT, 12);
            const pulse = interpolate(f, [45 + i * 30, 45 + i * 30 + 20], [0, 1], clamp);
            return (
              <React.Fragment key={n}>
                <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 26, opacity: 0.35 + 0.65 * on }}>
                  <div style={{ position: "relative", width: 86, height: 86, borderRadius: 86, border: `1.5px solid ${C.sage}`, background: `rgba(224,237,155,${on})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <div style={{ position: "absolute", inset: -2, borderRadius: 90, border: `2px solid ${C.sage}`, transform: `scale(${1 + pulse * 0.6})`, opacity: (1 - pulse) * (pulse > 0 ? 1 : 0) }} />
                    <Icon kind={i} color={C.ink} />
                  </div>
                  <div>
                    <div style={{ fontFamily: BODY, fontSize: 20, color: C.sage }}>0{i + 1}</div>
                    <div style={{ fontFamily: BODY, fontSize: 34, color: C.ink, marginTop: 4, whiteSpace: "nowrap" }}>{n}</div>
                  </div>
                </div>
                {i < 2 && (
                  <div style={{ width: 90, height: 2, background: C.line, marginRight: 30, position: "relative" }}>
                    <div style={{ position: "absolute", inset: 0, background: C.sage, transformOrigin: "left", transform: `scaleX(${prog(f, 52 + i * 30, 20)})` }} />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
        <div style={{ position: "absolute", left: 48, bottom: 36, fontFamily: BODY, fontSize: 28, color: C.muted, opacity: prog(f, 118, 18) }}>
          Your rules shape the response. Your team handles exceptions and the decisions that need a person.
        </div>
      </Rise>
    </AbsoluteFill>
  );
};

const Knowledge: React.FC<{ f: number }> = ({ f }) => (
  <AbsoluteFill>
    <CopyBlock f={f} color={C.plum} eyebrow="02 / Operations" title={["Make team knowledge", "easier to find."]} body="Help people find answers in approved documents, with source references and a clear route to ask for help." tags={["Internal AI assistant", "Team knowledge"]} />
    <Mock f={f} at={26} src="ui/knowledge.png" w={880} x={990} y={290} rot={[5, -12, -1.5]} />
  </AbsoluteFill>
);

const Brand: React.FC<{ f: number }> = ({ f }) => {
  const p = prog(f, 22, 40);
  return (
    <AbsoluteFill>
      <CopyBlock f={f} color={C.brown} eyebrow="03 / Brand & digital" title={["Make your business", "easier to understand."]} body="Bring your message, identity, and website together so visitors can see your value and find the next step." tags={["Brand identity", "Websites", "UI/UX"]} />
      <div style={{ position: "absolute", left: 1200, top: 170, perspective: 2200, opacity: p }}>
        <div style={{ transform: `rotateY(${(1 - p) * -70 - 8 + f * 0.04}deg) rotateZ(${-6 + (1 - p) * 8}deg) translateY(${(1 - p) * 60}px)` }}>
          <Img src={staticFile("ui/identity.png")} style={{ width: 520, display: "block", boxShadow: "0 50px 90px rgba(60,35,20,0.28)" }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Calc: React.FC<{ f: number }> = ({ f }) => {
  const t = interpolate(f, [40, 120], [0, 1], { ...clamp, easing: Easing.bezier(0.45, 0, 0.2, 1) });
  const hours = 20 * t;
  const freed = hours * 0.5 * 4.33;
  const segs = 28;
  const lit = Math.round((freed / 43.3) * 14);
  return (
    <AbsoluteFill>
      <Rise f={f} at={14} style={{ position: "absolute", left: 130, top: 250 }}><Eyebrow color="#c9d0b7">A little less repetition.</Eyebrow></Rise>
      <div style={{ position: "absolute", left: 130, top: 320 }}>
        <Words text="What could" f={f} at={18} step={4} style={headStyle(104, C.paper)} />
        <Words text="your team" f={f} at={26} step={4} style={headStyle(104, C.paper)} />
        <Words text="make time for?" f={f} at={34} step={4} style={headStyle(104, C.lime)} />
      </div>
      <Rise f={f} at={24} y={60} style={{ position: "absolute", left: 960, top: 200, width: 830, padding: "44px 50px", boxSizing: "border-box", borderRadius: 34, background: "#2a312a", border: "1.5px solid #3a433a" }}>
        <div style={{ fontFamily: BODY, fontSize: 18, letterSpacing: "0.1em", color: "#c9d0b7" }}>YOUR ROOM TO GROW</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginTop: 22 }}>
          <div>
            <div style={{ ...headStyle(170, "#f7f7f2"), letterSpacing: "-0.05em", fontVariantNumeric: "tabular-nums" }}>{freed.toFixed(1)}</div>
            <div style={{ fontFamily: BODY, fontSize: 24, color: "#dfe3d6", marginTop: 12 }}>Potential hours freed per month</div>
          </div>
          <div style={{ fontFamily: BODY, fontSize: 22, color: "#dfe3d6", textAlign: "right", marginBottom: 46 }}>
            That's about <span style={{ color: C.lime, fontSize: 34 }}>{(freed / 8).toFixed(1)}</span><br />eight-hour working days.
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, marginTop: 36 }}>
          {Array.from({ length: segs }).map((_, i) => (
            <div key={i} style={{ flex: 1, height: 58, borderRadius: 4, background: i < lit ? C.lime : "#465046" }} />
          ))}
        </div>
        <div style={{ height: 1.5, background: "#3d463d", margin: "34px 0 26px" }} />
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: BODY, fontSize: 24, color: "#f2f3ec" }}>
          <span>Time spent on this task each week</span><span style={{ color: C.lime }}>{Math.round(hours)} hours</span>
        </div>
        <div style={{ position: "relative", height: 30, marginTop: 14 }}>
          <div style={{ position: "absolute", top: 13, left: 0, right: 0, height: 4, borderRadius: 4, background: "#465046" }} />
          <div style={{ position: "absolute", top: 13, left: 0, width: `${t * 16.6}%`, height: 4, borderRadius: 4, background: C.lime }} />
          <div style={{ position: "absolute", top: 1, left: `calc(${t * 16.6}% - 14px)`, width: 28, height: 28, borderRadius: 28, background: C.lime, border: "5px solid #2a312a", boxShadow: `0 0 0 2px ${C.lime}` }} />
        </div>
        <div style={{ fontFamily: BODY, fontSize: 19, color: "#9aa394", marginTop: 26 }}>Illustrative estimate at 50% assumed reduction. Not an assessed saving.</div>
      </Rise>
    </AbsoluteFill>
  );
};

const Process: React.FC<{ f: number }> = ({ f }) => {
  const steps = ["Diagnose.", "Build.", "Run."];
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ display: "flex", gap: 70 }}>
        {steps.map((s, i) => {
          const p = interpolate(f, [16 + i * BEAT, 16 + i * BEAT + 14], [0, 1], { ...clamp, easing: Easing.bezier(0.2, 1.4, 0.4, 1) });
          return (
            <div key={s} style={{ textAlign: "left", opacity: p, transform: `translateY(${(1 - p) * 50}px) scale(${0.85 + 0.15 * p})` }}>
              <div style={{ fontFamily: BODY, fontSize: 24, color: C.sage, marginBottom: 6 }}>0{i + 1}</div>
              <div style={{ ...headStyle(170), background: i === 0 ? `linear-gradient(transparent 62%, ${C.lime} 62%, ${C.lime} 92%, transparent 92%)` : undefined }}>{s}</div>
            </div>
          );
        })}
      </div>
      <Rise f={f} at={68} style={{ marginTop: 70, ...headStyle(56, C.sage), letterSpacing: "-0.04em" }}>Understand it. Build it. Keep it useful.</Rise>
    </AbsoluteFill>
  );
};

const Cta: React.FC<{ f: number }> = ({ f }) => {
  // simulated cursor travelling to the button, then a click on the beat
  const move = prog(f, 60, 26);
  const click = f >= 90 && f < 98 ? 0.95 : 1;
  const ripple = interpolate(f, [90, 114], [0, 1], clamp);
  const cx = interpolate(move, [0, 1], [1260, 470]), cy = interpolate(move, [0, 1], [980, 728]);
  return (
    <AbsoluteFill>
      <Spheres f={f + 400} cx={1440} cy={470} scale={0.95} enterAt={400 + 10} />
      <Rise f={f} at={4} style={{ position: "absolute", left: 140, top: 190 }}><Eyebrow>A useful next step.</Eyebrow></Rise>
      <div style={{ position: "absolute", left: 140, top: 250, width: 980 }}>
        <Words text="What's the next thing you'd like to make better?" f={f} at={10} step={4} style={headStyle(112)} />
      </div>
      <div style={{ position: "absolute", left: 140, top: 680, opacity: prog(f, 50, 18), transform: `scale(${click})`, transformOrigin: "left center" }}>
        <div style={{ position: "relative", display: "flex", alignItems: "center", gap: 22, background: C.ink, color: C.paper, fontFamily: BODY, fontSize: 34, padding: "26px 44px", borderRadius: 70, overflow: "hidden" }}>
          <div style={{ position: "absolute", left: 330 - 300 * ripple, top: 50 - 300 * ripple, width: 600 * ripple, height: 600 * ripple, borderRadius: "50%", background: C.lime, opacity: 0.35 * (1 - ripple) }} />
          Tell us about your project
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={C.paper} strokeWidth="1.8"><path d="M7 17 17 7M8 7h9v9" /></svg>
        </div>
      </div>
      <svg width="44" height="44" viewBox="0 0 24 24" style={{ position: "absolute", left: cx, top: cy, opacity: prog(f, 54, 8) * interpolate(f, [130, 140], [1, 0], clamp), transform: `scale(${click})` }}>
        <path d="M5 3l14 8-6 1.5L10 19z" fill={C.paper} stroke={C.ink} strokeWidth="1.4" strokeLinejoin="round" />
      </svg>
      <Rise f={f} at={118} style={{ position: "absolute", left: 140, bottom: 90, display: "flex", alignItems: "baseline", gap: 40 }}>
        <span style={{ ...headStyle(64), fontWeight: 720 }}>roundhouse<span style={{ color: C.sage }}>.</span></span>
        <span style={{ fontFamily: BODY, fontSize: 28, color: C.muted }}>A little different. Better together.</span>
      </Rise>
    </AbsoluteFill>
  );
};

// ---------- fonts + assembly ----------
const FONTS: [string, string, string][] = [
  ["Inter Tight Variable", "fonts/InterTightVariable-100_900-normal.woff2", "100 900"],
  ["DM Sans", "fonts/DMSans-400-normal.woff2", "400"],
  ["DM Sans", "fonts/DMSans-500-normal.woff2", "500"],
];
const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all(FONTS.map(([fam, src, w]) => new FontFace(fam, `url(${staticFile(src)})`, { weight: w }).load().then((ff) => document.fonts.add(ff))))
      .then(() => continueRender(handle));
  }, [handle]);
};

export const RoundHouse: React.FC = () => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <Scene s={SCENES.hook}>{(f) => <Hook f={f} />}</Scene>
      <Scene s={SCENES.reveal}>{(f) => <Reveal f={f} />}</Scene>
      <Scene s={SCENES.statement}>{(f) => <Statement f={f} />}</Scene>
      <Scene s={SCENES.journey}>{(f) => <Journey f={f} />}</Scene>
      <Scene s={SCENES.workflow}>{(f) => <Workflow f={f} />}</Scene>
      <Scene s={SCENES.knowledge}>{(f) => <Knowledge f={f} />}</Scene>
      <Scene s={SCENES.brand}>{(f) => <Brand f={f} />}</Scene>
      <Scene s={SCENES.calc}>{(f) => <Calc f={f} />}</Scene>
      <Scene s={SCENES.process}>{(f) => <Process f={f} />}</Scene>
      <Scene s={SCENES.cta} exit={false}>{(f) => <Cta f={f} />}</Scene>
      <Audio src={staticFile("soundtrack.wav")} />
    </AbsoluteFill>
  );
};
