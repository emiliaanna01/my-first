import { BAYS, BAY_ANGLES } from "@/lib/content";

/* Drawing RH-01: a railroad turntable in plan view. Generated geometry, so it renders
   on the server and stays sharp at any size. Interactive pages animate it with GSAP. */

const R_PIT = 150;
const R_IN = 215;
const R_OUT = 285;

const P = (deg: number, r: number): [number, number] => {
  const a = (deg * Math.PI) / 180;
  return [r * Math.sin(a), -r * Math.cos(a)];
};
const f = (n: number) => n.toFixed(2);
const sector = (a1: number, a2: number, r1: number, r2: number) => {
  const large = a2 - a1 > 180 ? 1 : 0;
  const [x1, y1] = P(a1, r2);
  const [x2, y2] = P(a2, r2);
  const [x3, y3] = P(a2, r1);
  const [x4, y4] = P(a1, r1);
  return `M${f(x1)} ${f(y1)}A${r2} ${r2} 0 ${large} 1 ${f(x2)} ${f(y2)}L${f(x3)} ${f(y3)}A${r1} ${r1} 0 ${large} 0 ${f(x4)} ${f(y4)}Z`;
};
const arc = (a1: number, a2: number, r: number) => {
  const [x1, y1] = P(a1, r);
  const [x2, y2] = P(a2, r);
  return `M${f(x1)} ${f(y1)}A${r} ${r} 0 1 1 ${f(x2)} ${f(y2)}`;
};

function Track({ from, to }: { from: number; to: number }) {
  return (
    <>
      <line className="tt-ties" x1="0" y1={-from} x2="0" y2={-to} />
      <line className="tt-railline" x1="-5" y1={-from} x2="-5" y2={-to} />
      <line className="tt-railline" x1="5" y1={-from} x2="5" y2={-to} />
    </>
  );
}

const DIVIDERS = Array.from({ length: 9 }, (_, k) => -140 + 35 * k).map((a) => {
  const [x1, y1] = P(a, R_IN);
  const [x2, y2] = P(a, R_OUT);
  return { x1: f(x1), y1: f(y1), x2: f(x2), y2: f(y2) };
});

type Props = {
  id: string;
  title: string;
  /** Index of the lit bay, or null for none. */
  active?: number | null;
  labels?: boolean;
  /** Initial bridge angle. Kept constant after the first render so GSAP can own the transform. */
  bridgeAngle?: number;
  locoY?: number;
  onBayClick?: (i: number) => void;
};

export function Turntable({ id, title, active = 3, labels = true, bridgeAngle = BAY_ANGLES[3], locoY = -168, onBayClick }: Props) {
  const bridgeLen = R_PIT - 3;
  return (
    <svg className="tt-svg" id={id} viewBox="-430 -345 860 755" role="img" aria-label={title}>
      <g className="tt-lead" transform="rotate(180)">
        <Track from={R_PIT + 2} to={420} />
      </g>
      <path className="tt-house" d={sector(-140, 140, R_IN, R_OUT)} />
      <path className="tt-houseline" d={arc(-140, 140, R_OUT - 12)} />
      {DIVIDERS.map((d, i) => (
        <line key={i} className="tt-div" {...d} />
      ))}
      {BAYS.map((b, i) => (
        <g
          key={b.name}
          className={`tt-bay${i === active ? " is-active" : ""}`}
          data-i={i}
          transform={`rotate(${BAY_ANGLES[i]})`}
          onClick={onBayClick ? () => onBayClick(i) : undefined}
        >
          <path className="tt-sector" d={sector(-17.5, 17.5, R_PIT + 4, R_OUT)} />
          <Track from={R_PIT + 2} to={R_OUT - 6} />
          <circle className="tt-baylamp" cx="13" cy={-(R_IN - 9)} r="5" />
        </g>
      ))}
      <circle className="tt-pit" r={R_PIT} />
      <circle className="tt-ring" r={R_PIT - 12} />
      <circle className="tt-ring" r={R_PIT - 18} />
      <circle className="tt-pitwall" r={R_PIT} />
      <g className="tt-packets" aria-hidden="true" />
      <g className="tt-bridge" transform={`rotate(${bridgeAngle})`}>
        <rect className="tt-deck" x="-17" y={-bridgeLen} width="34" height={bridgeLen * 2} rx="4" />
        <line className="tt-deckties" x1="0" y1={-bridgeLen + 4} x2="0" y2={bridgeLen - 4} />
        <line className="tt-deckrail" x1="-5" y1={-bridgeLen} x2="-5" y2={bridgeLen} />
        <line className="tt-deckrail" x1="5" y1={-bridgeLen} x2="5" y2={bridgeLen} />
        <circle className="tt-pivot" r="9" />
        <g className="tt-loco" transform={`translate(0 ${locoY})`}>
          <circle className="tt-loco-glow" cx="0" cy="-96" r="12" />
          <rect className="tt-loco-body" x="-13" y="-98" width="26" height="72" rx="6" />
          <rect className="tt-loco-cab" x="-13" y="-46" width="26" height="20" rx="3" />
          <rect className="tt-loco-body" x="-8" y="-80" width="16" height="4" rx="2" opacity=".6" />
          <circle className="tt-loco-lamp" cx="0" cy="-92" r="3.6" />
        </g>
      </g>
      {labels &&
        BAYS.map((b, i) => {
          const [x, y] = P(BAY_ANGLES[i], 312);
          const anchor = x < -24 ? "end" : x > 24 ? "start" : "middle";
          return (
            <text key={b.name} className={`tt-label${i === active ? " is-active" : ""}`} data-i={i} x={f(x)} y={f(y + 6)} textAnchor={anchor}>
              {b.name}
            </text>
          );
        })}
      {labels && (
        <>
          <text className="tt-lead-label" x="24" y="330">Work comes in here</text>
          <g className="tt-scale" transform="translate(-410 380)">
            <line className="tt-dim" x1="0" y1="0" x2="150" y2="0" />
            <line className="tt-dim" x1="0" y1="-6" x2="0" y2="6" />
            <line className="tt-dim" x1="75" y1="-4" x2="75" y2="4" />
            <line className="tt-dim" x1="150" y1="-6" x2="150" y2="6" />
            <text className="tt-dimtext" x="0" y="-12">0</text>
            <text className="tt-dimtext" x="150" y="-12" textAnchor="middle">50 ft</text>
          </g>
        </>
      )}
    </svg>
  );
}

export const turntableMath = { P, nearest: (from: number, to: number) => from + ((((to - from) % 360) + 540) % 360) - 180 };
