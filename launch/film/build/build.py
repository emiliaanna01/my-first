#!/usr/bin/env python3
"""Generates compositions/s1..s7.html and index.html from the site's own DOM snapshots (../dom)."""
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

CURSOR = """<div id="{id}" class="rh-cur" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 3 L5 19 L9 15 L12 22 L15 20.5 L11.5 14 L18 14 Z"/></svg></div>"""


def dom(name):
    return (DOM / f"{name}.html").read_text()


def strip_inline_transforms(html):
    # The snapshot carries GSAP scroll-reveal leftovers; the film animates these elements itself.
    return re.sub(r' style="translate: none; rotate: none; scale: none;[^"]*"', "", html)


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


TITLE_CSS = """
    .rh-title { position: absolute; left: 140px; margin: 0; font-family: "Inter Tight Variable", sans-serif;
      font-weight: 550; font-size: 128px; line-height: 1.02; letter-spacing: -0.055em; white-space: nowrap; }
"""

# ---------------------------------------------------------------- 1 hook: the old way, on the dark ground
PILLS = [("CRM", 1240, 170, -6), ("Inbox", 1600, 300, 5), ("Spreadsheet", 1290, 430, 3), ("Calendar", 1620, 570, -4),
         ("Forms", 1200, 720, -3), ("Chat", 1500, 820, 6), ("Docs", 210, 170, -5), ("Invoices", 560, 120, 4),
         ("Notes", 240, 770, 3), ("Tasks", 690, 820, -6)]

s1_body = '    <div id="s1-ground" class="rh-ground" style="background:#20271f"></div>\n'
s1_body += "".join(
    f'    <span class="s1-pill" id="s1-p{i}" style="left:{x}px;top:{y}px">{t}</span>\n' for i, (t, x, y, r) in enumerate(PILLS))
s1_body += """    <div id="s1-sphere"></div>
    <h2 id="s1-a" class="rh-title" style="top:380px;color:#f3f5ea">More software.</h2>
    <h2 id="s1-b" class="rh-title" style="top:380px;color:#f3f5ea">More back-and-forth.</h2>
    <h2 id="s1-c" class="rh-title" style="top:330px;color:#f3f5ea">Not another tool.</h2>
    <h2 id="s1-d" class="rh-title" style="top:466px;color:#a9b78f">A better way to work.</h2>
"""
s1_css = TITLE_CSS + """
    .s1-pill { position: absolute; font-family: "DM Sans", sans-serif; font-weight: 500; font-size: 30px; color: #e5edcc;
      padding: 16px 30px; border-radius: 999px; background: #2b3429; border: 1.5px solid #3e4a39; white-space: nowrap; }
    #s1-sphere { position: absolute; left: 1330px; top: 420px; width: 240px; height: 240px; border-radius: 50%; background: #e0ed9b; }
"""
s1_js = """
    var pills = [%s];
    var rot = [%s];
    var sphereC = { x: 1450, y: 540 };
    // frame 0 already reads: the line and two tools are on screen
    pills.forEach(function (id, i) {
      var el = $(id), t = i === 0 || i === 6 ? 0 : 0.25 + 0.245 * (i < 6 ? i - 1 : i - 2);
      tl.fromTo(el, { scale: t === 0 ? 1 : 0.4, opacity: t === 0 ? 1 : 0, rotation: rot[i] },
        { scale: 1, opacity: 1, rotation: rot[i], duration: t === 0 ? 0.01 : 0.38, ease: "back.out(1.7)" }, t);
      // the old way churns: each tool keeps tipping on the beat until it is pulled in
      tl.to(el, { rotation: rot[i] * -0.6, duration: 0.49, ease: "power1.inOut", repeat: 3, yoyo: true }, 1.96 + (i %% 3) * 0.08);
      var bx = el.offsetLeft + el.offsetWidth / 2, by = el.offsetTop + el.offsetHeight / 2;
      tl.to(el, { x: sphereC.x - bx, y: sphereC.y - by, scale: 0.15, opacity: 0, rotation: 0,
        duration: 0.45, ease: "power3.in" }, 3.66 + i * 0.028);
    });
    tl.fromTo($("s1-sphere"), { scale: 0 }, { scale: 1, duration: 0.42, ease: "back.out(1.6)" }, 3.55);
    tl.to($("s1-sphere"), { scale: 1.08, duration: 0.12, ease: "power2.out" }, 4.05);
    tl.to($("s1-sphere"), { scale: 1, duration: 0.3, ease: "back.out(2)" }, 4.17);
    // lines: blur swap on the same spot
    tl.set($("s1-a"), { opacity: 1, filter: "blur(0px)" }, 0);
    tl.to($("s1-a"), { opacity: 0, filter: "blur(8px)", duration: 0.15, ease: "power2.in" }, 1.9);
    tl.fromTo($("s1-b"), { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, 1.98);
    tl.to($("s1-b"), { opacity: 0, filter: "blur(8px)", duration: 0.15, ease: "power2.in" }, 3.56);
    tl.fromTo($("s1-c"), { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, 3.68);
    tl.fromTo($("s1-d"), { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, 3.9);
    tl.to([$("s1-c"), $("s1-d")], { opacity: 0, filter: "blur(10px)", duration: 0.2, ease: "power2.in" }, 5.5);
    // the sphere becomes the next world: it grows past the frame and turns into the paper of the hero
    tl.to($("s1-sphere"), { scale: 19, duration: 0.62, ease: "power3.in" }, 5.2);
    tl.to($("s1-sphere"), { backgroundColor: "#f7f7f2", duration: 0.26, ease: "power2.inOut" }, 5.58);
""" % (", ".join(f'"s1-p{i}"' for i in range(len(PILLS))), ", ".join(str(r) for (_, _, _, r) in PILLS))

# ---------------------------------------------------------------- 2 reveal: the real hero
hero = strip_inline_transforms(dom("hero"))
hero = hero.replace('<a class="button dark" href="#/solutions">', '<a class="button dark" id="s2-btn" href="#/solutions">')
hero = hero.replace("<h1 ", '<h1 id="s2-h1" ')
s2_body = f"""    <div class="rh-ground" style="background:#f7f7f2"></div>
    <div id="s2-cam" class="rh-cam"><div class="rh-page"><main>{dom("header")}{hero}</main></div>
      <video id="s2-sph" class="clip" src="assets/spheres.webm" data-start="0" data-duration="5.88" muted playsinline></video>
    </div>
    {CURSOR.format(id="s2-cur")}
"""
s2_css = """
    #s2-sph { position: absolute; object-fit: contain; z-index: 3; }
    #s2-cam .agency-hero h1 em:after { transform: scaleX(var(--hl, 1)); transform-origin: left center; }
    #s2-cam .sculpture-stage canvas, #s2-cam .sculpture-fallback { visibility: hidden; }
    #s2-btn { position: relative; z-index: 20; }
"""
s2_js = """
    var cam = $("s2-cam"), h1 = $("s2-h1"), btn = $("s2-btn"), cur = $("s2-cur"), vid = $("s2-sph");
    var canvas = cam.querySelector(".sculpture-stage canvas"), hero = cam.querySelector("section.hero");
    var cv = RH.off(canvas, cam);
    vid.style.left = cv.x + "px"; vid.style.top = cv.y + "px";
    vid.style.width = canvas.offsetWidth + "px"; vid.style.height = canvas.offsetHeight + "px";
    var bottom = RH.off(hero, cam).y + hero.offsetHeight;
    var sFull = Math.min(1, 1080 / bottom);
    var full = { s: sFull, x: (1920 - 1920 * sFull) / 2, y: 0 };
    var start = RH.aim(RH.pt(h1, cam), 1.32 * sFull, 780, 560);
    RH.cam(tl, cam, start, 0, 0);
    // title: per word, blur to sharp, no travel
    var w = RH.words(h1);
    w.forEach(function (el, i) {
      tl.fromTo(el, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out" },
        (i < 2 ? 0.12 : 0.46) + (i % 2) * 0.07);
    });
    var em = h1.querySelector("em");
    tl.fromTo(em, { "--hl": 0 }, { "--hl": 1, duration: 0.45, ease: "power3.out" }, 0.98);
    tl.fromTo(vid, { opacity: 0, y: 70 }, { opacity: 1, y: 0, duration: 1.0, ease: "expo.out" }, 0.35);
    // the rest of the page settles in under the title, so nothing pops on at the cut
    var rest = [cam.querySelector("header"), cam.querySelector(".hero-top"), cam.querySelector(".hero-description"),
      cam.querySelector(".hero-actions"), cam.querySelector(".hero-footnote"), cam.querySelector(".sculpture-toolbar"),
      cam.querySelector(".form-controls"), cam.querySelector(".hero-bottom")];
    rest.forEach(function (e, i) {
      if (e) tl.fromTo(e, { opacity: 0 }, { opacity: 1, duration: 0.45, ease: "power2.out" }, 0.75 + i * 0.05);
    });
    // pull back to the whole page: the brand is seen inside the product
    RH.cam(tl, cam, full, 1.7, 0.9);
    // the cursor arrives and clicks the real call to action
    var b = RH.frame(RH.pt(btn, cam), full);
    tl.set(cur, { x: 2010, y: 1180, opacity: 1 }, 0);
    RH.move(tl, cur, { x: b.x + 18, y: b.y + 6 }, 3.75, 0.8);
    RH.click(tl, cur, 4.9, btn);
    tl.to(cur, { opacity: 0, duration: 0.12 }, 5.18);
    // zoom through the button: its dark fill becomes the next world
    tl.to(btn, { scale: 42, duration: 0.6, ease: "power3.in" }, 5.26);
"""

# ---------------------------------------------------------------- 3 workflow: one inquiry, one clear next step
wf = strip_inline_transforms(dom("workflow"))
wf = wf.replace('<div class="workflow-playground reveal"', '<div id="s3-pg1" class="workflow-playground reveal"')
wf = wf.replace('class="workflow-replay"', 'id="s3-replay" class="workflow-replay"')
wf = wf.replace('<div class="workflow-intro">', '<div class="workflow-intro" style="visibility:hidden">')
pg2 = strip_inline_transforms(dom("workflow-knowledge"))
pg2 = re.sub(r'\sid="([a-z-]+)"', r' id="k-\1"', pg2)
pg2 = pg2.replace('<div class="workflow-playground reveal"', '<div id="s3-pg2" class="workflow-playground reveal"', 1)
wf = wf.replace('<div class="workflow-bottom">', pg2 + '<div class="workflow-bottom">')
s3_body = f"""    <div id="s3-ground" class="rh-ground" style="background:#1d221e"></div>
    <div id="s3-cam" class="rh-cam"><div class="rh-page"><main>{wf}</main></div></div>
    <h2 id="s3-a" class="rh-title" style="top:330px;color:#f3f5ea">From first hello.</h2>
    <h2 id="s3-b" class="rh-title" style="top:466px;color:#a9b78f">To what&#8217;s next.</h2>
    {CURSOR.format(id="s3-cur")}
"""
s3_css = TITLE_CSS + """
    #s3-cam #workflow { background: transparent; }
    #s3-pg2 { position: absolute; }
    #s3-cam .workflow-bottom { visibility: hidden; }
"""
s3_js = """
    var cam = $("s3-cam"), pg1 = $("s3-pg1"), pg2 = $("s3-pg2"), cur = $("s3-cur");
    var o1 = RH.off(pg1, pg1.offsetParent);
    pg2.style.left = o1.x + "px"; pg2.style.top = o1.y + "px"; pg2.style.width = pg1.offsetWidth + "px";
    var panel = pg1.querySelector(".workflow-panel");
    var sP = Math.min(2.0, 1840 / panel.offsetWidth), sG = Math.min(1.4, 1780 / pg1.offsetWidth);
    var camP = RH.aim(RH.pt(panel, cam), sP, 960, 560), camG = RH.aim(RH.pt(pg1, cam), sG, 960, 560);
    RH.cam(tl, cam, camP, 0, 0);
    // title on the dark ground left by the button, per word from grey
    [["s3-a", "#f3f5ea", 0.1], ["s3-b", "#a9b78f", 0.55]].forEach(function (l) {
      RH.words($(l[0])).forEach(function (el, i) {
        tl.fromTo(el, { color: "#465043" }, { color: l[1], duration: 0.18, ease: "power2.out" }, l[2] + i * 0.08);
      });
    });
    tl.to([$("s3-a"), $("s3-b")], { opacity: 0, filter: "blur(10px)", duration: 0.2, ease: "power2.in" }, 1.86);
    tl.fromTo($("s3-ground"), { backgroundColor: "#1d221e" }, { backgroundColor: "#eef1e6", duration: 0.4, ease: "power2.inOut" }, 1.9);
    tl.fromTo(pg1, { opacity: 0, y: 90 }, { opacity: 1, y: 0, duration: 0.8, ease: "expo.out" }, 2.0);
    tl.set(pg2, { opacity: 0 }, 0);
    // a flow runs node by node: icon pops, connector lands, the middle node fills lime
    function flow(pg, t) {
      var nodes = pg.querySelectorAll(".preview-node"), cons = pg.querySelectorAll(".preview-connector"),
          icons = pg.querySelectorAll(".preview-icon"), status = pg.querySelector(".preview-status");
      tl.set(nodes, { opacity: 0.25 }, 0);
      tl.set(cons, { opacity: 0.15 }, 0);
      tl.set(icons[1], { backgroundColor: "rgba(224,237,155,0)", borderColor: "#66665b" }, 0);
      tl.set(status, { opacity: 0.3 }, 0);
      [0, 1, 2].forEach(function (k) {
        var tk = t + k * 0.42;
        tl.to(nodes[k], { opacity: 1, duration: 0.2, ease: "power2.out" }, tk);
        tl.fromTo(icons[k], { scale: 0.55 }, { scale: 1, duration: 0.42, ease: "back.out(2)" }, tk);
        if (k === 1) tl.to(icons[1], { backgroundColor: "#e0ed9b", borderColor: "#e0ed9b", duration: 0.2 }, tk + 0.05);
        if (k < 2) tl.fromTo(cons[k], { opacity: 0.15, x: -12 }, { opacity: 1, x: 0, duration: 0.25, ease: "power3.out" }, tk + 0.2);
      });
      tl.to(status, { opacity: 1, duration: 0.2 }, t + 1.05);
      tl.fromTo(status, { scale: 0.85 }, { scale: 1, duration: 0.35, ease: "back.out(2.4)" }, t + 1.05);
    }
    flow(pg1, 3.75);
    flow(pg2, 7.85);
    tl.set(cur, { x: 2010, y: 1160, opacity: 1 }, 0);
    var r = RH.frame(RH.pt($("s3-replay"), cam), camP);
    RH.move(tl, cur, { x: r.x + 12, y: r.y + 4 }, 2.75, 0.75);
    RH.click(tl, cur, 3.6, $("s3-replay"));
    // pull back to the whole playground, then pick the next workflow
    RH.cam(tl, cam, camG, 6.2, 0.8);
    var tab = pg1.querySelector('[data-workflow="knowledge-assistant"]');
    var tp = RH.frame(RH.pt(tab, cam, 0.35, 0.5), camG);
    RH.move(tl, cur, { x: tp.x, y: tp.y + 6 }, 6.55, 0.8);
    RH.click(tl, cur, 7.5, tab);
    tl.to(pg1, { opacity: 0, duration: 0.18, ease: "power2.in" }, 7.52);
    tl.to(pg2, { opacity: 1, duration: 0.18, ease: "power2.out" }, 7.52);
    tl.fromTo(pg2.querySelector(".workflow-panel"), { filter: "blur(8px)" }, { filter: "blur(0px)", duration: 0.2, ease: "power2.out" }, 7.55);
    // punch in on the answer, then whip out
    var n3 = pg2.querySelectorAll(".preview-node")[2];
    RH.cam(tl, cam, RH.aim(RH.pt(n3, cam), sG * 1.5, 1100, 540), 9.4, 0.6);
    tl.to(cur, { x: 1500, y: 1250, duration: 0.6, ease: "power3.in" }, 9.4);
    tl.to(cam, { x: "-=760", duration: 0.34, ease: "power3.in" }, 11.42);
    tl.fromTo(cam, { filter: "blur(0px)" }, { filter: "blur(16px)", duration: 0.34, ease: "power3.in" }, 11.42);
"""

# ---------------------------------------------------------------- 4 approach: diagnose, build, run
path = strip_inline_transforms(dom("path"))
path = path.replace("<details ", "<details open ").replace("<details open open", "<details open")
s4_body = f"""    <div class="rh-ground" style="background:#f7f7f2"></div>
    <div id="s4-cam" class="rh-cam"><div class="rh-page"><main>{path}</main></div></div>
    {CURSOR.format(id="s4-cur")}
"""
s4_css = """
    #s4-cam .approach-row > div { overflow: hidden; }
"""
s4_js = """
    var cam = $("s4-cam"), cur = $("s4-cur"), sec = cam.querySelector("#path");
    var rows = Array.prototype.slice.call(sec.querySelectorAll(".approach-row"));
    var body = rows.map(function (r) { return r.querySelector(":scope > div"); });
    var sum = rows.map(function (r) { return r.querySelector("summary"); });
    var plus = rows.map(function (r) { return r.querySelector("summary > svg"); });
    var h3 = rows.map(function (r) { return r.querySelector("h3"); });
    var hOpen = body.map(function (b) { return b.offsetHeight; });
    var openColor = getComputedStyle(h3[0]).color, closedColor = "#1d221e";
    var top = RH.off(sec, cam).y, h = sec.offsetHeight - (hOpen[1] + hOpen[2]);
    var s = Math.min(1, 1040 / h), base = { s: s, x: (1920 - 1920 * s) / 2, y: (1080 - h * s) / 2 - top * s };
    // closed rows: no body, ink title, plus upright
    [1, 2].forEach(function (i) {
      tl.set(body[i], { height: 0, paddingBottom: 0, opacity: 0 }, 0);
      tl.set(h3[i], { color: closedColor }, 0);
      tl.set(plus[i], { rotation: 0 }, 0);
    });
    tl.set(plus[0], { rotation: 45 }, 0);
    // whip in from the right, matching the outgoing whip
    tl.fromTo(cam, { scale: base.s, x: base.x + 760, y: base.y, filter: "blur(16px)" },
      { x: base.x, filter: "blur(0px)", duration: 0.34, ease: "power3.out" }, 0);
    var t2 = sec.querySelector(".approach-intro h2");
    RH.words(t2).forEach(function (el, i) {
      tl.fromTo(el, { opacity: 0, y: 36 }, { opacity: 1, y: 0, duration: 0.55, ease: "expo.out" }, 0.22 + i * 0.07);
    });
    function toggle(close, open, t) {
      tl.to(body[close], { height: 0, paddingBottom: 0, opacity: 0, duration: 0.45, ease: "power3.inOut" }, t);
      tl.to(h3[close], { color: closedColor, duration: 0.25 }, t);
      tl.to(plus[close], { rotation: 0, duration: 0.35, ease: "power3.inOut" }, t);
      tl.to(body[open], { height: hOpen[open], paddingBottom: 30, opacity: 1, duration: 0.5, ease: "power3.inOut" }, t + 0.05);
      tl.to(h3[open], { color: openColor, duration: 0.25 }, t + 0.05);
      tl.to(plus[open], { rotation: 45, duration: 0.35, ease: "power3.inOut" }, t + 0.05);
      body[open].querySelectorAll("li").forEach(function (li, i) {
        tl.fromTo(li, { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }, t + 0.3 + i * 0.08);
      });
    }
    // where each summary sits in camera space, before and after the first toggle
    var yBuild = RH.pt(sum[1], cam).y - hOpen[1] - hOpen[2] + hOpen[1];  // build itself closed, run closed: unchanged
    var yRunAfter = RH.pt(sum[2], cam).y - hOpen[0];                      // diagnose closed, build open
    var xs = RH.pt(sum[1], cam, 0.12, 0.5).x;
    var push = RH.aim({ x: RH.pt(rows[1], cam).x, y: RH.pt(sum[1], cam).y }, s * 1.12, 1150, 520);
    tl.set(cur, { x: 2010, y: 1160, opacity: 1 }, 0);
    var b1 = RH.frame({ x: xs, y: RH.pt(sum[1], cam).y }, base);
    RH.move(tl, cur, b1, 1.55, 0.8);
    RH.click(tl, cur, 2.7, sum[1]);
    toggle(0, 1, 2.75);
    RH.cam(tl, cam, push, 2.6, 0.9);
    tl.to(sec.querySelector(".approach-intro"), { opacity: 0, filter: "blur(8px)", duration: 0.3, ease: "power2.in" }, 2.55);
    var b2 = RH.frame({ x: xs, y: yRunAfter }, push);
    RH.move(tl, cur, b2, 3.95, 0.65);
    RH.click(tl, cur, 4.7, sum[2]);
    toggle(1, 2, 4.75);
    RH.cam(tl, cam, RH.aim({ x: RH.pt(rows[1], cam).x, y: yRunAfter }, s * 1.12, 1150, 470), 4.6, 0.9);
    tl.to(cur, { x: 1700, y: 1250, duration: 0.6, ease: "power3.in" }, 6.4);
"""

# ---------------------------------------------------------------- 5 payoff: the calculator, real formula
calc = strip_inline_transforms(dom("calc"))
s5_body = f"""    <div class="rh-ground" style="background:#f7f7f2"></div>
    <div id="s5-cam" class="rh-cam"><div class="rh-page"><main>{calc}</main></div></div>
    <div id="s5-dip" class="rh-ground" style="background:#000;opacity:0"></div>
    {CURSOR.format(id="s5-cur")}
"""
s5_css = ""
s5_js = """
    var cam = $("s5-cam"), cur = $("s5-cur"), card = cam.querySelector(".calculator");
    var hours = 20, rate = 40;
    var el = { h: cam.querySelector("#capacity-hours"), d: cam.querySelector("#capacity-days"),
      p: cam.querySelector("#capacity-portion"), rv: cam.querySelector("#reduction-value"),
      v: cam.querySelector("#capacity-value"), r: cam.querySelector("#reduction") };
    var bars = Array.prototype.slice.call(cam.querySelectorAll("[data-capacity-bar]"));
    function fmt(n) { return n.toLocaleString("en-US", { maximumFractionDigits: 1 }); }
    // the site's own formula: hours x reduction x 4.33 weeks; value = hours back x hourly cost
    function setVal(a) {
      var O = hours * a / 100 * 4.33;
      el.h.textContent = fmt(O); el.d.textContent = fmt(O / 8);
      el.p.textContent = a + "% potential reduction"; el.rv.value = a + "%"; el.rv.textContent = a + "%";
      el.v.textContent = (O * rate).toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
      el.r.value = a; el.r.style.setProperty("--range-fill", ((a - 10) / 70 * 100) + "%");
      var n = Math.round(a / 100 * 28);
      bars.forEach(function (b, i) { b.classList.toggle("is-recovered", i < n); });
    }
    var copy = cam.querySelector(".calculator-copy"), cL = RH.off(copy, cam).x, cR = RH.off(card, cam).x + card.offsetWidth;
    var cH = card.offsetHeight, s = Math.min(1.12, 1010 / cH, 1780 / (cR - cL));
    var base = { s: s, x: (1920 - (cR - cL) * s) / 2 - cL * s, y: 540 - RH.pt(card, cam).y * s };
    RH.cam(tl, cam, base, 0, 0);
    tl.fromTo(card, { y: 60, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: "expo.out" }, 0.05);
    var copyH = cam.querySelector(".calculator-copy h2");
    RH.words(copyH).forEach(function (w, i) {
      tl.fromTo(w, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out" }, 0.4 + i * 0.07);
    });
    // drag 10%% -> 50%% in the slider's real 5%% steps
    var proxy = { a: 10 }, T0 = 3.2, T1 = 5.4;
    tl.fromTo(proxy, { a: 10 }, { a: 50, duration: T1 - T0, ease: "none",
      onUpdate: function () { setVal(Math.round(proxy.a / 5) * 5); } }, T0);
    setVal(10);
    tl.call(function () { setVal(10); }, null, 0);
    // bars: each newly recovered bar settles in with a small spring
    var prevN = Math.round(10 / 100 * 28);
    bars.forEach(function (b, i) { tl.set(b, { scaleY: i < prevN ? 0.85 : 1 }, 0); });
    for (var a = 15; a <= 50; a += 5) {
      var n = Math.round(a / 100 * 28), tk = T0 + (a - 2.5 - 10) / 40 * (T1 - T0);
      for (var i = prevN; i < n; i++) tl.fromTo(bars[i], { scaleY: 0.5 }, { scaleY: 0.85, duration: 0.3, ease: "back.out(2.5)" }, tk);
      prevN = n;
    }
    // the cursor finds the thumb and drags it
    var rIn = el.r, ri = RH.pt(rIn, cam, 0, 0.5), rw = rIn.offsetWidth, th = 18;
    function thumb(a) { return RH.frame({ x: ri.x + th / 2 + (a - 10) / 70 * (rw - th), y: ri.y }, base); }
    tl.set(cur, { x: 2010, y: 1160, opacity: 1 }, 0);
    RH.move(tl, cur, thumb(10), 2.05, 0.85);
    tl.to(cur, { scale: 0.86, duration: 0.1, ease: "power2.out" }, 3.05);
    tl.to(cur, { x: thumb(50).x, duration: T1 - T0, ease: "none" }, T0);
    tl.to(cur, { scale: 1, duration: 0.25, ease: "back.out(2.2)" }, 5.5);
    // payoff: 43.3 lands, turns lime, the camera punches in and holds
    tl.to(el.h, { color: "#e0ed9b", duration: 0.2, ease: "power2.out" }, 5.45);
    tl.to(cur, { x: "+=260", y: 1260, duration: 0.5, ease: "power3.in" }, 5.75);
    var main = cam.querySelector(".capacity-main");
    var punch = RH.aim(RH.pt(main, cam), Math.min(2.1, 1500 / main.offsetWidth), 960, 560);
    RH.cam(tl, cam, punch, 5.6, 0.7);
    var row = cam.querySelector(".capacity-value-row");
    RH.cam(tl, cam, RH.aim(RH.pt(row, cam), Math.min(1.9, 1500 / row.offsetWidth), 960, 540), 7.9, 0.8);
    tl.to($("s5-dip"), { opacity: 0.4, duration: 0.1 }, 11.62);
"""

# ---------------------------------------------------------------- 6 claim: the site's own statement
s6_body = """    <div id="s6-ground" class="rh-ground" style="background:#f7f7f2"></div>
    <h2 id="s6-a" class="rh-title" style="top:230px">A clearer business.</h2>
    <h2 id="s6-b" class="rh-title" style="top:390px">A more useful system.</h2>
    <h2 id="s6-c" class="rh-title" style="top:550px">A brand with feeling.</h2>
"""
s6_css = TITLE_CSS
s6_js = """
    [["s6-a", "#1d221e", 0.2], ["s6-b", "#1d221e", 1.55], ["s6-c", "#7d8c6a", 2.9]].forEach(function (l) {
      RH.words($(l[0])).forEach(function (w, i) {
        tl.fromTo(w, { color: "#dcdfd3" }, { color: l[1], duration: 0.2, ease: "power2.out" }, l[2] + i * 0.09);
      });
    });
    tl.to([$("s6-a"), $("s6-b"), $("s6-c")], { opacity: 0, filter: "blur(10px)", duration: 0.2, ease: "power2.in", stagger: 0.03 }, 5.3);
    tl.fromTo($("s6-ground"), { backgroundColor: "#f7f7f2" }, { backgroundColor: "#e5edcc", duration: 0.4, ease: "power2.inOut" }, 5.45);
"""

# ---------------------------------------------------------------- 7 end card: let's talk, then the mark
cta = strip_inline_transforms(dom("cta"))
cta = cta.replace('<a class="button light" href="#/contact">', '<a class="button light" id="s7-btn" href="#/contact">')
s7_body = f"""    <div class="rh-ground" style="background:#e5edcc"></div>
    <div id="s7-cam" class="rh-cam"><div class="rh-page"><main>{cta}</main></div></div>
    <div id="s7-end" class="rh-ground" style="background:#f7f7f2">
      <div id="s7-lockup">
        <div id="s7-wm" class="s7-wm">roundhouse<span id="s7-stop">.</span><span id="s7-reg">&#174;</span></div>
        <div id="s7-dot"></div>
        <p id="s7-tag">Good ideas. Made real.</p>
        <span id="s7-go">Let&#8217;s talk</span>
      </div>
    </div>
    {CURSOR.format(id="s7-cur")}
"""
s7_css = """
    #s7-cam .cta-section { background: transparent; }
    #s7-lockup { position: absolute; left: 0; right: 0; top: 330px; display: flex; flex-direction: column; align-items: center; }
    .s7-wm { position: relative; font-family: "Inter Tight Variable", sans-serif; font-weight: 720; font-size: 200px;
      letter-spacing: -0.055em; line-height: 1; color: #1d221e; white-space: nowrap; }
    #s7-stop { visibility: hidden; }
    #s7-reg { font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 40px; letter-spacing: 0; vertical-align: top;
      display: inline-block; margin: 18px 0 0 10px; }
    #s7-dot { position: absolute; border-radius: 50%; background: #e0ed9b; box-shadow: inset 0 0 0 5px #6a813e; }
    #s7-tag { margin: 40px 0 0; font-family: "Inter Tight Variable", sans-serif; font-weight: 550; font-size: 56px;
      letter-spacing: -0.04em; color: #7d8c6a; }
    #s7-go { margin-top: 48px; font-family: "DM Sans", sans-serif; font-weight: 500; font-size: 30px; color: #f7f7f2;
      background: #1d221e; padding: 22px 44px; border-radius: 999px; }
"""
s7_js = """
    var cam = $("s7-cam"), cur = $("s7-cur"), sec = cam.querySelector(".cta-section"), btn = $("s7-btn");
    var top = RH.off(sec, cam).y, h = sec.offsetHeight, s = Math.min(1, 1040 / h);
    var base = { s: s, x: (1920 - 1920 * s) / 2, y: (1080 - h * s) / 2 - top * s };
    RH.cam(tl, cam, base, 0, 0);
    var title = cam.querySelector(".cta-title > span");
    RH.letters(title).forEach(function (l, i) {
      tl.fromTo(l, { opacity: 0, yPercent: 40 }, { opacity: 1, yPercent: 0, duration: 0.5, ease: "expo.out" }, 0.12 + i * 0.06);
    });
    var arrow = cam.querySelectorAll(".cta-title > svg path, .cta-title > svg line, .cta-title > svg polyline");
    arrow.forEach(function (p) {
      var L = (p.getTotalLength && p.getTotalLength()) || 400;
      tl.fromTo(p, { strokeDasharray: L, strokeDashoffset: L }, { strokeDashoffset: 0, duration: 0.6, ease: "power2.inOut" }, 0.95);
    });
    tl.fromTo([cam.querySelector(".cta-top"), cam.querySelector(".cta-bottom p")], { opacity: 0 }, { opacity: 1, duration: 0.4 }, 0.5);
    tl.fromTo(btn, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "expo.out" }, 1.1);
    // click "Start a conversation"; the page irises open from the click onto the mark
    var bp = RH.frame(RH.pt(btn, cam), base);
    tl.set(cur, { x: 2010, y: 1160, opacity: 1 }, 0);
    RH.move(tl, cur, { x: bp.x + 10, y: bp.y + 6 }, 1.75, 0.8);
    RH.click(tl, cur, 2.9, btn);
    var ix = bp.x, iy = bp.y;
    tl.fromTo($("s7-end"), { clipPath: "circle(0px at " + ix + "px " + iy + "px)" },
      { clipPath: "circle(2400px at " + ix + "px " + iy + "px)", duration: 0.5, ease: "power3.in" }, 3.0);
    tl.to(cur, { opacity: 0, duration: 0.12 }, 3.05);
    tl.set(cam, { opacity: 0 }, 3.52);
    // the mark: the wordmark wipes in, a lime sphere drops into its full stop
    var wm = $("s7-wm"), stop = $("s7-stop"), dot = $("s7-dot"), lock = $("s7-lockup");
    var so = RH.off(stop, lock), d = stop.offsetWidth * 0.8;
    dot.style.width = d + "px"; dot.style.height = d + "px";
    dot.style.left = (so.x + stop.offsetWidth * 0.5 - d / 2) + "px";
    dot.style.top = (so.y + stop.offsetHeight * 0.79 - d) + "px";
    tl.fromTo(wm, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "power3.out" }, 3.55);
    tl.fromTo(dot, { y: -760, scaleX: 1, scaleY: 1 }, { y: 0, duration: 0.36, ease: "power3.in" }, 3.73);
    tl.to(dot, { scaleX: 1.25, scaleY: 0.72, duration: 0.07, ease: "power2.out", transformOrigin: "50% 100%" }, 4.09);
    tl.to(dot, { scaleX: 1, scaleY: 1, duration: 0.4, ease: "back.out(3)" }, 4.16);
    tl.fromTo($("s7-reg"), { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }, 4.3);
    RH.words($("s7-tag")).forEach(function (w, i) {
      tl.fromTo(w, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out" }, 4.55 + i * 0.07);
    });
    tl.fromTo($("s7-go"), { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, 5.0);
"""

SCENES = [
    ("s1", 0.0, 5.88, s1_css, s1_body, s1_js),
    ("s2", 5.88, 5.88, s2_css, s2_body, s2_js),
    ("s3", 11.76, 11.76, s3_css, s3_body, s3_js),
    ("s4", 23.52, 7.84, s4_css, s4_body, s4_js),
    ("s5", 31.36, 11.76, s5_css, s5_body, s5_js),
    ("s6", 43.12, 5.88, s6_css, s6_body, s6_js),
    ("s7", 49.0, 9.8, s7_css, s7_body, s7_js),
]
TOTAL = 58.8

for cid, start, dur, css, body, js in SCENES:
    (OUT / f"{cid}.html").write_text(scene(cid, css, body, js))

# ---------------------------------------------------------------- sound: music bed + effects on visible actions
SFX_DIR = "assets/audio/sfx"
# (time in film seconds, file, volume); each placed so its peak lands a frame after the picture (see sound.md)
CUES = []
pill_takes = ["ui/pop.mp3", "ui/ui-message-pop.mp3", "ui/pop-electric.mp3"]
for k in range(8):
    CUES.append((0.25 + 0.245 * k, pill_takes[k % 3], 0.55))
CUES += [
    (3.62, "transition/air-zoom-vacuum.mp3", 0.8),     # tools sucked into the sphere
    (5.22, "transition/swoosh-slow.mp3", 0.7),         # sphere becomes the world
    (5.88 + 0.98, "text/marker-pen-line.mp3", 0.5),    # highlight under "real"
    (5.88 + 4.9, "ui/switch-click-quick.mp3", 1.0),    # click: See what's possible
    (5.88 + 5.26, "transition/air-woosh-quick.mp3", 0.8),  # zoom through the button
    (11.76 + 1.9, "transition/swoosh-quick.mp3", 0.6),     # flood to the workflow
    (11.76 + 3.6, "ui/switch-tap.mp3", 1.0),               # click: Replay flow
    (11.76 + 3.75, "ui/pop.mp3", 0.6),
    (11.76 + 4.17, "light/sparkle-touch.mp3", 0.6),
    (11.76 + 4.59, "ui/pop-electric.mp3", 0.5),
    (11.76 + 7.5, "ui/switch-click-quick.mp3", 1.0),       # click: tab 02
    (11.76 + 7.85, "ui/ui-message-pop.mp3", 0.45),
    (11.76 + 8.27, "light/sparkle-touch.mp3", 0.45),
    (11.76 + 8.69, "ui/pop.mp3", 0.45),
    (11.76 + 9.4, "transition/sweep-short.mp3", 0.5),      # punch in
    (11.76 + 11.4, "transition/sweep-fast.mp3", 0.8),      # whip out
    (23.52 + 2.7, "ui/switch-tap.mp3", 1.0),               # click: Build
    (23.52 + 2.78, "paper/paper-slide.mp3", 0.5),
    (23.52 + 4.7, "ui/switch-click-quick.mp3", 1.0),       # click: Run
    (23.52 + 4.78, "paper/paper-slide.mp3", 0.45),
    (31.36 - 0.05, "transition/transition-snap.mp3", 0.6),  # cut to the calculator
    (31.36 + 3.05, "ui/switch-tap.mp3", 0.9),               # grab the slider
    (31.36 + 5.45, "impact/impact-zoom-quick.mp3", 0.8),    # 43.3 lands
    (31.36 + 5.6, "transition/air-woosh-quick.mp3", 0.5),   # punch in
    (31.36 + 7.9, "transition/swoosh-slow.mp3", 0.45),      # pan to the value
    (43.12 + 5.42, "transition/swoosh-slow.mp3", 0.5),      # flood to lime
    (49.0 + 0.95, "text/marker-pen-line.mp3", 0.5),         # arrow draws
    (49.0 + 2.9, "ui/switch-click-quick.mp3", 1.0),        # click: Start a conversation
    (49.0 + 3.0, "transition/air-zoom-vacuum.mp3", 0.6),    # iris
    (49.0 + 4.3, "ui/pop.mp3", 0.5),                        # registered mark
]
# slider ticks: one per 5% step, as the thumb snaps
for a in range(15, 55, 5):
    CUES.append((31.36 + 3.2 + (a - 2.5 - 10) / 40 * 2.2, "counter/clock-tick-single.mp3", 3.5))
# the one riser in the film: into the mark landing at 53.09 (section E of the track)
RISER_LEN = 0.0  # filled from riser_peak.txt by the sound step
riser = (HERE / "riser_peak.txt")
riser_peak = float(riser.read_text()) if riser.exists() else 2.0
CUES.append((53.09 - riser_peak, "riser/riser-cine.mp3", 0.7))
CUES.append((53.09, "impact/bass-hit-futuristic.mp3", 0.9))

peaks = {}
pf = HERE / "peaks.txt"
if pf.exists():
    for line in pf.read_text().splitlines():
        f, p = line.split()
        peaks[f] = float(p)

durs = dict(l.split() for l in (HERE / "durations.txt").read_text().splitlines())
audio, lanes = [], []
for i, (t, f, v) in enumerate(sorted(CUES)):
    lead = peaks.get(f, 0.0) - 1 / 30  # peak lands one frame after the picture
    start = max(0.0, round(t - max(0.0, lead), 3))
    dur = round(min(float(durs[f]), TOTAL - start), 3)
    lane = next((k for k, end in enumerate(lanes) if end <= start), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = start + dur
    audio.append(f'      <audio id="sfx{i:02d}" class="clip" src="{SFX_DIR}/{f}" data-start="{start}" data-duration="{dur}" data-volume="{v}" data-track-index="{3 + lane}"></audio>')

index = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Round House: good ideas, made real</title>
    <script src="assets/gsap.min.js"></script>
    <script src="assets/rh.js"></script>
    <link rel="stylesheet" href="assets/site.css" />
    <style>
{FONTS}
      :root {{ --paper: #f7f7f2; --ink: #1d221e; --lime: #e0ed9b; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: var(--paper); }}
      /* the site's own hover/reveal transitions would fight the seeked timeline */
      #root *, #root *::before, #root *::after {{ transition: none !important; animation: none !important; }}
      .rh-ground {{ position: absolute; inset: 0; }}
      .rh-cam {{ position: absolute; left: 0; top: 0; width: 1920px; transform-origin: 0 0; }}
      .rh-page {{ width: 1920px; }}
      .rh-w, .rh-l {{ display: inline-block; }}
      .rh-cur {{ position: absolute; left: 0; top: 0; width: 66px; height: 66px; margin: -8.25px 0 0 -13.75px;
        transform-origin: 13.75px 8.25px; z-index: 100; pointer-events: none; opacity: 0; }}
      .rh-cur svg {{ width: 100%; height: 100%; overflow: visible; filter: drop-shadow(0 7px 9px rgba(20, 24, 18, 0.32)); }}
      .rh-cur path {{ fill: #ffffff; stroke: #1d221e; stroke-width: 1.35; stroke-linejoin: round; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
"""
for i, (cid, start, dur, *_rest) in enumerate(SCENES):
    index += f"""      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{start}" data-duration="{dur}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
"""
index += f"""      <audio id="music" class="clip" src="assets/audio/house-vibez.mp3" data-start="0" data-duration="{TOTAL}" data-media-start="9.915" data-volume="0.42" data-fade-in="0.3" data-fade-out="1.6" data-track-index="2"></audio>
""" + "\n".join(audio) + """
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = gsap.timeline({ paused: true });
    </script>
  </body>
</html>
"""
(FILM / "index.html").write_text(index)
print("wrote", len(SCENES), "scenes and", len(audio), "sound cues")
