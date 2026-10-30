#!/usr/bin/env python3
"""Score + sound design + mix for 'Be bored on purpose'.
usage: python3 motion/bored/audio.py <vo_dir> <out_wav>"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "audio"))
from dsp import SR, adsr, bp, bp_sweep, convolve, delay_pingpong, glide, hp, ir, lp, mtof, noise, osc, pan, pan_move, perc, place, t_, widen  # noqa: E402
from sfx import boom, chime, mech_click, pop, reverse_swell, tink, whoosh  # noqa: E402

DUR = 48.0
N = int(SR * DUR)
BEAT = 60 / 96
QUIET = [(10.35, 12.3), (23.25, 25.4)]          # drums drop out: coincidence, bored
THIN = [(0.0, 3.1), (39.1, 42.55), (42.55, 48.0)]  # sparse sections

# D dorian, slightly curious motif
PROG = [[50, 57, 60, 65], [48, 55, 59, 64], [46, 53, 57, 62], [45, 52, 57, 60]]   # Dm9-ish → C → Bb → Am
MOTIF = [74, 77, 81, 79, 77, 72, 74, None, 81, 79, 76, 74, 72, None, 69, 72]

def inside(t, spans): return any(a <= t < b for a, b in spans)
def chord_at(t): return PROG[int(t // (BEAT * 8)) % 4]

def marimba(f, d=0.6, g=0.2):
    t = t_(d)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / .28) + .2 * np.sin(2 * np.pi * f * 4.0 * t) * np.exp(-t / .04) + .05 * np.sin(2 * np.pi * f * 9.9 * t) * np.exp(-t / .015)
    return x * perc(d, .001, d) * g

def kick(g=.6):
    d = .35; return np.tanh(osc(glide(120, 46, d, .3), d) * perc(d, .001, .1) * 1.5) * g

def rim(g=.12):
    d = .06; return (bp(noise(d), 1500, 5000) * .6 + osc(1700, d) * .4) * perc(d, .0005, .012) * g

def tick(g=.05):
    d = .04; return hp(noise(d), 7000) * perc(d, .0005, .01) * g

def score():
    mus = np.zeros((N, 2)); kicks = []
    steps = int(DUR / (BEAT / 2))
    for i in range(steps):
        t = i * BEAT / 2
        if t > 47.0: break
        st = i % 16
        quiet, thin = inside(t, QUIET), inside(t, THIN)
        m = MOTIF[st]
        if m and not quiet and (not thin or st % 2 == 0):
            place(mus, t, pan(marimba(mtof(m), .7, .09 if thin else .11), .35 * np.sin(i * .7)))
        if not quiet and not thin:
            if st % 4 == 0: place(mus, t, pan(kick(.5))); kicks.append(t)
            if st in (6, 14): place(mus, t, pan(rim(.11), -.2))
            if 25.4 <= t < 34.05: place(mus, t + BEAT / 4, pan(tick(.03), .3))   # clock-like ticks under the screens beat
            elif st % 2: place(mus, t, pan(tick(.035), .3))
        if not quiet and st % 4 == 2 and not (thin and t < 3.1):
            r = chord_at(t)[0] - 24
            d = BEAT * .9; x = lp(osc(mtof(r), d) * .9 + osc(mtof(r), d, "tri") * .3, 400) * adsr(d, .01, .2, .6, .1)
            place(mus, t, pan(x * .32))
    for b in range(int(DUR / (BEAT * 8)) + 1):   # soft pad
        a = b * BEAT * 8; d = BEAT * 8 + .6
        x = sum(osc(mtof(n), d, "tri") + .5 * osc(mtof(n) * 1.005, d, "tri") for n in chord_at(a)) / 6
        place(mus, a, widen(lp(x, 1500) * adsr(d, .6, 1, .9, .8) * .07, .013, .8))
    end = sum(marimba(mtof(n), 2.2, .1) for n in [62, 69, 74, 77])
    place(mus, 46.2, widen(end))
    g = np.ones(N)
    for tk in kicks:
        a = int(tk * SR); n = min(N - a, int(.35 * SR)); g[a:a + n] = np.minimum(g[a:a + n], 1 - .3 * np.exp(-np.arange(n) / SR / .1))
    mus = mus * g[:, None]
    mus = mus + delay_pingpong(mus * .5, BEAT * .75, .25, 3) * .3 + convolve(mus, ir(1.6, 2.2, 6000)) * .35
    k = int(1.2 * SR); fade = np.ones(N); fade[-k:] = np.linspace(1, 0, k) ** 1.5
    return hp(mus * fade[:, None], 30)

def blip(f, g=.08):
    d = .07; return lp(osc(f, d, "square"), 2400) * adsr(d, .002, .03, .5, .02) * g

def design(vo):
    W = lambda cid, n=0: word_time(vo, cid, n)
    dry = np.zeros((N, 2)); send = np.zeros((N, 2))
    def put(t0, x, p=0., rv=.25):
        s = x if x.ndim == 2 else pan(x, p); place(dry, t0, s); place(send, t0, s * rv)
    # object entrances (soft, airy)
    for t0 in [0.0, 3.12, vo["walk"]["t"] - .05, vo["queue"]["t"] - .05, 7.3, 12.35, 20.1, 23.3, 25.45, 30.8, 31.9, 32.95, 34.1, 39.15, 42.6]:
        put(t0, whoosh(.32, 2600, 700, .15, .06, False), 0, .3)
        put(t0, pop(260, 520, .07), 0, .2)
    put(1.15, tink(1568, .05), .4, .5)
    # hero words: low, felt hits
    for cid, n in [("places", 2), ("coinc", 3), ("bored", 4), ("lost", 4), ("purpose", 2)]:
        put(W(cid, n) - .06, boom(1.2, 62, 30, .36, 0), 0, .3)
    put(W("coinc", 3) - .5, reverse_swell(.45, .14), 0, 0)
    # wandering line: faint pencil
    put(W("wander", 8), bp(noise(2.4), 1500, 5000) * adsr(2.4, .3, 1, .6, .8) * .02, 0, .1)
    # link line connects
    put(W("links", 4) + .7, mech_click(2600, .16), .2, .3)
    put(W("plays", 3), pop(500, 1100, .12), .3, .3)
    # network nodes
    t0 = W("dmn", 5)
    for i in range(8): put(t0 + i * .11, tink(1760 * 2 ** ((i % 5) * 2 / 12), .03), -.5 + i * .13, .4)
    # notification blips
    b0 = W("screen", 6)
    for i in range(14): put(b0 + i * .15, blip(880 * 2 ** ((i * 5 % 12) / 12), .022), -.6 + (i % 7) * .2, .15)
    for k, cid in enumerate(["bus", "lift", "kettle"]):
        put(vo[cid]["t"] + .3 - .05 * k, blip(988, .035), .4, .15)
    # scale: phone lands, bulb dissolves
    land = W("traded", 4) + .05
    put(land - .38, whoosh(.38, 800, 300, .9, .12, False), .3, .1)
    put(land, boom(.6, 110, 50, .45, .5), .3, .25); put(land, mech_click(1800, .18), .3, .2)
    put(W("lost", 2), chime(1318, 1.2, .05), -.3, .7)
    # phone into pocket: paper slide
    put(W("pocket", 9), bp_sweep(noise(.5), 3000, 800, 2) * adsr(.5, .05, .2, .6, .2) * .06, .2, .1)
    # final: halo swell
    tb = W("purpose", 2)
    put(tb - .1, reverse_swell(.4, .12), 0, 0)
    put(tb + .1, chime(1046.5, 2.6, .08), 0, .8)
    put(tb + .1, chime(1568, 2.2, .04), .2, .8)
    put(46.2, boom(1.6, 50, 30, .3, 0), 0, .3)
    return hp(dry + convolve(send, ir(1.4, 2.0, 7000)) * .8, 30)

def word_time(vo, cid, n):
    v = vo[cid]; words = v["text"].split(); wt = [len("".join(ch for ch in w if ch.isalnum() or ch == "'")) + 1.6 for w in words]
    return v["t"] + v["dur"] * (.04 + .9 * sum(wt[:n]) / sum(wt))

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json")); vo = {m["id"]: m for m in meta}
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 90); x = x / (np.abs(x).max() + 1e-9) * .8; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.5, .8, 5000)) * .22
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 4, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    music = score(); sfx = design(vo)
    buses = {"vo": v, "sfx": sfx * .65 * (1 - .55 * d), "music": music / (np.abs(music).max() + 1e-9) * .27 * (1 - .72 * d)}
    mix = sum(buses.values())
    fade = np.ones(N); k = int(.4 * SR); fade[-k:] = np.linspace(1, 0, k) ** 1.5
    mix = np.tanh(mix * fade[:, None] / (np.abs(mix).max() + 1e-9) * 1.2) * .9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    a_ = signal.sosfilt(sos, buses["vo"].mean(1)); r_ = signal.sosfilt(sos, (buses["sfx"] + buses["music"]).mean(1))
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        db = 20 * np.log10((np.sqrt(np.mean(a_[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(r_[i0:i1] ** 2)) + 1e-9))
        print(f"{m['t']:6.2f}s {db:5.1f} dB  {m['text']}")
    print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
