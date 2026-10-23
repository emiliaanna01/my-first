#!/usr/bin/env python3
"""Round House "how a project moves" film, in the style of a product walkthrough (inflight-like):
a real prototype, feedback pinned on it, an agent turning it into next steps, v2.
Generates compositions/*.html and index.html. UI pieces come from the site's own DOM (../dom)."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILM = HERE.parent
DOM = FILM.parent / "dom"
OUT = FILM / "compositions"

FONTS = """
@font-face{font-family:"DM Sans";font-weight:400;src:url("assets/fonts/DMSans-400-normal.woff2")}
@font-face{font-family:"DM Sans";font-weight:500;src:url("assets/fonts/DMSans-500-normal.woff2")}
@font-face{font-family:"Inter Tight Variable";font-weight:100 900;src:url("assets/fonts/InterTightVariable-100-900-normal.woff2")}
"""
CURSOR = """<div id="{id}" class="rh-cur" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 3 L5 19 L9 15 L12 22 L15 20.5 L11.5 14 L18 14 Z"/></svg>{tag}</div>"""


def cursor(cid, name=None):
    return CURSOR.format(id=cid, tag=f'<span class="rh-tag" data-layout-allow-occlusion data-layout-allow-overlap>{name}</span>' if name else "")


def dom(name):
    return (DOM / f"{name}.html").read_text()


def clean(html):
    html = re.sub(r' style="translate: none; rotate: none; scale: none;[^"]*"', "", html)
    return re.sub(r' style="--panel-index[^"]*"', "", html)


def scene(cid, css, body, js):
    return f"""<template>
  <style>
{FONTS}
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080">
    <i id="{cid}-anchor" style="position:absolute;width:0;height:0"></i>
{body}
  </div>
  <script>
(function () {{
  var tl = gsap.timeline({{ paused: true }});
  var $ = function (id) {{ return document.getElementById(id); }};
  document.fonts.ready.then(function () {{
    var restore = RH.unhide(document.getElementById("{cid}-anchor"));
{js}
    restore();
    window.__timelines["{cid}"] = tl;
  }});
}})();
  </script>
</template>
"""


TITLE = """
    .rh-title { position: absolute; left: 140px; margin: 0; font-family: "Inter Tight Variable", sans-serif;
      font-weight: 550; font-size: 120px; line-height: 1.02; letter-spacing: -0.055em; white-space: nowrap; }
"""

# The prototype: the site's own illustrative "customer journey" browser, inside its showcase panel.
PROTO = clean(dom("show0"))
PROTO_CSS = """
    .proto-cam .showcase-copy { visibility: hidden; }
    .proto-cam .showcase-panel { transform: none !important; background: transparent !important; box-shadow: none !important; border: 0 !important; }
    .proto-cam .case-art { background: transparent !important; }
    .proto-cam .product-browser, .proto-cam .lead-browser { transform: none !important; rotate: none !important; }
    .rh-ver { position: absolute; z-index: 5; font-family: "DM Sans", sans-serif; font-weight: 500; font-size: 15px;
      color: #1d221e; background: #e0ed9b; border-radius: 999px; padding: 6px 13px; letter-spacing: 0.02em; }
    .rh-chip { position: absolute; z-index: 6; font-family: "DM Sans", sans-serif; font-weight: 500; font-size: 11px;
      color: #1d221e; background: #e0ed9b; border-radius: 999px; padding: 4px 9px; white-space: nowrap; }
    .rh-pin { position: absolute; z-index: 8; width: 30px; height: 30px; margin: -30px 0 0 0; border-radius: 15px 15px 15px 3px;
      background: #1d221e; color: #e0ed9b; font: 500 13px/30px "DM Sans", sans-serif; text-align: center;
      box-shadow: 0 6px 14px rgba(20,24,18,.25); }
    .rh-pin.done { background: #e0ed9b; color: #1d221e; }
    .rh-bubble { position: absolute; z-index: 9; width: 250px; background: #fff; border-radius: 14px; padding: 12px 14px;
      box-shadow: 0 14px 30px rgba(20,24,18,.16), 0 0 0 1px rgba(29,34,30,.06); font-family: "DM Sans", sans-serif; }
    .rh-bubble b { display: block; font-weight: 500; font-size: 12px; color: #1d221e; }
    .rh-bubble b small { font-weight: 400; color: #8a8f82; margin-left: 6px; }
    .rh-bubble p { margin: 5px 0 0; font-size: 13px; line-height: 1.4; color: #2b322b; white-space: nowrap; }
"""


def proto_measure(cam="cam"):
    # shared measuring for the scenes that show the prototype
    return f"""
    var cam = $("{{p}}-{cam}"), browser = cam.querySelector(".product-browser");
    var steps = Array.prototype.slice.call(cam.querySelectorAll(".pipeline > div"));
    var bw = browser.offsetWidth, sB = Math.min(1.9, 1500 / bw);
    var full = RH.aim(RH.pt(browser, cam), sB, 960, 560);
    function place(el, target, fx, fy, dx, dy) {{
      var p = RH.pt(target, cam, fx, fy); el.style.left = (p.x + (dx || 0)) + "px"; el.style.top = (p.y + (dy || 0)) + "px";
    }}
"""

# ---------------------------------------------------------------- 1 hook: the inquiry nobody answers
s1_body = """    <div id="s1-ground" class="rh-ground" style="background:#1d221e"></div>
    <div id="s1-clock" class="s1-clock"><span id="s1-t1">11:48 PM</span><span id="s1-t2">8:30 AM</span></div>
    <p id="s1-cap" class="s1-cap">Your website, tonight.</p>
    <div id="s1-stack">
      <div class="s1-card s1-back" id="s1-c3"></div>
      <div class="s1-card s1-back" id="s1-c2"></div>
      <div class="s1-card" id="s1-c1">
        <div class="s1-row"><i>W</i><div><b>New inquiry</b><small>Website form</small></div><span id="s1-time">11:48 PM</span></div>
        <p>&#8220;Hi, do you have availability next week?&#8221;</p>
        <div class="s1-foot"><span id="s1-unread">Unread</span><span id="s1-waiting">No reply &#183; 9h</span></div>
      </div>
    </div>
"""
s1_css = """
    .s1-clock { position: absolute; left: 140px; top: 330px; height: 230px; overflow: hidden; font-family: "Inter Tight Variable", sans-serif;
      font-weight: 550; font-size: 200px; letter-spacing: -0.06em; line-height: 230px; color: #f3f5ea; }
    .s1-clock span { display: block; white-space: nowrap; }
    .s1-cap { position: absolute; left: 146px; top: 580px; margin: 0; font: 400 34px "DM Sans", sans-serif; color: #a9b78f; }
    #s1-stack { position: absolute; left: 1080px; top: 330px; width: 640px; height: 330px; }
    .s1-card { position: absolute; left: 0; top: 0; width: 640px; background: #f7f7f2; border-radius: 26px; padding: 30px 34px;
      box-shadow: 0 30px 60px rgba(0,0,0,.35); font-family: "DM Sans", sans-serif; color: #1d221e; box-sizing: border-box; }
    .s1-back { height: 250px; background: #e5e7dc; }
    .s1-row { display: flex; align-items: center; gap: 18px; }
    .s1-row i { width: 58px; height: 58px; border-radius: 50%; background: #e0ed9b; font: 500 26px/58px "DM Sans"; text-align: center; font-style: normal; }
    .s1-row b { display: block; font-weight: 500; font-size: 28px; }
    .s1-row small { font-size: 20px; color: #6b7064; }
    .s1-row span { margin-left: auto; font-size: 20px; color: #6b7064; }
    .s1-card p { margin: 22px 0 0; font-size: 30px; line-height: 1.35; }
    .s1-foot { display: flex; gap: 12px; margin-top: 24px; }
    .s1-foot span { font-size: 18px; font-weight: 500; padding: 7px 14px; border-radius: 999px; background: #1d221e; color: #f7f7f2; }
    #s1-waiting { background: #ec644f; color: #fff; }
"""
s1_js = """
    var t1 = $("s1-t1"), t2 = $("s1-t2");
    tl.fromTo($("s1-c1"), { y: -24 }, { y: 0, duration: 0.6, ease: "expo.out" }, 0);
    tl.fromTo($("s1-cap"), { opacity: 0 }, { opacity: 1, duration: 0.4 }, 0.5);
    tl.set($("s1-waiting"), { scale: 0, opacity: 0 }, 0);
    // the night passes: the clock rolls like a counter
    tl.to([t1, t2], { yPercent: -100, duration: 0.45, ease: "power3.inOut" }, 2.6);
    tl.to($("s1-time"), { opacity: 0.5, duration: 0.2 }, 2.6);
    tl.to($("s1-cap"), { opacity: 0, duration: 0.15 }, 2.55);
    tl.call(function () {}, null, 2.7);
    tl.to($("s1-waiting"), { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.2)" }, 3.15);
    // more inquiries pile up behind it
    tl.fromTo($("s1-c2"), { y: 0, x: 0, opacity: 0 }, { y: 26, x: 18, opacity: 1, duration: 0.45, ease: "back.out(1.8)" }, 3.7);
    tl.fromTo($("s1-c3"), { y: 0, x: 0, opacity: 0 }, { y: 50, x: 36, opacity: 1, duration: 0.45, ease: "back.out(1.8)" }, 4.0);
    tl.fromTo($("s1-stack"), { rotation: 0 }, { rotation: -1.5, duration: 0.4, ease: "power2.out" }, 3.7);
    // morning becomes the studio's world: the card lifts away and paper floods in
    tl.to([$("s1-clock")], { opacity: 0, filter: "blur(10px)", duration: 0.22, ease: "power2.in" }, 6.25);
    tl.to($("s1-stack"), { scale: 1.5, opacity: 0, filter: "blur(10px)", duration: 0.5, ease: "power3.in" }, 6.3);
    tl.fromTo($("s1-ground"), { backgroundColor: "#1d221e" }, { backgroundColor: "#e1e8cd", duration: 0.4, ease: "power2.inOut" }, 6.55);
"""

# ---------------------------------------------------------------- 2 the prototype: wordmark, then the real journey card
s2_body = f"""    <div class="rh-ground" style="background:#e1e8cd"></div>
    <div id="s2-cam" class="rh-cam proto-cam"><div class="rh-page"><main>{PROTO}</main></div>
      <span id="s2-ver" class="rh-ver">prototype &#183; v1</span>
    </div>
    <div id="s2-lock" class="s2-lock"><span id="s2-wm">roundhouse<span id="s2-stop">.</span></span><i id="s2-dot"></i></div>
    {cursor("s2-cur")}
"""
s2_css = PROTO_CSS + """
    .s2-lock { position: absolute; left: 0; right: 0; top: 400px; text-align: center; font-family: "Inter Tight Variable", sans-serif;
      font-weight: 720; font-size: 190px; letter-spacing: -0.055em; color: #1d221e; line-height: 1; }
    #s2-wm { position: relative; display: inline-block; }
    #s2-stop { visibility: hidden; }
    #s2-dot { position: absolute; border-radius: 50%; background: #e0ed9b; box-shadow: inset 0 0 0 5px #6a813e; }
"""
s2_js = (proto_measure().replace("{p}", "s2")) + """
    var lock = $("s2-lock"), wm = $("s2-wm"), stop = $("s2-stop"), dot = $("s2-dot");
    var so = RH.off(stop, lock), d = stop.offsetWidth * 0.8;
    dot.style.width = d + "px"; dot.style.height = d + "px";
    dot.style.left = (so.x + stop.offsetWidth * 0.5 - d / 2) + "px"; dot.style.top = (so.y + stop.offsetHeight * 0.79 - d) + "px";
    place($("s2-ver"), browser, 0, 0, 14, -46);
    // the studio introduces itself: wordmark wipes in, the lime full stop drops
    tl.fromTo(wm, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "power3.out" }, 0.35);
    tl.fromTo(dot, { y: -700 }, { y: 0, duration: 0.36, ease: "power3.in" }, 0.55);
    tl.to(dot, { scaleX: 1.25, scaleY: 0.72, duration: 0.07, transformOrigin: "50% 100%" }, 0.91);
    tl.to(dot, { scaleX: 1, scaleY: 1, duration: 0.4, ease: "back.out(3)" }, 0.98);
    // the dot becomes the prototype's world: lockup lifts away, the browser rises in
    tl.to(lock, { y: -260, opacity: 0, filter: "blur(10px)", duration: 0.45, ease: "power3.in" }, 2.3);
    var rise = { s: full.s, x: full.x, y: full.y + 520 };
    RH.cam(tl, cam, rise, 0, 0);
    tl.set(cam, { opacity: 0 }, 0);
    tl.to(cam, { opacity: 1, duration: 0.3 }, 2.5);
    RH.cam(tl, cam, full, 2.5, 1.0, "expo.out");
    tl.fromTo($("s2-ver"), { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.2)" }, 3.4);
    // the journey runs: push in, each step lights up as it is named
    var pipe = cam.querySelector(".pipeline"), tags = cam.querySelectorAll(".pipeline-tag");
    var push = RH.aim(RH.pt(pipe, cam), Math.min(3.2, 1650 / pipe.offsetWidth), 960, 600);
    RH.cam(tl, cam, push, 6.5, 0.8);
    tl.set(steps, { opacity: 0.35 }, 0);
    tl.set(tags, { scale: 0.6, opacity: 0 }, 0);
    [7.3, 8.35, 9.5].forEach(function (t, k) {
      tl.to(steps[k], { opacity: 1, duration: 0.2 }, t);
      tl.fromTo(steps[k], { y: 10 }, { y: 0, duration: 0.45, ease: "back.out(2)" }, t);
      tl.to(tags[k], { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.4)" }, t + 0.12);
    });
    tl.set(cur, { x: 2010, y: 1150, opacity: 1 }, 0);
    var cur = $("s2-cur");
    tl.set(cur, { x: 2010, y: 1150, opacity: 1 }, 0);
    [7.1, 8.15, 9.3].forEach(function (t, k) {
      var p = RH.frame(RH.pt(steps[k], cam, 0.75, 0.75), push);
      RH.move(tl, cur, p, t - 0.55, 0.55);
    });
    tl.to(cur, { x: 1980, y: 1200, duration: 0.6, ease: "power3.in" }, 12.0);
    RH.cam(tl, cam, full, 12.6, 0.9);
"""
# cursor variable must exist before first use: rewrite the stray early set
s2_js = s2_js.replace('    tl.set(cur, { x: 2010, y: 1150, opacity: 1 }, 0);\n    var cur = $("s2-cur");', '    var cur = $("s2-cur");')

# ---------------------------------------------------------------- 3 review: pin a comment, record a walkthrough, thread syncs
s3_body = f"""    <div class="rh-ground" style="background:#e1e8cd"></div>
    <div id="s3-cam" class="rh-cam proto-cam"><div class="rh-page"><main>{PROTO}</main></div>
      <span id="s3-ver" class="rh-ver">prototype &#183; v1</span>
      <span id="s3-pin1" class="rh-pin">M</span>
      <div id="s3-b1" class="rh-bubble" data-layout-allow-occlusion><b>Maya<small>just now</small></b><p id="s3-b1t">Can we flag repeat customers here?</p></div>
      <span id="s3-pin2" class="rh-pin">M</span>
      <div id="s3-vid" class="s3-vid" data-layout-allow-occlusion><i>M</i><div class="s3-wave">{"".join(f'<b style="--h:{h}"></b>' for h in [8,14,22,12,26,18,10,24,16,28,12,20,9,17,25,13])}</div><span id="s3-rec">0:07</span></div>
    </div>
    <div id="s3-bar" class="s3-bar">
      <span id="s3-bc" class="s3-btn"><svg viewBox="0 0 24 24"><path d="M5 5h14v10H10l-5 4z"/></svg>Comment</span>
      <span id="s3-br" class="s3-btn"><i class="s3-dot"></i>Record</span>
      <span id="s3-bn" class="s3-btn">Next steps<em>3</em></span>
    </div>
    <div id="s3-thread" class="s3-thread" data-layout-allow-occlusion>
      <div class="s3-head"># lead-flow-review<small>synced</small></div>
      <div class="s3-msg" id="s3-m1"><i>M</i><div><b>Maya <small>11:02</small></b><p>Can we flag repeat customers here?</p><span>&#8599; Qualified lead &#183; v1</span></div></div>
      <div class="s3-msg" id="s3-m2"><i>M</i><div><b>Maya <small>11:03</small></b><p class="s3-play">&#9654; Walkthrough &#183; 0:24</p></div></div>
      <div class="s3-msg" id="s3-m3"><i class="s">S</i><div><b>Sam <small>11:05</small></b><p>Yes, and send a text reply after hours.</p></div></div>
    </div>
    {cursor("s3-cur", "Maya &#183; Ops")}
"""
s3_css = PROTO_CSS + """
    .s3-bar { position: absolute; left: 0; right: 0; margin: 0 auto; width: fit-content; bottom: 46px; display: flex; gap: 6px; padding: 8px;
      background: #1d221e; border-radius: 999px; box-shadow: 0 18px 40px rgba(20,24,18,.28); z-index: 20; }
    .s3-btn { display: flex; align-items: center; gap: 10px; padding: 14px 24px; border-radius: 999px; color: #f3f5ea;
      font: 500 24px "DM Sans", sans-serif; white-space: nowrap; }
    .s3-btn svg { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linejoin: round; }
    .s3-dot { width: 14px; height: 14px; border-radius: 50%; background: #ec644f; }
    .s3-btn em { font-style: normal; font-size: 16px; background: #e0ed9b; color: #1d221e; border-radius: 999px; padding: 2px 9px; }
    .s3-vid { position: absolute; z-index: 9; display: flex; align-items: center; gap: 10px; padding: 8px 14px 8px 8px; background: #1d221e;
      border-radius: 999px; box-shadow: 0 12px 26px rgba(20,24,18,.25); }
    .s3-vid > i { width: 34px; height: 34px; border-radius: 50%; background: #e0ed9b; color: #1d221e; font: 500 15px/34px "DM Sans"; text-align: center; font-style: normal; }
    .s3-wave { display: flex; align-items: center; gap: 3px; height: 30px; }
    .s3-wave b { width: 3px; height: calc(var(--h) * 1px); background: #e0ed9b; border-radius: 2px; }
    #s3-rec { font: 500 14px "DM Sans", sans-serif; color: #f3f5ea; }
    .s3-thread { position: absolute; right: 70px; top: 120px; width: 560px; background: #fff; border-radius: 24px; padding: 26px 28px 10px;
      box-shadow: 0 30px 60px rgba(20,24,18,.14), 0 0 0 1px rgba(29,34,30,.06); font-family: "DM Sans", sans-serif; z-index: 15; }
    .s3-head { font: 500 26px "DM Sans", sans-serif; color: #1d221e; padding-bottom: 18px; border-bottom: 1px solid #e6e7e0; }
    .s3-head small { float: right; font-size: 16px; color: #6a813e; background: #eef3d6; padding: 5px 12px; border-radius: 999px; }
    .s3-msg { display: flex; gap: 16px; padding: 20px 0; border-bottom: 1px solid #f0f1ea; }
    .s3-msg > i { flex: none; width: 46px; height: 46px; border-radius: 12px; background: #e0ed9b; font: 500 20px/46px "DM Sans"; text-align: center; font-style: normal; color: #1d221e; }
    .s3-msg > i.s { background: #cfd8c2; }
    .s3-msg b { font-weight: 500; font-size: 22px; color: #1d221e; }
    .s3-msg b small { font-weight: 400; font-size: 17px; color: #8a8f82; margin-left: 6px; }
    .s3-msg p { margin: 6px 0 0; font-size: 22px; line-height: 1.35; color: #2b322b; }
    .s3-msg span { display: inline-block; margin-top: 8px; font-size: 16px; color: #6a813e; }
    .s3-play { display: inline-block; background: #1d221e; color: #f3f5ea !important; padding: 8px 14px; border-radius: 10px; font-size: 19px !important; }
"""
s3_js = (proto_measure().replace("{p}", "s3")) + """
    var cur = $("s3-cur"), pin1 = $("s3-pin1"), b1 = $("s3-b1"), pin2 = $("s3-pin2"), vid = $("s3-vid");
    place($("s3-ver"), browser, 0, 0, 14, -46);
    place(pin1, steps[1], 0.92, 0.12);
    place(b1, steps[1], 0.92, 0, 26, -86);
    place(pin2, steps[2], 0.92, 0.12);
    place(vid, steps[2], 0.05, 1.0, 0, 14);
    RH.cam(tl, cam, full, 0, 0);
    tl.set([pin1, pin2], { scale: 0, transformOrigin: "0% 100%" }, 0);
    tl.set([b1, vid], { opacity: 0, scale: 0.6, transformOrigin: "0% 0%" }, 0);
    // the review toolbar arrives on the prototype
    var tb = function (id, fx) { var r = $(id).getBoundingClientRect(), root = $("s3-anchor").parentElement.getBoundingClientRect();
      var k = 1920 / root.width; return { x: (r.left - root.left) * k + r.width * k * (fx || 0.5), y: (r.top - root.top) * k + r.height * k * 0.55 }; };
    var bc = tb("s3-bc", 0.35), br = tb("s3-br", 0.35), bn = tb("s3-bn", 0.35);
    tl.fromTo($("s3-bar"), { y: 140, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "expo.out" }, 0.4);
    // Maya picks Comment, pins the qualified step, types her note
    tl.set(cur, { x: 2000, y: 1160, opacity: 1 }, 0);
    RH.move(tl, cur, bc, 1.0, 0.7);
    RH.click(tl, cur, 1.8, $("s3-bc"));
    tl.to($("s3-bc"), { backgroundColor: "#e0ed9b", color: "#1d221e", duration: 0.15 }, 1.82);
    var p1 = RH.frame(RH.pt(steps[1], cam, 0.92, 0.12), full);
    RH.move(tl, cur, { x: p1.x + 4, y: p1.y + 4 }, 2.05, 0.7);
    RH.click(tl, cur, 2.9);
    tl.to(pin1, { scale: 1, duration: 0.4, ease: "back.out(2.6)" }, 2.92);
    tl.to(b1, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.8)" }, 3.05);
    var txt = $("s3-b1t"), full1 = txt.textContent, rec = $("s3-rec");
    RH.drive(tl, 14, function (T) {
      txt.textContent = full1.slice(0, Math.max(0, Math.min(full1.length, Math.round((T - 3.2) / 1.2 * full1.length))));
      var s = Math.max(0, Math.min(24, Math.round((T - 6.5) / 1.8 * 24)));
      rec.textContent = "0:" + (s < 10 ? "0" : "") + s;
    });
    tl.to($("s3-bc"), { backgroundColor: "rgba(224,237,155,0)", color: "#f3f5ea", duration: 0.2 }, 4.6);
    // a quick walkthrough: Record, the waveform runs, the clip pins to the booking step
    RH.move(tl, cur, br, 5.4, 0.7);
    RH.click(tl, cur, 6.3, $("s3-br"));
    tl.to(vid, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }, 6.4);
    var bars = vid.querySelectorAll(".s3-wave b");
    bars.forEach(function (b, i) {
      tl.fromTo(b, { scaleY: 0.3 }, { scaleY: 1.25, duration: 0.18 + (i % 4) * 0.05, ease: "sine.inOut", yoyo: true, repeat: 7 }, 6.5 + i * 0.03);
    });
    tl.to(pin2, { scale: 1, duration: 0.4, ease: "back.out(2.6)" }, 8.4);
    // the notes sync into the team's thread
    var shrink = RH.aim(RH.pt(browser, cam), full.s * 0.74, 640, 560);
    RH.cam(tl, cam, shrink, 8.6, 0.8);
    tl.fromTo($("s3-thread"), { x: 640, opacity: 0 }, { x: 0, opacity: 1, duration: 0.8, ease: "expo.out" }, 8.7);
    [["s3-m1", 9.4], ["s3-m2", 10.0], ["s3-m3", 10.9]].forEach(function (m) {
      tl.fromTo($(m[0]), { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.4, ease: "back.out(1.8)" }, m[1]);
    });
    tl.fromTo($("s3-bn").querySelector("em"), { scale: 1 }, { scale: 1.35, duration: 0.15, yoyo: true, repeat: 1 }, 11.2);
    // Next steps: the button becomes the agent's world
    RH.move(tl, cur, bn, 12.0, 0.7);
    RH.click(tl, cur, 12.95, $("s3-bn"));
    tl.to(cur, { opacity: 0, duration: 0.1 }, 13.15);
    tl.fromTo($("s3-iris"), { clipPath: "circle(0px at " + bn.x + "px " + bn.y + "px)" },
      { clipPath: "circle(2300px at " + bn.x + "px " + bn.y + "px)", duration: 0.55, ease: "power3.in" }, 13.1);
"""
s3_body += '    <div id="s3-iris" class="rh-ground" style="background:#20271f;z-index:40"></div>\n'

# ---------------------------------------------------------------- 4 agent: next steps, approval, v2
TERM_LINES = [
    ("t1", "prompt", "&#8250; Pull the review notes and build v2"),
    ("t2", "tool", "&#9210; roundhouse &#183; get_feedback"),
    ("t3", "sub", "&#9151; 3 next steps on lead-flow v1"),
    ("t4", "step", "Flag repeat customers at the qualify step"),
    ("t5", "step", "Send a text reply to after-hours inquiries"),
    ("t6", "step", "Book straight into the team calendar"),
    ("t7", "work", "&#10043; Working&#8230;"),
    ("t8", "ask", "Approve changes to lead-flow?"),
    ("t9", "done", "&#10003; v2 is ready for review &#183; lead-flow/v2 &#8599;"),
]
term = "".join(
    (f'<div class="tl {k}" id="s4-{i}"><span class="box" id="s4-{i}b"></span><span>{t}</span></div>' if k == "step"
     else f'<div class="tl {k}" id="s4-{i}"><span id="s4-{i}t">{t}</span></div>') for i, k, t in TERM_LINES)
s4_body = f"""    <div class="rh-ground" style="background:#20271f"></div>
    <div id="s4-win" class="s4-win">
      <div class="s4-top"><span><i></i><i></i><i></i></span>agent &#8212; ~/lead-flow</div>
      <div class="s4-body">{term}
        <div class="s4-ok" id="s4-ok"><span id="s4-yes">Yes, ship v2 for review</span><span class="no">Not yet</span></div>
      </div>
    </div>
    <p id="s4-note" class="s4-note">Human judgment stays in the loop.</p>
    {cursor("s4-cur", "Round House")}
"""
s4_css = """
    .s4-win { position: absolute; left: 230px; top: 110px; width: 1460px; height: 760px; background: #151a14; border-radius: 26px;
      box-shadow: 0 40px 80px rgba(0,0,0,.45), 0 0 0 1px rgba(224,237,155,.08); overflow: hidden; }
    .s4-top { height: 64px; display: flex; align-items: center; gap: 22px; padding: 0 26px; color: #8f9a85;
      font: 400 22px "JetBrains Mono", monospace; border-bottom: 1px solid #262d24; }
    .s4-top span { display: flex; gap: 9px; } .s4-top i { width: 14px; height: 14px; border-radius: 50%; background: #3a4337; }
    .s4-body { padding: 34px 44px; font: 400 30px/1.55 "JetBrains Mono", monospace; color: #d9dfcf; }
    .tl { white-space: nowrap; }
    .tl.prompt { color: #f3f5ea; margin-bottom: 16px; }
    .tl.tool { color: #e0ed9b; } .tl.sub { color: #8f9a85; padding-left: 26px; margin-bottom: 8px; }
    .tl.step { padding-left: 52px; display: flex; align-items: center; gap: 18px; }
    .tl .box { width: 24px; height: 24px; border: 2px solid #8f9a85; border-radius: 6px; flex: none; position: relative; }
    .tl .box.on { background: #e0ed9b; border-color: #e0ed9b; }
    .tl.work { color: #e0ed9b; margin-top: 16px; } .tl.ask { color: #f3f5ea; margin-top: 18px; }
    .tl.done { color: #e0ed9b; margin-top: 18px; }
    .s4-ok { display: flex; gap: 14px; margin: 14px 0 0 0; }
    .s4-ok span { font: 500 24px "DM Sans", sans-serif; padding: 12px 22px; border-radius: 12px; background: #e0ed9b; color: #1d221e; }
    .s4-ok .no { background: #262d24; color: #8f9a85; }
    .s4-note { position: absolute; left: 0; right: 0; bottom: 70px; margin: 0; text-align: center; font: 550 44px "Inter Tight Variable", sans-serif;
      letter-spacing: -0.03em; color: #a9b78f; }
"""
s4_js = """
    var cur = $("s4-cur");
    tl.fromTo($("s4-win"), { scale: 0.92, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: "expo.out" }, 0.05);
    var lines = ["t1","t2","t3","t4","t5","t6","t7","t8","t9"].map(function (k) { return $("s4-" + k); });
    tl.set(lines, { opacity: 0 }, 0);
    tl.set([$("s4-ok"), $("s4-note")], { opacity: 0 }, 0);
    // the request types out, then the tool call answers
    var p = $("s4-t1t"), ptxt = p.textContent;
    tl.set(lines[0], { opacity: 1 }, 0.35);
    [[1, 1.75], [2, 2.05], [3, 2.6], [4, 2.85], [5, 3.1], [6, 4.0]].forEach(function (l) {
      tl.fromTo(lines[l[0]], { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.25, ease: "power3.out" }, l[1]);
    });
    // the working line cycles its glyph, the steps tick off one by one
    var w = $("s4-t7t"), glyphs = ["\u273B", "\u273D", "\u2733", "\u273B"], boxes = [["s4-t4b", 4.6], ["s4-t5b", 5.4], ["s4-t6b", 6.2]];
    RH.drive(tl, 12, function (T) {
      p.textContent = ptxt.slice(0, Math.max(0, Math.min(ptxt.length, Math.round((T - 0.35) / 1.1 * ptxt.length))));
      w.textContent = T >= 7.0 ? "\u2713 3 of 3 done" : glyphs[Math.max(0, Math.floor((T - 4.0) / 0.3)) % 4] + " Working\u2026";
      boxes.forEach(function (b) { $(b[0]).classList.toggle("on", T >= b[1]); });
    });
    boxes.forEach(function (b) { tl.fromTo($(b[0]), { scale: 0.6 }, { scale: 1, duration: 0.35, ease: "back.out(3)" }, b[1]); });
    // a person approves before anything ships
    tl.fromTo(lines[7], { opacity: 0 }, { opacity: 1, duration: 0.25 }, 7.4);
    tl.fromTo($("s4-ok"), { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.35, ease: "back.out(1.8)" }, 7.6);
    tl.fromTo($("s4-note"), { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "expo.out" }, 6.8);
    var yes = $("s4-yes"), root = $("s4-anchor").parentElement;
    var yp = RH.pt(yes, root, 0.4, 0.55);
    tl.set(cur, { x: 2000, y: 1160, opacity: 1 }, 0);
    RH.move(tl, cur, yp, 8.2, 0.8);
    RH.click(tl, cur, 9.2, yes);
    tl.fromTo(lines[8], { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }, 9.5);
    tl.to(cur, { x: 2000, y: 1250, duration: 0.5, ease: "power3.in" }, 10.2);
    // zoom through the link into v2
    var lp = RH.pt(lines[8], root, 0.5, 0.5);
    tl.to($("s4-win"), { scale: 3.2, transformOrigin: lp.x - 230 + "px " + (lp.y - 110) + "px", opacity: 0, filter: "blur(6px)",
      duration: 0.6, ease: "power3.in" }, 11.35);
    tl.to($("s4-note"), { opacity: 0, duration: 0.2 }, 11.3);
"""

# ---------------------------------------------------------------- 5 v2 and the payoff
calc = clean(dom("calc"))
s5_body = f"""    <div id="s5-ground" class="rh-ground" style="background:#e1e8cd"></div>
    <div id="s5-cam" class="rh-cam proto-cam"><div class="rh-page"><main>{PROTO}</main></div>
      <span id="s5-ver" class="rh-ver"><span class="v-clip"><span class="v-in"><span>prototype &#183; v1</span><span>prototype &#183; v2</span></span></span></span>
      <span id="s5-c1" class="rh-chip" data-layout-allow-occlusion>Text reply sent &#10003;</span>
      <span id="s5-c2" class="rh-chip" data-layout-allow-occlusion>Repeat customer</span>
      <span id="s5-c3" class="rh-chip" data-layout-allow-occlusion>Booked &#183; Tue 10:00</span>
      <span id="s5-pin1" class="rh-pin done">&#10003;</span>
      <span id="s5-pin2" class="rh-pin done">&#10003;</span>
    </div>
    <div id="s5-calc" class="rh-cam"><div class="rh-page"><main>{calc}</main></div></div>
"""
s5_css = PROTO_CSS + """
    .v-clip { display: block; height: 20px; overflow: hidden; } .v-in { display: block; } .v-in > span { display: block; line-height: 20px; }
    #s5-calc .calculator-copy { visibility: hidden; }
    #s5-cam .app-bottom { visibility: hidden; }
"""
s5_js = (proto_measure().replace("{p}", "s5")) + """
    place($("s5-ver"), browser, 0, 0, 14, -46);
    place($("s5-c1"), steps[0], 0.04, 1.0, 0, 10);
    place($("s5-c2"), steps[1], 0.04, 1.0, 0, 10);
    place($("s5-c3"), steps[2], 0.04, 1.0, 0, 10);
    place($("s5-pin1"), steps[1], 0.92, 0.12);
    place($("s5-pin2"), steps[2], 0.92, 0.12);
    RH.cam(tl, cam, { s: full.s * 1.25, x: full.x - 300, y: full.y - 140 }, 0, 0);
    tl.fromTo(cam, { filter: "blur(10px)" }, { filter: "blur(0px)", duration: 0.35, ease: "power2.out" }, 0);
    RH.cam(tl, cam, full, 0.0, 0.8, "expo.out");
    tl.to($("s5-ver").querySelector(".v-in"), { yPercent: -50, duration: 0.35, ease: "power3.inOut" }, 0.9);
    tl.fromTo($("s5-ver"), { scale: 1 }, { scale: 1.15, duration: 0.15, yoyo: true, repeat: 1 }, 1.2);
    var tags = cam.querySelectorAll(".pipeline-tag");
    tl.set([$("s5-c1"), $("s5-c2"), $("s5-c3")], { scale: 0, opacity: 0, transformOrigin: "0% 50%" }, 0);
    // each change lands as it is named
    [["s5-c2", 2.75], ["s5-c1", 4.15], ["s5-c3", 5.05]].forEach(function (c) {
      tl.to($(c[0]), { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.4)" }, c[1]);
    });
    tl.fromTo([$("s5-pin1"), $("s5-pin2")], { scale: 0 }, { scale: 1, duration: 0.4, ease: "back.out(2.6)", stagger: 0.12 }, 1.6);
    // the payoff: the hours it gives back (the site's own calculator at its default 20 h, 50%)
    var calcCam = $("s5-calc"), card = calcCam.querySelector(".calculator"), main = calcCam.querySelector(".capacity-main");
    var cs = Math.min(1.6, 1500 / card.offsetWidth);
    var cAim = RH.aim(RH.pt(card, calcCam, 0.5, 0.3), cs, 960, 560);
    RH.cam(tl, calcCam, { s: cAim.s, x: cAim.x, y: cAim.y + 900 }, 0, 0);
    tl.to(cam, { y: "-=520", opacity: 0, filter: "blur(8px)", duration: 0.6, ease: "power3.in" }, 7.7);
    RH.cam(tl, calcCam, cAim, 7.9, 0.9, "expo.out");
    var hoursEl = calcCam.querySelector("#capacity-hours"), bars = calcCam.querySelectorAll("[data-capacity-bar]");
    RH.drive(tl, 13, function (T) {
      var k = Math.max(0, Math.min(1, (T - 8.4) / 1.4)), e = 1 - Math.pow(1 - k, 2);
      hoursEl.textContent = (Math.round(43.3 * e * 10) / 10).toFixed(1);
    });
    bars.forEach(function (b, i) { if (i < 14) tl.fromTo(b, { scaleY: 0.2, opacity: 0.3 }, { scaleY: 0.85, opacity: 1, duration: 0.3, ease: "back.out(2.5)" }, 8.45 + i * 0.08); });
    tl.to(hoursEl, { color: "#e0ed9b", duration: 0.2 }, 9.8);
"""

# ---------------------------------------------------------------- 6 diagnose, build, run
s6_body = """    <div class="rh-ground" style="background:#f7f7f2"></div>
    <div class="s6-words"><span id="s6-a">Diagnose.</span><span id="s6-b">Build.</span><span id="s6-c">Run.</span></div>
    <h2 id="s6-d" class="rh-title" style="top:640px;font-size:76px;color:#1d221e">Not another tool.</h2>
    <h2 id="s6-e" class="rh-title" style="top:730px;font-size:76px;color:#7d8c6a">A better way to work.</h2>
"""
s6_css = TITLE + """
    .s6-words { position: absolute; left: 140px; top: 280px; display: flex; gap: 60px; font-family: "Inter Tight Variable", sans-serif;
      font-weight: 550; font-size: 190px; letter-spacing: -0.06em; color: #1d221e; }
    .s6-words span { position: relative; display: inline-block; }
    .s6-words span:after { content: ""; position: absolute; left: 0; right: 0; bottom: 22px; height: 22%; background: #e0ed9b; z-index: -1;
      transform: scaleX(var(--hl, 0)); transform-origin: left center; }
    .s6-words { isolation: isolate; }
"""
s6_js = """
    [["s6-a", 0.35], ["s6-b", 1.25], ["s6-c", 2.0]].forEach(function (w, i) {
      tl.fromTo($(w[0]), { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "expo.out" }, w[1]);
      tl.fromTo($(w[0]), { "--hl": 0 }, { "--hl": 1, duration: 0.35, ease: "power3.out" }, w[1] + 0.12);
      if (i < 2) tl.to($(w[0]), { "--hl": 0, duration: 0.25, ease: "power2.in" }, w[1] + 0.8);
    });
    [["s6-d", 2.85], ["s6-e", 3.6]].forEach(function (l) {
      RH.words($(l[0])).forEach(function (w, i) {
        tl.fromTo(w, { color: "#dcdfd3" }, { color: l[0] === "s6-d" ? "#1d221e" : "#7d8c6a", duration: 0.2 }, l[1] + i * 0.09);
      });
    });
    tl.to(["s6-a","s6-b","s6-c","s6-d","s6-e"].map($), { opacity: 0, filter: "blur(10px)", duration: 0.2, stagger: 0.03, ease: "power2.in" }, 5.6);
"""

# ---------------------------------------------------------------- 7 end card
s7_body = f"""    <div class="rh-ground" style="background:#e5edcc"></div>
    <div id="s7-lockup">
      <div id="s7-wm" class="s7-wm">roundhouse<span id="s7-stop">.</span><span id="s7-reg">&#174;</span></div>
      <div id="s7-dot"></div>
      <p id="s7-tag">Good ideas. Made real.</p>
      <span id="s7-go">Let&#8217;s talk &#8599;</span>
    </div>
    {cursor("s7-cur")}
"""
s7_css = """
    #s7-lockup { position: absolute; left: 0; right: 0; top: 300px; display: flex; flex-direction: column; align-items: center; }
    .s7-wm { position: relative; font-family: "Inter Tight Variable", sans-serif; font-weight: 720; font-size: 200px;
      letter-spacing: -0.055em; line-height: 1; color: #1d221e; white-space: nowrap; }
    #s7-stop { visibility: hidden; }
    #s7-reg { font-family: "DM Sans", sans-serif; font-size: 40px; letter-spacing: 0; vertical-align: top; display: inline-block; margin: 18px 0 0 10px; }
    #s7-dot { position: absolute; border-radius: 50%; background: #e0ed9b; box-shadow: inset 0 0 0 5px #6a813e; }
    #s7-tag { margin: 40px 0 0; font-family: "Inter Tight Variable", sans-serif; font-weight: 550; font-size: 56px; letter-spacing: -0.04em; color: #4f5c42; }
    #s7-go { margin-top: 48px; font-family: "DM Sans", sans-serif; font-weight: 500; font-size: 32px; color: #f7f7f2;
      background: #1d221e; padding: 24px 48px; border-radius: 999px; }
"""
s7_js = """
    var wm = $("s7-wm"), stop = $("s7-stop"), dot = $("s7-dot"), lock = $("s7-lockup"), cur = $("s7-cur"), go = $("s7-go");
    var so = RH.off(stop, lock), d = stop.offsetWidth * 0.8;
    dot.style.width = d + "px"; dot.style.height = d + "px";
    dot.style.left = (so.x + stop.offsetWidth * 0.5 - d / 2) + "px"; dot.style.top = (so.y + stop.offsetHeight * 0.79 - d) + "px";
    tl.fromTo(wm, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "power3.out" }, 0.3);
    tl.fromTo(dot, { y: -760 }, { y: 0, duration: 0.36, ease: "power3.in" }, 0.62);
    tl.to(dot, { scaleX: 1.25, scaleY: 0.72, duration: 0.07, transformOrigin: "50% 100%" }, 0.98);
    tl.to(dot, { scaleX: 1, scaleY: 1, duration: 0.4, ease: "back.out(3)" }, 1.05);
    tl.fromTo($("s7-reg"), { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }, 1.2);
    RH.words($("s7-tag")).forEach(function (w, i) {
      tl.fromTo(w, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out" }, 1.6 + i * 0.08);
    });
    tl.fromTo(go, { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, 2.75);
    var gp = RH.pt(go, $("s7-anchor").parentElement, 0.5, 0.55);
    tl.set(cur, { x: 2000, y: 1160, opacity: 1 }, 0);
    RH.move(tl, cur, { x: gp.x + 20, y: gp.y + 8 }, 3.1, 0.8);
    RH.click(tl, cur, 4.15, go);
    tl.to(go, { backgroundColor: "#6a813e", duration: 0.15 }, 4.18);
"""

DUR = {"s1": 7.0, "s2": 15.0, "s3": 14.0, "s4": 12.0, "s5": 13.0, "s6": 6.0, "s7": 8.5}
JS = {"s1": (s1_css, s1_body, s1_js), "s2": (s2_css, s2_body, s2_js), "s3": (s3_css, s3_body, s3_js),
      "s4": (s4_css, s4_body, s4_js), "s5": (s5_css, s5_body, s5_js), "s6": (s6_css, s6_body, s6_js),
      "s7": (s7_css, s7_body, s7_js)}
ST, t = {}, 0.0
for k in DUR:
    ST[k] = round(t, 3); t += DUR[k]
TOTAL = round(t, 3)
for k in DUR:
    css, body, js = JS[k]
    (OUT / f"{k}.html").write_text(scene(k, css, body, js))

# ---------------------------------------------------------------- voice, a light bed, effects under the voice
VO = [("V1", "s1", 0.4), ("V2", "s2", 0.5), ("V3", "s2", 6.7), ("V4", "s3", 0.3), ("V5", "s3", 5.9),
      ("V6", "s4", 0.4), ("V7", "s4", 6.6), ("V8", "s5", 0.4), ("V9", "s5", 8.3), ("V10", "s6", 0.35), ("V11", "s7", 0.45)]
vo_durs = dict(l.split() for l in (HERE / "vo_durations.txt").read_text().splitlines())
SFX = "assets/audio/sfx"
C = [  # (scene, local time, file, volume[, duration, media start])
    ("s1", 2.62, "transition/sweep-short.mp3", 0.25),
    ("s1", 3.15, "ui/pop.mp3", 0.35), ("s1", 3.7, "ui/ui-message-pop.mp3", 0.3), ("s1", 4.0, "ui/pop-electric.mp3", 0.25),
    ("s1", 6.3, "transition/swoosh-slow.mp3", 0.3),
    ("s2", 0.98, "ui/pop.mp3", 0.3), ("s2", 2.3, "transition/air-woosh-quick.mp3", 0.3),
    ("s2", 6.5, "transition/sweep-short.mp3", 0.2),
    ("s2", 7.42, "ui/pop.mp3", 0.3), ("s2", 8.47, "ui/ui-message-pop.mp3", 0.3), ("s2", 9.62, "ui/pop-electric.mp3", 0.25),
    ("s3", 0.4, "transition/swoosh-quick.mp3", 0.25),
    ("s3", 1.8, "ui/switch-click-quick.mp3", 0.6), ("s3", 2.9, "ui/switch-tap.mp3", 0.7), ("s3", 2.94, "ui/pop.mp3", 0.3),
    ("s3", 3.2, "text/keyboard.mp3", 0.35, 1.2, 2.0),
    ("s3", 6.3, "ui/switch-click-quick.mp3", 0.6), ("s3", 8.4, "ui/pop.mp3", 0.3),
    ("s3", 8.7, "transition/swoosh-quick.mp3", 0.25),
    ("s3", 9.4, "ui/ui-message-pop.mp3", 0.3), ("s3", 10.0, "ui/ui-message-pop.mp3", 0.25), ("s3", 10.9, "ui/ui-message-pop.mp3", 0.3),
    ("s3", 12.95, "ui/switch-click-quick.mp3", 0.6), ("s3", 13.1, "transition/air-zoom-vacuum.mp3", 0.35),
    ("s4", 0.35, "text/keyboard.mp3", 0.35, 1.1, 6.0),
    ("s4", 1.75, "ui/switch-light.mp3", 0.5), ("s4", 2.6, "ui/pop.mp3", 0.2),
    ("s4", 4.6, "text/typewriter-hit-soft.mp3", 0.8), ("s4", 5.4, "text/typewriter-hit-soft.mp3", 0.8), ("s4", 6.2, "text/typewriter-hit-soft.mp3", 0.8),
    ("s4", 9.2, "ui/switch-click-quick.mp3", 0.6), ("s4", 9.5, "light/sparkle-touch.mp3", 0.3),
    ("s4", 11.35, "transition/air-woosh-quick.mp3", 0.35),
    ("s5", 0.95, "ui/switch-light.mp3", 0.5),
    ("s5", 2.75, "ui/pop.mp3", 0.35), ("s5", 4.15, "ui/ui-message-pop.mp3", 0.3), ("s5", 5.05, "ui/pop-electric.mp3", 0.25),
    ("s5", 7.7, "transition/swoosh-slow.mp3", 0.3),
    ("s5", 9.8, "impact/impact-zoom-quick.mp3", 0.35),
    ("s6", 5.6, "transition/swoosh-quick.mp3", 0.25),
    ("s7", 0.98, "impact/bass-hit-futuristic.mp3", 0.45), ("s7", 1.2, "ui/pop.mp3", 0.3),
    ("s7", 4.15, "ui/switch-click-quick.mp3", 0.6),
]
riser_peak = float((HERE / "riser_peak.txt").read_text())
C.append(("s7", 0.98 - riser_peak, "riser/riser-cine.mp3", 0.3))
peaks = {f: float(p) for f, p in (l.split()[:2] for l in (HERE / "peaks.txt").read_text().splitlines())}
durs = dict(l.split()[:2] for l in (HERE / "durations.txt").read_text().splitlines())
cues = []
for c in C:
    s, lt, f, v = c[:4]
    t = ST[s] + lt
    if len(c) > 4:
        cues.append((max(0.0, round(t, 3)), f, v, c[4], c[5]))
    else:
        lead = peaks.get(f, 0.0) - 1 / 30
        st = max(0.0, round(t - max(0.0, lead), 3))
        cues.append((st, f, v, round(min(float(durs[f]), TOTAL - st), 3), 0))
audio, lanes = [], []
for i, (st, f, v, d, ms) in enumerate(sorted(cues)):
    lane = next((k for k, end in enumerate(lanes) if end <= st), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = st + d
    m = f' data-media-start="{ms}"' if ms else ""
    audio.append(f'      <audio id="sfx{i:02d}" class="clip" src="{SFX}/{f}" data-start="{st}" data-duration="{d}"{m} data-volume="{v}" data-track-index="{3 + lane}"></audio>')
voice = "".join(
    f'      <audio id="vo-{lid}" class="clip" src="assets/audio/vo/{lid}.wav" data-start="{round(ST[s] + t, 3)}" data-duration="{vo_durs[lid]}" data-volume="1" data-track-index="20"></audio>\n'
    for lid, s, t in VO)

index = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Round House: how a project moves</title>
    <script src="assets/gsap.min.js"></script>
    <script src="assets/rh.js"></script>
    <link rel="stylesheet" href="assets/site.css" />
    <style>
{FONTS}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #f7f7f2; }}
      #root *, #root *::before, #root *::after {{ transition: none !important; animation: none !important; }}
      .rh-ground {{ position: absolute; inset: 0; }}
      .rh-cam {{ position: absolute; left: 0; top: 0; width: 1920px; transform-origin: 0 0; }}
      .rh-page {{ width: 1920px; }}
      .rh-w, .rh-l {{ display: inline-block; }}
      .rh-cur {{ position: absolute; left: 0; top: 0; width: 66px; height: 66px; margin: -8.25px 0 0 -13.75px;
        transform-origin: 13.75px 8.25px; z-index: 100; pointer-events: none; opacity: 0; }}
      .rh-cur svg {{ width: 100%; height: 100%; overflow: visible; filter: drop-shadow(0 7px 9px rgba(20, 24, 18, 0.32)); }}
      .rh-cur path {{ fill: #ffffff; stroke: #1d221e; stroke-width: 1.35; stroke-linejoin: round; }}
      .rh-tag {{ position: absolute; left: 50px; top: 52px; white-space: nowrap; font: 500 22px "DM Sans", sans-serif; color: #1d221e;
        background: #e0ed9b; padding: 7px 14px; border-radius: 999px; box-shadow: 0 6px 14px rgba(20,24,18,.18); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
""" + "".join(
    f'      <div id="{k}" data-composition-id="{k}" data-composition-src="compositions/{k}.html" data-start="{ST[k]}" data-duration="{DUR[k]}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>\n'
    for k in DUR) + f"""      <audio id="music" class="clip" src="assets/audio/bgm-inspiration-profonde.mp3" data-start="0" data-duration="{TOTAL}" data-volume="0.1" data-fade-in="1.2" data-fade-out="2.5" data-track-index="2"></audio>
{voice}""" + "\n".join(audio) + """
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = gsap.timeline({ paused: true });
    </script>
  </body>
</html>
"""
(FILM / "index.html").write_text(index)
print("scenes", len(DUR), "total", TOTAL, "cues", len(audio))
