#!/usr/bin/env python3
"""Music edit + sound design + mix for 'The Man Who Never Was'.
Music: Leberch "Cinematic Documentary" (Pixabay), cut on its beat grid to the story: intro under the hook, a hard
drop to silence on "They find a body", the build re-entering at the drifter and peaking at the landing, then the
track's own fade under the grave. It sits higher than in the earlier reels and ducks less, like the reference.
Effects: rendered by id from earshot's code-made bank (no recordings), plus one CC0 clock recording and a few
filtered-noise beds (rain-less sea, underwater rumble, wind).
usage: python3 motion/mincemeat/audio.py <vo_dir> <out_wav>"""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "audio"))
from dsp import SR, adsr, bp, convolve, hp, ir, lp, noise, pan, place, t_, widen  # noqa: E402

VO = {m["id"]: m for m in json.load(open(os.path.join(HERE, "vo.json")))}
W = lambda cid, n=0: VO[cid]["words"][min(n, len(VO[cid]["words"]) - 1)]
END = lambda cid: VO[cid]["t"] + VO[cid]["dur"]
DUR = round(END("never") + 3.4, 2); N = int(SR * DUR)
TRACK = os.path.join(HERE, "music.mp3")
# scene cuts, identical to the film
T_FACE, T_SIC, T_LON, T_BODY = W("hook", 6) - .12, W("sicily", 0) - .25, W("london", 0) - .25, W("body", 0) - .2
T_DRI, T_NEW, T_MAR, T_PAM = W("drifter", 0) - .15, W("newlife", 0) - .12, W("martin", 0) - .12, W("pam", 0) - .15
T_GRE, T_APR, T_FIS, T_COP = W("greece", 0) - .15, W("april", 0) - .2, W("fisher", 0) - .15, W("copy", 0) - .15
T_PAN, T_JUL, T_MSG, T_GRV = W("panzer", 0) - .15, W("july", 0) - .15, W("message", 0) - .15, W("grave", 0) - .2
T_STN = W("grave", 8) + .35

_CACHE = {}
def es(sid, **kw):
    """render one earshot bank sound -> mono float array at SR"""
    key = (sid, tuple(sorted(kw.items())))
    if key not in _CACHE:
        f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        args = ["earshot", "sfx", "render", sid, "-o", f, "--sr", str(SR)] + sum([[f"--{k}", str(v)] for k, v in kw.items()], [])
        subprocess.run(args, check=True, capture_output=True)
        x, _ = sf.read(f); os.remove(f); _CACHE[key] = x.mean(1) if x.ndim > 1 else x
    return _CACHE[key]

# ---------------- music ----------------
def music():
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", TRACK, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
    BEAT = 60 / 117.45
    # (video start, video end, track time at video start); piece 2 puts the track's loud section on the landing
    sh2 = 112.27 - (W("july", 0) - .15)
    s2 = T_DRI - .05; s2 += ((s2 + sh2 - .79) % BEAT and BEAT - (s2 + sh2 - .79) % BEAT)   # start on a beat
    sh3 = 159.0 - (END("never") + 1.4)
    pieces = [(0, T_BODY, .3), (s2, T_GRV + .4, s2 + sh2), (T_GRV - .4, DUR, T_GRV - .4 + sh3)]
    out = np.zeros((N, 2)); xf = int(.06 * SR)
    for v0, v1, src in pieces:
        a, b = int(v0 * SR), min(N, int(v1 * SR)); s0 = int(src * SR); seg = x[s0: s0 + (b - a)].copy()
        fi = int((.8 if v0 > 30 else .05) * SR); fo = int((.8 if v1 < DUR and v1 > 30 else .03) * SR)
        if a > 0: seg[:fi] *= np.linspace(0, 1, fi)[:, None]
        if b < N: seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        out[a: a + len(seg)] += seg
    tt = np.arange(N) / SR; g = np.ones(N)
    def dip(a, b, db, ra=.08, rb=.08): g[:] *= 10 ** (db / 20 * np.clip(np.minimum((tt - a) / ra, (b - tt) / rb), 0, 1))
    dip(W("sicily", 3) - .25, W("sicily", 3) + .05, -9)          # breath before "Sicily."
    dip(W("greece", 8) - .35, W("greece", 8) + .02, -12)          # breath before "Greece."
    dip(T_JUL - .35, T_JUL + .02, -30, .05, .02)                  # silence, then the landing hits
    dip(W("message", 6) - .3, W("message", 6) + .02, -10)         # before "rod, line and sinker"
    dip(W("beneath", 2) - .3, W("beneath", 2) + .05, -8)
    k = int(2.0 * SR); g[-k:] *= np.linspace(1, 0, k) ** 1.5
    return out * g[:, None]

# ---------------- sound design ----------------
def pencil(d, g=.05, rate=3.2):
    return bp(noise(d), 2500, 7500) * (np.abs(np.sin(2 * np.pi * rate * t_(d))) ** 2) * (.6 + .4 * np.sin(2 * np.pi * .7 * t_(d))) * g

def bed(d, lo, hi, g, swell=.15, seed=1):
    rng = np.random.default_rng(seed); x = bp(noise(d), lo, hi)
    env = np.convolve(np.abs(rng.normal(0, 1, len(x))), np.ones(int(SR * .6)) / (SR * .6), "same")
    return x * (1 + swell * (env / env.mean() - 1)) * adsr(d, min(.6, d / 4), 1, 1, min(.8, d / 4)) * g

def waves(d, g=.06):
    t = t_(d); env = .35 + .65 * np.clip(np.sin(2 * np.pi * t / 2.6 - 1.2), 0, 1) ** 2
    return (bp(noise(d), 200, 2500) * env + lp(noise(d), 180) * .5) * adsr(d, .3, 1, 1, .5) * g

def design():
    dry = np.zeros((N, 2)); send = np.zeros((N, 2)); rng = np.random.default_rng(3)
    def put(t0, x, p=0., rv=.2, g=1.):
        x = x * g; s = x if x.ndim == 2 else pan(x, p); place(dry, t0, s); place(send, t0, s * rv)
    def hit(sid, t, g=1., p=0., rv=.25, **kw):     # place a bank sound so its peak lands on t
        x = es(sid, **kw); pk = np.argmax(np.abs(x)) / SR; put(t - pk, x, p, rv, g)
    # hook: drips on the wet briefcase, the date lands, the face, "Hitler"
    for tt in (.5, 1.35, 2.2): hit("drip/drop", tt, .35, .2, .5)
    hit("cut_hit/sub", W("hook", 4), .7)
    hit("whoosh_big/swell", T_FACE, .55)
    hit("pro_sub_drop/soft", W("hook", 11) + .05, .6)
    hit("reverse_swell/dark", W("believed", 2), .4, 0, .1)
    # Sicily: map paper, the pencil circles
    hit("swipe/paper", T_SIC + .05, .5); put(T_SIC + .4, pencil(2.4, .06, 2.4), .25, .1)
    hit("cut_hit/air", W("sicily", 3), .45)
    # London: street + the planners' print drops
    hit("whoosh_fast/crisp", T_LON, .45); put(T_LON, widen(bed(T_BODY - T_LON, 150, 1800, .035, seed=4)), 0, .3)
    hit("knock/desk", W("london", 3) + .45, .5); hit("swipe/paper", W("london", 3) + .2, .45)
    hit("cut_hit/kick", W("london", 8) + .1, .45)
    # a body: music out; one card in the silence, a clock
    clock, csr = sf.read(os.path.join(HERE, "sfx/rec/clock_ticking.ogx")); clock = clock.mean(1) if clock.ndim > 1 else clock
    clock = signal.resample_poly(clock, SR, csr)[: int((T_DRI - T_BODY + .3) * SR)]; clock *= adsr(len(clock) / SR, .1, 1, 1, .3)
    put(T_BODY, clock, .3, .3, .12)
    hit("swipe/paper", T_BODY + .45, .6); hit("pro_typing_run/soft", T_BODY + .8, .35, dur=1.0)
    hit("pro_sub_drop/low", W("body", 3), .5)
    # the drifter: pencil underline, his name
    put(T_DRI + .45, pencil(2.0, .07, 1.2), .2, .1)
    hit("reverse_swell/ring", W("drifter", 3), .4, 0, .1); hit("cut_hit/sub", W("drifter", 3) + .02, .5)
    # a new life: typewriter + carriage bell
    hit("pro_typing_run/standard", T_NEW + .9, .55, dur=1.6, p=.2)
    hit("fit/bell/small_bell", T_NEW + 1.75, .25, .3, .3)
    # Major Martin: the cut-out lands, the tag stamps
    hit("whoosh_big/thump", T_MAR + .4, .5); hit("knock/wood", W("martin", 3), .6); hit("cut_hit/kick", W("martin", 3), .45)
    # pocket litter
    for i, tt in enumerate([W("pam", 3), W("pam", 4), W("pam", 6), W("pam", 9)]):
        hit(["swipe/paper", "swipe/velvet", "swipe/flick", "swipe/paper"][i], tt + .15, .5, (-1) ** i * .3)
        hit("knock/desk", tt + .4, .3, (-1) ** i * .3)
    put(W("pam", 4) + .1, pencil(1.8, .03, 4), -.2, .1)
    # the briefcase: clasps, the letter, "Greece"
    hit("toggle/latch", T_GRE + .25, .55, -.2); hit("toggle/latch", T_GRE + .45, .5, .2)
    hit("swipe/paper", W("greece", 4) - .05, .55); hit("pro_typing_run/tick", W("greece", 4) + .6, .3, dur=1.4)
    hit("impact/deep", W("greece", 8) + .02, .7, 0, .35)
    # submarine: underwater rumble, one ping, the date
    put(T_APR - .3, widen(lp(noise(T_FIS - T_APR + .5), 260) * adsr(T_FIS - T_APR + .5, .6, 1, 1, .5) * .12), 0, .2)
    hit("whoosh_big/deep", T_APR + .2, .45)
    hit("mallet/glock", W("april", 6) + .1, .35, .1, .9, pitch="E5"); hit("mallet/glock", W("april", 6) + 1.3, .12, .1, .9, pitch="E5")
    hit("cut_hit/sub", W("april", 2), .55)
    # fisherman: the sea at dawn
    put(T_FIS - .3, widen(waves(T_COP - T_FIS + .5, .07)), 0, .2)
    # copied: two camera shutters with flash
    hit("shutter/film", W("copy", 5) + .05, .8, .1); hit("shutter/film", W("copy", 7) + .1, .65, -.1)
    hit("whoosh_fast/crisp", T_COP, .35)
    # panzers: engine rumble, the arrow, "Greece"
    hit("whoosh_fast/heavy", T_PAN, .45)
    eng = lp(np.sign(np.sin(2 * np.pi * 34 * t_(2.6))) * (.6 + .4 * np.sin(2 * np.pi * 9 * t_(2.6))), 260) * adsr(2.6, .4, 1, 1, .6) * .06
    put(W("panzer", 1), widen(eng), 0, .2)
    hit("sub_drop/punch", W("panzer", 6) + .02, .6)
    # July: silence, then the landing
    hit("impact/classic", T_JUL + .02, .7, 0, .4)
    put(T_JUL, widen(waves(END("july") - T_JUL + .6, .05) + bed(END("july") - T_JUL + .6, 120, 900, .03, .4, 9)), 0, .3)
    hit("cut_hit/rumble", W("july", 6) + .02, .55)
    # the telegram: teleprinter typing, a riser into "rod, line and sinker", bell
    hit("pro_typing_run/tick", W("message", 1) + 1.2, .5, dur=2.6, p=-.2)
    hit("riser/tension", W("message", 6) - .05, .35, dur=1.6)
    hit("impact/swell", W("message", 6) + .02, .55, 0, .4)
    hit("fit/bell/small_bell", W("message", 9) + .3, .2, .3, .4)
    # Huelva: wind, a distant bell, the inscription
    put(T_GRV - .4, widen(bed(DUR - T_GRV + .4, 300, 1500, .035, .35, 7)), 0, .3)
    hit("fit/bell/small_bell", T_GRV + .5, .22, .4, .8, pitch="E5")
    hit("reverse_swell/ring", W("beneath", 2), .45, 0, .2)
    hit("impact/deep", W("never", 0) + .02, .45, 0, .45)
    hit("downlifter/sub_sink", END("never") + 1.0, .4)
    return hp(dry + convolve(send, ir(1.6, 2.2, 6000)) * .7, 30)

# ---------------- mix ----------------
def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    v = np.zeros((N, 2))
    for m in meta:
        x, sr = sf.read(m["file"]); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        x = hp(x, 80); x = x + bp(x, 2500, 5000) * .25 + bp(x, 120, 240) * .15; x = x / (np.abs(x).max() + 1e-9) * .85; place(v, m["t"], pan(x))
    v = v + convolve(v, ir(.4, .6, 5000)) * .12
    lvl = np.abs(v).max(1); k = int(.03 * SR)
    e = signal.sosfiltfilt(signal.butter(1, 4, "lowpass", fs=SR, output="sos"), np.convolve(lvl, np.ones(k) / k, "same"))
    d = np.clip(e / (e.max() + 1e-9) * 3, 0, 1)[:, None]
    mus = music(); mus = mus - bp(mus, 1200, 3800) * .3      # a little room for the voice
    sfx = design()
    buses = {"vo": v, "sfx": sfx / (np.abs(sfx).max() + 1e-9) * .7 * (1 - .35 * d), "music": mus / (np.abs(mus).max() + 1e-9) * .42 * (1 - .42 * d)}
    mix = sum(buses.values())
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.25) * .9
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    sos = signal.butter(4, [300, 4000], "bandpass", fs=SR, output="sos")
    a_ = signal.sosfilt(sos, buses["vo"].mean(1)); r_ = signal.sosfilt(sos, (buses["sfx"] + buses["music"]).mean(1))
    rows = []
    for m in meta:
        i0, i1 = int(m["t"] * SR), int((m["t"] + m["dur"]) * SR)
        rows.append((20 * np.log10((np.sqrt(np.mean(a_[i0:i1] ** 2)) + 1e-9) / (np.sqrt(np.mean(r_[i0:i1] ** 2)) + 1e-9)), m["t"], m["text"]))
    for db, t, txt in sorted(rows)[:5]: print(f"{t:6.2f}s {db:5.1f} dB  {txt}")
    rv = np.sqrt(np.mean(buses["music"] ** 2)) / (np.sqrt(np.mean(buses["vo"] ** 2)) + 1e-9)
    print(f"music/voice overall {20 * np.log10(rv):.1f} dB"); print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
