#!/usr/bin/env python3
"""Score + period sound design + mix for 'The woman who cleared the glass'.
usage: python3 motion/anderson/audio.py <vo_dir> <out_wav>"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "audio"))
from dsp import SR, adsr, bp, bp_sweep, convolve, glide, hp, ir, lp, mtof, noise, osc, pan, perc, place, t_, widen  # noqa: E402
from sfx import boom, mech_click, reverse_swell, riser, whoosh  # noqa: E402
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("paxton_audio", os.path.join(os.path.dirname(__file__), "..", "paxton", "audio.py"))
_pax = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_pax)
piano, strings, pulse, paper, clank, step = _pax.piano, _pax.strings, _pax.pulse, _pax.paper, _pax.clank, _pax.step   # paxton score voices

DUR = 59.0
N = int(SR * DUR)
BEAT = 60 / 80
# D minor, wistful -> warmer at the end: Dm(add9) · B♭maj7 · F/A · Csus
PROG = [[38, 45, 50, 53, 57, 64], [34, 46, 50, 53, 57], [33, 45, 48, 53, 57], [36, 43, 48, 50, 55]]
MOTIF = [69, None, 72, None, 74, 72, 69, None, 67, None, 69, None, 65, None, None, None]
HERE = os.path.dirname(os.path.abspath(__file__))
VO = {m["id"]: m for m in json.load(open(os.path.join(HERE, "vo.json")))}
W = lambda cid, n=0: VO[cid]["words"][min(n, len(VO[cid]["words"]) - 1)]
SWEEP = W("clear", 3) - .05
DROPS = [(W("watch", 0) - .15, W("watch", 1) - .05), (W("follows", 0) - .15, W("follows", 1) - .05), (W("nobody", 0) - .2, W("expire", 0) - .15)]
dropped = lambda t: any(a <= t < b for a, b in DROPS)

def score():
    m = np.zeros((N, 2))
    i = 0
    while (t := 5.9 + i * BEAT / 2) < 57.0:      # piano motif enters with 1902
        st = i % 16; note = MOTIF[st]; i += 1
        if not note or dropped(t) or (t < 16 and st % 4): continue
        if 40.6 < t < 42.3: continue
        lift = 12 if 46.5 < t < 49 or t > 51 else 0
        place(m, t, pan(piano(mtof(note + lift), 2.6, .1 if t < 30 else .12), .35 * np.sin(i * 1.7)))
    for b in range(int(DUR / (BEAT * 4)) + 1):     # left hand + strings, building
        a = b * BEAT * 4
        if a > 56.5: break
        ch = PROG[b % 4]
        if any(dropped(x) for x in (a, a + .5)) or 40.6 < a < 42.3: continue
        if a >= 5.5: place(m, a, pan(piano(mtof(ch[0]), 3.2, .13) + piano(mtof(ch[2]), 3.2, .06), -.2))
        lvl = .045 if a < 16 else .06 if a < 33 else .07 if a < 42 else .08 if a < 51 else .085
        place(m, a, widen(strings(ch[1:], BEAT * 4 + 1.3, lvl, 1300 if a < 33 else 2300), .015, .9))
    # hook: low drone under the rain, then a swell into 1902
    place(m, 0, widen(strings([38, 45], 6.2, .07, 600, 1.0)))
    for k in range(int((33.2 - 27.0) / BEAT)):     # invention: pulse quickening toward the sweep
        tt = 27.0 + k * BEAT
        if tt < SWEEP - .1: place(m, tt, pan(pulse(.16 + .02 * k)))
    for k in range(int((56.5 - 51.0) / BEAT)): place(m, 51.0 + k * BEAT, pan(pulse(.15 if k % 2 == 0 else .07)))
    for k in range(int((46.4 - 42.4) / BEAT)): place(m, 42.4 + k * BEAT, pan(pulse(.18)))
    place(m, W("nobody", 0), pan(piano(mtof(38), 3.0, .16)))            # the lone low note under "Nobody"
    place(m, 56.6, pan(piano(mtof(74), 4.0, .18) + piano(mtof(62), 4.0, .1) + piano(mtof(50), 4.0, .08)))   # final chord
    m = m + convolve(m, ir(2.6, 3.2, 6000)) * .45
    k = int(1.6 * SR); fade = np.ones(N); fade[-k:] = np.linspace(1, 0, k) ** 1.4
    return hp(m * fade[:, None], 30)

def rain(d, g=.03, bright=6000, seed=1):
    rng = np.random.default_rng(seed); x = bp(noise(d), 400, bright) * .5
    for _ in range(int(d * 60)):                 # individual drops on glass
        a = int(rng.uniform(0, d - .05) * SR); dd = .03; dr = bp(noise(dd), 2000, 9000) * perc(dd, .0005, .006) * rng.uniform(.4, 1.6); x[a:a + len(dr)] += dr
    return x * adsr(d, .4, 1, 1, .6) * g

def wind(d, g=.03, seed=3):
    x = noise(d); env = .55 + .45 * np.sin(2 * np.pi * .23 * t_(d) + seed) * np.sin(2 * np.pi * .11 * t_(d))
    return bp_sweep(x, 300, 1400, 1.5) * env * adsr(d, .8, 1, 1, 1) * g

def squeak(d=.55, g=.06):   # rubber on wet glass
    f = glide(900, 1500, d, .6) * (1 + .03 * np.sin(2 * np.pi * 34 * t_(d)))
    return (osc(f, d, "saw") * .3 + osc(f * 2, d) * .2) * bp(noise(d), 600, 3000).clip(-1, 1).__abs__() ** .3 * adsr(d, .05, 1, .8, .15) * g

def mixx(*xs):
    out = np.zeros(max(len(x) for x in xs))
    for x in xs: out[:len(x)] += x
    return out

def swish(d=.6, g=.08):
    return bp_sweep(noise(d), 600, 3500, 1.4) * adsr(d, .1, 1, .7, .25) * g

def bell(g=.12):   # trolley bell: two quick dings
    def ding(): return clank(1250, 1)[: int(1.2 * SR)]
    x = np.zeros(int(1.6 * SR)); a = ding(); x[:len(a)] += a; b = int(.22 * SR); x[b:b + len(a)] += a[: len(x) - b] * .8
    return x * g

def clop(g=.1):
    d = .12; return (bp(noise(d), 500, 2500) * perc(d, .001, .02) + osc(220, d) * perc(d, .001, .03) * .5) * g

def key(g=.06, seed=0):
    rng = np.random.default_rng(seed); d = .06
    return (bp(noise(d), 1500, 6000) * perc(d, .0005, .008) + osc(rng.uniform(140, 200), d) * perc(d, .001, .015) * .6) * g

def engine(d, f=38, g=.04):
    t = t_(d); x = osc(f * (1 + .04 * np.sin(2 * np.pi * .6 * t)), d, "saw") * (0.6 + .4 * np.sin(2 * np.pi * 11 * t))
    return lp(x, 300) * adsr(d, .6, 1, 1, 1) * g

def horn(g=.07):   # old bulb horn: "ah-oo-ga"-ish two tone
    d = .9; f = np.where(t_(d) < .35, glide(260, 420, d, .4), 420 - (t_(d) - .35) * 120)
    return bp(osc(f, d, "saw"), 300, 2200) * adsr(d, .03, 1, .8, .2) * g

def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2)); rng = np.random.default_rng(11)
    def put(t0, x, p=0., rv=.25):
        s = x if x.ndim == 2 else pan(x, p); place(dry, t0, s); place(send, t0, s * rv)
    # hook: rain on the old windshield, two sweeps
    put(0, widen(rain(5.9, .05)), 0, .3)
    for tt in (1.0, 2.9): put(tt, mixx(swish(.7, .07), squeak(.6, .03)), -.2 if tt < 2 else .2, .2)
    put(W("hook2", 6) - .35, reverse_swell(.4, .12), 0, 0)                    # into "a woman"
    put(5.9 - .9, reverse_swell(.9, .16), 0, 0)
    # 1902: sleet, wind, trolley bell, horses, the date hit
    put(5.9, widen(wind(10.5, .05)), 0, .4); put(5.9, widen(rain(10.5, .018, 4000, 2)), 0, .2)
    put(6.05, bell(.1), .3, .5)
    put(W("ny", 2), boom(1.4, 70, 30, .5, .2), 0, .4)
    for k in range(10): put(8.6 + k * .27, clop(.08 if k % 2 else .06), .4, .3)
    put(W("cantsee", 2), whoosh(.5, 2000, 400, .4, .05, False), 0, .3)            # frost blur
    put(W("opens", 1) - .05, mech_click(700, .18), -.1, .2); put(W("opens", 1) + .1, clank(300, .05)[: int(.5 * SR)], -.1, .3)
    put(W("opens", 6), widen(wind(2.0, .09, 5)), 0, .3)                         # leans into the storm
    put(W("watch", 0) - .1, mech_click(2400, .08), 0, .6)                        # paper frame ticks
    put(W("follows", 0) - .1, mech_click(2400, .08), 0, .6)
    put(W("nobody", 0) - .12, mech_click(2400, .08), 0, .6)
    # Mary: card lands
    put(W("name", 0) - .1, paper(.45, .12), 0, .2); put(W("name", 0) - .05, whoosh(.35, 600, 2500, .5, .05, False), 0, .2)
    put(W("visiting", 3) - .05, mech_click(1200, .1), 0, .2)
    put(W("engineer", 2) - .02, boom(.8, 90, 50, .25, .2), 0, .3)
    # sketch: pencil scratching
    sp = W("sketch", 0); pen = bp(noise(1.5), 2500, 7000) * (np.abs(np.sin(2 * np.pi * 3.3 * t_(1.5))) ** 2) * .04; put(sp, pen, .2, .1)
    # lever & blade: mechanism clicks, circles drawn
    for k, tt in enumerate([W("lever", 0), W("lever", 1) + .1, W("blade", 0), W("blade", 1) + .1]): put(tt, mech_click(900 + 300 * k, .1, k), (-1) ** k * .3, .2)
    put(W("lever", 1), paper(.4, .05), .3, .1); put(W("blade", 1), paper(.4, .05), -.3, .1)
    # clear: riser, the sweep, the glass ring
    put(SWEEP - 1.3, riser(1.3, .12), 0, .2)
    put(SWEEP - .1, mixx(swish(.8, .14), squeak(.7, .06)), 0, .3)
    put(SWEEP + .15, boom(1.2, 80, 40, .35, .3), 0, .4)
    put(SWEEP + .2, clank(2200, .03), 0, .8)
    # 1903: stamp
    put(W("patent", 1), boom(.6, 140, 60, .45, .7), 0, .3); put(W("patent", 1), mech_click(900, .22), 0, .2)
    put(W("patent", 0) - .1, paper(.6, .1), 0, .2)
    # sell it: footsteps on the sidewalk
    t = W("sell", 0) - .1
    while t < W("canada", 0) - .2: put(t, step(.14), rng.uniform(-.2, .2), .3); t += .52
    # letter: typewriter, then the carriage bell
    t0 = W("canada", 0) - .1; t = t0 + .05
    while t < W("nobody", 0) - .35:
        put(t, key(rng.uniform(.04, .07), int(t * 100)), rng.uniform(-.2, .2), .15); t += rng.uniform(.06, .12)
    put(W("canada", 7), clank(2600, .03)[: int(.8 * SR)], .3, .3)
    # 1920: engines, horn, crowd
    put(W("expire", 0) - .1, widen(engine(4.2, 40, .03) + bp(noise(4.2), 200, 2400) * .012 * adsr(4.2, .6, 1, 1, 1)), 0, .3)
    put(W("expire", 5), boom(1.4, 70, 30, .5, .2), 0, .4); put(W("expire", 5) - .5, reverse_swell(.5, .12), 0, 0)
    put(W("roads", 2), horn(.06), .4, .4)
    # standard: rain returns, a period wiper
    put(W("standard", 0) - .1, widen(rain(2.6, .03, 5000, 4)), 0, .3)
    put(W("standard", 6) - .1, mixx(swish(.6, .08), squeak(.5, .03)), 0, .2)
    put(W("standard", 6), boom(.9, 90, 45, .3, .2), 0, .3)
    # profit: quiet room, a clock
    for k in range(4): put(W("profit", 0) + k * .5, mech_click(3000, .03, k), .5, .4)
    # still moving: modern night rain + the wiper rhythm
    st = W("every", 0) - .12
    put(st - .6, reverse_swell(.6, .14), 0, 0)
    put(st, widen(rain(6.4, .025, 7000, 5)), 0, .3)
    t = st + .5
    while t < 56.8: put(t, mixx(swish(.7, .04), squeak(.6, .015)), .25 if int(t * 10) % 2 else -.25, .2); t += 1.45
    put(W("still", 3), boom(1.6, 70, 32, .35, .1), 0, .5)
    return hp(dry + convolve(send, ir(1.6, 2.2, 6000)) * .7, 30)

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 90); x = x / (np.abs(x).max() + 1e-9) * .8; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.5, .8, 5000)) * .18
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 3, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    music = score(); sfx = design()
    tt = np.arange(N) / SR; ride = np.ones(N)     # ride the music down under the quieter lines
    for a0, a1, db in [(30.2, 31.6, -3), (42.3, 44.5, -3), (50.9, 55.1, -6)]:
        ride *= 10 ** (db / 20 * np.clip(np.minimum((tt - a0 + .3) / .3, (a1 + .3 - tt) / .3), 0, 1))
    music = music * ride[:, None]
    buses = {"vo": v, "sfx": sfx / (np.abs(sfx).max() + 1e-9) * .55 * (1 - .45 * d), "music": music / (np.abs(music).max() + 1e-9) * .28 * (1 - .7 * d)}
    mix = sum(buses.values())
    fade = np.ones(N); k = int(.8 * SR); fade[-k:] = np.linspace(1, 0, k) ** 1.5
    mix = np.tanh(mix * fade[:, None] / (np.abs(mix).max() + 1e-9) * 1.2) * .9
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
