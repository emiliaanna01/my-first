"""Background score for the control reel — dark synthwave, 120 BPM, D minor.

At 120 BPM every scene boundary (2.5, 6.0, 10.0, 13.5, 17.0 s) sits on a beat,
so the drops, stops and fills line up with the picture cuts.
"""
import numpy as np

from dsp import (DUR, N, SR, adsr, convolve, delay_pingpong, glide, hp, ir, lp, lp_sweep, mtof, noise, osc, pan,
                 perc, place, t_, widen)

BEAT = 0.5
S16 = BEAT / 4

CHORDS = {
    "Dm": [50, 53, 57], "Bb": [46, 50, 53], "Gm": [43, 46, 50], "A": [45, 49, 52],
    "F": [41, 45, 48], "C": [48, 52, 55], "Dadd9": [50, 53, 57, 64],
}
# (start, end, chord, pad cutoff start, pad cutoff end, pad level)
SECTIONS = [
    (0.0, 2.5, "Dm", 350, 900, 0.55),
    (2.5, 4.0, "Dm", 900, 1100, 0.50),
    (4.0, 6.0, "Bb", 1000, 1300, 0.50),
    (6.0, 8.0, "Gm", 1800, 2600, 0.70),
    (8.0, 10.0, "A", 1600, 5200, 0.70),
    (10.0, 12.0, "Dm", 3200, 2600, 0.85),
    (12.0, 14.0, "Bb", 2600, 2400, 0.80),
    (14.0, 16.0, "F", 2400, 2800, 0.80),
    (16.0, 17.0, "C", 2800, 4200, 0.80),
    (17.0, 20.0, "Dadd9", 2600, 900, 0.90),
]
# hard stops (start, end) — silence in the score so the hits land
STOPS = [(5.86, 6.0), (9.75, 10.0), (13.0, 13.5)]


def chord_at(t):
    for a, b, ch, *_ in SECTIONS:
        if a <= t < b:
            return CHORDS[ch]
    return CHORDS["Dadd9"]


def supersaw(f, d, voices=5, spread=0.14):
    x = np.zeros(int(SR * d))
    for i in range(voices):
        det = (i - (voices - 1) / 2) / ((voices - 1) / 2) * spread
        x += osc(f * 2 ** (det / 12), d, "saw", phase=(i * 0.37) % 1)
    return x / voices


def pad_bus():
    bus = np.zeros((N, 2))
    for a, b, ch, c0, c1, lvl in SECTIONS:
        d = b - a + 0.45
        x = np.zeros(int(SR * d))
        for m in CHORDS[ch]:
            x += supersaw(mtof(m), d) + 0.35 * supersaw(mtof(m + 12), d, 3, 0.08)
        x = lp_sweep(x, c0, c1) * adsr(d, 0.25 if a else 0.9, 0.6, 0.85, 0.45) * lvl
        place(bus, a, widen(x, 0.014, 0.9))
    return bus * 0.16


def bass_note(f, d, cut0=1400, cut1=220, gain=1.0):
    x = osc(f, d, "saw") * 0.6 + osc(f / 2, d, "sine") * 0.7
    x = lp_sweep(x, cut0, cut1, blocks=12, curve=0.5)
    return np.tanh(x * 1.6 * adsr(d, 0.003, 0.08, 0.7, 0.03)) * gain


def bass_bus():
    bus = np.zeros((N, 2))
    t = 2.5
    while t < 5.86 - 1e-6:  # pulsing 8ths
        root = mtof(chord_at(t)[0] - 12)
        place(bus, t, pan(bass_note(root, 0.22, 900, 180, 0.55)))
        t += BEAT / 2
    for a, b in [(10.0, 13.0), (13.5, 16.5)]:  # rolling off-beat 16ths
        t = a
        while t < b - 1e-6:
            step = round((t - a) / S16) % 4
            if step:
                root = mtof(chord_at(t)[0] - 12)
                place(bus, t, pan(bass_note(root, S16 * 0.95, 1800 if step == 2 else 1300, 240, 0.7)))
            t += S16
    place(bus, 17.0, pan(bass_note(mtof(38), 2.6, 600, 120, 0.6) * np.linspace(1, 0, int(SR * 2.6)) ** 1.2))
    return bus * 0.55


ARP_PATTERN = [0, 2, 4, 3, 1, 4, 5, 2]


def arp_bus():
    bus = np.zeros((N, 2))
    spans = [(2.5, 5.86, 1100, 0.45), (6.0, 9.75, None, 0.6), (10.0, 13.0, 3400, 0.6), (13.5, 16.5, 3000, 0.55)]
    for a, b, cut, lvl in spans:
        t, i = a, 0
        while t < b - 1e-6:
            ch = chord_at(t)
            tones = [ch[0], ch[1], ch[2], ch[0] + 12, ch[1] + 12, ch[2] + 12]
            m = tones[ARP_PATTERN[i % 8]] + 12
            c = cut if cut else (2200 if t < 8 else 2200 + 4800 * ((t - 8) / 1.75) ** 2)
            d = 0.16
            x = osc(mtof(m), d, "saw") * 0.5 + osc(mtof(m) * 1.003, d, "square") * 0.25
            x = lp(x, c) * perc(d, 0.002, 0.07) * lvl * (1.0 if i % 4 == 0 else 0.75)
            place(bus, t, pan(x, 0.25 * np.sin(i * 0.9)))
            t += S16
            i += 1
    # end: slow bell arpeggio on Dadd9
    for i, m in enumerate([62, 69, 74, 76, 81, 74]):
        d = 1.6
        x = (osc(mtof(m), d) + 0.3 * osc(mtof(m) * 2.01, d) + 0.12 * osc(mtof(m) * 3.0, d)) * perc(d, 0.003, 0.5)
        place(bus, 17.0 + i * BEAT / 2, pan(x * 0.4, -0.4 + i * 0.16))
    return delay_pingpong(bus, 0.375, 0.33, 5) * 0.2


def kick(gain=1.0):
    d = 0.42
    body = osc(glide(160, 44, d, 0.28), d) * perc(d, 0.001, 0.15)
    click = hp(noise(0.012), 2500) * perc(0.012, 0.0003, 0.003) * 0.4
    body[: len(click)] += click
    return np.tanh(body * 1.8) * gain


def hat(d=0.05, gain=0.15, open_=False):
    d = 0.22 if open_ else d
    return hp(noise(d), 7500) * perc(d, 0.0005, 0.07 if open_ else 0.014) * gain


def clap(gain=0.35):
    d = 0.3
    x = np.zeros(int(SR * d))
    for k, off in enumerate([0, 0.009, 0.018, 0.028]):
        burst = hp(lp(noise(0.25), 5000), 900) * perc(0.25, 0.0005, 0.09 if k == 3 else 0.008)
        x[int(off * SR): int(off * SR) + len(burst)] += burst[: len(x) - int(off * SR)]
    return x * gain


def snare_tick(pitch, gain):
    d = 0.09
    return (hp(noise(d), 1500) * 0.7 + osc(pitch, d, "tri") * 0.3) * perc(d, 0.0005, 0.03) * gain


def drum_bus():
    bus = np.zeros((N, 2))
    kicks = []
    beats = lambda a, b, step=BEAT: list(np.arange(a, b - 1e-6, step))
    for t in beats(2.5, 5.86):
        kicks.append((t, 0.7))
    for t in [8.0, 8.5, 9.0, 9.25, 9.5, 9.625]:
        kicks.append((t, 0.6))
    for t in beats(10.0, 13.0) + beats(13.5, 16.5):
        kicks.append((t, 1.0))
    for t in [16.5, 16.75, 16.875]:
        kicks.append((t, 0.7))
    kicks.append((17.0, 1.0))
    for t, g in kicks:
        place(bus, t, pan(kick(g)))
    for t in beats(2.75, 5.86):                       # off-beat hats
        place(bus, t, pan(hat(gain=0.12), 0.3))
    for i, t in enumerate(beats(6.0, 9.75, S16)):     # light 16ths in the lift
        place(bus, t, pan(hat(gain=0.05 + 0.04 * (i % 4 == 2)), -0.25))
    for t in beats(10.25, 13.0) + beats(13.75, 16.5): # open off-beat hats in the groove
        place(bus, t, pan(hat(open_=True, gain=0.1), 0.2))
    for i, t in enumerate(beats(10.0, 13.0, S16) + beats(13.5, 16.5, S16)):
        if i % 2:
            place(bus, t, pan(hat(gain=0.06), -0.3))
    for t in [10.5, 11.5, 12.5, 14.5, 15.5]:
        place(bus, t, pan(clap()))
    roll = beats(8.0, 9.0, S16) + beats(9.0, 9.75, S16 / 2)  # build snare roll
    for i, t in enumerate(roll):
        k = (t - 8.0) / 1.75
        place(bus, t, pan(snare_tick(180 + 260 * k, 0.05 + 0.28 * k ** 1.5)))
    for t in [16.5, 16.625, 16.75, 16.8125, 16.875, 16.9375]:
        place(bus, t, pan(snare_tick(300 + 300 * (t - 16.5) * 2, 0.18)))
    return bus, [t for t, _ in kicks]


def sidechain(kicks, depth=0.55, rel=0.14):
    g = np.ones(N)
    for tk in kicks:
        a = int(tk * SR)
        n = min(N - a, int(0.6 * SR))
        g[a:a + n] = np.minimum(g[a:a + n], 1 - depth * np.exp(-np.arange(n) / SR / rel))
    return g


def sub_drone():
    bus = np.zeros((N, 2))
    d = 2.6
    x = (osc(mtof(26), d) + 0.3 * osc(mtof(38), d)) * adsr(d, 0.9, 1, 1, 0.5)
    place(bus, 0.0, pan(x * 0.35))
    d = 3.0
    x = (osc(mtof(26), d) + 0.3 * osc(mtof(38), d)) * adsr(d, 0.4, 1, 1, 1.2)
    place(bus, 17.0, pan(x * 0.3))
    return bus


def stop_gain():
    g = np.ones(N)
    f = int(0.008 * SR)
    for a, b in STOPS:
        ia, ib = int(a * SR), int(b * SR)
        g[ia:ib] = 0
        g[ia - f:ia] = np.minimum(g[ia - f:ia], np.linspace(1, 0, f))
        g[ib:ib + f] = np.minimum(g[ib:ib + f], np.linspace(0, 1, f))
    return g


def score():
    drums, kicks = drum_bus()
    sc = sidechain(kicks)[:, None]
    pads, bass, arps = pad_bus(), bass_bus(), arp_bus()
    music = pads * sc + bass * sc + arps * (0.5 + 0.5 * sc) + drums + sub_drone()
    music += convolve(pads * 0.4 + arps * 0.5 + drums * 0.08, ir(2.2, 3.0, 6000)) * 0.6
    music = hp(music, 28)
    music *= stop_gain()[:, None]
    fade = np.ones(N)
    k = int(0.9 * SR)
    fade[-k:] = np.linspace(1, 0, k) ** 1.6
    music *= fade[:, None]
    return np.tanh(music * 1.3) / 1.3, kicks


if __name__ == "__main__":
    import sys

    import soundfile as sf

    m, _ = score()
    sf.write(sys.argv[1], (m / np.abs(m).max() * 0.9).astype(np.float32), SR, subtype="FLOAT")
    print("wrote", sys.argv[1], f"{DUR}s")
