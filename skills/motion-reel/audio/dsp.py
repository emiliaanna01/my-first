"""Small synthesis toolkit shared by music.py and sfx.py (48 kHz, numpy/scipy)."""
import numpy as np
from scipy import signal

SR = 48000
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(SR * d)) / SR


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def noise(d):
    return rng.standard_normal(int(SR * d))


def _sos(kind, f, order=2):
    f = np.clip(f, 20, SR / 2 - 200)
    return signal.butter(order, f, kind, fs=SR, output="sos")


def lp(x, f, order=2):
    return signal.sosfilt(_sos("lowpass", f, order), x, axis=0)


def hp(x, f, order=2):
    return signal.sosfilt(_sos("highpass", f, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bandpass", [lo, hi], order), x, axis=0)


def lp_sweep(x, f0, f1, blocks=48, curve=1.0):
    """Low-pass whose cutoff glides f0 -> f1 (log), state carried block to block."""
    n = len(x)
    out = np.zeros_like(x)
    zi = None
    for i in range(blocks):
        a, b = i * n // blocks, (i + 1) * n // blocks
        k = (i / max(1, blocks - 1)) ** curve
        sos = _sos("lowpass", f0 * (f1 / f0) ** k)
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        out[a:b], zi = signal.sosfilt(sos, x[a:b], zi=zi)
    return out


def bp_sweep(x, f0, f1, q=2.0, blocks=64):
    n = len(x)
    out = np.zeros_like(x)
    zi = None
    for i in range(blocks):
        a, b = i * n // blocks, (i + 1) * n // blocks
        fc = f0 * (f1 / f0) ** (i / max(1, blocks - 1))
        sos = _sos("bandpass", [max(25, fc / (1 + 1 / q)), fc * (1 + 1 / q)])
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        out[a:b], zi = signal.sosfilt(sos, x[a:b], zi=zi)
    return out / (np.abs(out).max() + 1e-9)


def osc(f, d, kind="sine", phase=0.0):
    """f may be a scalar or an array (glide)."""
    n = int(SR * d)
    f = np.broadcast_to(np.asarray(f, float), (n,)) if np.ndim(f) else np.full(n, float(f))
    ph = np.cumsum(f) / SR + phase
    if kind == "sine":
        return np.sin(2 * np.pi * ph)
    if kind == "saw":
        return 2 * (ph % 1) - 1
    if kind == "square":
        return np.sign(np.sin(2 * np.pi * ph))
    if kind == "tri":
        return 2 * np.abs(2 * (ph % 1) - 1) - 1
    raise ValueError(kind)


def glide(f0, f1, d, shape=1.0):
    k = (t_(d) / d) ** shape
    return f0 * (f1 / f0) ** k


def adsr(d, a=0.005, dc=0.1, s=0.6, r=0.1):
    n = int(SR * d)
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-5), s + (1 - s) * np.exp(-(t - a) / max(dc, 1e-5)))
    rel = int(SR * min(r, d))
    if rel:
        e[-rel:] *= np.linspace(1, 0, rel)
    return e


def perc(d, a=0.001, decay=0.2):
    t = t_(d)
    return np.minimum(1, t / max(a, 1e-5)) * np.exp(-np.maximum(0, t - a) / decay)


def pan(x, p=0.0):
    p = np.asarray(p)
    return np.stack([x * np.cos((p + 1) * np.pi / 4), x * np.sin((p + 1) * np.pi / 4)], 1)


def pan_move(x, p0, p1):
    return pan(x, np.linspace(p0, p1, len(x)))


def widen(x, ms=0.012, amt=0.6):
    """Mono -> stereo via short decorrelating delay on one side."""
    k = int(ms * SR)
    l = x
    r = np.concatenate([np.zeros(k), x[:-k]]) if k else x
    mid = (l + r) / 2
    side = (l - r) / 2 * amt
    return np.stack([mid + side, mid - side], 1)


def ir(decay=1.6, d=2.6, bright=7000, pre=0.012):
    t = t_(d)
    e = np.exp(-t / (decay / 6.9))
    e[: int(pre * SR)] = 0
    l = lp(noise(d), bright) * e
    r = lp(noise(d), bright) * e
    return np.stack([l, r], 1) / np.sqrt(np.sum(l ** 2) + 1e-9) * 0.5


def convolve(x, h):
    return np.stack([signal.fftconvolve(x[:, c], h[:, c])[: len(x)] for c in range(2)], 1)


def delay_pingpong(x, dt, fb=0.35, n=6, damp=4500):
    out = x.copy()
    k = int(dt * SR)
    tap = x.copy()
    for i in range(1, n + 1):
        tap = lp(tap, damp) * fb
        sh = np.zeros_like(x)
        if k * i < len(x):
            sh[k * i:] = tap[: len(x) - k * i][:, ::-1] if i % 2 else tap[: len(x) - k * i]
        out += sh
    return out


def crush(x, bits=6, hold=4):
    y = np.repeat(x[::hold], hold)[: len(x)]
    q = 2 ** (bits - 1)
    return np.round(y * q) / q


def place(bus, t0, x):
    a = int(round(t0 * SR))
    if a >= len(bus) or a + len(x) <= 0:
        return
    s = max(0, -a)
    a = max(0, a)
    b = min(len(bus), a + len(x) - s)
    bus[a:b] += x[s:s + b - a]


def norm(x, peak=1.0):
    return x / (np.abs(x).max() + 1e-12) * peak
