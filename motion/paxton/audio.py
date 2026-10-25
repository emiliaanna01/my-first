#!/usr/bin/env python3
"""Documentary score + period sound design + mix for 'The leaf and the Crystal Palace'.
usage: python3 motion/paxton/audio.py <vo_dir> <out_wav>"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "audio"))
from dsp import SR, adsr, bp, bp_sweep, convolve, glide, hp, ir, lp, mtof, noise, osc, pan, perc, place, t_, widen  # noqa: E402
from sfx import boom, mech_click, reverse_swell, whoosh  # noqa: E402

DUR = 66.5
N = int(SR * DUR)
BEAT = 60 / 84

# C lydian-ish, hopeful but restrained: Cmaj9 · Am7 · Fmaj7#11 · G6
PROG = [[48, 55, 59, 62, 64], [45, 52, 55, 60, 64], [41, 48, 52, 57, 59], [43, 50, 55, 59, 64]]
MOTIF = [76, None, 74, 72, 74, None, 79, None, 76, None, 74, None, 72, None, 67, None]

def piano(f, d=2.4, g=.2):
    t = t_(d); x = sum(a * np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (1.2 + k * .9)) for k, a in [(1, 1), (2, .45), (3, .22), (4, .1), (5.01, .05)])
    ham = bp(noise(.02), 1500, 6000) * perc(.02, .0003, .005) * .12; x[:len(ham)] += ham
    return x * perc(d, .002, d) * g

def strings(notes, d, g=.07, cut=1800, att=1.2):
    x = np.zeros(int(SR * d))
    for m in notes:
        for det in (-.07, 0, .06):
            vib = 1 + .003 * np.sin(2 * np.pi * 5.2 * t_(d) + m)
            x += osc(mtof(m) * 2 ** (det / 12) * vib, d, "saw")
    return lp(x / (len(notes) * 3), cut) * adsr(d, att, 1, .9, min(1.5, d / 2)) * g

def pulse(g=.25):   # soft timpani-like pulse
    d = .6; return osc(glide(78, 60, d, .4), d) * perc(d, .004, .22) * g + lp(noise(d), 300) * perc(d, .002, .05) * g * .3

def chord_at(t): return PROG[int(t // (BEAT * 8)) % 4]

def score(vo):
    W = lambda c, n=0: word_time(vo, c, n)
    m = np.zeros((N, 2))
    held = W("held2", 0)
    # piano motif: sparse at first, steadier later
    i = 0
    while True:
        t = i * BEAT / 2
        if t > 64.6: break
        st = i % 16; note = MOTIF[st]
        quiet = 45.2 < t < 47.3 or held - .3 < t < 52.2
        dense = 33.0 < t < 45.2 or 52.2 < t < 61.0
        if note and not quiet and (dense or st % 4 == 0 or t < 15):
            place(m, t, pan(piano(mtof(note), 2.4, .11 if t < 15 else (.08 if dense else .12)), .3 * np.sin(i)))
        i += 1
    # chords: piano left hand + strings pad, building
    for b in range(int(DUR / (BEAT * 4)) + 1):
        a = b * BEAT * 4
        if a > 64.6: break
        ch = chord_at(a)
        if 45.2 < a < 47.3 or held - .3 < a < 52.2: continue
        place(m, a, pan(piano(mtof(ch[0] - 12), 3.0, .12) + piano(mtof(ch[1]), 3.0, .07), -.2))
        lvl = .05 if a < 15 else .07 if a < 33 else .085 if a < 45 else .11 if a > 52 else .08
        place(m, a, widen(strings(ch[1:], BEAT * 4 + 1.2, lvl, 1400 if a < 33 else 2200), .015, .9))
    # pulses under construction and opening
    for k in range(int((45.2 - 40.8) / BEAT)): place(m, 40.8 + k * BEAT, pan(pulse(.22)))
    for k in range(int((61.0 - 52.2) / BEAT)): place(m, 52.2 + k * BEAT, pan(pulse(.26 if k % 2 == 0 else .14)))
    # drone for the warning
    d = 2.4; place(m, 45.2, widen(strings([36, 43], d, .1, 700, .4)))
    # final: lone piano note + octave over the callback
    place(m, 64.4, pan(piano(mtof(72), 3.5, .18) + piano(mtof(60), 3.5, .1)))
    m = m + convolve(m, ir(2.4, 3.0, 6000)) * .45
    k = int(1.4 * SR); fade = np.ones(N); fade[-k:] = np.linspace(1, 0, k) ** 1.4
    return hp(m * fade[:, None], 30)

def word_time(vo, cid, n):
    v = vo[cid]; words = v["text"].split(); wt = [len("".join(ch for ch in w if ch.isalnum() or ch == "'")) + 1.6 for w in words]
    return v["t"] + v["dur"] * (.04 + .9 * sum(wt[:n]) / sum(wt))

def drip(g=.08):
    d = .18; return osc(glide(1400, 2600, d, .3), d) * perc(d, .001, .03) * g

def paper(d=.35, g=.1):
    return bp_sweep(noise(d), 1800, 5000, 1.6) * adsr(d, .02, .1, .5, .1) * g

def clank(f=420, g=.2):
    d = 1.4; t = t_(d); x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (d * k)) for r, a, k in [(1, 1, .3), (2.76, .6, .18), (5.4, .4, .1), (8.9, .2, .05)])
    return (x + lp(noise(d), 2000) * perc(d, .001, .02) * .6) * perc(d, .0005, d) * g

def chain(d=1.2, g=.06):
    x = np.zeros(int(SR * d)); rng = np.random.default_rng(4)
    for k in range(int(d * 22)):
        c = clank(rng.uniform(1800, 3200), 1)[: int(.06 * SR)] * rng.uniform(.3, 1); a = int(k / 22 * SR); x[a:a + len(c)] += c[: len(x) - a]
    return x * g

def step(g=.2):
    d = .14; return (lp(noise(d), 900) * perc(d, .002, .03) + osc(90, d) * perc(d, .002, .04) * .4) * g

def crowd(d, g=.05):
    x = bp(noise(d), 300, 2400); env = np.convolve(np.abs(np.random.default_rng(2).normal(0, 1, len(x))), np.ones(4000) / 4000, "same")
    return x * env * adsr(d, 1.5, 1, .9, 2) * g

def design(vo):
    W = lambda c, n=0: word_time(vo, c, n)
    dry = np.zeros((N, 2)); send = np.zeros((N, 2))
    def put(t0, x, p=0., rv=.25):
        s = x if x.ndim == 2 else pan(x, p); place(dry, t0, s); place(send, t0, s * rv)
    # glasshouse: airy room tone + water drips + lapping
    room = bp(noise(15.5), 200, 3000) * .012 * adsr(15.5, 1.5, 1, 1, 1.5); put(0, widen(room), 0, .6)
    rng = np.random.default_rng(7)
    for k in range(18): put(rng.uniform(.3, 14.5), drip(rng.uniform(.02, .05)), rng.uniform(-.6, .6), .7)
    lap = lp(noise(8), 500) * (0.5 + .5 * np.sin(2 * np.pi * .4 * t_(8))) * .03 * adsr(8, 1, 1, 1, 2); put(.2, widen(lap), 0, .3)
    # flip + ribs
    put(W("over", 2), paper(.6, .1), 0, .3)
    put(W("ribs", 1) - .4, reverse_swell(.4, .1), 0, 0)
    # Hyde Park: birds + breeze
    put(23.9, widen(bp(noise(3.6), 400, 2500) * .012 * adsr(3.6, .8, 1, 1, 1)), 0, .3)
    for k in range(6): tt = 24.2 + k * .55; put(tt, osc(glide(3200, 4200, .09), .09) * perc(.09, .002, .03) * .03, rng.uniform(-.7, .7), .5)
    # designs falling + stamp
    t0 = W("designs", 0)
    for i in range(15): put(t0 + i * (2.6 / 14), paper(.22, .06), rng.uniform(-.4, .4), .2)
    st = W("rejected", 1); put(st, boom(.5, 140, 60, .4, .6), 0, .3); put(st, mech_click(900, .2), 0, .2)
    # meeting room + pen
    put(32.9, widen(bp(noise(3.4), 120, 500) * .008 * adsr(3.4, .5, 1, 1, .8)), 0, .4)
    sp = W("sketch", 0)
    pen = bp(noise(2.4), 2500, 7000) * (np.abs(np.sin(2 * np.pi * 3.1 * t_(2.4))) ** 2) * .035; put(sp, pen, .2, .1)
    # construction: clanks and chains
    for k, tt in enumerate([41.0, 41.9, 42.9, 43.6, 44.4]): put(tt, lp(clank(380 + k * 40, .07), 2500), (-1) ** k * .4, .5)
    put(42.2, chain(1.4, .022), .3, .4)
    # warning: wood creak
    creak = osc(glide(180, 140, 1.2), 1.2, "saw") * (0.5 + .5 * np.sin(2 * np.pi * 9 * t_(1.2))) * adsr(1.2, .2, .4, .7, .3)
    put(W("warned", 2), lp(creak, 1200) * .05, -.3, .4)
    # marching feet, stopping before "It held."
    held = W("held2", 0); t = 47.6
    while t < held - .25:
        put(t, step(.16), rng.uniform(-.3, .3), .3); put(t + .02, step(.08), rng.uniform(-.5, .5), .3); t += np.pi / 6.2
    put(held - .02, boom(1.2, 60, 32, .3, 0), 0, .4)
    # opening day: crowd swell, a distant cheer
    put(52.0, widen(crowd(9.5, .022)), 0, .5)
    put(W("opened", 9), whoosh(1.0, 300, 1600, .5, .04, False), 0, .4)
    return hp(dry + convolve(send, ir(1.8, 2.4, 6000)) * .8, 30)

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json")); vo = {m["id"]: m for m in meta}
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 90); x = x / (np.abs(x).max() + 1e-9) * .8; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.5, .8, 5000)) * .2
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 3, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    music = score(vo); sfx = design(vo)
    buses = {"vo": v, "sfx": sfx * .8 * (1 - .4 * d), "music": music / (np.abs(music).max() + 1e-9) * .26 * (1 - .7 * d)}
    mix = sum(buses.values())
    fade = np.ones(N); k = int(.6 * SR); fade[-k:] = np.linspace(1, 0, k) ** 1.5
    mix = np.tanh(mix * fade[:, None] / (np.abs(mix).max() + 1e-9) * 1.2) * .9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    a_ = signal.sosfilt(sos, buses["vo"].mean(1)); r_ = signal.sosfilt(sos, (buses["sfx"] + buses["music"]).mean(1))
    rows = []
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        rows.append((20 * np.log10((np.sqrt(np.mean(a_[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(r_[i0:i1] ** 2)) + 1e-9)), m["t"], m["text"]))
    for db, t, txt in sorted(rows)[:4]: print(f"{t:6.2f}s {db:5.1f} dB  {txt}")
    print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
