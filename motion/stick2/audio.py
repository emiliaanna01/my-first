#!/usr/bin/env python3
"""Dark mystery score + sound design + mix for the D.B. Cooper stick-figure reel.
Score: 80 BPM, D minor — low string drone, a heartbeat-like pulse that builds to the jump, sparse piano, steady rain and
distant thunder. Silence on "He disappears.", a cold quiet aftermath, a single piano note on "nobody knows".
usage: python3 motion/stick2/audio.py <vo_dir> <out_wav>"""
import importlib.util, json, os, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "audio"))
from dsp import SR, adsr, bp, convolve, glide, hp, ir, lp, mtof, noise, osc, pan, perc, place, t_, widen  # noqa: E402
_spec = importlib.util.spec_from_file_location("pax", os.path.join(HERE, "..", "paxton", "audio.py"))
_pax = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_pax); piano, strings = _pax.piano, _pax.strings

CUT = json.load(open(os.path.join(HERE, "cut.json"))); ST = CUT["starts"]; DUR = float(sum(CUT["durs"])); N = int(SR * DUR)
VO = {m["id"]: m for m in json.load(open(os.path.join(HERE, "vo.json")))}
W = lambda s, n: VO[s]["words"][min(n, len(VO[s]["words"]) - 1)]
B = 60 / 80
JUMP, GONE, AFTER, END = ST[8], ST[9], ST[10], ST[14]
PROG = [[38, 45, 50, 53], [34, 41, 46, 50], [36, 43, 48, 52], [33, 40, 45, 49]]   # Dm · B♭ · C · A

def es(sid, **kw):
    cdir = os.environ.get("SFX_CACHE", "/tmp/sfxcache"); os.makedirs(cdir, exist_ok=True)
    f = os.path.join(cdir, (sid + "".join(f"_{k}{v}" for k, v in sorted(kw.items()))).replace("/", "_") + ".wav")
    if not os.path.exists(f):
        subprocess.run(["earshot", "sfx", "render", sid, "-o", f, "--sr", str(SR)] + sum([[f"--{k}", str(v)] for k, v in kw.items()], []), check=True, capture_output=True)
    x, _ = sf.read(f); return x.mean(1) if x.ndim > 1 else x

def thump(g=.4):
    d = .5; return np.tanh(osc(glide(70, 42, d, .3), d) * perc(d, .003, .16) * 1.4) * g

def rain(d, g=.03, seed=1):
    rng = np.random.default_rng(seed); x = bp(noise(d), 400, 6000) * .5 + lp(noise(d), 300) * .2
    for _ in range(int(d * 50)):
        a = int(rng.uniform(0, d - .05) * SR); dr = bp(noise(.025), 2000, 9000) * perc(.025, .0004, .005) * rng.uniform(.3, 1.4); x[a:a + len(dr)] += dr[: len(x) - a]
    return x * adsr(d, .8, 1, 1, 1.2) * g

def thunder(d=4.0, g=.12, seed=2):
    rng = np.random.default_rng(seed); x = lp(noise(d), 220) * (np.exp(-t_(d) / 1.6))
    for _ in range(5): a = int(rng.uniform(0, 1.2) * SR); x[a:] += lp(noise(d)[: len(x) - a], 500) * np.exp(-t_(d)[: len(x) - a] / .4) * rng.uniform(.3, .8)
    return x * adsr(d, .15, 1, 1, .5) * g

def engine(d, g=.05):
    t = t_(d); x = bp(noise(d), 200, 1800) * .6 + osc(110 * (1 + .01 * np.sin(2 * np.pi * .3 * t)), d, "saw") * .15
    return lp(x, 1500) * adsr(d, .6, 1, 1, .8) * g

def score():
    m = np.zeros((N, 2))
    def put(t, x, g=1., p=0.):
        place(m, t, x * g if x.ndim == 2 else pan(x * g, p))
    t = 0.
    while t < END - .2:                                                      # drone, chord every 2 bars
        bar = int(t / (8 * B)); ch = PROG[bar % 4]; d = min(8 * B + .6, END + .3 - t)
        if not GONE - .1 <= t < AFTER:
            put(t, widen(strings([ch[0], ch[1]], d, .07 if t < AFTER else .05, 600, 1.0), .02, .8))
        t += 8 * B
    for k in range(int(END / B)):                                            # heartbeat pulse, faster and louder into the jump
        t = k * B
        if t < ST[2] or GONE - .3 <= t < AFTER + 2 or t >= END - 1: continue
        g = .22 + .25 * np.clip((t - ST[2]) / (JUMP - ST[2]), 0, 1) if t < GONE else .16
        put(t, thump(g));
        if ST[6] <= t < GONE - .3: put(t + B / 2, thump(g * .55))
    MOT = [62, 65, 69, 67, 65, 64]                                           # sparse piano
    for k in range(int(END / (4 * B))):
        t = k * 4 * B + 2 * B
        if t < ST[1] or GONE - .5 <= t < AFTER or t >= END - .5: continue
        put(t, piano(mtof(MOT[k % len(MOT)]), 3.0, .07), 1., .3 * np.sin(k))
    put(JUMP - 1.6, es("riser/dark", dur=1.6), .35)                          # into the jump
    put(GONE + .02, es("impact/deep"), .5)                                    # "He disappears."
    put(END + .1, piano(mtof(50), 4.0, .14) + piano(mtof(62), 4.0, .08))      # "...nobody knows."
    put(END + .1, widen(strings([38, 45], 4.0, .05, 500, .8)))
    m = m + convolve(m, ir(2.4, 3.2, 5000)) * .35
    g = np.ones(N); k = int(2.0 * SR); g[-k:] = np.linspace(1, 0, k) ** 1.4
    return hp(m * g[:, None], 28)

def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2))
    def put(t0, x, p=0., rv=.25):
        s = x if x.ndim == 2 else pan(x, p); place(dry, t0, s); place(send, t0, s * rv)
    def hit(sid, t, g, p=0., **kw):
        x = es(sid, **kw); pk = np.argmax(np.abs(x)) / SR; put(t - pk, x * g, p, .25)
    put(0, widen(rain(ST[1] + .5, .045)), 0, .3); put(.4, widen(thunder(4.5, .14)), 0, .4)           # S01 storm
    put(0, widen(bp(noise(ST[1]), 300, 2500) * adsr(ST[1], .5, 1, 1, .8) * .03), 0, .2)               # wind on the canopy
    for i in range(1, 15): hit("whoosh_fast/crisp" if i % 2 else "swipe/paper", ST[i] + .04, .22, .3 * np.sin(i))
    hit("swipe/paper", ST[1] + .4, .35); hit("pro_typing_run/soft", ST[1] + 1.4, .2, dur=1.2)          # case board
    put(ST[2], widen(rain(ST[3] - ST[2], .02, 3)), 0, .3)                                               # terminal, rain on glass
    for k in range(6): hit("knock/desk", ST[2] + .5 + k * .55, .12, .2)                                 # footsteps
    put(ST[3], widen(engine(ST[7] - ST[3], .035)), 0, .2)                                                # cabin hum
    hit("pro_tap/glass", ST[3] + .9, .3); hit("swipe/flick", W("S04", 8), .35)                            # drink, note
    hit("toggle/latch", ST[4] + .5, .5, -.2); hit("toggle/latch", ST[4] + .7, .45, .2)                  # briefcase
    hit("sub_drop/punch", W("S05", 5), .45)                                                              # "bomb"
    hit("swipe/velvet", ST[5] + .5, .35); hit("swipe/paper", ST[5] + 1.4, .3)                            # cash bundles
    put(ST[6], widen(rain(ST[7] - ST[6], .03, 4)), 0, .3)                                                # tarmac in the rain
    put(ST[7] - .2, widen(engine(ST[8] - ST[7] + .6, .09)), 0, .3); hit("whoosh_big/jet", ST[7] + .8, .4)   # takeoff
    put(JUMP, widen(bp(noise(GONE - JUMP), 200, 3000) * adsr(GONE - JUMP, 1.2, 1, 1, .3) * .07), 0, .2)   # wind roaring in the open door
    hit("whoosh_big/deep", JUMP + 4.3, .5)                                                               # the jump
    put(GONE, widen(rain(ST[11] - GONE, .03, 5)), 0, .4); put(GONE + .5, widen(thunder(4.0, .1, 7)), 0, .5)
    put(AFTER, widen(bp(noise(ST[11] - AFTER), 200, 1200) * adsr(ST[11] - AFTER, .8, 1, 1, .8) * .025), 0, .2)   # river
    hit("swipe/velvet", AFTER + 2.6, .3); hit("swipe/paper", AFTER + 3.6, .3)                            # finds the cash
    hit("swipe/paper", ST[11] + .4, .35); hit("swipe/paper", ST[12] + 1.2, .35); hit("knock/desk", ST[12] + 2.6, .3)   # files
    put(ST[13], widen(rain(END - ST[13] + 1, .02, 6)), 0, .4); hit("whoosh_big/swell", ST[13] + 2.5, .2)   # fog road, car passing
    return hp(dry + convolve(send, ir(1.4, 2.0, 6000)) * .6, 30)

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 70); x = x + bp(x, 2500, 5000) * .2 + bp(x, 100, 220) * .12; x = x / (np.abs(x).max() + 1e-9) * .85; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.4, .6, 5000)) * .1
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 4, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    mus = score(); mus = mus - bp(mus, 1200, 3800) * .3; mus = mus / (np.abs(mus).max() + 1e-9)
    sfx = design(); sfx = sfx / (np.abs(sfx).max() + 1e-9)
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    vb = signal.sosfilt(sos, v.mean(1)); mb = signal.sosfilt(sos, (mus * .45 * (1 - .42 * d)).mean(1))
    tt = np.arange(N) / SR; ride = np.ones(N)
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        dm = 20 * np.log10((np.sqrt(np.mean(vb[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(mb[i0:i1] ** 2)) + 1e-9))
        if dm < 10: ride *= 10 ** ((dm - 10) / 20 * np.clip(np.minimum((tt - m["t"] + .25) / .25, (m["t"] + m["dur"] + .2 - tt) / .2), 0, 1))
    buses = {"vo": v, "sfx": sfx * .45 * (1 - .35 * d), "music": mus * ride[:, None] * .45 * (1 - .42 * d)}
    mix = sum(buses.values()); mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.25) * .9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    a_ = signal.sosfilt(sos, buses["vo"].mean(1)); r_ = signal.sosfilt(sos, (buses["music"] + buses["sfx"]).mean(1))
    rows = []
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        rows.append((20 * np.log10((np.sqrt(np.mean(a_[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(r_[i0:i1] ** 2)) + 1e-9)), m["id"]))
    for db, i in sorted(rows)[:4]: print(f"{i} {db:5.1f} dB")
    print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
