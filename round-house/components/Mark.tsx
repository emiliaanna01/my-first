/** The Round House mark: a turntable in plan view, with five stalls and a locomotive on the bridge. */
const STALLS = [-60, -30, 0, 30, 60].map((a) => {
  const r = (a * Math.PI) / 180;
  const p = (rad: number) => [20 + rad * Math.sin(r), 20 - rad * Math.cos(r)].map((v) => +v.toFixed(2));
  const [x1, y1] = p(15.5);
  const [x2, y2] = p(19);
  return { x1, y1, x2, y2 };
});

export function Mark({ className = "brand-mark" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 40 40" aria-hidden="true">
      <circle className="bm-pit" cx="20" cy="20" r="12.5" />
      <circle className="bm-ring" cx="20" cy="20" r="12.5" />
      {STALLS.map((s, i) => (
        <line key={i} className="bm-stall" {...s} />
      ))}
      <g className="bm-rot">
        <rect className="bm-bridge" x="18.2" y="8.6" width="3.6" height="22.8" rx="1" />
        <rect className="bm-loco" x="17.6" y="10" width="4.8" height="7.5" rx="1.2" />
      </g>
    </svg>
  );
}
