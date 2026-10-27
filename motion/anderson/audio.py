#!/usr/bin/env python3
"""Score + sound design + mix for 'The woman who cleared the glass'.
Built like a documentary reel: a low drone and string ostinato that never stops moving, ticking tension,
a whoosh on every cut, a hit on every reveal, silence just before each punchline, and dense period foley.
usage: python3 motion/anderson/audio.py <vo_dir> <out_wav>"""
import importlib.util, json, os, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "audio"))
from dsp import SR, adsr, bp, bp_sweep, convolve, glide, hp, ir, lp, mtof, noise, osc, pan, pan_move, perc, place, t_, widen  # noqa: E402
from sfx import boom, metal, reverse_swell, riser, whoosh, mech_click  # noqa: E402
_spec = importlib.util.spec_from_file_location("paxton_audio", os.path.join(HERE, "..", "paxton", "audio.py"))
_pax = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_pax)
piano, strings, paper, clank, step = _pax.piano, _pax.strings, _pax.paper, _pax.clank, _pax.step

DUR = 59.0   # replaced below from the voice-over
N = int(SR * DUR)
BPM = 104; B = 60 / BPM; S16 = B / 4
VO = {m["id"]: m for m in json.load(open(os.path.join(HERE, "vo.json")))}
W = lambda cid, n=0: VO[cid]["words"][min(n, len(VO[cid]["words"]) - 1)]
END = lambda cid: VO[cid]["t"] + VO[cid]["dur"]
SWEEP = W("clear", 3) - .05
FADE = END("still") + 1.1
DUR = round(END("still") + 3.2, 2); N = int(SR * DUR)
# scene cuts (same as the film)
CUTS = [W("hook2", 6) - .08, W("ny", 0) - .1, W("cantsee", 0) - .12, W("only", 0) - .1, W("watch", 0) - .08, W("watch", 1) - .06,
        W("name", 0) - .1, W("engineer", 0) - .1, W("follows", 0) - .08, W("follows", 1) - .05, W("sketch", 0) - .1, W("lever", 0) - .1,
        W("turn", 0) - .1, W("patent", 0) - .1, W("sell", 0) - .1, W("canada", 0) - .1, W("nobody", 0) - .08, W("expire", 0) - .1,
        W("standard", 0) - .1, W("profit", 0) - .1, W("every", 0) - .12]
# blank paper frames: everything drops out
DROPS = [(W("watch", 0) - .2, W("watch", 1) - .06), (W("follows", 0) - .2, W("follows", 1) - .05), (W("nobody", 0) - .25, W("expire", 0) - .1),
         (SWEEP - .3, SWEEP + .12)]
# D minor: Dm · B♭ · Gm · A (tension) — then Dm · B♭ · F · C (release) for the ending
TENSE = [38, 34, 31, 33]; WARM = [38, 34, 41, 36]

def mixx(*xs):
    out = np.zeros(max(len(x) for x in xs))
    for x in xs: out[:len(x)] += x
    return out

# ---------------- instruments ----------------
def stac(f, g=.1, d=.22, cut=1400):          # staccato low strings (the ostinato)
    x = sum(osc(f * 2 ** (c / 1200), d, "saw") for c in (-8, 0, 7)) / 3
    return lp(x, cut) * perc(d, .006, .07) * g

def drone(m, d, g=.08, cut=500):              # cello / sub drone that swells and breathes
    t = t_(d); x = sum(osc(mtof(m) * 2 ** (c / 1200) * (1 + .002 * np.sin(2 * np.pi * 4.6 * t + c)), d, "saw") for c in (-6, 0, 5)) / 3
    sub = osc(mtof(m - 12), d) * .9
    return (lp(x, cut) + sub) * adsr(d, min(1.2, d / 3), 1, .9, min(1.4, d / 3)) * (0.85 + .15 * np.sin(2 * np.pi * .25 * t)) * g

def kick(g=.5):
    d = .45; return np.tanh(mixx(osc(glide(130, 42, d, .25), d) * perc(d, .002, .16), lp(noise(.02), 2000) * perc(.02, .0005, .004) * .4) * 1.6) * g

def tick(g=.05, f=5200):
    d = .03; return bp(noise(d), f * .7, f * 1.4) * perc(d, .0003, .004) * g

def hit(g=.6, f0=55):                          # cinematic impact: sub drop + body + metallic tail
    d = 2.6; body = osc(glide(f0 * 1.6, f0 * .55, d, .2), d) * perc(d, .002, .55)
    thump = lp(noise(.25), 400) * perc(.25, .001, .05) * 1.2
    crack = hp(noise(.05), 2500) * perc(.05, .0003, .01) * .5
    x = mixx(np.tanh(body * 1.8), thump, crack, metal(2.2, 92, .25))
    return x * g

def braam_hit(g=.4):
    d = 2.2; x = np.zeros(int(SR * d))
    for m in (26, 38, 45):
        for c in (-10, 0, 9): x += osc(mtof(m) * 2 ** (c / 1200), d, "saw")
    return np.tanh(lp(x / 9, 700) * adsr(d, .015, .5, .55, .9) * 2.5) * g

def swish(d=.6, g=.08, lo=600, hi=3500):
    return bp_sweep(noise(d), lo, hi, 1.4) * adsr(d, .1, 1, .7, .25) * g

def squeak(d=.55, g=.06):                      # rubber on wet glass
    f = glide(820, 1350, d, .6) * (1 + .025 * np.sin(2 * np.pi * 31 * t_(d)))
    rough = np.abs(bp(noise(d), 500, 3000)) ** .3
    return (osc(f, d, "saw") * .3 + osc(f * 2.01, d) * .15) * rough * adsr(d, .05, 1, .8, .15) * g

def rain(d, g=.03, bright=6000, seed=1, drops=70):
    rng = np.random.default_rng(seed); x = bp(noise(d), 300, bright) * .45 + lp(noise(d), 300) * .25
    for _ in range(int(d * drops)):
        a = int(rng.uniform(0, max(.01, d - .05)) * SR); dd = .025
        dr = bp(noise(dd), rng.uniform(1500, 3500), 9000) * perc(dd, .0004, .005) * rng.uniform(.3, 1.8); x[a:a + len(dr)] += dr[: len(x) - a]
    return x * adsr(d, .3, 1, 1, .5) * g

def wind(d, g=.03, seed=3):
    t = t_(d); env = .5 + .5 * np.sin(2 * np.pi * .21 * t + seed) * np.sin(2 * np.pi * .09 * t + 1)
    return bp_sweep(noise(d), 250, 1500, 1.3) * env * adsr(d, .8, 1, 1, 1) * g

def bell(g=.12):                               # trolley bell: ding-ding
    a = clank(1250, 1)[: int(1.2 * SR)]; x = np.zeros(int(1.6 * SR)); x[:len(a)] += a; b = int(.22 * SR); x[b:b + len(a)] += a[: len(x) - b] * .8
    return x * g

def clop(g=.1):
    d = .12; return (bp(noise(d), 500, 2500) * perc(d, .001, .02) + osc(220, d) * perc(d, .001, .03) * .5) * g

def key(g=.06, seed=0):                        # typewriter key
    rng = np.random.default_rng(seed); d = .07
    return (bp(noise(d), 1500, 6500) * perc(d, .0004, .007) + osc(rng.uniform(150, 210), d) * perc(d, .001, .016) * .7) * g

def carriage(g=.08):
    d = .5; return mixx(bp(noise(d), 800, 3000) * adsr(d, .01, .6, .4, .1) * .5, clank(3100, 1)[: int(.9 * SR)] * .6) * g

def engine(d, f=38, g=.04):
    t = t_(d); x = osc(f * (1 + .05 * np.sin(2 * np.pi * .5 * t)), d, "saw") * (.6 + .4 * np.sin(2 * np.pi * 12 * t))
    return lp(x, 320) * adsr(d, .5, 1, 1, 1) * g

def horn(g=.07):                               # bulb horn
    d = .8; tt = t_(d); f = np.where(tt < .3, glide(240, 400, d, .4), 400 - (tt - .3) * 100)
    return bp(osc(f, d, "saw"), 300, 2200) * adsr(d, .03, 1, .8, .2) * g

def shutter(g=.12):                            # photo card lands: camera shutter
    return mixx(mech_click(2600, 1, 1), np.concatenate([np.zeros(int(.05 * SR)), mech_click(1800, .7, 2)])) * g

def pencil(d, g=.04):
    return bp(noise(d), 2500, 7500) * (np.abs(np.sin(2 * np.pi * 3.4 * t_(d))) ** 2) * (0.6 + .4 * np.sin(2 * np.pi * .7 * t_(d))) * g

def stamp(g=.5):
    return mixx(boom(.7, 150, 60, 1, .9), lp(noise(.12), 1200) * perc(.12, .0005, .03) * .8) * g

def heartbeat(g=.35):
    a = kick(1); x = np.zeros(int(.8 * SR)); x[:len(a)] += a; b = int(.22 * SR); x[b:b + len(a)] += a[: len(x) - b] * .6
    return lp(x, 300) * g

# ---------------- score ----------------
dropped = lambda t: any(a <= t < b for a, b in DROPS)

def score():
    m = np.zeros((N, 2)); stems = {}
    # 1) drone bed under everything, chord changes every 2 bars
    t = 0.
    while t < FADE + 1.2:
        bar = int(t / (B * 8)); prog = WARM if t > W("every", 0) - .2 else TENSE; root = prog[bar % 4]
        d = B * 8 + .8; g = .07 if t < W("ny", 0) else .085
        place(m, t, widen(drone(root + 12, d, g, 420 if t < W("lever", 0) else 650), .02, .8)); t += B * 8
    # 2) ostinato: 8ths in the story, 16ths in the builds
    sections = [(W("ny", 0) - .1, W("watch", 0) - .2, 2, .06), (W("watch", 1), W("follows", 0) - .2, 2, .045),
                (W("follows", 1), W("lever", 0), 2, .05), (W("lever", 0), SWEEP - .3, 4, .065),
                (W("patent", 0) + .3, W("nobody", 0) - .25, 2, .055), (W("expire", 0) - .1, W("profit", 0) - .2, 4, .07),
                (W("every", 0) - .1, FADE - .2, 4, .06)]
    for a, b, div, g in sections:
        k = int(np.ceil(a / (B / div)))
        while (tt := k * B / div) < b:
            if not dropped(tt):
                prog = WARM if tt > W("every", 0) - .2 else TENSE; root = prog[int(tt / (B * 8)) % 4]
                pat = [0, 12, 7, 12] if div == 2 else [0, 12, 7, 12, 0, 12, 10, 12]
                acc = 1.0 if k % (div * 2) == 0 else .7
                ramp = 1 + .6 * (tt - a) / max(1, b - a)
                place(m, tt, pan(stac(mtof(root + 12 + pat[k % len(pat)]), g * acc * ramp, cut=1100 + 900 * (tt - a) / max(1, b - a)), .25 * np.sin(k)))
            k += 1
    # 3) heartbeat / kick on beats in the tense parts, ticks on 16ths in the builds
    for a, b in [(W("ny", 0), W("watch", 0) - .2), (W("lever", 0), SWEEP - .3), (W("sell", 0), W("nobody", 0) - .25), (W("expire", 0), W("profit", 0) - .2), (W("every", 0), FADE - .3)]:
        k = int(np.ceil(a / B))
        while (tt := k * B) < b:
            if not dropped(tt): place(m, tt, pan(kick(.32 if k % 2 == 0 else .2)))
            k += 1
    for a, b in [(0, W("ny", 0) - .3), (W("lever", 0), SWEEP - .3), (W("canada", 0), W("nobody", 0) - .25), (W("every", 0), FADE - .3)]:
        k = int(np.ceil(a / S16))
        while (tt := k * S16) < b:
            if not dropped(tt): place(m, tt, pan(tick(.035 if k % 4 == 0 else .018), .3 if k % 2 else -.3))
            k += 1
    # 4) piano: sparse, high, lots of air — the emotion line
    MOT = [74, 69, 72, 69, 77, 76, 74, 69]
    for a, b, step_ in [(W("watch", 1), W("lever", 0) - .3, 2), (W("patent", 1), W("sell", 0), 2), (W("profit", 0) - .1, FADE + .5, 1)]:
        k = int(np.ceil(a / (B * step_)))
        while (tt := k * B * step_) < b:
            if not dropped(tt): place(m, tt, pan(piano(mtof(MOT[k % len(MOT)]), 3.0, .09), .4 * np.sin(k * 1.3)))
            k += 1
    place(m, W("nobody", 0), pan(piano(mtof(38), 3.4, .2) + piano(mtof(50), 3.4, .1)))      # lone low note under "Nobody"
    # 5) string swells into the big moments
    place(m, W("patent", 1), widen(strings([62, 65, 69, 74], 3.0, .07, 2200, .3)))
    place(m, W("standard", 6), widen(strings([62, 65, 69, 74], 2.6, .06, 2400, .2)))
    place(m, W("every", 0), widen(strings([50, 57, 62, 65, 69], FADE - W("every", 0) + .5, .075, 2600, 1.6)))
    place(m, FADE - .05, widen(strings([50, 57, 62, 65, 69, 74], 3.0, .06, 2400, .05)))
    place(m, FADE, pan(piano(mtof(74), 3.5, .16) + piano(mtof(62), 3.5, .1) + piano(mtof(50), 3.5, .09)))
    m = m + convolve(m, ir(2.4, 3.0, 6500)) * .4
    # silences: hard drop on the blank frames (with a short tail so it breathes)
    g = np.ones(N); tt = np.arange(N) / SR
    for a, b in DROPS:
        g *= 1 - np.clip(np.minimum((tt - a) / .06, (b - tt) / .04), 0, 1) * .97
    k = int(1.4 * SR); fade = np.ones(N); fade[-k:] = np.linspace(1, 0, k) ** 1.4
    return hp(m * (g * fade)[:, None], 28)

# ---------------- licensed track, cut to the story ----------------
TRACK = os.path.join(HERE, "music.mp3")   # "Documentary" by dailyvibe (Pixabay): soft intro, long build, breakdown, drop
T_BEAT, T_GRID0, T_DROP, T_BUILD = 60 / 117.3, .14, 94.13, 62.14   # beat length, first beat, the drop, a bar inside the build

def track():
    """Three beat-aligned pieces: intro -> build -> breakdown tail, so the drop lands on "Her patent runs out"."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", TRACK, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    P = T_BEAT; vdrop = W("expire", 0)
    off1 = (T_GRID0 - vdrop) % P                          # intro offset that puts its beats on the drop's grid
    k1 = round((vdrop - (W("lever", 0) - .1)) / P)          # first splice: near the lever cut
    k3 = 6                                                # breakdown tail: 6 beats before the drop
    cut1, cut2 = vdrop - k1 * P, vdrop - k3 * P
    pieces = [(0, cut1, off1), (cut1, cut2, T_BUILD - cut1), (cut2, DUR, T_DROP - vdrop)]   # (v0, v1, track = v + shift)
    out = np.zeros((N, 2)); xf = int(.04 * SR)
    for v0, v1, sh in pieces:
        a, b = int(v0 * SR), min(N, int(v1 * SR)); s0 = int((v0 + sh) * SR); seg = x[s0: s0 + (b - a)].copy()
        if a > 0: seg[:xf] *= np.linspace(0, 1, xf)[:, None]
        if b < N: seg[-xf:] *= np.linspace(1, 0, xf)[:, None]
        out[a: a + len(seg)] += seg
    tt = np.arange(N) / SR; g = np.ones(N)
    for a, b in DROPS: g *= 1 - np.clip(np.minimum((tt - a) / .05, (b - tt) / .03), 0, 1) * .97   # silence on the blank frames + before "clear"
    a0, a1 = W("lever", 0) - .3, SWEEP - .3                                                           # sit back under the lever/blade lines
    g *= 10 ** (-3 / 20 * np.clip(np.minimum((tt - a0) / .3, (a1 - tt) / .3), 0, 1))
    a0, a1 = W("profit", 0) - .2, W("every", 0) - .15                                                # dip for "never profits"
    g *= 10 ** (-7 / 20 * np.clip(np.minimum((tt - a0) / .4, (a1 - tt) / .4), 0, 1))
    k = int(2.2 * SR); g[-k:] *= np.linspace(1, 0, k) ** 1.6
    return out * g[:, None]

# ---------------- sound design ----------------
def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2)); rng = np.random.default_rng(11)
    def put(t0, x, p=0., rv=.25):
        s = x if x.ndim == 2 else pan(x, p); place(dry, t0, s); place(send, t0, s * rv)
    # every cut gets air: alternating whooshes, pitched to the moment
    for i, c in enumerate(CUTS):
        lo, hi = (250, 2600) if i % 2 else (400, 4200)
        put(c - .32, pan_move(whoosh(.5, lo, hi, .62, .09, False), -.6 if i % 2 else .6, .6 if i % 2 else -.6), 0, .25)
    # hook: rain on the windshield, wiper strokes, the tension hit on "a woman"
    NY = W("ny", 0) - .1
    put(0, widen(rain(NY + .2, .05)), 0, .3)
    for tt in (1.0, 2.9): put(tt, mixx(swish(.7, .08), squeak(.6, .035)), -.2 if tt < 2 else .2, .2)
    put(W("hook2", 0), mech_click(2400, .07), 0, .3)
    put(W("hook2", 6) - .5, reverse_swell(.5, .14), 0, 0); put(W("hook2", 6), hit(.5), 0, .4)
    put(NY - 1.2, riser(1.2, .1), 0, .2)
    # 1902: the city in sleet
    put(NY, widen(wind(W("watch", 0) - NY, .055)), 0, .4); put(NY, widen(rain(W("watch", 0) - NY, .02, 4000, 2, 40)), 0, .2)
    put(NY + .1, bell(.11), .3, .5)
    put(W("ny", 2), hit(.55, 50), 0, .45)
    put(W("ny", 0) - .05, shutter(.08), 0, .2)                                          # NEW YORK tag
    for k in range(12): put(W("crawl", 0) + .4 + k * .27, clop(.07 if k % 2 else .05), .4 - k * .05, .3)
    put(W("cantsee", 2), whoosh(.5, 2600, 300, .4, .07, False), 0, .3)                 # frost blur
    put(W("only", 6), heartbeat(.3), 0, .1)
    put(W("opens", 1) - .05, mech_click(700, .2), -.1, .2); put(W("opens", 1) + .12, clank(300, .05)[: int(.5 * SR)], -.1, .3)
    put(W("opens", 6) - .2, widen(wind(2.4, .12, 5)), 0, .3)                           # leans into the storm
    put(W("opens", 8), boom(1.2, 60, 30, .35, .2), 0, .4)
    # blank frames: one tick in the silence
    for cid in ("watch", "follows", "nobody"): put(W(cid, 0), tick(.12, 3000), 0, .7)
    # passenger: train interior rumble
    dd = W("name", 0) - W("watch", 1) + .2; put(W("watch", 1) - .06, widen(lp(noise(dd), 220) * .05 * adsr(dd, .3, 1, 1, .4)), 0, .2)
    # Mary: the photo card lands
    put(W("name", 0) - .1, mixx(paper(.45, .14), shutter(.12)), 0, .2)
    put(W("name", 3), mech_click(1500, .1), 0, .2); put(W("visiting", 3) - .05, mech_click(1200, .1), 0, .2)
    put(W("engineer", 2) - .02, hit(.35, 70), 0, .3)
    # sketch: pencil
    put(W("sketch", 0), pencil(W("lever", 0) - W("sketch", 0), .045), .2, .1)
    put(W("sketch", 2), paper(.4, .06), .2, .1)
    # lever & blade: metal mechanism + marker circles
    put(W("lever", 0), clank(900, .04)[: int(.6 * SR)], -.3, .2); put(W("lever", 1), mixx(mech_click(800, .25), clank(500, .05)[: int(.5 * SR)]), .3, .2)
    put(W("blade", 0), mixx(mech_click(1200, .2, 2), swish(.35, .05, 1500, 5000)), -.3, .2)
    put(W("lever", 1), pencil(.45, .05), .3, .1); put(W("blade", 1), pencil(.6, .05), -.3, .1)
    # clear: tick-tock build, silence, then the sweep and the hit
    put(SWEEP - 1.6, riser(1.6, .14), 0, .2)
    put(SWEEP - .05, mixx(swish(.9, .16, 400, 4500), squeak(.8, .07)), 0, .3)
    put(SWEEP + .15, hit(.7, 50), 0, .5); put(SWEEP + .2, braam_hit(.18), 0, .4)
    put(SWEEP + .15, metal(2.4, 880, .05), 0, .7)                                      # the glass rings
    # 1903: stamp + hit
    put(W("patent", 0) - .1, paper(.6, .12), 0, .2)
    put(W("patent", 1) - .45, reverse_swell(.45, .14), 0, 0)
    put(W("patent", 1), stamp(.5), 0, .3); put(W("patent", 1), hit(.45, 55), 0, .4)
    put(W("patent", 5) - .05, pencil(.5, .05), 0, .1)
    # sell it: footsteps + the street
    put(W("sell", 0) - .1, widen(bp(noise(W("canada", 0) - W("sell", 0) + .2), 250, 2500) * .012), 0, .3)
    t = W("sell", 0)
    while t < W("canada", 0) - .2: put(t, step(.15), rng.uniform(-.2, .2), .3); t += .5
    # letter: typewriter, line returns, the rejection lands
    t0 = W("canada", 0) - .1; t = t0 + .05; n = 0
    while t < W("nobody", 0) - .4:
        put(t, key(rng.uniform(.05, .08), n), rng.uniform(-.2, .2), .15); t += rng.uniform(.055, .11); n += 1
        if n % 28 == 0: put(t, carriage(.07), .3, .2); t += .25
    put(W("canada", 2), shutter(.07), 0, .2)
    put(W("canada", 7), boom(.9, 80, 40, .3, .3), 0, .3)
    put(W("nobody", 0), hit(.5, 42), 0, .55)                                           # the drop
    # 1920: the modern city roars in
    E0 = W("expire", 0) - .1
    put(E0 - .5, reverse_swell(.5, .16), 0, 0)
    put(E0, widen(engine(W("standard", 0) - E0 + .2, 40, .035) + bp(noise(W("standard", 0) - E0 + .2), 200, 2400) * .014), 0, .3)
    put(W("expire", 5) - .4, reverse_swell(.4, .12), 0, 0); put(W("expire", 5), hit(.55, 55), 0, .45)
    put(W("roads", 2), horn(.06), .4, .4); put(W("roads", 5), horn(.04), -.5, .5)
    # standard: rain, a period wiper, hit on the word
    put(W("standard", 0) - .1, widen(rain(W("profit", 0) - W("standard", 0) + .1, .03, 5000, 4)), 0, .3)
    put(W("standard", 6) - .15, mixx(swish(.6, .09), squeak(.5, .035)), 0, .2)
    put(W("standard", 6), hit(.45, 60), 0, .4)
    # profit: a quiet room, a clock
    put(W("profit", 0) - .1, paper(.4, .08), 0, .2)
    for k in range(int((W("every", 0) - W("profit", 0)) / .5)): put(W("profit", 0) + k * .5, tick(.05 if k % 2 else .035, 2800), .5, .4)
    put(W("profit", 1), hit(.3, 45), 0, .5)
    # still moving: night rain, the wiper rhythm, the last hit
    ST = W("every", 0) - .12
    put(ST - .6, reverse_swell(.6, .16), 0, 0)
    put(ST, widen(rain(FADE - ST + 1, .03, 7000, 5)), 0, .3)
    t = ST + .5
    while t < FADE - .3: put(t, mixx(swish(.7, .05), squeak(.6, .018)), .25 if int(t * 10) % 2 else -.25, .2); t += 1.45
    put(W("still", 3) - .4, reverse_swell(.4, .14), 0, 0); put(W("still", 3), hit(.55, 50), 0, .5)
    put(FADE, paper(.5, .08), 0, .3)
    return hp(dry + convolve(send, ir(1.6, 2.2, 6000)) * .7, 30)

# ---------------- mix ----------------
def voice_chain(x):
    """Documentary narrator polish: low-cut, a little chest, presence, de-harsh, gentle compression."""
    x = hp(x, 70)
    lowmid = bp(x, 110, 220); pres = bp(x, 2500, 5000); harsh = bp(x, 6500, 9500)
    x = x + lowmid * .12 + pres * .15 - harsh * .15
    env = np.abs(signal.hilbert(x)); env = signal.sosfiltfilt(signal.butter(1, 12, "lowpass", fs=SR, output="sos"), env)
    thr = np.percentile(env[env > 1e-4], 70); gain = np.where(env > thr, (thr / (env + 1e-9)) ** .45, 1.0)
    return x * gain

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = voice_chain(x); x = x / (np.abs(x).max() + 1e-9) * .85; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.45, .7, 5000)) * .12
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 4, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    if os.path.exists(TRACK):
        music = track(); music = music - bp(music, 1000, 4000) * .45 * 1.0   # pocket for the voice
        mlev = .17
    else: music = score(); mlev = .4
    sfx = design()
    buses = {"vo": v, "sfx": sfx / (np.abs(sfx).max() + 1e-9) * .85 * (1 - .4 * d), "music": music / (np.abs(music).max() + 1e-9) * mlev * (1 - .6 * d)}
    mix = sum(buses.values())
    fade = np.ones(N); k = int(.8 * SR); fade[-k:] = np.linspace(1, 0, k) ** 1.5
    mix = np.tanh(mix * fade[:, None] / (np.abs(mix).max() + 1e-9) * 1.25) * .9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    a_ = signal.sosfilt(sos, buses["vo"].mean(1)); r_ = signal.sosfilt(sos, (buses["sfx"] + buses["music"]).mean(1))
    rows = []
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        rows.append((20 * np.log10((np.sqrt(np.mean(a_[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(r_[i0:i1] ** 2)) + 1e-9)), m["t"], m["text"]))
    for db, t, txt in sorted(rows)[:5]: print(f"{t:6.2f}s {db:5.1f} dB  {txt}")
    print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
