// The mark: a five-stall roundhouse in plan view with the turntable at its centre.

const pt = (cx: number, cy: number, r: number, deg: number) => {
  const a = (deg * Math.PI) / 180;
  return [+(cx + r * Math.cos(a)).toFixed(2), +(cy + r * Math.sin(a)).toFixed(2)] as const;
};

const CX = 16,
  CY = 24,
  R1 = 8.5,
  R2 = 15,
  A0 = 200,
  A1 = 340;

const ring = (() => {
  const [ax, ay] = pt(CX, CY, R2, A0);
  const [bx, by] = pt(CX, CY, R2, A1);
  const [cx, cy] = pt(CX, CY, R1, A1);
  const [dx, dy] = pt(CX, CY, R1, A0);
  return `M${ax} ${ay}A${R2} ${R2} 0 0 1 ${bx} ${by}L${cx} ${cy}A${R1} ${R1} 0 0 0 ${dx} ${dy}Z`;
})();

const dividers = [1, 2, 3, 4].map((i) => {
  const a = A0 + (i * (A1 - A0)) / 5;
  return [...pt(CX, CY, R1 - 0.5, a), ...pt(CX, CY, R2 + 0.5, a)];
});

export function LogoMark({ className, tone = "ink" }: { className?: string; tone?: "ink" | "plant" }) {
  const body = tone === "ink" ? "var(--ink)" : "var(--plant)";
  const gap = tone === "ink" ? "var(--plant)" : "var(--ink)";
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <path d={ring} fill={body} />
      {dividers.map(([x1, y1, x2, y2], i) => (
        <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={gap} strokeWidth={1.2} />
      ))}
      <circle cx={CX} cy={CY} r={3.6} fill="var(--signal)" stroke={body} strokeWidth={1.5} />
    </svg>
  );
}

export function Wordmark({ tone = "ink" }: { tone?: "ink" | "plant" }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark className="size-[30px]" tone={tone} />
      <span className="wide text-[19px] font-[760] tracking-[-0.01em] leading-none">Round House</span>
    </span>
  );
}
