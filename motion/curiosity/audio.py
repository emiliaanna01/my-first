#!/usr/bin/env python3
"""Original score + sound design + mix for the phone-addiction reel (10 clips x 6 s).
Score: minimal modern beat, 100 BPM, A minor — soft plucks and a warm bass that build clip by clip, a full groove for the
slot-machine middle, a strip-down on S09, a hard stop before the last line and a closing hit on the question mark.
Effects: earshot bank (code-made), each placed so its peak lands on the motion measured in the clip.
usage: python3 motion/curiosity/audio.py <vo_dir> <out_wav>"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "audio"))
from dsp import SR, adsr, bp, convolve, glide, hp, ir, lp, mtof, noise, osc, pan, perc, place, t_, widen  # noqa: E402

DUR = 60.0; N = int(SR * DUR); CLIP = 6.0
BPM = 100; B = 60 / BPM; S16 = B / 4
PROG = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 65]]      # Am7 · Fmaj7 · Cmaj7 · G7
VOICE_END = None

def es(sid, **kw):
    """render an earshot bank sound (cached on disk) -> mono array"""
    cdir = os.environ.get("SFX_CACHE", "/tmp/sfxcache"); os.makedirs(cdir, exist_ok=True)
    f = os.path.join(cdir, (sid + "".join(f"_{k}{v}" for k, v in sorted(kw.items()))).replace("/", "_") + ".wav")
    if not os.path.exists(f):
        subprocess.run(["earshot", "sfx", "render", sid, "-o", f, "--sr", str(SR)] + sum([[f"--{k}", str(v)] for k, v in kw.items()], []), check=True, capture_output=True)
    x, _ = sf.read(f); return x.mean(1) if x.ndim > 1 else x

def mixx(*xs):
    out = np.zeros(max(len(x) for x in xs))
    for x in xs: out[:len(x)] += x
    return out

# ---------------- instruments ----------------
def pluck(f, d=1.2, g=.12, bright=3200):
    t = t_(d); x = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3 + k * 2.2)) for k, a in [(1, 1), (2, .5), (3, .25), (4, .12)])
    return lp(x, bright) * perc(d, .003, d) * g

def keys(notes, d, g=.05):                     # soft electric-piano pad
    t = t_(d); x = sum(np.sin(2 * np.pi * mtof(m) * t + .3 * np.sin(2 * np.pi * mtof(m) * 2 * t)) for m in notes) / len(notes)
    return lp(x * (1 + .15 * np.sin(2 * np.pi * 5 * t)), 1800) * adsr(d, .08, .8, .7, .5) * g

def bass(f, d, g=.22):
    return lp(osc(f, d, "saw") * .5 + osc(f, d) * .8, 380) * adsr(d, .01, .6, .7, .08) * g

def kick(g=.5):
    d = .4; return np.tanh(mixx(osc(glide(120, 45, d, .3), d) * perc(d, .002, .14), lp(noise(.02), 2500) * perc(.02, .0005, .004) * .5) * 1.5) * g

def rim(g=.12):
    d = .12; return mixx(bp(noise(d), 1800, 6000) * perc(d, .0005, .02), osc(820, d) * perc(d, .001, .015) * .4) * g

def hat(g=.04, open_=False):
    d = .25 if open_ else .06; return hp(noise(d), 7000) * perc(d, .0005, .08 if open_ else .012) * g

def vinyl(d, g=.008):
    rng = np.random.default_rng(5); x = lp(noise(d), 4000) * .25
    for _ in range(int(d * 9)): a = int(rng.uniform(0, d - .01) * SR); x[a:a + 40] += rng.uniform(-1, 1) * 3
    return x * g

def score():
    m = np.zeros((N, 2)); tt = np.arange(N) / SR
    STOP = 54.0 - .02                                  # everything stops before the last clip
    bars = int(STOP / (4 * B)) + 1
    for b in range(bars):
        a = b * 4 * B; ch = PROG[b % 4]
        if a >= STOP: break
        sec = a / CLIP                                 # which clip we're in (0..9)
        d = min(4 * B, STOP - a)
        place(m, a, widen(keys([x - 12 for x in ch], d + .4, .045 if sec < 2 else .055), .015, .8))
        if sec >= 2 and not 8 <= sec < 9:              # bass: root on 1 and the "and" of 3
            place(m, a, pan(bass(mtof(ch[0] - 24), min(1.6 * B, d), .2)))
            if a + 2.5 * B < STOP: place(m, a + 2.5 * B, pan(bass(mtof(ch[0] - 24), min(1.4 * B, STOP - a - 2.5 * B), .16)))
    # plucked motif on 8ths, sparse at first
    MOT = [0, 2, 1, 3, 2, 0, 3, 1]
    for k in range(int(STOP / (B / 2))):
        t = k * B / 2; sec = t / CLIP; ch = PROG[int(t / (4 * B)) % 4]
        if sec < 2 and k % 4: continue
        if 8 <= sec < 9 and k % 2: continue
        place(m, t, pan(pluck(mtof(ch[MOT[k % 8]] + 12), 1.1, .07 if sec < 4 else .085), .35 * np.sin(k * .9)))
    # drums from S03, full from S05, out on S09
    for k in range(int(STOP / S16)):
        t = k * S16; sec = t / CLIP; step = k % 16
        if sec < 2 or 8 <= sec < 9: continue
        full = 4 <= sec < 8
        if step in (0, 10) or (full and step == 7): place(m, t, pan(kick(.42 if full else .3)))
        if step in (4, 12): place(m, t, pan(rim(.11 if full else .08), .1))
        if full or step % 2 == 0: place(m, t, pan(hat(.035 if step % 2 == 0 else .02, open_=(full and step == 14)), -.3 if step % 4 else .3))
    place(m, 0, widen(vinyl(STOP)))
    # the ending: a single deep chord + hit under "It's addictive because it's uncertain."
    place(m, 54.0, widen(keys([45, 52, 57, 60], 6.0, .07), .02, .9))
    place(m, 54.0, pan(bass(mtof(33), 3.0, .22)))
    m = m + convolve(m, ir(1.4, 2.0, 6000)) * .25
    g = np.ones(N); k = int(1.5 * SR); g[-k:] = np.linspace(1, 0, k) ** 1.5
    return hp(m * g[:, None], 30)

# ---------------- sound design (clip-relative times from measured motion peaks) ----------------
CUES = {   # clip: [(time in clip, sound id, gain, kwargs)]
    1: [(.13, "whoosh_fast/crisp", .45, {}), (1.37, "pro_click/mouse", .6, {}), (1.45, "pro_pop/thup", .35, {}), (4.85, "whoosh_big/swell", .45, {})],
    2: [(.33, "cut_hit/punch", .55, {}), (1.87, "tap/glass", .28, {}), (2.1, "pro_zip/up", .12, {}), (5.6, "whoosh_fast/heavy", .45, {})],
    3: [(3.33, "pro_pop_in/round", .5, {}), (4.5, "pro_pop/tink", .45, {}), (5.0, "swipe/paper", .45, {})],
    4: [(.93, "knock/wood", .6, {}), (1.37, "knock/plastic", .35, {}), (2.17, "knock/wood", .5, {}), (2.45, "pro_pop/bloop", .35, {}), (5.67, "whoosh_big/swell", .45, {})],
    5: [(.7, "cut_hit/kick", .55, {}), (2.17, "toggle/latch", .5, {}), (5.5, "whoosh_fast/crisp", .4, {})],
    6: [(.2, "pro_riser/roll", .35, {"dur": 1.8}), (2.1, "toggle/latch", .55, {}), (2.12, "pro_pop/thup", .35, {}), (4.83, "swipe/paper", .45, {})],
    7: [(2.17, "glitch/mid", .3, {}), (2.2, "pro_notify/ding_2045", .25, {}), (5.1, "cut_hit/punch", .6, {})],
    8: [(1.67, "pro_notify/ding_1930", .3, {}), (2.0, "toggle/latch", .4, {}), (2.05, "whoosh_fast/tight", .18, {}), (5.85, "whoosh_big/thump", .5, {})],
    9: [(1.17, "knock/desk", .55, {}), (1.7, "swipe/flick", .35, {}), (3.0, "cut_hit/kick", .45, {}), (5.6, "whoosh_fast/crisp", .4, {})],
    10: [(1.15, "impact/punch", .6, {}), (2.6, "pro_pop_in/deep", .4, {}), (4.6, "impact/deep", .55, {}), (4.2, "reverse_swell/dark", .35, {})],
}

def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2))
    for c, cues in CUES.items():
        for tc, sid, g, kw in cues:
            x = es(sid, **kw); pk = np.argmax(np.abs(x)) / SR; t = (c - 1) * CLIP + tc
            s = pan(x * g, .2 * np.sin(c + tc)); place(dry, t - pk, s); place(send, t - pk, s * .2)
    # coins spilling out of the slot machine (S05 ≈ 2.6–4.6 s)
    rng = np.random.default_rng(8)
    for i in range(22):
        t = 24 + 2.6 + i * .09 + rng.uniform(0, .05); x = es("tap/glass") * rng.uniform(.15, .3)
        place(dry, t, pan(x, rng.uniform(-.5, .5)))
    return hp(dry + convolve(send, ir(1.2, 1.8, 6000)) * .6, 30)

# ---------------- mix ----------------
def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 70); x = x + bp(x, 2500, 5000) * .2 + bp(x, 100, 200) * .12; x = x / (np.abs(x).max() + 1e-9) * .85; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.35, .5, 5000)) * .1
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 4, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    mus = score(); mus = mus - bp(mus, 1200, 3800) * .3; mus = mus / (np.abs(mus).max() + 1e-9)
    sfx = design(); sfx = sfx / (np.abs(sfx).max() + 1e-9)
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    vb = signal.sosfilt(sos, v.mean(1)); mb = signal.sosfilt(sos, (mus * .6 * (1 - .42 * d)).mean(1))
    tt = np.arange(N) / SR; ride = np.ones(N)
    for m in meta:        # ride the music down only under lines where it would mask the voice
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        dm = 20 * np.log10((np.sqrt(np.mean(vb[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(mb[i0:i1] ** 2)) + 1e-9))
        if dm < 8.5: ride *= 10 ** ((dm - 8.5) / 20 * np.clip(np.minimum((tt - m["t"] + .25) / .25, (m["t"] + m["dur"] + .2 - tt) / .2), 0, 1))
    buses = {"vo": v, "sfx": sfx * .65 * (1 - .35 * d), "music": mus * ride[:, None] * .6 * (1 - .42 * d)}
    mix = sum(buses.values()); mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.25) * .9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    a_ = signal.sosfilt(sos, buses["vo"].mean(1)); m_ = signal.sosfilt(sos, buses["music"].mean(1)); s_ = signal.sosfilt(sos, buses["sfx"].mean(1))
    rows = []
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR); vr = np.sqrt(np.mean(a_[i0:i1] ** 2)) + 1e-9
        rows.append((20 * np.log10(vr / (np.sqrt(np.mean((m_[i0:i1] + s_[i0:i1]) ** 2)) + 1e-9)), m["id"], 20 * np.log10(vr / (np.sqrt(np.mean(m_[i0:i1] ** 2)) + 1e-9)), 20 * np.log10(vr / (np.sqrt(np.mean(s_[i0:i1] ** 2)) + 1e-9))))
    for db, i, dm, ds in sorted(rows)[:4]: print(f"{i} {db:5.1f} dB (vs music {dm:5.1f}, vs sfx {ds:5.1f})")
    print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
