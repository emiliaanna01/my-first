"""Sound design for the control reel — every effect synthesized here, placed on the film's cue points."""
import numpy as np

from dsp import (N, SR, adsr, bp, bp_sweep, convolve, crush, glide, hp, ir, lp, mtof, noise, norm, osc, pan, pan_move,
                 perc, place, t_, widen)


# ---------------- instruments ----------------
def boom(d=1.6, f0=70, f1=28, gain=1.0, click=0.6):
    body = osc(glide(f0, f1, d, 0.3), d) * perc(d, 0.002, d / 3.2)
    knock = lp(noise(0.06), 600) * perc(0.06, 0.0005, 0.02) * 0.8
    crack = hp(noise(0.02), 3000) * perc(0.02, 0.0002, 0.004) * click
    body[: len(knock)] += knock
    body[: len(crack)] += crack
    return np.tanh(body * 1.7) * gain


def metal(d=2.5, base=180, gain=0.35):
    t = t_(d)
    parts = [(1, 1, .9), (1.59, .7, .6), (2.14, .55, .45), (2.83, .4, .35), (3.76, .3, .25), (5.4, .2, .15)]
    x = sum(a * np.sin(2 * np.pi * base * r * t + r) * np.exp(-t / (d * k)) for r, a, k in parts)
    return x * perc(d, 0.0008, d) * gain


def braam(d=1.8, gain=0.35):
    x = np.zeros(int(SR * d))
    for m in (38, 45, 50):
        for det in (-0.12, 0, 0.11):
            x += osc(mtof(m) * 2 ** (det / 12), d, "saw")
    x = lp(x, 900) * adsr(d, 0.02, 0.5, 0.5, 0.7)
    return np.tanh(x * 0.4) * gain


def crash(d=2.6, gain=0.3):
    x = hp(noise(d), 3500) * perc(d, 0.001, 0.7)
    return x * gain


def reverse_swell(d=1.0, gain=0.5, bright=9000):
    """Reverb-tail of a noise burst, reversed — ends exactly at the hit."""
    burst = np.zeros((int(SR * (d + 0.05)), 2))
    burst[:int(0.03 * SR)] = noise(0.03)[:, None] * [[1, 1]]
    tail = convolve(burst, ir(d * 1.1, d + 0.05, bright, pre=0))
    tail = tail[::-1][-int(SR * d):]
    shape = np.linspace(0, 1, len(tail)) ** 2.2
    return norm(tail * shape[:, None]) * gain


def whoosh(d=0.6, f0=300, f1=4000, peak=0.7, gain=0.6, tone=True):
    x = bp_sweep(noise(d), f0, f1, q=2.2)
    if tone:
        x += osc(glide(f0 * 0.6, f1 * 0.25, d), d) * 0.18
    u = t_(d) / d
    e = np.where(u < peak, (u / peak) ** 2, ((1 - u) / (1 - peak + 1e-9)) ** 1.6)
    return x * e * gain


def mech_click(f=3000, gain=0.3, seed=0):
    d = 0.04
    x = np.zeros(int(SR * d))
    for off, g in ((0, 1.0), (0.0045 + 0.001 * (seed % 3), 0.55)):
        b = bp(noise(0.012), f * 0.7, f * 1.6) * perc(0.012, 0.0002, 0.0025) * g
        i = int(off * SR)
        x[i:i + len(b)] += b[: len(x) - i]
    x[:int(0.006 * SR)] += osc(f * 0.5, 0.006) * perc(0.006, 0.0002, 0.0015) * 0.3
    return x * gain


def buzz(d=0.08, gain=0.25):
    x = osc(100, d, "saw") * 0.6 + osc(150, d, "square") * 0.3 + hp(noise(d), 4000) * 0.3
    return lp(x, 3500) * adsr(d, 0.002, 0.03, 0.7, 0.01) * gain


def power_down(d=1.1, gain=0.4):
    f = glide(220, 26, d, 0.55)
    x = osc(f, d, "saw") * 0.5 + osc(f * 2.01, d, "saw") * 0.25 + osc(f / 2, d) * 0.6
    return lp(x, 2200) * np.exp(-t_(d) / 0.5) * gain


def charge(d=0.24, gain=0.35):
    t = t_(d)
    x = osc(glide(350, 3200, d, 1.3), d) * (0.7 + 0.3 * np.sin(2 * np.pi * 40 * t))
    return x * (t / d) ** 1.5 * gain


def alarm(gain=0.22):
    x = np.concatenate([osc(988, 0.09, "square"), osc(784, 0.09, "square")])
    return lp(x, 3000) * adsr(len(x) / SR, 0.002, 0.05, 0.8, 0.03) * gain


def slow_tick(gain=0.3):
    d = 0.32
    return osc(glide(1400, 260, d, 0.6), d, "tri") * perc(d, 0.001, 0.09) * gain


def glitch(d=0.28, gain=0.3, seed=3):
    rng = np.random.default_rng(seed)
    x = np.zeros(int(SR * d))
    pos = 0
    while pos < len(x):
        seg = int(SR * rng.uniform(0.008, 0.03))
        f = rng.choice([300, 600, 1200, 2400, 4800])
        chunk = (osc(f, seg / SR, "square") * 0.5 + noise(seg / SR) * 0.5) * rng.uniform(0.2, 1)
        n = min(len(chunk), len(x) - pos)
        x[pos:pos + n] = chunk[:n] * (rng.random() > 0.25)
        pos += seg
    return crush(x, 5, 6) * perc(d, 0.001, d / 2) * gain


def stutter(x, reps=4, gap=0.045, decay=0.55):
    out = np.zeros(int(len(x) + reps * gap * SR))
    for i in range(reps):
        a = int(i * gap * SR)
        out[a:a + len(x)] += x * decay ** i
    return out


def zap(d=0.28, gain=0.35):
    return osc(glide(2600, 90, d, 0.45), d, "saw") * perc(d, 0.0005, 0.07) * gain


def tink(f=1760, gain=0.18):
    d = 0.6
    t = t_(d)
    mod = np.sin(2 * np.pi * f * 1.41 * t) * 2.2 * np.exp(-t / 0.05)
    return np.sin(2 * np.pi * f * t + mod) * perc(d, 0.0008, 0.16) * gain


def chirp_stream(d=0.55, gain=0.12, seed=5):
    rng = np.random.default_rng(seed)
    x = np.zeros(int(SR * d))
    t = 0.0
    while t < d - 0.03:
        dd = rng.uniform(0.018, 0.035)
        f0 = rng.uniform(1500, 4000)
        c = osc(glide(f0, f0 * rng.uniform(0.6, 1.8), dd), dd) * perc(dd, 0.0005, dd / 3)
        a = int(t * SR)
        x[a:a + len(c)] += c[: len(x) - a]
        t += dd * rng.uniform(0.8, 1.4)
    return x * gain


def glass_swipe(d=0.8, gain=0.22):
    t = t_(d)
    air = bp_sweep(noise(d), 2500, 12000, q=3)
    partials = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([2349, 2793, 3520, 4699, 5588]))
    trem = 0.55 + 0.45 * np.sin(2 * np.pi * 22 * t)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    return (air * 0.6 + partials / 5 * trem * 0.5) * e * gain


def chime(f=1046.5, d=2.2, gain=0.2):
    t = t_(d)
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / (d * k)) for m, a, k in [(1, 1, .4), (2.0, .4, .25), (3.01, .25, .14), (4.17, .12, .08)])
    return x * perc(d, 0.002, d) * gain


def riser(d=1.6, gain=0.35):
    u = t_(d) / d
    tone = osc(glide(140, 1800, d, 1.5), d, "saw") * 0.12 + osc(glide(210, 2700, d, 1.5), d) * 0.15
    air = bp_sweep(noise(d), 400, 10000, q=1.4) * 0.6
    return lp(tone, 5000) * u ** 2.4 * gain + air * u ** 2.6 * gain


def pop(f0=500, f1=1500, gain=0.25):
    d = 0.12
    return osc(glide(f0, f1, d, 0.35), d) * perc(d, 0.001, 0.035) * gain


def warm_swell(d=1.1, gain=0.25):
    x = sum(osc(mtof(m), d, "saw") for m in (50, 57, 62, 64)) / 4
    return lp(x, 1400) * np.sin(np.pi * np.clip(t_(d) / d, 0, 1)) ** 2 * gain


# ---------------- arrangement ----------------
def design():
    dry = np.zeros((N, 2))
    send = np.zeros((N, 2))

    def put(t0, x, p=0.0, rev=0.25):
        s = x if x.ndim == 2 else pan(x, p)
        place(dry, t0, s)
        place(send, t0, s * rev)

    # beat 1 — hook
    put(0.00, boom(1.6, 64, 30, 0.9), rev=0.25)
    put(0.00, tink(2637, 0.14), 0.3, 0.5)
    for i in range(9):
        put(0.10 + i * 0.046, mech_click(2600 + 260 * (i % 4), 0.2, i), -0.3 + i * 0.07, 0.12)
    for i, k in enumerate([0.55, 0.61, 0.69, 0.78, 0.85]):
        put(k, buzz(0.05 + 0.02 * (i % 2), 0.16), 0.3, 0.2)
    put(0.95, power_down(1.1, 0.34), rev=0.3)
    put(1.95, reverse_swell(0.27, 0.35), rev=0.0)
    put(2.00, charge(0.22, 0.25), 0.3, 0.3)
    put(2.22, boom(1.2, 80, 34, 0.6, 0.4), rev=0.3)
    put(2.20, pan_move(whoosh(0.6, 250, 7000, 0.25, 0.65), 0.35, -0.7), rev=0.35)

    # beat 2 — each problem word has its own sound
    for k, tk in enumerate([2.5, 3.6, 4.7]):
        put(tk - 0.12, whoosh(0.13, 1500, 6000, 0.85, 0.22, False), rev=0.15)
        put(tk, boom(0.6, 92 - 8 * k, 42, 0.55, 0.7), rev=0.3)
    put(2.5, alarm(0.16), 0.25, 0.4)
    put(2.72, alarm(0.08), 0.35, 0.5)
    put(3.6, slow_tick(0.24), -0.2, 0.45)
    put(4.7, stutter(glitch(0.12, 0.22), 4, 0.05), 0.0, 0.25)
    put(5.48, whoosh(0.4, 500, 8000, 0.94, 0.45), rev=0.25)
    put(5.86, zap(0.3, 0.3), rev=0.5)
    put(5.86, boom(0.5, 110, 50, 0.35, 0.9), rev=0.3)

    # beat 3 — solution
    w = whoosh(0.75, 3500, 220, 0.1, 0.5)
    put(6.00, np.stack([w, np.concatenate([np.zeros(int(0.018 * SR)), w])[: len(w)]], 1), rev=0.4)
    put(6.00, boom(0.9, 56, 30, 0.4, 0), rev=0.15)
    for i, tk in enumerate([5.98, 6.04, 6.10, 6.18, 6.30, 6.36]):
        put(tk, whoosh(0.3, 900, 3000, 0.55, 0.06, False), [-0.6, 0.6, -0.5, 0.5, -0.8, 0.8][i], 0.2)
        put(tk + 0.05, tink([1568, 1976, 2349, 1760, 2637, 3136][i], 0.06), [-0.6, 0.6, -0.5, 0.5, -0.8, 0.8][i], 0.6)
    put(6.90, mech_click(2200, 0.2, 2), 0.5, 0.25)
    put(7.30, pan_move(glass_swipe(0.9, 0.2), -0.7, 0.7), rev=0.5)
    put(8.15, chime(1174.7, 2.0, 0.14), 0.0, 0.7)
    put(8.15, riser(1.6, 0.3), rev=0.3)
    put(9.05, pan_move(chirp_stream(0.55, 0.1), 0.6, -0.1), rev=0.35)
    put(9.60, mech_click(3400, 0.35, 1), rev=0.5)
    put(9.60, boom(0.35, 120, 60, 0.25, 0.3), rev=0.2)
    put(9.25, reverse_swell(0.75, 0.42), rev=0.0)

    # beat 4 — main impact
    put(10.00, boom(2.6, 74, 26, 1.0, 1.0), rev=0.45)
    put(10.00, metal(2.6, 196, 0.22), 0.0, 0.6)
    put(10.00, widen(braam(1.9, 0.28), 0.015, 0.8), rev=0.35)
    put(10.00, widen(crash(2.6, 0.18)), rev=0.5)
    put(10.35, pan_move(whoosh(0.5, 2000, 7000, 0.3, 0.12, False), -0.6, 0.6), rev=0.3)
    put(11.15, pan_move(glass_swipe(0.7, 0.14), -0.6, 0.6), rev=0.5)
    put(12.70, reverse_swell(0.3, 0.12), rev=0.0)
    put(13.00, whoosh(0.5, 150, 6000, 0.96, 0.7), rev=0.25)

    # beat 5 — benefit
    put(13.50, boom(1.1, 60, 30, 0.55, 0.5), rev=0.3)
    put(13.50, whoosh(0.45, 3200, 500, 0.08, 0.2, False), rev=0.3)
    put(14.60, mech_click(2000, 0.26, 4), 0.15, 0.25)
    put(14.64, pop(880, 1320, 0.1), 0.15, 0.35)
    put(15.35, pan_move(glass_swipe(0.75, 0.16), -0.5, 0.5), rev=0.5)
    put(16.30, reverse_swell(0.7, 0.3), rev=0.0)
    put(16.50, whoosh(0.5, 200, 8000, 0.96, 0.6), rev=0.3)

    # beat 6 — end frame
    put(17.00, widen(warm_swell(1.2, 0.2)), rev=0.5)
    put(17.00, boom(1.6, 54, 28, 0.45, 0.2), rev=0.3)
    put(17.50, pop(600, 1600, 0.16), rev=0.5)
    put(18.30, pan_move(glass_swipe(0.7, 0.06), -0.6, 0.6), rev=0.4)
    put(18.42, pop(500, 1000, 0.08), rev=0.3)
    for i in range(15):
        put(18.70 + i * 0.03, mech_click(3000 + 200 * (i % 3), 0.035, i), -0.3 + i * 0.04, 0.1)
    put(19.00, boom(1.0, 46, 28, 0.5, 0), rev=0.2)
    put(19.00, chime(880, 2.4, 0.06), 0.0, 0.8)

    wet = convolve(send, ir(1.7, 2.6))
    return hp(dry + wet * 0.85, 25)
