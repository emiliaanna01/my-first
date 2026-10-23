#!/usr/bin/env python3
"""Round House launch film, structured like a Launchreel film (hook, overflowing inbox, reveal on the drop,
the click, floating features, stat band, orbit finale, end card). Generates compositions/*.html and index.html.
Every product surface is the site's own DOM and CSS (../../dom)."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILM = HERE.parent
DOM = FILM.parent.parent / "dom"
OUT = FILM / "compositions"

FONTS = """
@font-face{font-family:"DM Sans";font-weight:400;src:url("assets/fonts/DMSans-400-normal.woff2")}
@font-face{font-family:"DM Sans";font-weight:500;src:url("assets/fonts/DMSans-500-normal.woff2")}
@font-face{font-family:"Inter Tight Variable";font-weight:100 900;src:url("assets/fonts/InterTightVariable-100-900-normal.woff2")}
"""
CUR = """<div id="{id}" class="rh-cur" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 3 L5 19 L9 15 L12 22 L15 20.5 L11.5 14 L18 14 Z"/></svg></div>"""


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
    var ROOT = document.getElementById("{cid}-anchor").parentElement;
{js}
    restore();
    window.__timelines["{cid}"] = tl;
  }});
}})();
  </script>
</template>
"""


SHOW = {k: clean(dom(f"show{k}")) for k in (0, 1, 2)}
CALC = clean(dom("calc"))
HERO = clean(dom("hero")).replace('<a class="button dark" href="#/solutions">', '<a class="button dark" id="s2-btn" href="#/solutions">')
HERO = HERO.replace(
    "We connect business thinking, intelligent systems, and thoughtful design. So your team can work better. And your brand can stand apart.",
    'We connect <span class="hl" id="hl1">business thinking</span>, <span class="hl" id="hl2">intelligent systems</span>, and '
    '<span class="hl" id="hl3">thoughtful design</span>. <span class="hl" id="hl4">So your team can work better.</span> '
    '<span class="hl" id="hl5">And your brand can stand apart.</span>')
assert 'id="hl5"' in HERO
HEADER = dom("header")

COMMON_CSS = """
    .mini { position: absolute; left: 0; top: 0; width: 1920px; transform-origin: 0 0; }
    .mini .showcase-copy, .mini .calculator-copy { visibility: hidden; }
    .mini .showcase-panel { transform: none !important; background: transparent !important; box-shadow: none !important; border: 0 !important; }
    .mini .case-art { background: transparent !important; }
    .mini .art-index, .mini .art-category { visibility: hidden; }
    .mini .product-browser { transform: none !important; rotate: none !important; }
    .k-title { position: absolute; left: 140px; margin: 0; font-family: "Inter Tight Variable", sans-serif; font-weight: 550;
      letter-spacing: -0.055em; line-height: 1.02; white-space: nowrap; color: #1d221e; }
"""
# a helper every scene uses: put a real component (inner) of a wrapper at a frame point with a given width
FIT = """
    function fit(wrap, inner, cx, cy, w) {
      var o = RH.off(inner, wrap), s = w / inner.offsetWidth;
      return { s: s, x: cx - (o.x + inner.offsetWidth / 2) * s, y: cy - (o.y + inner.offsetHeight / 2) * s };
    }
    function put(tl, wrap, st, t, d, ease) {
      if (!d) { tl.set(wrap, { scale: st.s, x: st.x, y: st.y }, t); return; }
      tl.to(wrap, { scale: st.s, x: st.x, y: st.y, duration: d, ease: ease || "power3.inOut" }, t);
    }
"""

# =============================================================== 1 hook + the overflowing inbox (0-15)
INQ = [("2d", 150, 620), ("1d", 190, 700), ("9h", 230, 780), ("4h", 270, 860)]
FUP = [("Follow up: quote request", "Overdue 5d", 760, 600), ("Call back about pricing", "Overdue 3d", 800, 690),
       ("Send the proposal", "Due yesterday", 840, 780), ("Check in after the demo", "Overdue 1w", 880, 870)]
DOCS = ["Onboarding_v7_FINAL.pdf", "Pricing (old) (2).docx", "SOP new client - copy.pdf", "Policies_2024_draft.pdf"]
OVER = [(-6, 120, 240), (5, 560, 180), (-4, 1020, 220), (7, 1380, 160), (-8, 300, 420), (4, 720, 380), (-3, 1180, 420), (6, 1540, 360)]
s1_body = """    <div id="s1-ground" class="rh-ground" style="background:#f7f7f2"></div>
    <div id="s1-m0" class="mini" data-layout-allow-overlap data-layout-allow-occlusion>%s</div>
    <div id="s1-m1" class="mini" data-layout-allow-overlap data-layout-allow-occlusion>%s</div>
    <div id="s1-m2" class="mini" data-layout-allow-overlap data-layout-allow-occlusion>%s</div>
    <div id="s1-m3" class="mini" data-layout-allow-overlap data-layout-allow-occlusion>%s</div>
    <h1 id="s1-a" class="k-title" style="top:330px;font-size:230px">Good ideas</h1>
    <h2 id="s1-b" class="k-title" style="top:580px;font-size:84px;color:#7d8c6a">are everywhere.</h2>
    <h1 id="s1-c" data-layout-allow-overlap data-layout-allow-occlusion class="k-title" style="top:360px;font-size:170px">Making them real?</h1>
""" % (SHOW[0], SHOW[1], SHOW[2], CALC)
s1_body += "".join(
    f'    <div data-layout-allow-overlap data-layout-allow-occlusion class="ib-card ib-inq" id="s1-i{k}" style="left:{x}px;top:{y - 470}px"><i>W</i><div><b>New inquiry</b><small>Website form</small></div><span>No reply &#183; {a}</span></div>\n'
    for k, (a, x, y) in enumerate(INQ))
s1_body += "".join(
    f'    <div data-layout-allow-overlap data-layout-allow-occlusion class="ib-card ib-fup" id="s1-f{k}" style="left:{x}px;top:{y - 470}px"><i>&#8635;</i><div><b>{t}</b><small>Reminder</small></div><span>{d}</span></div>\n'
    for k, (t, d, x, y) in enumerate(FUP))
s1_body += """    <div class="ib-search" id="s1-q"><i>&#9906;</i>Where&#8217;s the refund policy?<span id="s1-q0">0 results</span></div>
""" + "".join(f'    <div data-layout-allow-overlap data-layout-allow-occlusion class="ib-file" id="s1-d{k}" style="top:{250 + k * 92}px"><i>PDF</i>{n}</div>\n' for k, n in enumerate(DOCS)) + """
    <div class="ib-week" id="s1-week">""" + "".join(
    f'<div class="ib-day"><b>{d}</b>' + "".join(f'<i class="adm" id="s1-w{j}{k}"></i>' for k in range(4)) + '</div>' for j, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"])) + """</div>
    <div class="ib-count" id="s1-cnt"><span id="s1-cntv">12</span> unread</div>
""" + "".join(
    f'    <div data-layout-allow-overlap data-layout-allow-occlusion class="ib-card ib-inq ib-over" id="s1-o{k}" style="left:{x}px;top:{y}px"><i>W</i><div><b>New inquiry</b><small>Website form</small></div><span>No reply</span></div>\n'
    for k, (r, x, y) in enumerate(OVER)) + """    <div id="s1-dot"></div>
"""
s1_css = COMMON_CSS + """
    .ib-card { position: absolute; width: 520px; display: flex; align-items: center; gap: 16px; padding: 20px 22px; background: #fff;
      border-radius: 20px; box-shadow: 0 16px 34px rgba(20,24,18,.14), 0 0 0 1px rgba(29,34,30,.05); font-family: "DM Sans", sans-serif; box-sizing: border-box; }
    .ib-card i { flex: none; width: 48px; height: 48px; border-radius: 50%; background: #e0ed9b; font: 500 22px/48px "DM Sans"; text-align: center; font-style: normal; color: #1d221e; }
    .ib-fup i { background: #f9e9d7; }
    .ib-card b { display: block; font-weight: 500; font-size: 24px; color: #1d221e; white-space: nowrap; }
    .ib-card small { font-size: 17px; color: #7a7f73; }
    .ib-card span { margin-left: auto; font-size: 17px; font-weight: 500; padding: 6px 12px; border-radius: 999px; background: #ec644f; color: #fff; white-space: nowrap; }
    .ib-fup span { background: #b52b18; }
    .ib-search { position: absolute; left: 1400px; top: 140px; width: 460px; box-sizing: border-box; padding: 18px 22px; background: #fff; border-radius: 16px;
      font: 400 22px "DM Sans", sans-serif; color: #1d221e; box-shadow: 0 16px 34px rgba(20,24,18,.14); display: flex; gap: 12px; align-items: center; white-space: nowrap; }
    .ib-search i { font-style: normal; color: #7a7f73; }
    .ib-search span { margin-left: auto; font-size: 16px; color: #b52b18; }
    .ib-file { position: absolute; left: 1430px; width: 420px; box-sizing: border-box; display: flex; align-items: center; gap: 14px; padding: 16px 18px;
      background: #fff; border-radius: 14px; font: 400 21px "DM Sans", sans-serif; color: #2b322b; box-shadow: 0 12px 26px rgba(20,24,18,.12); white-space: nowrap; }
    .ib-file i { font: 500 13px/34px "DM Sans"; font-style: normal; width: 44px; height: 34px; border-radius: 8px; background: #20271f; color: #e0ed9b; text-align: center; }
    .ib-week { position: absolute; left: 1330px; top: 640px; display: flex; gap: 10px; padding: 22px; background: #fff; border-radius: 20px; box-shadow: 0 16px 34px rgba(20,24,18,.12); }
    .ib-day { width: 88px; display: flex; flex-direction: column; gap: 8px; }
    .ib-day b { font: 500 18px "DM Sans"; color: #1d221e; }
    .ib-day .adm { height: 40px; border-radius: 8px; background: #d9dbd2; }
    .ib-count { position: absolute; right: 70px; top: 60px; font: 500 26px "DM Sans", sans-serif; color: #fff; background: #ec644f; padding: 10px 20px; border-radius: 999px; }
    #s1-dot { position: absolute; left: 948px; top: 528px; width: 24px; height: 24px; border-radius: 50%; background: #e0ed9b; box-shadow: inset 0 0 0 4px #6a813e; }
"""
s1_js = FIT + """
    // live product glimpses float around the opening line (the site's own UI, small)
    var minis = [["s1-m0", ".product-browser", 1490, 240, 560], ["s1-m1", ".product-browser", 1530, 790, 520],
                 ["s1-m2", ".identity-card", 330, 850, 230], ["s1-m3", ".calculator", 300, 235, 300]];
    var mst = minis.map(function (m) { var w = $(m[0]); return fit(w, w.querySelector(m[1]), m[2], m[3], m[4]); });
    minis.forEach(function (m, i) {
      var w = $(m[0]), st = mst[i];
      put(tl, w, st, 0);
      tl.fromTo(w, { opacity: i === 0 ? 1 : 0, rotation: 0 }, { opacity: 1, duration: 0.3 }, i === 0 ? 0 : 0.25 * i);
      tl.fromTo(w, { y: st.y + (i === 0 ? 0 : 40) }, { y: st.y, duration: 0.6, ease: "expo.out" }, i === 0 ? 0 : 0.25 * i);
      // "messy": they tip and slide in on each other, then leave for the pile-up
      tl.to(w, { rotation: [-7, 6, -5, 8][i], x: st.x + [-120, -160, 140, 160][i], y: st.y + [80, -60, -90, 60][i], duration: 0.7, ease: "power3.inOut" }, 3.9 + i * 0.05);
      tl.to(w, { opacity: 0, filter: "blur(8px)", duration: 0.3, ease: "power2.in" }, 5.1 + i * 0.04);
    });
    tl.fromTo($("s1-a"), { scale: 1.04 }, { scale: 1, duration: 0.9, ease: "expo.out", transformOrigin: "0% 50%" }, 0);
    tl.fromTo($("s1-b"), { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "expo.out" }, 1.0);
    tl.to([$("s1-a"), $("s1-b")], { opacity: 0, filter: "blur(10px)", duration: 0.16, ease: "power2.in" }, 2.3);
    RH.words($("s1-c")).forEach(function (w, i) {
      tl.fromTo(w, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out" }, 2.45 + i * 0.12);
    });
    tl.to($("s1-c"), { rotation: -3, y: 20, duration: 0.5, ease: "back.out(2)" }, 3.95);
    tl.to($("s1-c"), { opacity: 0, filter: "blur(10px)", duration: 0.2, ease: "power2.in" }, 5.2);
    // the inbox overflows, one kind of mess per line of voice
    function pop(el, t, rot) { tl.fromTo(el, { opacity: 0, scale: 0.7, y: -30, rotation: 0 }, { opacity: 1, scale: 1, y: 0, rotation: rot || 0, duration: 0.45, ease: "back.out(1.9)" }, t); }
    [0, 1, 2, 3].forEach(function (k) { pop($("s1-i" + k), 5.65 + k * 0.28, [-2, 1.5, -1, 2][k]); });
    [0, 1, 2, 3].forEach(function (k) { pop($("s1-f" + k), 7.65 + k * 0.28, [1.5, -2, 2, -1][k]); });
    pop($("s1-q"), 9.6, 0);
    [0, 1, 2, 3].forEach(function (k) { pop($("s1-d" + k), 10.0 + k * 0.25, [-1.5, 1, -2, 1.5][k]); });
    tl.fromTo($("s1-q0"), { opacity: 0 }, { opacity: 1, duration: 0.2 }, 11.0);
    pop($("s1-week"), 12.55, -1);
    var blocks = [];
    for (var j = 0; j < 5; j++) for (var k = 0; k < 4; k++) blocks.push($("s1-w" + j + k));
    blocks.forEach(function (b, i) { tl.fromTo(b, { backgroundColor: "#eeeee8", scaleX: 0.3 }, { backgroundColor: "#b9bdb0", scaleX: 1, duration: 0.25, ease: "power3.out" }, 12.85 + i * 0.06); });
    pop($("s1-cnt"), 5.8, 0);
    var cnt = $("s1-cntv");
    RH.drive(tl, 15, function (T) { cnt.textContent = String(Math.round(12 + Math.max(0, Math.min(1, (T - 5.8) / 8.2)) * 35)); });
    for (var o = 0; o < 8; o++) pop($("s1-o" + o), 13.1 + o * 0.11, [-6, 5, -4, 7, -8, 4, -3, 6][o]);
    // silence before the drop: everything is pulled into one lime dot
    var all = Array.prototype.slice.call(ROOT.querySelectorAll(".ib-card,.ib-search,.ib-file,.ib-week,.ib-count"));
    all.forEach(function (el, i) {
      var cx = el.offsetLeft + el.offsetWidth / 2, cy = el.offsetTop + el.offsetHeight / 2;
      tl.to(el, { x: 960 - cx, y: 540 - cy, scale: 0.08, opacity: 0, rotation: 0, duration: 0.5, ease: "power3.in" }, 14.05 + (i % 6) * 0.025);
    });
    tl.fromTo($("s1-dot"), { scale: 0 }, { scale: 1, duration: 0.3, ease: "back.out(3)" }, 14.45);
"""

# =============================================================== 2 reveal on the drop + the click (15-28.5)
s2_body = f"""    <div id="s2-ground" class="rh-ground" style="background:#f7f7f2"></div>
    <div id="s2-cam" class="rh-cam"><div class="rh-page"><main>{HEADER}{HERO}</main></div>
      <video id="s2-sph" class="clip" src="assets/spheres.webm" data-start="0" data-duration="10" muted playsinline></video>
    </div>
    <div id="s2-flood"></div>
    <div id="s2-lock"><span id="s2-wm">roundhouse<span id="s2-stop">.</span></span><i id="s2-dot"></i></div>
    {CUR.format(id="s2-cur")}
"""
s2_css = """
    #s2-sph { position: absolute; object-fit: contain; z-index: 3; }
    #s2-cam .sculpture-stage canvas, #s2-cam .sculpture-fallback { visibility: hidden; }
    #s2-cam .agency-hero h1 em:after { transform: scaleX(var(--hl, 1)); transform-origin: left center; }
    #s2-btn { position: relative; z-index: 20; }
    #s2-cam .hl { background-image: linear-gradient(#e0ed9b, #e0ed9b); background-repeat: no-repeat; background-position: 0 85%;
      background-size: var(--w, 0%) 42%; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
    #s2-flood { position: absolute; left: 948px; top: 528px; width: 24px; height: 24px; border-radius: 50%; background: #e0ed9b; z-index: 30; }
    #s2-lock { position: absolute; left: 0; right: 0; top: 420px; text-align: center; z-index: 31; font-family: "Inter Tight Variable", sans-serif;
      font-weight: 720; font-size: 220px; letter-spacing: -0.055em; line-height: 1; color: #1d221e; }
    #s2-wm { position: relative; display: inline-block; }
    #s2-stop { visibility: hidden; }
    #s2-dot { position: absolute; border-radius: 50%; background: #1d221e; }
"""
s2_js = """
    var cam = $("s2-cam"), cur = $("s2-cur"), vid = $("s2-sph"), btn = $("s2-btn"), lock = $("s2-lock");
    var canvas = cam.querySelector(".sculpture-stage canvas"), hero = cam.querySelector("section.hero"), h1 = cam.querySelector(".hero h1");
    var cv = RH.off(canvas, cam);
    vid.style.left = cv.x + "px"; vid.style.top = cv.y + "px"; vid.style.width = canvas.offsetWidth + "px"; vid.style.height = canvas.offsetHeight + "px";
    var bottom = RH.off(hero, cam).y + hero.offsetHeight, sFull = Math.min(1, 1080 / bottom);
    var full = { s: sFull, x: (1920 - 1920 * sFull) / 2, y: 0 };
    // the drop: the dot from the pile-up floods the frame lime, the wordmark slams in
    tl.fromTo($("s2-flood"), { scale: 1 }, { scale: 120, duration: 0.42, ease: "power3.in" }, 0.0);
    var stop = $("s2-stop"), dot = $("s2-dot"), so = RH.off(stop, lock), d = stop.offsetWidth * 0.8;
    dot.style.width = d + "px"; dot.style.height = d + "px";
    dot.style.left = (so.x + stop.offsetWidth * 0.5 - d / 2) + "px"; dot.style.top = (so.y + stop.offsetHeight * 0.79 - d) + "px";
    tl.fromTo($("s2-wm"), { opacity: 0, scale: 1.25, filter: "blur(14px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }, 0.36);
    tl.fromTo(dot, { scale: 0 }, { scale: 1, duration: 0.4, ease: "back.out(3)" }, 0.55);
    // then the studio's own page rises out of the lime
    tl.to(lock, { y: -300, opacity: 0, filter: "blur(10px)", duration: 0.35, ease: "power3.in" }, 1.5);
    tl.to($("s2-flood"), { opacity: 0, duration: 0.3, ease: "power2.inOut" }, 1.82);
    var titleCam = RH.aim(RH.pt(h1, cam), 1.3 * sFull, 780, 560);
    RH.cam(tl, cam, { s: titleCam.s, x: titleCam.x, y: titleCam.y + 500 }, 0, 0);
    RH.cam(tl, cam, titleCam, 1.95, 1.0, "expo.out");
    tl.fromTo(cam, { opacity: 0 }, { opacity: 1, duration: 0.25 }, 1.95);
    tl.fromTo(vid, { opacity: 0, y: 80 }, { opacity: 1, y: 0, duration: 1.0, ease: "expo.out" }, 2.2);
    tl.fromTo(h1.querySelector("em"), { "--hl": 0 }, { "--hl": 1, duration: 0.45, ease: "power3.out" }, 2.7);
    // what the studio connects, highlighted as it is said
    var para = cam.querySelector(".hero-description");
    var paraCam = RH.aim(RH.pt(para, cam), Math.min(2.6, 1500 / para.offsetWidth), 960, 540);
    RH.cam(tl, cam, paraCam, 3.15, 0.8);
    [["hl1", 3.6], ["hl2", 5.2], ["hl3", 6.9], ["hl4", 9.3], ["hl5", 11.0]].forEach(function (h) {
      tl.fromTo($(h[0]), { "--w": "0%" }, { "--w": "100%", duration: 0.5, ease: "power2.out" }, h[1]);
    });
    RH.cam(tl, cam, full, 8.1, 0.9);
    // the click
    var b = RH.frame(RH.pt(btn, cam), full);
    tl.set(cur, { x: 2010, y: 1180, opacity: 1 }, 0);
    RH.move(tl, cur, { x: b.x + 18, y: b.y + 6 }, 10.6, 0.85);
    RH.click(tl, cur, 11.9, btn);
    tl.to(cur, { opacity: 0, duration: 0.12 }, 12.2);
    tl.to(btn, { scale: 44, duration: 0.6, ease: "power3.in" }, 12.25);
"""

# =============================================================== 3 floating features (28.5-45)
s3_body = f"""    <div id="s3-ground" class="rh-ground" style="background:#1d221e"></div>
    <div id="s3-f0" class="mini feat">{SHOW[0]}</div>
    <div id="s3-f1" class="mini feat">{SHOW[1]}</div>
    <div id="s3-f2" class="mini feat" data-layout-allow-overlap data-layout-allow-occlusion>{SHOW[2]}</div>
    <div id="s3-lab">
      <div class="lab" id="s3-l0"><span>01 / REVENUE</span><b>Faster lead response.</b></div>
      <div class="lab" id="s3-l1"><span>02 / OPERATIONS</span><b>Internal AI assistants.</b></div>
      <div class="lab" id="s3-l2"><span>03 / BRAND &amp; DIGITAL</span><b>A brand that feels like you.</b></div>
    </div>
"""
s3_css = COMMON_CSS + """
    #s3-lab { position: absolute; left: 140px; top: 80px; height: 160px; width: 1600px; }
    .lab { position: absolute; left: 0; top: 0; }
    .lab span { display: block; font: 500 22px "DM Sans", sans-serif; letter-spacing: 0.08em; color: #6a813e; }
    .lab b { display: block; margin-top: 10px; font: 550 92px/1 "Inter Tight Variable", sans-serif; letter-spacing: -0.055em; color: #1d221e; white-space: nowrap; }
"""
s3_js = FIT + """
    var F = [$("s3-f0"), $("s3-f1"), $("s3-f2")];
    var inner = [F[0].querySelector(".product-browser"), F[1].querySelector(".product-browser"), F[2].querySelector(".case-art")];
    // three depths of the fan: front centre, back left, back right
    var slot = { front: [960, 650, 1000], left: [235, 650, 430], right: [1685, 650, 430] };
    function st(i, where) { var s = slot[where]; return fit(F[i], inner[i], s[0], s[1], s[2]); }
    var order = [["front", "right", "left"], ["left", "front", "right"], ["right", "left", "front"]];
    var times = [0, 6.55, 11.35];
    tl.fromTo($("s3-ground"), { backgroundColor: "#1d221e" }, { backgroundColor: "#e1e8cd", duration: 0.35, ease: "power2.inOut" }, 0.0);
    order.forEach(function (o, step) {
      var t = times[step];
      F.forEach(function (f, i) {
        var where = o[i], front = where === "front", target = st(i, where);
        if (step === 0) { put(tl, f, { s: target.s * 0.8, x: target.x + (front ? 0 : (where === "left" ? -300 : 300)), y: target.y + 120 }, 0); }
        put(tl, f, target, step === 0 ? 0.15 : t, step === 0 ? 0.9 : 0.75, step === 0 ? "expo.out" : "power3.inOut");
        tl.to(f, { opacity: front ? 1 : 0.5, filter: front ? "blur(0px)" : "blur(4px)", zIndex: front ? 3 : 1, duration: step === 0 ? 0.5 : 0.6 }, step === 0 ? 0.15 : t);
      });
      var lab = $("s3-l" + step);
      tl.fromTo(lab, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }, t + 0.25);
      if (step < 2) tl.to(lab, { opacity: 0, y: -16, duration: 0.25, ease: "power2.in" }, times[step + 1] - 0.05);
    });
    // lead: the journey lights up on "captured, qualified, booked"
    var steps = F[0].querySelectorAll(".pipeline > div"), tags = F[0].querySelectorAll(".pipeline-tag");
    tl.set(steps, { opacity: 0.35 }, 0); tl.set(tags, { opacity: 0, scale: 0.6 }, 0);
    [2.85, 3.85, 4.6].forEach(function (t, k) {
      tl.to(steps[k], { opacity: 1, duration: 0.2 }, t);
      tl.to(tags[k], { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2.4)" }, t + 0.1);
    });
    // assistant: the question lands, then an answer with its sources
    var q = F[1].querySelector(".question-bubble"), a = F[1].querySelector(".answer-card"), rows = F[1].querySelectorAll(".answer-card > div");
    tl.set([q, a], { opacity: 0 }, 0); tl.set(rows, { opacity: 0, x: -10 }, 0);
    tl.fromTo(q, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.4, ease: "back.out(1.8)" }, 7.4);
    tl.fromTo(a, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.45, ease: "back.out(1.6)" }, 8.3);
    rows.forEach(function (r, i) { tl.to(r, { opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }, 8.9 + i * 0.35); });
    // brand: a slow push into the identity card
    var push = st(2, "front"); push = { s: push.s * 1.12, x: push.x - (push.s * 0.12) * (RH.off(inner[2], F[2]).x + inner[2].offsetWidth / 2), y: push.y - (push.s * 0.12) * (RH.off(inner[2], F[2]).y + inner[2].offsetHeight / 2) };
    put(tl, F[2], push, 12.2, 3.6, "power1.inOut");
    tl.to(F, { opacity: 0, filter: "blur(10px)", duration: 0.3, ease: "power2.in" }, 16.1);
    tl.to($("s3-l2"), { opacity: 0, duration: 0.2 }, 16.1);
"""

# =============================================================== 4 stat band (45-52.5)
s4_body = """    <div class="rh-ground" style="background:#f7f7f2"></div>
    <div id="s4-band">
      <div class="s4-left"><span id="s4-a">20 hrs a week of busywork</span><span id="s4-b">&#247; 2</span></div>
      <div class="s4-right"><b id="s4-n">0.0</b><span>hours back / month</span>
        <div class="s4-bars">""" + "".join(f'<i id="s4-g{k}"></i>' for k in range(28)) + """</div></div>
    </div>
    <p id="s4-foot">A planning estimate from the Round House calculator: 20 hours a week &#215; 50% &#215; 4.33 weeks.</p>
"""
s4_css = """
    #s4-band { position: absolute; left: 0; right: 0; top: 250px; height: 520px; background: #20271f; transform-origin: 50% 50%; }
    .s4-left { position: absolute; left: 140px; top: 170px; }
    #s4-a { display: block; font: 550 64px "Inter Tight Variable", sans-serif; letter-spacing: -0.04em; color: #f3f5ea; white-space: nowrap; }
    #s4-b { display: inline-block; margin-top: 26px; font: 500 46px "DM Sans", sans-serif; color: #1d221e; background: #e0ed9b; padding: 10px 26px; border-radius: 999px; }
    .s4-right { position: absolute; right: 140px; top: 70px; width: 700px; }
    #s4-n { display: block; font: 550 280px/1 "Inter Tight Variable", sans-serif; letter-spacing: -0.06em; color: #e0ed9b; }
    .s4-right > span { display: block; margin-top: 4px; font: 400 34px "DM Sans", sans-serif; color: #cad6bd; }
    .s4-bars { display: flex; gap: 6px; height: 60px; margin-top: 30px; }
    .s4-bars i { flex: 1; border-radius: 4px; background: #485140; }
    #s4-foot { position: absolute; left: 140px; top: 810px; margin: 0; font: 400 24px "DM Sans", sans-serif; color: #6b7064; }
"""
s4_js = """
    tl.fromTo($("s4-band"), { scaleY: 0 }, { scaleY: 1, duration: 0.45, ease: "expo.out" }, 0.0);
    tl.fromTo($("s4-a"), { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.5, ease: "expo.out" }, 0.45);
    tl.fromTo($("s4-b"), { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2.6)" }, 2.15);
    tl.to($("s4-a"), { opacity: 0.45, duration: 0.3 }, 2.3);
    var n = $("s4-n"), bars = [];
    for (var k = 0; k < 28; k++) bars.push($("s4-g" + k));
    RH.drive(tl, 7.5, function (T) {
      var p = Math.max(0, Math.min(1, (T - 2.6) / 1.8)), e = 1 - Math.pow(1 - p, 3);
      n.textContent = (Math.round(433 * e) / 10).toFixed(1);
      bars.forEach(function (b, i) { b.style.background = i < Math.round(14 * e) ? "#e0ed9b" : "#485140"; });
    });
    tl.fromTo(n, { scale: 1 }, { scale: 1.06, duration: 0.12, yoyo: true, repeat: 1, transformOrigin: "0% 50%" }, 4.4);
    tl.fromTo($("s4-foot"), { opacity: 0 }, { opacity: 1, duration: 0.4 }, 1.0);
    tl.to([$("s4-band"), $("s4-foot")], { opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power2.in" }, 7.2);
"""

# =============================================================== 5 orbit finale (52.5-60)
s5_body = """    <div class="rh-ground" style="background:#f7f7f2"></div>
    <video id="s5-sph" class="clip" src="assets/spheres.webm" data-start="0" data-duration="7.5" data-media-start="2" muted playsinline></video>
    <h2 id="s5-a" class="k-title" style="top:90px;font-size:78px">No six-service shopping list.</h2>
    <h2 id="s5-b" class="k-title" style="top:180px;font-size:78px;color:#7d8c6a">Just a clear path.</h2>
    <svg id="s5-path" viewBox="0 0 1920 1080"><path id="s5-line" d="M 560 930 L 1360 930"/></svg>
    <span class="pill" id="s5-p0">Diagnose</span><span class="pill" id="s5-p1">Build</span><span class="pill" id="s5-p2">Run</span>
"""
s5_css = COMMON_CSS + """
    #s5-sph { position: absolute; left: 620px; top: 300px; width: 680px; height: 558px; object-fit: contain; }
    #s5-path { position: absolute; inset: 0; width: 1920px; height: 1080px; }
    #s5-line { fill: none; stroke: #6a813e; stroke-width: 4; stroke-linecap: round; stroke-dasharray: 800; }
    .pill { position: absolute; left: 0; top: 0; font: 500 44px "DM Sans", sans-serif; color: #f3f5ea; background: #1d221e;
      padding: 18px 36px; border-radius: 999px; white-space: nowrap; }
"""
s5_js = """
    var P = [$("s5-p0"), $("s5-p1"), $("s5-p2")], line = $("s5-line");
    var row = [560, 960, 1360], lit = [3.95, 4.55, 5.15];
    RH.drive(tl, 7.5, function (T) {
      P.forEach(function (p, k) {
        var a = (k / 3) * Math.PI * 2 + T * 0.9, ox = 960 + Math.cos(a) * 640, oy = 600 + Math.sin(a) * 170;
        var depth = (Math.sin(a) + 1) / 2;
        var b = Math.max(0, Math.min(1, (T - lit[k]) / 0.55)), e = b * b * (3 - 2 * b);
        var x = ox + (row[k] - ox) * e, y = oy + (930 - oy) * e, s = (0.8 + 0.3 * depth) * (1 - e) + 1.1 * e;
        p.style.transform = "translate(" + (x - p.offsetWidth / 2) + "px," + (y - p.offsetHeight / 2) + "px) scale(" + s + ")";
        p.style.zIndex = String(depth > 0.5 || e > 0.5 ? 5 : 1);
        p.style.background = e > 0.5 ? "#e0ed9b" : "#1d221e"; p.style.color = e > 0.5 ? "#1d221e" : "#f3f5ea";
      });
      line.style.strokeDashoffset = String(800 * (1 - Math.max(0, Math.min(1, (T - 5.9) / 0.6))));
    });
    tl.fromTo($("s5-sph"), { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: 0.7, ease: "expo.out" }, 0.0);
    RH.words($("s5-a")).forEach(function (w, i) { tl.fromTo(w, { color: "#dcdfd3" }, { color: "#1d221e", duration: 0.2 }, 0.35 + i * 0.09); });
    RH.words($("s5-b")).forEach(function (w, i) { tl.fromTo(w, { color: "#e8eadf" }, { color: "#7d8c6a", duration: 0.2 }, 1.95 + i * 0.09); });
    tl.to([$("s5-a"), $("s5-b"), $("s5-sph")].concat(P), { opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power2.in" }, 7.2);
    tl.to($("s5-path"), { opacity: 0, duration: 0.25 }, 7.2);
"""

# =============================================================== 6 end card (60-67.5)
s6_body = f"""    <div class="rh-ground" style="background:#e5edcc"></div>
    <div id="s6-lockup">
      <div id="s6-wm" class="s6-wm">roundhouse<span id="s6-stop">.</span><span id="s6-reg">&#174;</span></div>
      <div id="s6-dot"></div>
      <p id="s6-tag">Good ideas. Made real.</p>
      <span id="s6-go">Let&#8217;s talk &#8599;</span>
    </div>
    {CUR.format(id="s6-cur")}
"""
s6_css = """
    #s6-lockup { position: absolute; left: 0; right: 0; top: 300px; display: flex; flex-direction: column; align-items: center; }
    .s6-wm { position: relative; font-family: "Inter Tight Variable", sans-serif; font-weight: 720; font-size: 200px; letter-spacing: -0.055em; line-height: 1; color: #1d221e; white-space: nowrap; }
    #s6-stop { visibility: hidden; }
    #s6-reg { font-family: "DM Sans", sans-serif; font-size: 40px; letter-spacing: 0; vertical-align: top; display: inline-block; margin: 18px 0 0 10px; }
    #s6-dot { position: absolute; border-radius: 50%; background: #e0ed9b; box-shadow: inset 0 0 0 5px #6a813e; }
    #s6-tag { margin: 40px 0 0; font-family: "Inter Tight Variable", sans-serif; font-weight: 550; font-size: 56px; letter-spacing: -0.04em; color: #4f5c42; }
    #s6-go { margin-top: 48px; font-family: "DM Sans", sans-serif; font-weight: 500; font-size: 32px; color: #f7f7f2; background: #1d221e; padding: 24px 48px; border-radius: 999px; }
"""
s6_js = """
    var wm = $("s6-wm"), stop = $("s6-stop"), dot = $("s6-dot"), lock = $("s6-lockup"), cur = $("s6-cur"), go = $("s6-go");
    var so = RH.off(stop, lock), d = stop.offsetWidth * 0.8;
    dot.style.width = d + "px"; dot.style.height = d + "px";
    dot.style.left = (so.x + stop.offsetWidth * 0.5 - d / 2) + "px"; dot.style.top = (so.y + stop.offsetHeight * 0.79 - d) + "px";
    tl.fromTo(wm, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "power3.out" }, 0.25);
    tl.fromTo(dot, { y: -760 }, { y: 0, duration: 0.36, ease: "power3.in" }, 0.39);
    tl.to(dot, { scaleX: 1.25, scaleY: 0.72, duration: 0.07, transformOrigin: "50% 100%" }, 0.75);
    tl.to(dot, { scaleX: 1, scaleY: 1, duration: 0.4, ease: "back.out(3)" }, 0.82);
    tl.fromTo($("s6-reg"), { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }, 1.0);
    RH.words($("s6-tag")).forEach(function (w, i) {
      tl.fromTo(w, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out" }, 1.5 + i * 0.08);
    });
    tl.fromTo(go, { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, 2.6);
    var gp = RH.pt(go, ROOT, 0.5, 0.55);
    tl.set(cur, { x: 2000, y: 1160, opacity: 1 }, 0);
    RH.move(tl, cur, { x: gp.x + 20, y: gp.y + 8 }, 3.0, 0.8);
    RH.click(tl, cur, 4.15, go);
    tl.to(go, { backgroundColor: "#6a813e", duration: 0.15 }, 4.18);
"""

DUR = {"s1": 15.0, "s2": 13.5, "s3": 16.5, "s4": 7.5, "s5": 7.5, "s6": 7.5}
JS = {"s1": (s1_css, s1_body, s1_js), "s2": (s2_css, s2_body, s2_js), "s3": (s3_css, s3_body, s3_js),
      "s4": (s4_css, s4_body, s4_js), "s5": (s5_css, s5_body, s5_js), "s6": (s6_css, s6_body, s6_js)}
ST, t = {}, 0.0
for k in DUR:
    ST[k] = round(t, 3); t += DUR[k]
TOTAL = round(t, 3)
for k in DUR:
    css, body, js = JS[k]
    (OUT / f"{k}.html").write_text(scene(k, css, body, js))

# =============================================================== sound
VO = [("A1", 0.3), ("A2", 2.4), ("B1", 5.6), ("B2", 7.6), ("B3", 9.6), ("B4", 12.6), ("C1", 15.6), ("D1", 24.2),
      ("E1", 28.8), ("E2", 35.4), ("E3", 40.2), ("F1", 45.4), ("G1", 52.8), ("G2", 56.4), ("H1", 60.6)]
vo_d = dict(l.split() for l in (HERE / "vo_durations.txt").read_text().splitlines())
MUSIC_START, MUSIC_VOL = 2.985, 0.22   # track drop (12.015 s) lands on film 15.0, the reveal
# duck the bed under every line: full between lines, 0.35 while the voice speaks
pts, ramp = [{"t": 0, "v": 1}], 0.18
for lid, s in VO:
    a, b = s - MUSIC_START, s + float(vo_d[lid]) - MUSIC_START
    if b <= 0:
        continue
    a = max(0.0, a)
    pts += [{"t": round(max(0, a - ramp), 3), "v": 1}, {"t": round(a, 3), "v": 0.35},
            {"t": round(b, 3), "v": 0.35}, {"t": round(b + ramp * 2, 3), "v": 1}]
pts.sort(key=lambda p: p["t"])
clean_pts = []
for p in pts:  # drop overlapping ramps where two lines nearly touch
    if clean_pts and p["t"] <= clean_pts[-1]["t"]:
        clean_pts[-1] = {"t": clean_pts[-1]["t"], "v": min(clean_pts[-1]["v"], p["v"])}
        continue
    clean_pts.append(p)
automation = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": clean_pts}]}).replace('"', "&quot;")

SFX = "assets/audio/sfx"
C = [  # (film time, file, volume)
    (0.25, "ui/pop.mp3", 0.2), (0.5, "ui/ui-message-pop.mp3", 0.18), (0.75, "ui/pop-electric.mp3", 0.15),
    (2.3, "transition/sweep-short.mp3", 0.2), (3.9, "transition/swoosh-quick.mp3", 0.3),
    (5.65, "ui/pop.mp3", 0.3), (6.2, "ui/pop.mp3", 0.22), (7.65, "ui/ui-message-pop.mp3", 0.28), (8.2, "ui/ui-message-pop.mp3", 0.2),
    (9.6, "paper/paper-slide.mp3", 0.3), (10.25, "ui/pop-electric.mp3", 0.2),
    (12.85, "text/typewriter-hit-soft.mp3", 0.7), (13.25, "text/typewriter-hit-soft.mp3", 0.6), (13.65, "text/typewriter-hit-soft.mp3", 0.6),
    (13.1, "transition/swoosh-slow.mp3", 0.25), (14.05, "transition/air-zoom-vacuum.mp3", 0.45),
    (15.0, "impact/bass-hit-futuristic.mp3", 0.5), (15.36, "ui/pop.mp3", 0.3),
    (16.5, "transition/air-woosh-quick.mp3", 0.3),
    (18.6, "text/marker-pen-line.mp3", 0.22), (20.2, "text/marker-pen-line.mp3", 0.2), (21.9, "text/marker-pen-line.mp3", 0.22),
    (26.9, "ui/switch-click-quick.mp3", 0.6), (27.25, "transition/air-woosh-quick.mp3", 0.35),
    (28.65, "transition/swoosh-quick.mp3", 0.25),
    (31.35, "ui/pop.mp3", 0.25), (32.35, "ui/ui-message-pop.mp3", 0.25), (33.1, "ui/pop-electric.mp3", 0.2),
    (35.05, "transition/swoosh-quick.mp3", 0.25), (36.8, "ui/ui-message-pop.mp3", 0.25), (37.4, "light/sparkle-touch.mp3", 0.2),
    (39.85, "transition/swoosh-quick.mp3", 0.25),
    (45.0, "transition/swoosh-slow.mp3", 0.25), (47.15, "ui/pop.mp3", 0.3), (49.4, "impact/impact-zoom-quick.mp3", 0.3),
    (56.45, "ui/pop.mp3", 0.25), (57.05, "ui/pop.mp3", 0.22), (57.65, "ui/pop-electric.mp3", 0.2), (58.4, "text/marker-pen-line.mp3", 0.2),
    (60.75, "impact/bass-hit-futuristic.mp3", 0.4), (61.0, "ui/pop.mp3", 0.25), (64.15, "ui/switch-click-quick.mp3", 0.55),
]
riser_peak = float((HERE / "riser_peak.txt").read_text())
C.append((15.0 - riser_peak, "riser/riser-cine.mp3", 0.3))
peaks = {f: float(p) for f, p in (l.split()[:2] for l in (HERE / "peaks.txt").read_text().splitlines())}
durs = dict(l.split()[:2] for l in (HERE / "durations.txt").read_text().splitlines())
audio, lanes = [], []
for i, (tt, f, v) in enumerate(sorted(C)):
    st = max(0.0, round(tt - max(0.0, peaks.get(f, 0.0) - 1 / 30), 3))
    d = round(min(float(durs[f]), TOTAL - st), 3)
    lane = next((k for k, end in enumerate(lanes) if end <= st), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = st + d
    audio.append(f'      <audio id="sfx{i:02d}" class="clip" src="{SFX}/{f}" data-start="{st}" data-duration="{d}" data-volume="{v}" data-track-index="{4 + lane}"></audio>')
voice = "".join(
    f'      <audio id="vo-{lid}" class="clip" src="assets/audio/vo/{lid}.wav" data-start="{s}" data-duration="{vo_d[lid]}" data-volume="1" data-track-index="3"></audio>\n'
    for lid, s in VO)

index = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Round House: launch film</title>
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
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
""" + "".join(
    f'      <div id="{k}" data-composition-id="{k}" data-composition-src="compositions/{k}.html" data-start="{ST[k]}" data-duration="{DUR[k]}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>\n'
    for k in DUR) + f"""      <audio id="music" class="clip" src="assets/audio/fresh-fit.mp3" data-start="{MUSIC_START}" data-duration="{round(TOTAL - MUSIC_START, 3)}" data-volume="{MUSIC_VOL}" data-fade-in="0.6" data-fade-out="2.6" data-automation="{automation}" data-track-index="2"></audio>
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
print("scenes", len(DUR), "total", TOTAL, "cues", len(audio), "duck points", len(clean_pts))
