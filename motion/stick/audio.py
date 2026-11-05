#!/usr/bin/env python3
"""Playful score + cartoon sound design + mix for the stick-figure money reel.
Score: bouncy 112 BPM in C major — kalimba melody, marimba offbeats, finger-snap claps, a round plucked bass. Deflates into a
"sad trombone" under the horror-movie bank balance, comes back brighter for "pay yourself first".
usage: python3 motion/stick/audio.py <vo_dir> <out_wav>"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "audio"))
from dsp import SR, adsr, bp, convolve, glide, hp, ir, lp, mtof, noise, osc, pan, perc, place, t_, widen  # noqa: E402

CUT = json.load(open(os.path.join(HERE, "cut.json"))); ST = CUT["starts"]; DUR = float(sum(CUT["durs"])); N = int(SR * DUR)
VO = {m["id"]: m for m in json.load(open(os.path.join(HERE, "vo.json")))}
W = lambda s, n: VO[s]["words"][min(n, len(VO[s]["words"]) - 1)]
BPM = 112; B = 60 / BPM; S16 = B / 4
NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]; nm = lambda m: f"{NOTE[m % 12]}{m // 12 - 1}"
PROG = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]       # C · Am · F · G
SAD0, SAD1 = ST[4], ST[5]                                              # the horror-movie scene

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

def bass(f, d=.4, g=.3):
    t = t_(d); return lp(np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t), 600) * perc(d, .004, .22) * g

def trombone(notes, g=.16):                                            # wah-wah-wah-waaah
    out = []
    for k, m in enumerate(notes):
        d = 1.1 if k == len(notes) - 1 else .42; t = t_(d)
        f = mtof(m) * (1 - (.06 * t / d if k == len(notes) - 1 else 0)) * (1 + (.012 * np.sin(2 * np.pi * 6 * t) if k == len(notes) - 1 else 0))
        x = osc(f, d, "saw") * .6 + osc(f * 2, d, "saw") * .2
        wah = .5 + .5 * np.sin(np.pi * np.clip(t / d, 0, 1))
        out.append(lp(x, 900) * (.4 + .6 * wah) * adsr(d, .04, .9, .8, .12) * g)
    return np.concatenate(out)

def score():
    m = np.zeros((N, 2))
    def put(t, x, g=1., p=0.):
        place(m, t, pan(x * g, p))
    MEL = [76, 79, 81, 79, 76, 74, 72, 74]
    for k in range(int(DUR / (B / 2))):
        t = k * B / 2; bar = int(t / (4 * B)); ch = PROG[bar % 4]
        if SAD0 - .1 <= t < SAD1 or t > DUR - 1.2: continue
        bright = t >= ST[6]
        if k % 2 == 0 or bright: put(t, es("pluck/kalimba_soft", pitch=nm(MEL[k % 8] + (12 if bright and k % 4 == 3 else 0))), .14, .3 * np.sin(k))
        if k % 4 in (1, 3): put(t, es("mallet/marimba", pitch=nm(ch[k % 3])), .1, -.35)
        if k % 2 == 0: put(t, bass(mtof(ch[0] - 24), .45, .3 if k % 4 == 0 else .2))
        if k % 4 == 2: put(t, mixx(es("knock/snap"), hp(noise(.1), 1500) * perc(.1, .001, .03) * .5), .3, .1)
        if t > ST[1]: put(t + S16, es("hover_tick/air"), .1, -.3)
    put(SAD0 + .45, trombone([67, 66, 65, 64]), 1.0)                  # sad trombone under "horror movie"
    put(ST[6] - .9, es("pro_riser/air_gate", dur=.9), .3)             # lift into "pay yourself first"
    for n in (72, 76, 79, 84): put(DUR - 1.25, es("pluck/kalimba_ring", pitch=nm(n)), .12)   # happy final chord
    m = m + convolve(m, ir(.9, 1.4, 7000)) * .2
    g = np.ones(N); k = int(1.0 * SR); g[-k:] = np.linspace(1, 0, k) ** 1.5
    return hp(m * g[:, None], 30)

CUES = [   # (time, sound id, gain, kwargs)
    (W("S01", 1), "pro_notify/ding_2296", .3, {}), (W("S01", 1) + .12, "mallet/flourish", .2, {}), (W("S01", 7), "logo_sting/zip_ping", .2, {}),
    (W("S02", 3), "pro_pop/tink", .3, {}), (ST[1] + 1.9, "whoosh_fast/whistle", .3, {}), (ST[1] + 2.6, "pro_pop/boop", .35, {}),
    (ST[2] + .35, "impact/punch", .6, {}), (ST[2] + .4, "swipe/paper", .4, {}),
    (W("S04", 1), "pro_pop/bloop", .4, {}), (W("S04", 2), "pro_pop/bloop", .4, {}), (W("S04", 3), "pro_pop/bloop", .4, {}), (W("S04", 7), "pro_pop/bloop", .4, {}),
    (SAD0 + .1, "reverse_swell/dark", .35, {}), (W("S05", 7) + .05, "braam_hit", .0, {}),
    (W("S06", 3), "pro_pop_in/round", .4, {}), (ST[5] + 1.3, "pro_pop/double", .3, {}), (ST[5] + 2.0, "pro_pop/double", .3, {}), (ST[5] + 2.7, "pro_pop/double", .3, {}),
    (W("S07", 3), "mallet/up4", .2, {}),
    (W("S08", 0), "pro_pop/thup", .35, {}), (W("S08", 3), "pro_pop/thup", .35, {}), (ST[7] + 3.6, "mallet/flourish", .3, {}),
]

def coins(t0, n, g=.12, step=.07, rng=np.random.default_rng(3)):
    x = np.zeros(int((n * step + .4) * SR))
    for i in range(n):
        c = es("tap/glass") * rng.uniform(.5, 1); a = int((i * step + rng.uniform(0, .03)) * SR); x[a:a + len(c)] += c[: len(x) - a]
    return x * g

def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2))
    def hit(sid, t, g, p=0., **kw):
        x = es(sid, **kw); pk = np.argmax(np.abs(x)) / SR; s = pan(x * g, p); place(dry, t - pk, s); place(send, t - pk, s * .2)
    for i, t in enumerate(ST[1:], 1): hit("whoosh_fast/crisp" if i % 2 else "swipe/flick", t + .05, .25, .3 * np.sin(i))
    for t, sid, g, kw in CUES:
        if g > 0: hit(sid, t, g, .15 * np.sin(t), **kw)
    for k in range(5): hit("hover_tick/detent", ST[1] + .2 + k * .5, .3, .3)                  # the clock on "five minutes"
    for k, w in enumerate((1, 2, 3, 7)):                                                          # money draining on each expense
        place(dry, W("S04", w) + .1, pan(coins(0, 5, .07, .06)[::-1].copy(), -.3 + .2 * k))
    stab = osc(glide(220, 90, 1.0, .5), 1.0, "saw") * .5 + osc(glide(233, 95, 1.0, .5), 1.0, "saw") * .5
    place(dry, W("S05", 7), pan(lp(stab, 1400) * adsr(1.0, .005, .6, .5, .3) * .16))       # horror sting on "horror movie"
    place(dry, ST[6] + .9, pan(coins(0, 7, .07), .2)); place(dry, ST[7] + 1.1, pan(coins(0, 9, .09), -.2))   # coins into the jar
    return hp(dry + convolve(send, ir(1.0, 1.5, 6500)) * .5, 30)

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 70); x = x + bp(x, 2500, 5000) * .2 + bp(x, 110, 220) * .1; x = x / (np.abs(x).max() + 1e-9) * .85; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.3, .45, 5000)) * .08
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
        if dm < 9: ride *= 10 ** ((dm - 9) / 20 * np.clip(np.minimum((tt - m["t"] + .25) / .25, (m["t"] + m["dur"] + .2 - tt) / .2), 0, 1))
    buses = {"vo": v, "sfx": sfx * .5 * (1 - .35 * d), "music": mus * ride[:, None] * .45 * (1 - .42 * d)}
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
