"use client";
import { useEffect, useRef, useState } from "react";
import { STORY } from "@/lib/content";
import { gsap, prefersReducedMotion, ScrollTrigger } from "@/lib/gsap";
import { Turntable } from "./Turntable";

const LEADS = 3;
const LEADS_ANGLE = -17.5;

/** About: the turntable stays in view while the four steps of a roundhouse scroll past,
    and the engine acts each one out. */
export function Story() {
  const wrap = useRef<HTMLDivElement>(null);
  const [step, setStep] = useState(0);
  const [lit, setLit] = useState(true);

  useEffect(() => {
    const root = wrap.current;
    const svg = root?.querySelector<SVGSVGElement>("#tt-story");
    if (!root || !svg || prefersReducedMotion()) return;
    const bridge = svg.querySelector<SVGGElement>(".tt-bridge")!;
    const loco = svg.querySelector<SVGGElement>(".tt-loco")!;
    bridge.removeAttribute("transform");
    loco.removeAttribute("transform");
    setLit(false);
    const ctx = gsap.context(() => {
      gsap.set(bridge, { rotation: 180, svgOrigin: "0 0" });
      gsap.set(loco, { y: -330 });
      const tl = gsap.timeline({ paused: true, defaults: { ease: "power2.inOut" } });
      tl.to(loco, { y: 62, duration: 1 }, 0) // roll onto the bridge
        .to(bridge, { rotation: 360 + LEADS_ANGLE, svgOrigin: "0 0", duration: 1 }, 1) // turn to the bay
        .to(loco, { y: -168, duration: 0.7 }, 2) // into the stall
        .to(svg.querySelector(".tt-loco-glow"), { scale: 2.2, opacity: 0.8, svgOrigin: "0 -96", duration: 0.3, yoyo: true, repeat: 1 }, 2.7)
        .to(loco, { y: 62, duration: 0.45 }, 3) // back onto the bridge
        .to(bridge, { rotation: 540, svgOrigin: "0 0", duration: 0.35 }, 3.45) // turn to the main line
        .to(loco, { y: -330, duration: 0.2 }, 3.8); // and away
      ScrollTrigger.create({
        trigger: root.querySelector(".story-steps"),
        start: "top 60%",
        end: "bottom 60%",
        scrub: 0.8,
        onUpdate: (self) => {
          const p = self.progress;
          tl.progress(p);
          setLit(p >= 0.45 && p < 0.95);
          setStep(Math.min(STORY.length - 1, Math.floor(p * STORY.length)));
        },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section className="section" style={{ paddingTop: "clamp(24px,4vw,48px)" }} aria-labelledby="story-title">
      <div className="wrap story" ref={wrap}>
        <figure className="tt-figure story-fig" style={{ margin: 0 }}>
          <div className="tt-stage">
            <Turntable id="tt-story" active={lit ? LEADS : null} title="A turntable taking an engine from the main line into a bay and back out." />
          </div>
          <figcaption className="tt-caption"><span>How a roundhouse turns an engine around</span><span>Drawing RH-02, rev D</span></figcaption>
        </figure>
        <div>
          <h2 className="sr-only" id="story-title">How a roundhouse works, and how we do</h2>
          <ol className="story-steps">
            {STORY.map(([h, rail, us], i) => (
              <li key={h} className={`story-step${i === step ? " is-on" : ""}`}>
                <span className="ss-n">{i + 1} of 4</span>
                <h3>{h}</h3>
                <p>{rail}</p>
                <p className="maps">{us}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
