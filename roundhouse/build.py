"""RoundHouse 30 s reel: writes out/project (a HyperFrames composition) and out/cues.json (voice + sfx times).

Paper look and stop-motion cadence come from the papercut engine (.claude/skills/papercut/engine);
the scenes, UI cards and timing are specific to this film. Run vo.py first, then this, then audio.py, then render.
"""
import json
import math
import re
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", ".claude", "skills", "papercut", "engine")
sys.path.insert(0, ENGINE)
from paper import _noise, card, scrap, tape  # noqa: E402

W, H, TOTAL = 1080, 1920, 30.0
OUT = os.path.join(HERE, "out")
PROJ = os.path.join(OUT, "project")
CAP_Y = 1372

INK, CREAM, VERM, COBALT, SUN = "#161513", "#efe8da", "#e4472b", "#2f4ad0", "#f3d35b"

# paper stocks (RGB) for backgrounds and cards
STOCK = {"cream": (238, 231, 216), "white": (246, 243, 236), "newsprint": (214, 209, 198), "kraft": (186, 150, 108),
         "sky": (196, 211, 222), "blush": (233, 205, 192), "ink": (20, 19, 18), "sun": (243, 211, 91)}


# silence before each voice line: measured documentary pacing (~145 wpm overall), longest pause before the reveal
GAPS = [.4, .45, .15, .55, .2, .7, .5, .3, .3, .55, .2, 1.1]
VO_AT = []  # filled from the voice durations in build()
BPM = 100
BEAT = 60 / BPM
DROP = 13.85  # RoundHouse reveal, re-set in build() to the moment the name is spoken


def Q(t):
    """Snap a time to the beat grid (grid anchored on the drop)."""
    return round(DROP + round((t - DROP) / BEAT) * BEAT, 3)


def beats(t0, t1, step=1.0):
    k = math.ceil((t0 - DROP) / (BEAT * step) - 1e-6)
    out = []
    while DROP + k * BEAT * step < t1 - .05:
        out.append(round(DROP + k * BEAT * step, 3))
        k += 1
    return out


class Film:
    """Scenes are layered: wrap (rip / slide) > cam (hard-cut reframes) > camk (beat punches) > cams (shake) > pieces."""

    def __init__(self, vo):
        self.vo = vo
        self.scenes, self.js, self.ev = [], [], []
        self.rng = np.random.default_rng(31)
        self.n = 0
        self.cur = None

    def id(self, p="e"):
        self.n += 1
        return f"{p}{self.n}"

    def r(self, a, b):
        return float(a + (b - a) * self.rng.random())

    def sfx(self, t, k, g=1.0):
        self.ev.append({"t": round(t, 3), "k": k, "g": g})

    def wt(self, line, word, nth=0):
        """Absolute time a word is spoken (first match in that voice line)."""
        hits = [w for w in self.vo[line]["words"] if re.sub(r"\W", "", w["w"]).lower() == re.sub(r"\W", "", word).lower()]
        return round(VO_AT[line] + hits[nth]["s"], 3)

    def scene(self, start, end, bg, z, punch=True):
        sid = self.id("s")
        self.cur = {"id": sid, "start": start, "end": end, "bg": bg, "z": z, "body": []}
        self.scenes.append(self.cur)
        if punch:  # slow push-in, on twos: the camera creeps toward the idea while the narrator explains it
            d = end - start
            self.js.append(f'tl.fromTo("#{sid}k", {{scale: 1}}, {{scale: {1.05 + self.r(0, .02):.3f}, duration: {d:.3f}, ease: st("sine.inOut", {d:.3f})}}, {start:.3f});')
        return sid

    def el(self, x, y, w, inner, rot=0.0, z=2, boil=1.0):
        i = self.id()
        self.cur["body"].append(
            f'<div class="el" id="{i}" style="left:{x}px;top:{y}px;width:{w}px;z-index:{z}">'
            f'<div style="transform:rotate({rot:.1f}deg)"><div class="boil" id="{i}b">{inner}</div></div></div>')
        if boil:
            s0, s1 = self.cur["start"], self.cur["end"]
            self.js.append(f'boil("#{i}b", {s0:.3f}, {s1 - s0:.3f}, {self.n % 23}, {boil});')
        return i

    def row(self, y, inner, z=20, boil=1.0):
        """A full-width centred row."""
        i = self.id()
        self.cur["body"].append(f'<div class="el" id="{i}" style="left:0;right:0;top:{y}px;z-index:{z};display:flex;justify-content:center">'
                                f'<div class="boil" id="{i}b">{inner}</div></div>')
        if boil:
            self.js.append(f'boil("#{i}b", {self.cur["start"]:.3f}, {self.cur["end"] - self.cur["start"]:.3f}, {self.n % 23}, {boil});')
        return i

    def enter(self, i, t, kind="drop", sfx=True, g=1.0):
        R = self.r(-6, 6)
        fr, d, ease, k = {
            "drop": (f"y: -120, scale: 1.08, rotation: {R:.1f}", .25, "back.out(1.3)", "drop"),
            "left": (f"x: -1000, rotation: {-abs(R) - 4:.1f}", .25, "power3.out", "slide"),
            "right": (f"x: 1000, rotation: {abs(R) + 4:.1f}", .25, "power3.out", "slide"),
            "up": (f"y: 1100, rotation: {R:.1f}", .25, "power3.out", "slide"),
            "snap": (f"scale: .55, rotation: {R:.1f}", .17, "back.out(1.6)", "click"),
            "pop": ("scale: .2", .17, "back.out(1.8)", "ping"),
            "slam": (f"scale: 1.45, rotation: {R:.1f}", .17, "power3.out", "hit"),
            "tape": ("scale: .6", .09, "power2.out", "tape"),
            "none": ("scale: 1", .01, "none", None),
        }[kind]
        self.js.append(f'tl.set("#{i}", {{opacity: 1}}, {t:.3f});')
        self.js.append(f'tl.fromTo("#{i}", {{{fr}}}, {{x: 0, y: 0, scale: 1, rotation: 0, duration: {d}, ease: st("{ease}", {d})}}, {t:.3f});')
        if sfx and k:
            self.sfx(t, k, g)
        return i

    def leave(self, i, t, dx=None, dy=None, d=.17):
        dx = int(self.r(-1100, 1100)) if dx is None else dx
        dy = int(self.r(-1700, 1700)) if dy is None else dy
        self.js.append(f'tl.to("#{i}", {{x: {dx}, y: {dy}, rotation: {self.r(-40, 40):.0f}, duration: {d}, ease: st("power2.in", {d})}}, {t:.3f});')
        self.js.append(f'tl.set("#{i}", {{opacity: 0}}, {t + d:.3f});')

    def cut(self, sid, t, s=1.0, px=540, py=883, sfx=False):
        """Hard-cut reframe: centre point (px, py) of the layout at scale s, instantly."""
        x, y = (540 - px) * s, (883 - py) * s
        # keep the paper filling the frame
        x = max(-540 * (s - 1), min(540 * (s - 1), x))
        y = max(-1037 * (s - 1), min(883 * (s - 1), y))
        self.js.append(f'tl.set("#{sid}c", {{scale: {s}, x: {x:.0f}, y: {y:.0f}}}, {t:.3f});')
        if sfx:
            self.sfx(t, "whoosh", .5)

    def shake(self, sid, t, amp=14):
        for k, (a, b) in enumerate([(1, -.7), (-.8, .6), (.45, -.3), (0, 0)]):
            self.js.append(f'tl.set("#{sid}x", {{x: {a * amp:.0f}, y: {b * amp:.0f}}}, {t + k / 12:.3f});')

    def draw(self, path_id, t, d=.17, sfx="draw"):
        self.js.append(f'tl.fromTo("#{path_id}", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: {d}, ease: st("none", {d})}}, {t:.3f});')
        if sfx:
            self.sfx(t, sfx, .8)

    def rip_out(self, sid, t, d=.25):
        offs = [self.r(-22, 22) for _ in range(25)]
        slope = 0.14

        def poly(e):
            pts = ["0px 0px"] + [f"{e + slope * (k / 24) * H + offs[k]:.0f}px {k / 24 * H:.0f}px" for k in range(25)] + [f"0px {H}px"]
            return "polygon(" + ", ".join(pts) + ")"

        self.js.append(f'tl.fromTo("#{sid}w", {{clipPath: "{poly(W + 60)}"}}, {{clipPath: "{poly(-slope * H - 80)}", '
                       f'duration: {d}, ease: st("power2.in", {d})}}, {t:.3f});')
        self.sfx(t, "rip")

    def slide_in(self, sid, t, d=.17):
        self.js.append(f'tl.fromTo("#{sid}w", {{y: {H}, rotation: 3}}, {{y: 0, rotation: 0, duration: {d}, ease: st("power3.out", {d})}}, {t:.3f});')
        self.sfx(t, "slide")
        self.sfx(t, "whoosh", .8)

    # ---------- kinetic type ----------
    def slam(self, lines, y, times, size=118, tone="ink", gap=None, sid=None, shake_on=()):
        """Headline built word by word: each word its own torn chip, slammed in at its time (usually when it is spoken)."""
        gap = gap or int(size * 1.22)
        ids, k = [], 0
        for li, ln in enumerate(lines):
            chips = []
            for w in ln.split():
                wid = self.id("w")
                html = (f'<span class="serif" style="font-size:{int(size * 1.35)}px;color:{VERM};line-height:.8">{w[1:]}</span>'
                        if w.startswith("~") else strip(w, size, tone, pad=f"{int(size * .14)}px {int(size * .2)}px {int(size * .09)}px"))
                chips.append(f'<div class="wd" id="{wid}" style="transform:rotate({self.r(-2.5, 2.5):.1f}deg)">{html}</div>')
                t = times[k]
                self.js.append(f'tl.set("#{wid}", {{opacity: 1}}, {t:.3f});')
                self.js.append(f'tl.fromTo("#{wid}", {{scale: 1.3}}, {{scale: 1, duration: .17, ease: st("power3.out", .17)}}, {t:.3f});')
                self.sfx(t, "hit", .35)
                if sid and k in shake_on:
                    self.shake(sid, t)
                ids.append(wid)
                k += 1
            ri = self.row(y + li * gap, f'<div class="line">{"".join(chips)}</div>', z=60, boil=.8)
            self.js.append(f'tl.set("#{ri}", {{opacity: 1}}, 0);')
        return ids

    def ransom(self, word, y, t0, size=150, step=.085, sid=None):
        """Ransom-note letters, one per 16th note."""
        fonts = ["Anton", "Archivo", "Serif", "Elite", "Anton", "Archivo"]
        tones = [("#161513", "#efe8da"), ("url(assets/paper/white.jpg) center/cover", "#161513"), (VERM, "#f6f1e7"),
                 ("url(assets/paper/sun.jpg) center/cover", "#161513"), ("url(assets/paper/kraft.jpg) center/cover", "#161513")]
        ls, k = [], 0
        for ch in word:
            if ch == " ":
                ls.append('<span style="display:inline-block;width:30px"></span>')
                continue
            lid = self.id("l")
            fnt = fonts[(k * 7 + len(word)) % len(fonts)]
            bg, fg = tones[(k * 3 + len(word)) % len(tones)]
            fs = int(size * self.r(.86, 1.08) * (1.15 if fnt in ("Serif", "Elite") else 1))
            st_ = "font-style:italic;" if fnt == "Serif" else ""
            ls.append(f'<span class="rl" id="{lid}" style="background:{bg};color:{fg};font-family:{fnt};{st_}font-size:{fs}px;'
                      f'transform:rotate({self.r(-7, 7):.1f}deg) translateY({self.r(-8, 8):.0f}px)">{ch}</span>')
            t = t0 + k * step
            self.js.append(f'tl.set("#{lid}", {{opacity: 1}}, {t:.3f}); tl.fromTo("#{lid}", {{scale: 1.35}}, {{scale: 1, duration: .09, ease: st("power3.out", .09)}}, {t:.3f});')
            self.sfx(t, "key", .55)
            k += 1
        i = self.row(y, f'<div class="line" style="gap:6px">{"".join(ls)}</div>', z=60, boil=.7)
        self.js.append(f'tl.set("#{i}", {{opacity: 1}}, 0);')
        if sid:
            self.shake(sid, t0 + (k - 1) * step + .05, 10)
        return t0 + (k - 1) * step


# ---------- paper UI pieces (HTML) ----------
def strip(text, size=110, tone="ink", pad="18px 34px 12px", font="Anton", extra=""):
    return f'<div class="strip {tone}" style="font-family:{font};font-size:{size}px;padding:{pad};{extra}">{text}</div>'


def sticky(text, size=40, rot=0):
    return f'<div class="sticky"><div class="mk" style="font-size:{size}px">{text}</div></div>'


def notif(title, body, color=VERM, icon="●"):
    return (f'<div class="notif"><div class="ic" style="background:{color}">{icon}</div>'
            f'<div class="tx"><b>{title}</b><span>{body}</span></div><div class="now">now</div></div>')


def keycap(k):
    return f'<div class="key">{k}</div>'


def chip(text, size=64, tone="paper"):
    return f'<div class="chip {tone}" style="font-size:{size}px">{text}</div>'


def arrow_down(pid, h=90):
    return (f'<svg viewBox="0 0 60 {h}" width="60" height="{h}" style="overflow:visible"><path id="{pid}" pathLength="1" class="pen" '
            f'd="M30,4 C26,{h * .35:.0f} 34,{h * .6:.0f} 30,{h - 8} M16,{h - 26} L30,{h - 6} L44,{h - 28}"/></svg>')


def arrow_right(pid, w=70):
    return (f'<svg viewBox="0 0 {w} 50" width="{w}" height="50" style="overflow:visible"><path id="{pid}" pathLength="1" class="pen" '
            f'd="M4,26 C{w * .35:.0f},20 {w * .6:.0f},31 {w - 8},25 M{w - 26},11 L{w - 6},25 L{w - 28},40"/></svg>')


def browser(url, inner, w=700):
    return (f'<div class="card print" style="width:{w}px"><div class="bar"><i></i><i></i><i></i><span class="url">{url}</span></div>'
            f'{inner}</div>')


def site_clean(w=700):
    inner = ('<div class="pg"><div class="nav"><b class="logo"><span class="mark"></span>Your Brand</b>'
             '<span class="lk"></span><span class="lk"></span><span class="lk"></span><span class="btn sm">Contact</span></div>'
             '<div class="hero"><div class="copy"><div class="serif h">A clear first<br>impression.</div>'
             '<div class="ln w80"></div><div class="ln w60"></div><span class="btn">Get in touch →</span></div>'
             '<div class="img ht"></div></div></div>')
    return browser("yourbrand.com", inner, w)


def site_phone():
    return ('<div class="card print phone"><div class="notch"></div><div class="pg">'
            '<div class="nav"><b class="logo"><span class="mark"></span></b><span class="burger">≡</span></div>'
            '<div class="img ht" style="height:150px"></div><div class="serif h" style="font-size:40px">A clear first impression.</div>'
            '<div class="ln w80"></div><div class="ln w60"></div><span class="btn" style="font-size:20px">Get in touch →</span></div></div>')


def form_card():
    return ('<div class="card print form"><div class="fh">Start a project</div>'
            '<label>Name</label><div class="in"></div><label>Email</label><div class="in"></div>'
            '<label>Tell us more</label><div class="in tall"></div><span class="btn" id="sendbtn">Send inquiry →</span></div>')


def brand_card():
    return ('<div class="card print bcard"><span class="mark big"></span><div><b>Your Brand</b>'
            '<div class="ln w80" style="margin-top:10px"></div><div class="ln w60"></div></div></div>')


def inbox_card(rows=None):
    rows = rows or [("Website form", "New inquiry: kitchen refit", 1), ("Sam", "Re: Re: Fwd: quote?", 1),
                    ("Alex", "Can you resend the details?", 1), ("Ops", "Fwd: leads sheet v3 FINAL", 0),
                    ("Jo", "Re: did anyone reply to this?", 1), ("Website form", "New inquiry: question", 0)]
    trs = "".join(f'<div class="row"><i class="{"u" if u else ""}"></i><b>{a}</b><span>{s}</span></div>' for a, s, u in rows)
    return f'<div class="card print inbox"><div class="ih">Inbox <em>●</em></div>{trs}</div>'


def sheet_card():
    head = "<tr><th></th><th>A</th><th>B</th><th>C</th><th>D</th></tr>"
    cols = "<tr><td>1</td><td><b>Name</b></td><td><b>Email</b></td><td><b>Source</b></td><td><b>Status</b></td></tr>"
    body = ""
    for r in range(2, 8):
        cells = "".join(f'<td><div class="ln" style="width:{40 + (r * 17 + c * 23) % 50}%"></div></td>' for c in range(3))
        st = ['<span class="mk red">??</span>', '<div class="ln" style="width:55%"></div>', '<span class="hl">follow up</span>'][r % 3]
        body += f"<tr><td>{r}</td>{cells}<td>{st}</td></tr>"
    return f'<div class="card print sheet"><div class="sh">leads_FINAL_v3.xlsx</div><table>{head}{cols}{body}</table></div>'


def crm_card(tag, color):
    return (f'<div class="card print crm"><span class="tag" style="background:{color}">{tag}</span>'
            '<div class="who"><span class="av"></span><div><div class="ln w80"></div><div class="ln w60"></div></div></div>'
            '<div class="stage">Stage: <span class="mk">?</span></div></div>')


def site_messy(w=900):
    inner = ('<div class="pg messy"><div class="ban">NEWS: updated opening hours, see page 4 · new services · read more</div>'
             '<div class="nav"><b class="logo"><span class="mark"></span>Your Brand</b>'
             + "".join('<span class="lk sm"></span>' for _ in range(9)) +
             '</div><div class="cols"><div><div class="h2">Welcome to our website where you can find everything</div>'
             + "".join(f'<div class="ln" style="width:{60 + (k * 13) % 38}%"></div>' for k in range(8)) +
             '<span class="btn" style="background:#3a8f4a">Click here</span> <span class="btn" style="background:#b8862b">Learn more</span> '
             '<span class="btn">Contact us</span></div><div><div class="img ht" style="height:170px"></div>'
             + "".join(f'<div class="ln" style="width:{50 + (k * 19) % 45}%"></div>' for k in range(5)) +
             '</div></div><div class="pop"><b>Subscribe?</b><div class="ln w80"></div><span class="x">×</span></div>'
             '<div class="chat">Hi! Need help?</div><div class="cookie">We use cookies. Accept · Settings · More</div></div>')
    return browser("yourbrand.com/home-new-2", inner, w)


def site_structured(w=900):
    inner = ('<div class="pg"><div class="nav"><b class="logo"><span class="mark"></span>Your Brand</b>'
             '<span class="lk"></span><span class="lk"></span><span class="lk"></span><span class="btn sm">Contact</span></div>'
             '<div class="serif h" style="font-size:66px;margin:26px 0 8px">What we do, clearly.</div><div class="ln w60"></div>'
             '<div class="tri">' + "".join(f'<div class="svc"><span class="dot" style="background:{c}"></span><div class="ln w80"></div>'
                                           f'<div class="ln w60"></div></div>' for c in (VERM, COBALT, "#3f7d5c")) +
             '</div><span class="btn">Start a project →</span></div>')
    return browser("yourbrand.com", inner, w)


def logo_sheet():
    return ('<div class="card print logos"><svg viewBox="0 0 420 260" width="420" height="260">'
            '<circle cx="130" cy="130" r="96" fill="none" stroke="#b9b2a5" stroke-width="2" stroke-dasharray="6 6"/>'
            '<line x1="10" y1="130" x2="250" y2="130" stroke="#b9b2a5" stroke-width="2" stroke-dasharray="6 6"/>'
            '<circle cx="130" cy="130" r="70" fill="#161513"/><path d="M130,60 A70,70 0 0 1 130,200 Z" fill="#e4472b"/>'
            '<text x="250" y="122" font-family="Inter" font-weight="800" font-size="38" fill="#161513">Your</text>'
            '<text x="250" y="166" font-family="Inter" font-weight="800" font-size="38" fill="#161513">Brand</text></svg>'
            '<div class="cap2">identity · v2</div></div>')


def swatch(color, name):
    return f'<div class="card print sw"><div style="background:{color};height:150px"></div><div class="cap2">{name}</div></div>'


def type_card():
    return ('<div class="card print typ"><div><span class="serif" style="font-size:150px;font-style:italic">Aa</span>'
            '<span style="font-family:Inter;font-weight:800;font-size:130px;margin-left:16px">Aa</span></div>'
            '<div class="cap2">display · text</div></div>')


def message_card():
    return ('<div class="card print msg"><div class="cap2">messaging</div>'
            '<div class="type">What do you do,<br>and who is it for?</div>'
            '<div class="mk" style="font-size:44px;color:#e4472b;margin-top:12px">say it simply.</div></div>')


def wordmark(size=150, color=INK):
    return f'<div class="wm" style="font-size:{size}px;color:{color}">ROUNDHOUSE</div>'


CSS = """
@font-face { font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf"); }
@font-face { font-family: "Marker"; src: url("assets/fonts/PermanentMarker-Regular.ttf"); }
@font-face { font-family: "Archivo"; src: url("assets/fonts/ArchivoBlack-Regular.ttf"); }
@font-face { font-family: "Elite"; src: url("assets/fonts/SpecialElite-Regular.ttf"); }
@font-face { font-family: "Serif"; font-style: italic; src: url("assets/fonts/instrument-serif-latin-400-italic.woff2"); }
@font-face { font-family: "Serif"; font-style: normal; src: url("assets/fonts/instrument-serif-latin-400-normal.woff2"); }
@font-face { font-family: "Inter"; font-weight: 400; src: url("assets/fonts/inter-latin-400-normal.woff2"); }
@font-face { font-family: "Inter"; font-weight: 500; src: url("assets/fonts/inter-latin-500-normal.woff2"); }
@font-face { font-family: "Inter"; font-weight: 600; src: url("assets/fonts/inter-latin-600-normal.woff2"); }
@font-face { font-family: "Inter"; font-weight: 700; src: url("assets/fonts/inter-latin-700-normal.woff2"); }
@font-face { font-family: "Inter"; font-weight: 800; src: url("assets/fonts/inter-latin-800-normal.woff2"); }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: WWpx; height: HHpx; overflow: hidden; background: #141312; }
#root { position: relative; width: WWpx; height: HHpx; overflow: hidden; }
.scene { position: absolute; inset: 0; filter: drop-shadow(-10px 0 14px rgba(0,0,0,.45)); }
.wrap, .cam, .camk, .cams { position: absolute; inset: 0; }
.cam, .camk { transform-origin: 50% 46%; }
.line { display: flex; gap: 16px; align-items: center; justify-content: center; }
.wd { display: inline-block; opacity: 0; }
.rl { display: inline-block; opacity: 0; padding: .07em .13em .02em; line-height: 1; text-transform: uppercase; filter: drop-shadow(4px 6px 4px rgba(20,14,8,.45)); }
.strip.cr { background: none; color: #efe8da; filter: none; }
.bg { position: absolute; left: -40px; top: -40px; width: calc(100% + 80px); height: calc(100% + 80px); }
.el { position: absolute; opacity: 0; }
.boil { --bx: .5; --by: .5; --br: .5; --amp: 1;
  transform: translate(calc((var(--bx) - .5) * 3px * var(--amp)), calc((var(--by) - .5) * 3px * var(--amp))) rotate(calc((var(--br) - .5) * .6deg * var(--amp))); }
.strip { display: inline-block; line-height: 1; white-space: nowrap; text-transform: uppercase; letter-spacing: .5px;
  filter: drop-shadow(5px 8px 6px rgba(20,14,8,.45)); }
.strip.ink { background: #161513 url("assets/paper/ink.jpg") center/cover; color: #efe8da; }
.strip.paper { background: url("assets/paper/white.jpg") center/cover; color: #161513; }
.strip.verm { background: #e4472b; color: #f6f1e7; }
.strip.none { background: none; filter: none; }
.serif { font-family: "Serif"; font-style: italic; text-transform: none; letter-spacing: 0; }
.mk { font-family: "Marker"; color: #161513; line-height: 1.05; }
.mk.red { color: #e4472b; }
.hl { background: rgba(243,211,91,.9); padding: 0 6px; font-family: Inter; font-weight: 600; }
.card { position: relative; background: #f6f3ec url("assets/paper/white.jpg") center/cover; border-radius: 8px; overflow: hidden;
  font-family: Inter; color: #161513; filter: drop-shadow(7px 11px 9px rgba(20,14,8,.42)) contrast(1.04) saturate(.92); }
.card.print::after { content: ""; position: absolute; inset: 0; pointer-events: none; mix-blend-mode: multiply; opacity: .32;
  background-image: radial-gradient(rgba(0,0,0,.35) .8px, transparent 1.3px); background-size: 5px 5px; }
.bar { height: 44px; background: #e6e0d4; display: flex; align-items: center; gap: 9px; padding: 0 16px; border-bottom: 2px solid #d6cfc1; }
.bar i { width: 13px; height: 13px; border-radius: 50%; background: #c9c1b2; }
.bar .url { margin-left: 18px; flex: 1; height: 26px; border-radius: 13px; background: #f6f3ec; font-size: 15px; color: #6d675d;
  display: flex; align-items: center; padding-left: 14px; }
.pg { padding: 24px 32px 30px; position: relative; }
.nav { display: flex; align-items: center; gap: 22px; margin-bottom: 22px; }
.logo { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 22px; margin-right: auto; }
.mark { width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(90deg, #161513 50%, #e4472b 50%); display: inline-block; }
.mark.big { width: 92px; height: 92px; flex: none; }
.lk { width: 62px; height: 10px; border-radius: 5px; background: #cfc8bb; }
.lk.sm { width: 34px; height: 8px; }
.btn { display: inline-block; background: #161513; color: #f6f1e7; font-weight: 700; font-size: 22px; padding: 12px 20px; border-radius: 30px; }
.btn.sm { font-size: 16px; padding: 8px 14px; }
.hero { display: flex; gap: 26px; }
.copy { flex: 1.1; }
.h { font-size: 54px; line-height: 1.02; margin-bottom: 18px; }
.ln { height: 11px; border-radius: 6px; background: #d3ccbf; margin: 10px 0; }
.w80 { width: 80%; } .w60 { width: 60%; }
.copy .btn { margin-top: 16px; }
.img { flex: 1; border-radius: 6px; min-height: 230px; }
.ht { background-color: #2f4ad0; background-image: radial-gradient(rgba(246,241,231,.55) 2.2px, transparent 2.8px),
  linear-gradient(135deg, rgba(0,0,0,0) 30%, rgba(0,0,0,.35)); background-size: 9px 9px, 100% 100%; }
.phone { width: 300px; border-radius: 36px; border: 10px solid #161513; }
.phone .pg { padding: 18px 18px 26px; }
.phone .notch { width: 110px; height: 22px; background: #161513; border-radius: 0 0 14px 14px; margin: 0 auto; }
.phone .h { margin: 16px 0 6px; }
.burger { font-size: 34px; font-weight: 700; }
.form { width: 400px; padding: 30px 32px 34px; }
.form .fh { font-family: Serif; font-style: italic; font-size: 46px; margin-bottom: 14px; }
.form label { display: block; font-size: 17px; font-weight: 600; color: #6d675d; margin: 12px 0 6px; }
.form .in { height: 46px; border: 2px solid #cfc8bb; border-radius: 8px; background: #fbf9f4; }
.form .in.tall { height: 96px; }
.form .btn { margin-top: 20px; background: #e4472b; }
.bcard { width: 330px; height: 190px; display: flex; align-items: center; gap: 22px; padding: 26px; }
.bcard b { font-size: 30px; font-weight: 800; }
.inbox { width: 540px; padding-bottom: 8px; }
.ih { font-weight: 800; font-size: 30px; padding: 20px 24px 12px; border-bottom: 2px solid #ddd6c9; }
.ih em { color: #e4472b; font-style: normal; font-size: 22px; vertical-align: middle; }
.row { display: flex; align-items: center; gap: 12px; padding: 13px 24px; border-bottom: 1px solid #e3ddd1; font-size: 20px; white-space: nowrap; }
.row i { width: 11px; height: 11px; border-radius: 50%; flex: none; }
.row i.u { background: #2f4ad0; }
.row b { width: 140px; flex: none; overflow: hidden; }
.row span { color: #5d574e; overflow: hidden; }
.sheet { width: 560px; }
.sheet .sh { font-size: 17px; font-weight: 600; padding: 12px 16px; background: #dfe8de; border-bottom: 2px solid #c4cfc3; }
.sheet table { border-collapse: collapse; width: 100%; font-size: 18px; }
.sheet td, .sheet th { border: 1px solid #cfc8bb; height: 40px; padding: 0 8px; }
.sheet th, .sheet td:first-child { background: #ebe6dc; color: #7a7368; font-weight: 600; width: 34px; text-align: center; }
.sheet .ln { margin: 0; height: 9px; }
.sheet .mk { font-size: 28px; }
.crm { width: 280px; padding: 18px; }
.crm .tag { color: #fff; font-weight: 800; font-size: 15px; padding: 5px 10px; border-radius: 6px; letter-spacing: .5px; }
.crm .who { display: flex; gap: 12px; align-items: center; margin-top: 14px; }
.crm .who > div { flex: 1; }
.crm .av { width: 46px; height: 46px; border-radius: 50%; background: #cfc8bb; flex: none; }
.crm .stage { margin-top: 10px; font-size: 18px; font-weight: 600; }
.crm .stage .mk { font-size: 30px; color: #e4472b; }
.notif { width: 400px; display: flex; gap: 14px; align-items: center; background: rgba(250,248,243,.97); border-radius: 22px; padding: 16px 18px;
  font-family: Inter; filter: drop-shadow(5px 9px 8px rgba(20,14,8,.4)); }
.notif .ic { width: 50px; height: 50px; border-radius: 12px; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24px; flex: none; }
.notif .tx { flex: 1; display: flex; flex-direction: column; font-size: 19px; color: #5d574e; }
.notif .tx b { color: #161513; font-size: 21px; }
.notif .now { font-size: 15px; color: #8a8378; align-self: flex-start; }
.sticky { width: 240px; height: 220px; background: #f3d35b url("assets/paper/sun.jpg") center/cover; padding: 26px 22px;
  filter: drop-shadow(6px 10px 8px rgba(20,14,8,.4)); display: flex; align-items: center; justify-content: center; text-align: center; }
.key { width: 118px; height: 112px; border-radius: 16px; background: #f6f3ec; border-bottom: 9px solid #bdb5a6; font-family: Inter; font-weight: 700;
  font-size: 40px; display: flex; align-items: center; justify-content: center; filter: drop-shadow(4px 8px 6px rgba(20,14,8,.45)); }
.chip { display: inline-block; font-family: Anton; text-transform: uppercase; line-height: 1; padding: 18px 30px 13px; white-space: nowrap;
  filter: drop-shadow(5px 8px 6px rgba(20,14,8,.42)); }
.chip.paper { background: url("assets/paper/white.jpg") center/cover; color: #161513; }
.chip.ink { background: #161513 url("assets/paper/ink.jpg") center/cover; color: #efe8da; }
.chip.verm { background: #e4472b; color: #f6f1e7; }
.chip.kraft { background: url("assets/paper/kraft.jpg") center/cover; color: #161513; }
.pen { fill: none; stroke: #161513; stroke-width: 6; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; }
.pen.red { stroke: #e4472b; }
.pen.light { stroke: #efe8da; }
.messy { font-size: 15px; }
.messy .ban { background: #e4472b; color: #fff; font-weight: 700; padding: 8px 12px; margin: -24px -32px 16px; font-size: 16px; white-space: nowrap; }
.messy .cols { display: flex; gap: 22px; }
.messy .cols > div { flex: 1; }
.messy .h2 { font-family: "Times New Roman", serif; font-size: 34px; line-height: 1.05; margin-bottom: 8px; color: #3a3530; }
.messy .btn { font-size: 15px; padding: 8px 12px; margin-top: 10px; }
.messy .pop { position: absolute; left: 330px; top: 170px; width: 300px; background: #fff; border: 2px solid #161513; padding: 20px; border-radius: 8px;
  box-shadow: 8px 10px 0 rgba(0,0,0,.18); font-size: 24px; }
.messy .pop .x { position: absolute; right: 12px; top: 6px; font-size: 28px; }
.messy .chat { position: absolute; right: 26px; bottom: 70px; background: #2f4ad0; color: #fff; font-weight: 700; padding: 12px 18px; border-radius: 20px 20px 4px 20px; font-size: 18px; }
.messy .cookie { position: absolute; left: 0; right: 0; bottom: 0; background: #2c2a27; color: #ddd; padding: 12px 20px; font-size: 16px; }
.tri { display: flex; gap: 20px; margin: 26px 0; }
.svc { flex: 1; border: 2px solid #ddd6c9; border-radius: 10px; padding: 18px; }
.svc .dot { display: block; width: 40px; height: 40px; border-radius: 50%; margin-bottom: 8px; }
.logos { width: 460px; padding: 20px; }
.cap2 { font-family: Inter; font-size: 17px; font-weight: 600; color: #7a7368; letter-spacing: 1px; text-transform: uppercase; padding: 10px 4px 2px; }
.sw { width: 170px; padding: 10px; }
.typ { width: 420px; padding: 18px 26px; }
.msg { width: 460px; padding: 24px 28px 28px; }
.msg .type { font-family: Elite; font-size: 34px; line-height: 1.3; margin-top: 8px; }
.wm { font-family: Anton; letter-spacing: 4px; line-height: 1; white-space: nowrap; }
.tick { width: 64px; height: 64px; border-radius: 50%; background: #3f7d5c; color: #fff; font-family: Inter; font-weight: 800; font-size: 40px;
  display: flex; align-items: center; justify-content: center; filter: drop-shadow(3px 6px 5px rgba(20,14,8,.4)); }
.token { width: 40px; height: 40px; border-radius: 50%; background: #e4472b; border: 5px solid #f6f1e7; filter: drop-shadow(3px 5px 4px rgba(20,14,8,.5)); }
.small { font-family: Inter; font-weight: 600; font-size: 34px; color: #efe8da; letter-spacing: .5px; white-space: nowrap; }
#grain { position: absolute; inset: -40px; pointer-events: none; opacity: .14; mix-blend-mode: multiply; z-index: 900;
  background: url("assets/paper/grain.png"); --gx: 0; --gy: 0; background-position: calc(var(--gx) * 300px) calc(var(--gy) * 300px); }
#vig { position: absolute; inset: 0; pointer-events: none; z-index: 901;
  background: radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 58%, rgba(20,12,4,.32) 100%); }
.cap { position: absolute; left: 0; right: 0; top: CAPYpx; display: flex; justify-content: center; z-index: 800; }
.cap .strip { font-family: Inter; font-weight: 700; font-size: 50px; padding: 16px 28px 15px; text-transform: none; letter-spacing: 0; }
.cap .w { display: inline-block; margin: 0 7px; }
"""

JS_HEAD = r"""
// on twos: quantise any ease to 12 poses per second of its own duration
function st(base, dur){ const n = Math.max(1, Math.round(dur * 12)); const f = gsap.parseEase(base || "none");
  return p => f(Math.min(1, Math.floor(p * n + 1e-6) / n)); }
function jit(seed, dur){ const n = Math.max(1, Math.round(dur * 12));
  return p => { const k = Math.floor(p * n) + seed * 97.13; const v = Math.sin(k * 12.9898 + seed * 78.233) * 43758.5453; return v - Math.floor(v); }; }
const tl = gsap.timeline({ paused: true });
function boil(sel, t0, dur, seed, amp){
  const e = document.querySelector(sel); if (!e) return;
  e.style.setProperty("--amp", amp || 1);
  tl.fromTo(e, {"--bx": 0}, {"--bx": 1, duration: dur, ease: jit(seed, dur)}, t0);
  tl.fromTo(e, {"--by": 0}, {"--by": 1, duration: dur, ease: jit(seed + 3, dur)}, t0);
  tl.fromTo(e, {"--br": 0}, {"--br": 1, duration: dur, ease: jit(seed + 7, dur)}, t0);
}
"""


def tape_at(f, x, y, rot, t, w=180):
    i = f.el(x, y, w, f'<img src="assets/paper/tape.png" style="width:{w}px;display:block">', rot=rot, z=30, boil=0)
    f.enter(i, t, "tape")
    return i


def rsize(word, cap=150):
    return int(min(cap, 880 / len(word)))


def build():
    global DROP
    vo = json.load(open(os.path.join(OUT, "vo", "lines.json")))["lines"]
    t = 0.0
    VO_AT.clear()
    for g, ln in zip(GAPS, vo):
        t += g
        VO_AT.append(round(t, 3))
        t += ln["dur"]
    f = Film(vo)
    wt = f.wt
    V = VO_AT
    end = lambda i: V[i] + vo[i]["dur"]  # noqa: E731
    DROP = round(wt(5, "RoundHouse") - .05, 3)
    RIP = .3
    c1 = V[1] - .15                 # customers see
    c2 = V[2] - .05                 # team deals with
    c3 = V[3] - .15                 # the chain
    c4 = V[4] - .05                 # work gets messy
    c5 = end(4) + .2                # black: the gap
    c7 = V[6] - .1                  # brand
    c8 = V[7] - .1                  # website
    c9 = V[8] - .1                  # workflows
    c10 = V[9] - .05                # easier to understand
    c11 = V[10] - .15               # easier to do
    c12 = V[11] - .1                # the question
    c13 = end(11) + .2              # end card

    # ---- S1 two sides: the polished half and the messy half, words land as they are said ----
    s = f.scene(0, c1 + RIP, "white", 20)
    f.enter(f.el(540, -40, 600, '<img src="assets/paper/half_kraft.png" style="width:600px;display:block">', z=1, boil=0), 0, "none")
    f.enter(f.el(60, 330, 420, site_clean(700).replace('style="width:700px"', 'style="width:700px;zoom:.6"'), rot=-3), 0, "none")
    f.enter(f.el(90, 1010, 330, brand_card(), rot=4), .25, "drop")
    f.enter(f.el(600, 290, 420, f'<div style="zoom:.78">{inbox_card()}</div>', rot=3.5), wt(0, "two"), "right")
    f.enter(f.el(660, 1020, 240, sticky("copy into<br>the sheet??", 38), rot=-7), wt(0, "sides.") + .15, "drop")
    f.enter(f.el(590, 880, 400, notif("3 new emails", "Re: Re: Fwd: quote?")), end(0) - .1, "pop")
    f.slam(["YOUR BUSINESS", "HAS TWO SIDES."], 610, [wt(0, w) for w in "Your business has two sides.".split()], 108)
    f.rip_out(s, c1)

    # ---- S2 what customers see: the site, the form, one cut in to the click ----
    s = f.scene(c1, c2, "cream", 19)
    f.slam(["WHAT CUSTOMERS SEE."], 400, [V[1], wt(1, "customers"), wt(1, "see…")], 92)
    f.enter(f.el(70, 600, 760, site_clean(760), rot=-1.5), c1, "none")
    tape_at(f, 360, 575, -4, c1 + .2)
    f.enter(f.el(110, 860, 370, f'<div style="zoom:.9">{form_card()}</div>', rot=-3), wt(1, "customers"), "drop")
    f.enter(f.el(640, 1000, 330, brand_card(), rot=5), wt(1, "see…"), "right")
    tci = end(1) - .25
    f.cut(s, tci, 1.45, 310, 1100)
    cur = f.el(390, 1340, 60, '<svg viewBox="0 0 40 52" width="56"><path d="M4,2 L4,40 L14,30 L22,48 L29,45 L21,28 L35,28 Z" fill="#161513" stroke="#fff" stroke-width="3"/></svg>', z=70, boil=0)
    f.enter(cur, tci, "none")
    f.js.append(f'tl.fromTo("#{cur}", {{x: 160, y: 140}}, {{x: 0, y: 0, duration: .25, ease: st("power2.out", .25)}}, {tci:.3f});')
    tc = tci + .4
    f.js.append(f'tl.to("#sendbtn", {{scale: .9, duration: .08, ease: st("none", .08)}}, {tc:.3f}); tl.to("#sendbtn", {{scale: 1, background: "#3f7d5c", duration: .08, ease: st("none", .08)}}, {tc + .083:.3f});')
    f.sfx(tc, "click", 1.2)

    # ---- S3 what your team deals with: the pile builds while he says it ----
    s = f.scene(c2, c3, "newsprint", 18)
    f.slam(["WHAT YOUR TEAM", "DEALS WITH."], 430, [V[2], wt(2, "your"), wt(2, "team"), wt(2, "deal"), wt(2, "with.")], 104)
    step = (c3 - c2 - .4) / 10
    f.enter(f.el(95, 690, 540, inbox_card(), rot=-4), c2, "none")
    f.enter(f.el(470, 760, 560, sheet_card(), rot=3), c2 + step, "right")
    f.enter(f.el(80, 1080, 280, crm_card("NEW LEAD", COBALT), rot=6), c2 + 2 * step, "drop")
    f.enter(f.el(320, 1130, 280, crm_card("FOLLOW UP", VERM), rot=-5), c2 + 3 * step, "drop")
    pops = [(560, 640, "New form submission", "just now", "#3f7d5c", "✉"), (90, 255, "Did anyone reply?", "#ops channel", COBALT, "#"),
            (600, 1215, "3 new emails", "Re: Re: Fwd: quote?", VERM, "●"), (130, 900, "Reminder", "Update the sheet", "#b8862b", "⏰")]
    for k, (x, y, a, b, c, ic) in enumerate(pops):
        f.enter(f.el(x, y, 400, notif(a, b, c, ic), rot=f.r(-4, 4), z=40), c2 + (4 + k * 1.2) * step, "pop", g=.8)
    for k in range(3):
        f.enter(f.el(780 + (k % 2) * 30, 1010 + k * 28, 118, keycap("⌘C" if k % 2 == 0 else "⌘V"), rot=f.r(-8, 8), z=45), c2 + 8.5 * step + k * .12, "snap", sfx=False)
        f.sfx(c2 + 8.5 * step + k * .12, "key", .9)
    f.enter(f.el(700, 250, 240, sticky("who's on<br>this one?", 38), rot=6, z=50), c2 + 9.5 * step, "drop")

    # ---- S4 the manual chain: one step at a time, the camera following it down; then it falls apart ----
    s = f.scene(c3, c5, "kraft", 21)
    f.slide_in(s, c3)
    chain = [("CUSTOMER INQUIRY", "paper"), ("EMAIL", "paper"), ("COPY", "paper"), ("SPREADSHEET", "paper"), ("FOLLOW-UP?", "verm")]
    ys = [300, 490, 680, 870, 1060]
    gap_ = (V[4] - .35 - (c3 + .15)) / 4
    parts = []
    for k, ((txt, tone), y) in enumerate(zip(chain, ys)):
        t = c3 + .15 + k * gap_
        i = f.row(y, f'<div style="transform:rotate({f.r(-2.5, 2.5):.1f}deg)">{chip(txt, 74, tone)}</div>')
        f.enter(i, t, "slam" if k == 4 else "drop", g=.7)
        parts.append(i)
        if k:
            pid = f.id("p")
            a = f.el(510, y - 92, 60, arrow_down(pid, 86), z=15, boil=.6)
            f.enter(a, t - .17, "none")
            f.draw(pid, t - .17, .17, sfx=None)
            parts.append(a)
        if k in (2,):
            f.cut(s, t, 1.18, 540, 760)
    f.cut(s, c3 + .15 + 4 * gap_, 1.0)
    for txt, x, y, rot, t in [("by hand", 760, 690, -6, c3 + .15 + 2.4 * gap_), ("again…", 110, 885, 5, c3 + .15 + 3.4 * gap_)]:
        i = f.el(x, y, 220, f'<div class="mk" style="font-size:40px">{txt}</div>', rot=rot, z=25)
        f.enter(i, t, "snap", sfx=False)
        f.sfx(t, "draw", .6)
        parts.append(i)
    lp, ci = f.id("p"), f.id("p")
    loop = f.el(700, 520, 300, f'<svg viewBox="0 0 300 640" width="300" height="640" style="overflow:visible"><path id="{lp}" pathLength="1" class="pen red" '
                f'd="M40,600 C230,600 280,420 250,260 C225,130 150,60 40,40 M70,18 L38,40 L72,66"/></svg>', z=24, boil=.8)
    circ = f.el(300, 1035, 480, f'<svg viewBox="0 0 480 150" width="480" height="150" style="overflow:visible"><path id="{ci}" pathLength="1" class="pen red" '
                f'd="{wobble(f.rng, 480, 150)}"/></svg>', z=26, boil=.8)
    tl4 = c3 + .15 + 4 * gap_ + .25
    f.enter(circ, tl4, "none")
    f.draw(ci, tl4, .25)
    f.enter(loop, tl4 + .25, "none")
    f.draw(lp, tl4 + .25, .33)
    parts += [loop, circ]
    # strip it back
    for k, i in enumerate(parts):
        f.leave(i, c4 + (k % 4) * .05, d=.25)
    f.sfx(c4, "whoosh", 1.0)
    f.slam(["WORK GETS", "MESSY."], 720, [c4 + .4, c4 + .7, wt(4, "harder")], 150, sid=s, shake_on=(2,))
    for k in range(3):
        f.enter(f.el(int(f.r(60, 760)), int(f.r(250, 1250)), 260, f'<img src="assets/paper/scrap{k % 2}.png" style="width:260px">', rot=f.r(-30, 30), z=5),
                wt(4, "harder") + .4 + k * .35, "drop", g=.5)

    # ---- S5 a clean black frame: the music drops out ----
    s = f.scene(c5, DROP, "ink", 22, punch=False)
    f.slam(["THAT'S THE", "~gap."], 660, [wt(5, "That's"), wt(5, "the"), wt(5, "gap")], 150, tone="cr", gap=190, sid=s, shake_on=(2,))

    # ---- S6 the reveal on the name: two halves join, ROUNDHOUSE builds ----
    s = f.scene(DROP, c7 + RIP, "ink", 23)
    f.ransom("ROUNDHOUSE", 420, DROP, size=104)
    left = f.el(95, 720, 445, '<img src="assets/paper/piece_l.png" style="width:445px;display:block">', z=20, boil=.8)
    right = f.el(540, 720, 445, '<img src="assets/paper/piece_r.png" style="width:445px;display:block">', z=21, boil=.8)
    f.enter(left, DROP + .1, "left", sfx=False)
    f.enter(right, DROP + .1, "right")
    f.js.append(f'tl.set("#{left}", {{x: -80}}, {DROP + .36:.3f}); tl.set("#{right}", {{x: 80}}, {DROP + .36:.3f});')
    tj = DROP + .75
    f.js.append(f'tl.to("#{left}", {{x: 0, duration: .17, ease: st("power3.in", .17)}}, {tj - .17:.3f}); tl.to("#{right}", {{x: 0, duration: .17, ease: st("power3.in", .17)}}, {tj - .17:.3f});')
    f.sfx(tj, "hit", 1.1)
    f.shake(s, tj, 12)
    tape_at(f, 450, 800, 86, tj + .25, w=200)
    tape_at(f, 450, 1050, 92, tj + .42, w=200)
    sub = f.el(0, 1325, W, '<div style="text-align:center" class="small">brand · websites · workflows</div>', z=40, boil=.4)
    f.enter(sub, tj + .6, "snap", sfx=False)
    f.js.append(f'tl.set("#{sub}", {{opacity: 0}}, {c7 - .02:.3f});')
    f.rip_out(s, c7)

    # ---- S7 BRAND ----
    s = f.scene(c7, c8, "cream", 22)
    f.ransom("BRAND.", 380, wt(6, "brand.") - .1, size=rsize("BRAND."))
    f.enter(f.el(80, 640, 460, logo_sheet(), rot=-3), c7 + .45, "drop")
    for k, (c, nm) in enumerate([(INK, "ink"), (VERM, "signal"), (COBALT, "cobalt")]):
        f.enter(f.el(590 + k * 120, 660 + k * 40, 170, swatch(c, nm), rot=f.r(-8, 8)), c7 + .6 + k * .1, "snap", sfx=k == 0)
    f.enter(f.el(100, 1000, 460, message_card(), rot=-2), c7 + .85, "left")
    f.enter(f.el(560, 950, 420, type_card(), rot=4), c7 + 1.0, "drop")

    # ---- S8 WEBSITE ----
    s = f.scene(c8, c9, "sky", 23)
    f.ransom("WEBSITE.", 380, wt(7, "website.") - .1, size=rsize("WEBSITE."))
    f.enter(f.el(60, 640, 680, site_clean(680), rot=-2), c8 + .3, "drop")
    f.enter(f.el(690, 800, 300, site_phone(), rot=4, z=5), c8 + .65, "right")
    pa = f.id("p")
    an = f.el(250, 1150, 420, f'<div class="mk" style="font-size:44px">same site, any screen</div>'
                             f'<svg viewBox="0 0 120 70" width="120" height="70" style="position:absolute;left:420px;top:-40px;overflow:visible"><path id="{pa}" pathLength="1" class="pen" d="M6,56 C50,60 90,40 110,8 M84,12 L110,6 L108,34"/></svg>', rot=-4, z=30)
    f.enter(an, c8 + .95, "snap", sfx=False)
    f.draw(pa, c8 + .95, .25)

    # ---- S9 WORKFLOWS: FORM -> CRM -> TASK -> REPLY ----
    s = f.scene(c9, c10, "blush", 24)
    f.ransom("WORKFLOWS.", 380, wt(8, "workflows.") - .1, size=rsize("WORKFLOWS."))
    xs = [90, 330, 545, 770]
    t0 = c9 + .55
    for k, (txt, x) in enumerate(zip(["FORM", "CRM", "TASK", "REPLY"], xs)):
        f.enter(f.el(x, 800, 200, chip(txt, 58, "ink" if k < 3 else "verm"), rot=f.r(-3, 3), z=20), t0 + k * .2, "snap", g=.8)
        if k:
            pid = f.id("p")
            f.enter(f.el(x - 62, 812, 60, arrow_right(pid, 56), z=15, boil=.6), t0 + k * .2 - .08, "none")
            f.draw(pid, t0 + k * .2 - .08, .08, sfx=None)
    tok = f.el(140, 740, 40, '<div class="token"></div>', z=40, boil=0)
    f.enter(tok, t0 + .85, "pop", sfx=False)
    f.js.append(f'tl.to("#{tok}", {{x: 680, duration: .5, ease: st("none", .5)}}, {t0 + .85:.3f});')
    f.sfx(t0 + .85, "slide", .6)
    f.enter(f.el(890, 900, 64, '<div class="tick">✓</div>', z=45, boil=.4), t0 + 1.37, "slam", g=.7)

    # ---- S10 EASIER TO UNDERSTAND: the cluttered site is torn away, a clear one underneath ----
    s = f.scene(c10, c11 + RIP, "newsprint", 25)
    f.slide_in(s, c10)
    f.enter(f.el(80, 600, 920, site_structured(920), rot=-1, z=10), c10, "none")
    messy = f.el(80, 600, 920, site_messy(920), rot=1.5, z=12)
    f.enter(messy, c10, "none")
    q = f.el(560, 1180, 380, '<div class="mk red" style="font-size:52px">where do I click?</div>', rot=-6, z=30)
    f.enter(q, wt(9, "make"), "snap", sfx=False)
    f.sfx(wt(9, "make"), "draw")
    f.cut(s, wt(9, "business"), 1.4, 600, 880)
    te = wt(9, "easier")
    f.cut(s, te - .1, 1.0)
    f.leave(messy, te - .1, dx=-300, dy=-1700, d=.25)
    f.leave(q, te - .1, dx=500, dy=-1600, d=.25)
    f.sfx(te - .1, "rip")
    f.slam(["EASIER TO", "UNDERSTAND."], 300, [te, wt(9, "to", 1), wt(9, "understand…")], 116)
    f.rip_out(s, c11)

    # ---- S11 EASIER TO DO: the tangle clears into three steps ----
    s = f.scene(c11, c12, "cream", 24)
    tangle = []
    for txt, x, y, r in [("EMAIL", 110, 560, -8), ("COPY", 620, 520, 7), ("SHEET", 160, 980, 5), ("???", 640, 1010, -6), ("PASTE", 400, 770, 3)]:
        i = f.el(x, y, 260, chip(txt, 66, "kraft"), rot=r, z=20)
        f.enter(i, c11, "none")
        tangle.append(i)
    tg = f.id("p")
    scrib = f.el(120, 520, 860, f'<svg viewBox="0 0 860 640" width="860" height="640"><path id="{tg}" pathLength="1" class="pen red" '
                 f'd="M120,90 C400,20 600,300 560,90 C520,-40 230,400 150,480 C60,560 700,620 650,500 C600,380 300,260 420,250 '
                 f'C540,240 700,540 130,520"/></svg>', z=15, boil=.8)
    f.enter(scrib, c11, "none")
    f.draw(tg, c11, .4)
    te = wt(10, "easier")
    for k, i in enumerate(tangle + [scrib]):
        f.leave(i, te - .15 + (k % 3) * .04, dy=int(f.r(-1700, -900)), d=.25)
    f.sfx(te - .15, "whoosh", 1.0)
    f.slam(["EASIER TO DO."], 330, [te, wt(10, "to"), wt(10, "do.")], 120)
    ts = wt(10, "do.") + .1
    for k, (txt, y) in enumerate([("INQUIRY", 560), ("CHECK", 790), ("NEXT STEP", 1020)]):
        f.enter(f.row(y, f'<div style="transform:rotate({f.r(-2, 2):.1f}deg)">{chip(txt, 84, "ink")}</div>'), ts + k * .22, "snap", g=.8)
        if k:
            pid = f.id("p")
            f.enter(f.el(510, y - 120, 60, arrow_down(pid, 104), z=15, boil=.6), ts + k * .22 - .1, "none")
            f.draw(pid, ts + k * .22 - .1, .1, sfx=None)
    f.enter(f.el(760, 1030, 64, '<div class="tick">✓</div>', z=45, boil=.4), ts + .72, "slam", g=.7)

    # ---- S12 black: the question ----
    s = f.scene(c12, c13, "ink", 26)
    f.slam(["WHAT WOULD YOU", "MAKE WORK", "~better?"], 600, [wt(11, w) for w in "What would you make work better?".split()], 138, tone="cr", gap=175)

    # ---- S13 end card ----
    s = f.scene(c13, TOTAL, "cream", 27)
    f.slide_in(s, c13)
    last = f.ransom("ROUNDHOUSE", 700, c13 + .3, size=100)
    tape_at(f, 150, 670, -8, last + .3, w=170)
    cta = f.row(930, strip("TELL US ABOUT YOUR PROJECT →", 42, "verm", font="Inter", extra="font-weight:800;letter-spacing:.5px;padding:24px 36px 22px"))
    tcta = last + .55
    f.enter(cta, tcta, "slam", g=.8)
    for b in beats(tcta + .6, TOTAL - .4, 2):
        f.js.append(f'tl.set("#{cta}", {{x: 12}}, {b:.3f}); tl.to("#{cta}", {{x: 0, duration: .25, ease: st("power2.out", .25)}}, {b + .001:.3f});')

    # ---- captions: the narration, 2-4 words at a time, current word lit ----
    caps = []
    for li, (row, t0) in enumerate(zip(vo, VO_AT)):
        words = [dict(w, s=w["s"] + t0, e=w["e"] + t0) for w in row["words"]]
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 4 or w["w"][-1] in ".,;:?!…" or (len(cur) >= 3 and sum(len(x["w"]) for x in cur) > 16):
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        for j, ch in enumerate(chunks):
            s0 = ch[0]["s"] - .05
            nxt = chunks[j + 1][0]["s"] - .05 if j + 1 < len(chunks) else ch[-1]["e"] + .25
            cid = f.id("c")
            spans = "".join(f'<span class="w" id="{cid}w{n}">{x["w"]}</span>' for n, x in enumerate(ch))
            caps.append(f'<div class="clip cap" id="{cid}" data-start="{s0:.3f}" data-duration="{max(.2, nxt - s0):.3f}" data-track-index="5" '
                        f'style="z-index:800"><div class="strip ink" id="{cid}s">{spans}</div></div>')
            f.js.append(f'tl.fromTo("#{cid}s", {{scale: 1.1}}, {{scale: 1, duration: .17, ease: st("power2.out", .17)}}, {s0:.3f});')
            for n, x in enumerate(ch):
                f.js.append(f'tl.set("#{cid}w{n}", {{color: "{SUN}"}}, {x["s"]:.3f}); tl.set("#{cid}w{n}", {{color: "{CREAM}"}}, {x["e"] + .02:.3f});')
    f.gap = c5
    return f, caps


def wobble(rng, w, h):
    cx, cy, rx, ry = w / 2, h / 2, w / 2 - 10, h / 2 - 10
    pts = []
    for i in range(41):
        a = -math.pi / 2 + i / 36 * 2 * math.pi
        k = 1 + 0.04 * math.sin(i * 0.9) + rng.normal(0, 0.012)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return f"M{pts[0][0]:.1f},{pts[0][1]:.1f} " + " ".join(f"L{x:.1f},{y:.1f}" for x, y in pts[1:])


def paper_assets(pd):
    os.makedirs(pd, exist_ok=True)

    def save(name, im, **kw):
        p = os.path.join(pd, name)
        if not os.path.exists(p):
            im.save(p, **kw)

    for k, c in STOCK.items():
        save(f"bg_{k}.jpg", card(c, W, H, seed=len(k) * 7), quality=90)
        save(f"{k}.jpg", card(c, 900, 600, seed=len(k) * 3), quality=90)
    save("tape.png", tape(220, 64, 3))
    for v, col in enumerate(("newsprint", "kraft")):
        save(f"scrap{v}.png", scrap(420, 340, seed=40 + v, color=STOCK[col]))
    # right half of the opening frame: kraft sheet with a torn left edge
    from paper import torn_mask, with_shadow
    if not os.path.exists(os.path.join(pd, "half_kraft.png")):
        k = card(STOCK["kraft"], 600, 2000, seed=12).convert("RGBA")
        k.putalpha(torn_mask(600, 2000, seed=4, tear=16, edges="l"))
        with_shadow(k, pad=0, off=(-8, 0), blur=10).save(os.path.join(pd, "half_kraft.png"))
    # the two pieces that join: one torn sheet split down a jagged seam, cream (front) and kraft (back)
    if not os.path.exists(os.path.join(pd, "piece_l.png")):
        from PIL import ImageDraw
        w, h = 445, 560
        rng = np.random.default_rng(8)
        seam = [(w - 6 + rng.normal(0, 7), y) for y in range(0, h + 1, 20)]
        for name, col, side in (("piece_l.png", STOCK["white"], "l"), ("piece_r.png", STOCK["kraft"], "r")):
            im = card(col, w, h, seed=3 if side == "l" else 5).convert("RGBA")
            d = ImageDraw.Draw(im)
            if side == "l":  # customer side: a clean page, headline + button
                d.rounded_rectangle((40, 50, 260, 70), 10, fill=(207, 200, 187))
                d.rounded_rectangle((40, 110, 400, 150), 12, fill=(22, 21, 19))
                d.rounded_rectangle((40, 170, 330, 210), 12, fill=(22, 21, 19))
                d.rounded_rectangle((40, 250, 360, 262), 6, fill=(207, 200, 187))
                d.rounded_rectangle((40, 280, 300, 292), 6, fill=(207, 200, 187))
                d.rounded_rectangle((40, 330, 230, 380), 25, fill=(228, 71, 43))
                d.rectangle((40, 420, 400, 520), fill=(47, 74, 208))
                poly = [(0, 0)] + [(x, y) for x, y in seam] + [(0, h)]
            else:  # team side: a grid of cells, scribbles
                x0 = 60
                for r in range(9):
                    for c in range(4):
                        d.rectangle((x0 + c * 90, 50 + r * 52, x0 + c * 90 + 90, 50 + r * 52 + 52), outline=(90, 70, 50), width=2)
                d.line((80, 300, 360, 340), fill=(228, 71, 43), width=6)
                d.line((90, 360, 300, 260), fill=(228, 71, 43), width=6)
                poly = [(x - w + 12, y) for x, y in seam] + [(w, h), (w, 0)]
                poly = [(max(0, x), y) for x, y in poly[:-2]] + [(w, h), (w, 0)]
            m = Image.new("L", (w, h), 0)
            ImageDraw.Draw(m).polygon(poly, fill=255)
            im.putalpha(m)
            with_shadow(im, pad=0, off=(6, 10), blur=8).save(os.path.join(pd, name))
    if not os.path.exists(os.path.join(pd, "grain.png")):
        rng = np.random.default_rng(2)
        g = (rng.random((300, 300)) * 255).astype(np.uint8)
        Image.fromarray(255 - (g > 200).astype(np.uint8) * 90 - (rng.random((300, 300)) * 40).astype(np.uint8)).convert("L").save(os.path.join(pd, "grain.png"))


def write():
    f, caps = build()
    os.makedirs(PROJ, exist_ok=True)
    pd = os.path.join(PROJ, "assets", "paper")
    paper_assets(pd)
    fd = os.path.join(PROJ, "assets", "fonts")
    shutil.copytree(os.path.join(HERE, "fonts"), fd, dirs_exist_ok=True)
    jd = os.path.join(PROJ, "assets", "js")
    os.makedirs(jd, exist_ok=True)
    shutil.copy(os.path.join(ENGINE, "data", "gsap.min.js"), jd)

    scenes = []
    for sc in f.scenes:
        sid, s0, s1 = sc["id"], sc["start"], sc["end"]
        scenes.append(f'<div class="clip scene" id="{sid}" data-start="{s0:.3f}" data-duration="{s1 - s0:.3f}" data-track-index="1" '
                      f'data-layout-allow-overlap data-layout-allow-overflow style="z-index:{sc["z"]}"><div class="wrap" id="{sid}w">'
                      f'<div class="cam" id="{sid}c"><div class="camk" id="{sid}k"><div class="cams" id="{sid}x"><img class="bg" src="assets/paper/bg_{sc["bg"]}.jpg">'
                      f'{"".join(sc["body"])}</div></div></div></div></div>')
    css = CSS.replace("WW", str(W)).replace("HH", str(H)).replace("CAPY", str(CAP_Y))
    tail = f"""
tl.fromTo("#grain", {{"--gx": 0}}, {{"--gx": 1, duration: {TOTAL}, ease: jit(5, {TOTAL})}}, 0);
tl.fromTo("#grain", {{"--gy": 0}}, {{"--gy": 1, duration: {TOTAL}, ease: jit(9, {TOTAL})}}, 0);
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
"""
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width={W}, height={H}">
<script src="assets/js/gsap.min.js"></script>
<style>{css}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}" data-fps="30">
{''.join(scenes)}
{''.join(caps)}
<div id="grain"></div><div id="vig"></div>
<audio id="mix" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9" src="assets/audio/mix.wav"></audio>
</div>
<script>
{JS_HEAD}
{chr(10).join(f.js)}
{tail}
</script></body></html>"""
    open(os.path.join(PROJ, "index.html"), "w", encoding="utf-8").write(html)
    json.dump({"vo_at": VO_AT, "sfx": sorted(f.ev, key=lambda e: e["t"]), "drop": DROP, "gap": f.gap, "bpm": BPM, "total": TOTAL},
              open(os.path.join(OUT, "cues.json"), "w"), indent=0)
    print(f"{len(f.scenes)} scenes, {len(caps)} captions, {len(f.ev)} sfx cues")


if __name__ == "__main__":
    write()
