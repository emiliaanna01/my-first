/* Round House film helpers: camera-space measurement, cursor moves and clicks. Deterministic, no clocks. */
window.RH = (function () {
  // Layout offset of el inside anc (ignores transforms, so measure once at build time).
  function off(el, anc) {
    var x = 0, y = 0, e = el;
    while (e && e !== anc) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; }
    return { x: x, y: y };
  }
  // A point on el (fractions of its box) in the camera's own space.
  function pt(el, cam, fx, fy) {
    var o = off(el, cam);
    return { x: o.x + el.offsetWidth * (fx == null ? 0.5 : fx), y: o.y + el.offsetHeight * (fy == null ? 0.5 : fy) };
  }
  // Camera state {s,x,y} (transform-origin 0 0) that puts camera point p at frame point (fx, fy).
  function aim(p, s, fx, fy) {
    return { s: s, x: (fx == null ? 960 : fx) - p.x * s, y: (fy == null ? 540 : fy) - p.y * s };
  }
  // Where camera point p shows on the frame for camera state c.
  function frame(p, c) { return { x: c.x + p.x * c.s, y: c.y + p.y * c.s }; }
  function cam(tl, el, c, t, d, ease) {
    if (d === 0) { tl.set(el, { scale: c.s, x: c.x, y: c.y }, t); return; }
    tl.to(el, { scale: c.s, x: c.x, y: c.y, duration: d, ease: ease || "power2.inOut" }, t);
  }
  // Cursor travel with a little motion blur at its fastest frame.
  function move(tl, cur, to, t, d) {
    d = d || 0.7;
    tl.to(cur, { x: to.x, y: to.y, duration: d, ease: "power3.inOut" }, t);
    tl.fromTo(cur, { filter: "blur(0px)" }, { filter: "blur(1.6px)", duration: d / 2, ease: "power2.in" }, t);
    tl.to(cur, { filter: "blur(0px)", duration: d / 2, ease: "power2.out" }, t + d / 2);
  }
  // Click: the cursor squashes for 3 frames and rebounds; the target presses on the same frame.
  function click(tl, cur, t, target) {
    tl.to(cur, { scale: 0.82, duration: 0.1, ease: "power2.out" }, t);
    tl.to(cur, { scale: 1, duration: 0.25, ease: "back.out(2.2)" }, t + 0.1);
    if (target) {
      tl.to(target, { scale: 0.95, duration: 0.1, ease: "power2.out" }, t);
      tl.to(target, { scale: 1, duration: 0.3, ease: "back.out(2.2)" }, t + 0.1);
    }
  }
  // Wrap each word of el's text in <span class="rh-w"> (keeps child elements such as <em>).
  function words(el) {
    var out = [];
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var parts = n.textContent.split(/(\s+)/);
          var frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(p)); return; }
            var s = document.createElement("span"); s.className = "rh-w"; s.textContent = p;
            frag.appendChild(s); out.push(s);
          });
          node.replaceChild(frag, n);
        } else if (n.nodeType === 1 && n.tagName !== "SVG" && n.tagName !== "svg") { walk(n); }
      });
    })(el);
    return out;
  }
  function letters(el) {
    var t = el.textContent, out = [];
    el.textContent = "";
    t.split("").forEach(function (ch) {
      var s = document.createElement("span"); s.className = "rh-l"; s.textContent = ch === " " ? "\u00a0" : ch;
      el.appendChild(s); out.push(s);
    });
    return out;
  }
  // Scenes that start later are display:none while their timeline is built; lay them out to measure.
  function unhide(el) {
    var touched = [];
    for (var e = el; e && e !== document.documentElement; e = e.parentElement) {
      if (getComputedStyle(e).display === "none") {
        touched.push([e, e.style.getPropertyValue("display"), e.style.getPropertyPriority("display")]);
        e.style.setProperty("display", "block", "important");
      }
    }
    return function () {
      touched.forEach(function (t) {
        if (t[1]) t[0].style.setProperty("display", t[1], t[2]); else t[0].style.removeProperty("display");
      });
    };
  }
  // Text and class state that must be a pure function of time: called on every seek with the scene time.
  function drive(tl, dur, fn) {
    var o = { t: 0 };
    tl.fromTo(o, { t: 0 }, { t: dur, duration: dur, ease: "none", onUpdate: function () { fn(o.t); } }, 0);
    fn(0);
  }
  return { drive: drive, unhide: unhide, off: off, pt: pt, aim: aim, frame: frame, cam: cam, move: move, click: click, words: words, letters: letters };
})();
