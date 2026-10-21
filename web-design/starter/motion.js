// Progressive enhancement: the page is complete without this file.
// All motion runs only when the visitor has not asked for reduced motion.
(() => {
  if (!window.gsap || !window.ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);

  const mm = gsap.matchMedia();
  mm.add("(prefers-reduced-motion: no-preference)", () => {
    // Hero: staggered entrance.
    gsap.from(".hero .reveal", { y: 24, autoAlpha: 0, duration: 0.7, ease: "power3.out", stagger: 0.08 });

    // Trend line draws itself, like a recorder pen.
    const pv = document.querySelector(".trend .pv");
    if (pv) {
      const len = pv.getTotalLength();
      gsap.fromTo(pv, { strokeDasharray: len, strokeDashoffset: len },
        { strokeDashoffset: 0, duration: 2.2, ease: "power1.inOut", delay: 0.4 });
    }

    // Everything below the fold reveals once on scroll.
    gsap.utils.toArray("main > section:not(.hero) .reveal, main > section.reveal").forEach((el) => {
      gsap.from(el, { y: 24, autoAlpha: 0, duration: 0.6, ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 88%", once: true } });
    });

    // Stat counters tick up to their value.
    document.querySelectorAll("[data-count]").forEach((el) => {
      const end = Number(el.dataset.count);
      const state = { v: 0 };
      gsap.to(state, { v: end, duration: 1.4, ease: "power2.out",
        onUpdate: () => { el.textContent = Math.round(state.v).toLocaleString("en-US"); },
        scrollTrigger: { trigger: el, start: "top 90%", once: true } });
    });
  });
})();
