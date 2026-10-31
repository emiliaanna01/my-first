#!/usr/bin/env python3
"""Original score + paper-collage sound design + mix for the Jimmy Hoffa reel.
Score: vintage true-crime noir, 92 BPM, D minor — pizzicato upright bass, brushed snare, a ticking clock, sparse piano,
a low string drone. Silence on "Then he is gone.", a quieter search section, a final stop and piano chord on the last line.
Effects (earshot bank): a paper swipe on every cut, a desk knock / pin tap where each element lands (measured from the
clip motion), stamps on the stamped words, typing on name tags, phone rings, clock ticks, a closing impact.
usage: python3 motion/lustig/audio.py <vo_dir> <out_wav>"""
import importlib.util, json, os, subprocess, sys
import cv2, numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "audio"))
from dsp import SR, adsr, bp, convolve, glide, hp, ir, lp, mtof, noise, osc, pan, perc, place, t_, widen  # noqa: E402
_spec = importlib.util.spec_from_file_location("pax", os.path.join(HERE, "..", "paxton", "audio.py"))
_pax = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_pax); piano, strings = _pax.piano, _pax.strings

CUT = json.load(open(os.path.join(HERE, "cut.json")))
STARTS = np.cumsum([0] + CUT["durs"][:-1]); DUR = float(sum(CUT["durs"])); N = int(SR * DUR)
PLAN = {p[0]: p for p in CUT["plan"]}                         # i -> (i, ws, we, speed, d)
BPM = 92; B = 60 / BPM; S16 = B / 4
PROG = [[50, 53, 57], [46, 50, 53], [43, 46, 50], [45, 49, 52]]   # Dm · B♭ · Gm · A
GONE = STARTS[20]; SEARCH0 = STARTS[21]; FINAL = STARTS[26]

def es(sid, **kw):
    cdir = os.environ.get("SFX_CACHE", "/tmp/sfxcache"); os.makedirs(cdir, exist_ok=True)
    f = os.path.join(cdir, (sid + "".join(f"_{k}{v}" for k, v in sorted(kw.items()))).replace("/", "_") + ".wav")
    if not os.path.exists(f):
        subprocess.run(["earshot", "sfx", "render", sid, "-o", f, "--sr", str(SR)] + sum([[f"--{k}", str(v)] for k, v in kw.items()], []), check=True, capture_output=True)
    x, _ = sf.read(f); return x.mean(1) if x.ndim > 1 else x

def mixx(*xs):
    out = np.zeros(max(len(x) for x in xs))
    for x in xs: out[:len(x)] += x
    return out

def out_t(i, src_t):                                          # source time in clip i -> film time
    _, ws, we, sp, d = PLAN[i]; return STARTS[i - 1] + min(d, max(0, (src_t - ws) / sp))

# ---------------- music ----------------
def pizz(f, g=.3):
    d = .7; t = t_(d); x = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (6 + 3 * k)) for k, a in [(1, 1), (2, .45), (3, .2)])
    return lp(x + lp(noise(d), 900) * perc(d, .001, .01) * .3, 1400) * perc(d, .002, .45) * g

def brush(g=.05, d=.22):
    return bp(noise(d), 2500, 9000) * adsr(d, .03, .4, .3, .1) * g

def score():
    m = np.zeros((N, 2))
    def put(t, x, g=1., p=0.):
        place(m, t, (x * g) if x.ndim == 2 else pan(x * g, p))
    nb = int(DUR / B) + 1
    for k in range(nb):
        t = k * B
        if GONE - .05 <= t < SEARCH0 or t >= FINAL - .05: continue
        bar = k // 4; ch = PROG[bar % 4]; quiet = t >= SEARCH0
        put(t, pizz(mtof(ch[0] - 12 if k % 4 in (0, 2) else ch[2] - 12)), .2 if quiet else .3, -.1)       # walking pizz bass
        if not quiet or k % 2 == 0: put(t, es("hover_tick/detent"), .1, .4)                               # the clock
        if k % 4 in (1, 3) and t > STARTS[3]: put(t, brush(.06 if not quiet else .035), 1., .15)          # brushed backbeat
        if k % 4 == 0:
            put(t, widen(strings([ch[0] - 12, ch[1] - 12], 4 * B + .4, .05 if t > STARTS[6] else .035, 900, .6), .02, .8))
            if k % 8 == 0 and t > STARTS[6]: put(t + 2.5 * B, piano(mtof(ch[2] + 12), 2.2, .07), 1., .35)   # sparse piano
    # tension swell into "Then he is gone." and the silence after it
    put(GONE - 1.6, widen(strings([38, 45, 50], 1.7, .07, 1100, 1.2)))
    put(GONE + .05, es("impact/deep"), .55)
    # the ending: stop, one low piano chord under the last two lines
    for n in (38, 45, 50, 53): put(FINAL, piano(mtof(n), 4.5, .12))
    put(FINAL, widen(strings([38, 45, 50], 5.0, .05, 900, .8)))
    m = m + convolve(m, ir(1.6, 2.4, 5500)) * .3
    g = np.ones(N); k = int(1.8 * SR); g[-k:] = np.linspace(1, 0, k) ** 1.4
    return hp(m * g[:, None], 30)

# ---------------- sound design ----------------
def land_times(i):
    """film times where big motion settles inside clip i (an element landing)"""
    c = cv2.VideoCapture(os.path.join(HERE, f"video/S{i:02d}.mp4")); prev = None; d = []
    while True:
        ok, f = c.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f, (90, 160)), cv2.COLOR_BGR2GRAY).astype(float)
        if prev is not None: d.append(np.abs(g - prev).mean())
        prev = g
    d = np.convolve(np.array(d), np.ones(3) / 3, "same")
    pk, _ = signal.find_peaks(d, height=max(2.0, d.max() * .45), distance=12)
    _, ws, we, sp, dd = PLAN[i]
    return [out_t(i, p / 24) for p in pk if ws <= p / 24 <= we - .05][:3]

SPECIAL = {   # clip: [(source time, sound id, gain)] for stamps, tags, phones
    1: [(3.9, "knock/wood", .55), (3.9, "cut_hit/kick", .35)],
    3: [(3.6, "pro_typing_run/tick", .25)],
    7: [(3.2, "knock/wood", .6), (3.2, "cut_hit/kick", .4)],
    8: [(3.0, "knock/wood", .5)],
    9: [(1.2, "fit/bell/small_bell", .12)],
    11: [(3.0, "pro_typing_run/soft", .3)],
    13: [(2.85, "pro_typing_key/tick", .4)],
    15: [(1.5, "knock/wood", .55), (1.5, "cut_hit/kick", .35)],
    17: [(3.0, "knock/wood", .55), (3.0, "cut_hit/kick", .35)],
    18: [(3.0, "pro_typing_run/standard", .3)],
    21: [(1.4, "pro_pop_in/deep", .35)],
    24: [(3.2, "knock/wood", .55), (3.2, "cut_hit/kick", .35)],
    26: [(1.0, "knock/wood", .55), (4.8, "knock/wood", .6), (4.8, "cut_hit/kick", .4)],
    27: [(3.0, "knock/wood", .55)],
    28: [(4.4, "knock/wood", .5)],
}

def ring(d=1.4, g=.12):                                       # old rotary phone bell: two-burst ring
    t = t_(d); x = (np.sin(2 * np.pi * 1180 * t) + .6 * np.sin(2 * np.pi * 1530 * t)) * (np.sin(2 * np.pi * 20 * t) > 0)
    env = ((t % .7) < .45).astype(float); return bp(x, 900, 4000) * env * adsr(d, .01, 1, 1, .05) * g

def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2))
    def hit(sid, t, g, p=0., **kw):
        x = es(sid, **kw); pk = np.argmax(np.abs(x)) / SR; s = pan(x * g, p); place(dry, t - pk, s); place(send, t - pk, s * .25)
    swipes = ["swipe/paper", "swipe/flick", "swipe/velvet"]
    for i in range(1, 29):
        st = STARTS[i - 1]
        if i > 1: hit(swipes[i % 3], st + .06, .38, .3 * np.sin(i))                       # every cut: a sheet of paper
        for k, lt in enumerate(land_times(i)): hit("knock/desk" if k % 2 == 0 else "pro_tap/finger", lt, .3, .25 * np.cos(i + k))
        for src, sid, g in SPECIAL.get(i, []): hit(sid, out_t(i, src), g, .1 * np.sin(i))
    for i in (13, 22):                                                                     # the phone calls
        place(dry, STARTS[i - 1] + .3, pan(ring(1.3, .09), .25))
    for k in range(int(PLAN[9][4] / (B / 2))): hit("hover_tick/detent", STARTS[8] + k * B / 2, .18, .3)   # 2 o'clock: clock ticks
    hit("reverse_swell/dark", STARTS[27] + 2.0, .3)
    hit("impact/deep", STARTS[27] + 2.62, .5)                                               # "...never found Jimmy Hoffa."
    return hp(dry + convolve(send, ir(1.2, 1.8, 6000)) * .6, 30)

# ---------------- mix ----------------
def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 80); x = x + bp(x, 2500, 5000) * .2 + bp(x, 150, 300) * .1; x = x / (np.abs(x).max() + 1e-9) * .85; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.35, .5, 5000)) * .1
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 4, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    mus = score(); mus = mus - bp(mus, 1200, 3800) * .3; mus = mus / (np.abs(mus).max() + 1e-9)
    sfx = design(); sfx = sfx / (np.abs(sfx).max() + 1e-9)
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    vb = signal.sosfilt(sos, v.mean(1)); mb = signal.sosfilt(sos, (mus * .36 * (1 - .42 * d)).mean(1))
    tt = np.arange(N) / SR; ride = np.ones(N)
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        dm = 20 * np.log10((np.sqrt(np.mean(vb[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(mb[i0:i1] ** 2)) + 1e-9))
        if dm < 9: ride *= 10 ** ((dm - 9) / 20 * np.clip(np.minimum((tt - m["t"] + .25) / .25, (m["t"] + m["dur"] + .2 - tt) / .2), 0, 1))
    buses = {"vo": v, "sfx": sfx * .42 * (1 - .4 * d), "music": mus * ride[:, None] * .36 * (1 - .42 * d)}
    mix = sum(buses.values()); mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.25) * .9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    a_ = signal.sosfilt(sos, buses["vo"].mean(1)); m_ = signal.sosfilt(sos, buses["music"].mean(1)); s_ = signal.sosfilt(sos, buses["sfx"].mean(1))
    rows = []
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR); vr = np.sqrt(np.mean(a_[i0:i1] ** 2)) + 1e-9
        rows.append((20 * np.log10(vr / (np.sqrt(np.mean((m_[i0:i1] + s_[i0:i1]) ** 2)) + 1e-9)), m["id"], 20 * np.log10(vr / (np.sqrt(np.mean(m_[i0:i1] ** 2)) + 1e-9)), 20 * np.log10(vr / (np.sqrt(np.mean(s_[i0:i1] ** 2)) + 1e-9))))
    for db, i, dm, ds in sorted(rows)[:5]: print(f"{i} {db:5.1f} dB (vs music {dm:5.1f}, vs sfx {ds:5.1f})")
    print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
