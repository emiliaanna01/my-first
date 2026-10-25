#!/usr/bin/env python3
"""Turn studio renders into period plates.

engrave: hatched line-work (line width follows shading, cross-hatch in the darks), ink contours
         from material boundaries, hand-tinted washes (teal glass, walnut wood), sepia ink on cream.
albumen: soft sepia photograph with grain, for the wide establishing shots.

usage: python3 post.py raw cut
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ALBUMEN = {"hydepark", "palace", "towers"}
INK = np.array([42, 28, 18], float)
PAPER = np.array([241, 230, 207], float)
# id colour → (wash colour, strength, hatch angle offset)
IDS = {
    (0, 255, 255): ((111, 152, 158), .55, 1.6),   # glass → teal
    (192, 128, 64): ((176, 128, 88), .42, .4),    # wood → walnut
    (64, 192, 64): ((190, 184, 140), .4, 1.1),    # leaf → olive sepia
    (255, 0, 0): ((160, 96, 78), .35, .7),        # soldiers' coats
    (255, 128, 128): ((228, 200, 172), .3, 2.2),  # skin
    (32, 64, 96): ((120, 104, 92), .2, .9),       # coats
    (255, 255, 128): ((246, 238, 214), .2, 2.6),  # flower
    (0, 0, 255): ((150, 170, 168), .35, 0.0),     # water
    (160, 96, 192): ((160, 140, 128), .25, 1.9),  # dress
}

def smooth_noise(h, w, scale, amp, seed):
    r = np.random.default_rng(seed).normal(0, 1, (h // scale + 2, w // scale + 2))
    r = ndimage.zoom(r, scale, order=3)[:h, :w]
    return r / (r.std() + 1e-9) * amp

def load(name, src):
    sh = np.asarray(Image.open(os.path.join(src, name + ".png")).convert("RGBA")).astype(float)
    idp = os.path.join(src, name + "_id.png")
    ids = np.asarray(Image.open(idp).convert("RGB")).astype(int) if os.path.exists(idp) else None
    return sh, ids

def stretch(L, m, lo=1, hi=99.3, gamma=1.0):
    a, b = np.percentile(L[m], lo), np.percentile(L[m], hi)
    return np.clip((L - a) / max(b - a, 1e-3), 0, 1) ** gamma

def engrave(sh, ids, seed):
    h, w = sh.shape[:2]
    alpha = sh[..., 3] / 255; m = alpha > .5
    L = stretch((sh[..., :3] @ [.299, .587, .114]) / 255, m, gamma=1.15)
    Y, X = np.mgrid[0:h, 0:w].astype(float)
    base = np.tile(PAPER, (h, w, 1)); ang = np.full((h, w), .95)
    edge = np.zeros((h, w), bool)
    if ids is not None:
        key = ids[..., 0] * 65536 + ids[..., 1] * 256 + ids[..., 2]
        for col, (wash, s, da) in IDS.items():
            sel = key == col[0] * 65536 + col[1] * 256 + col[2]
            base[sel] = base[sel] * (1 - s) + np.array(wash, float) * s; ang[sel] += da
        edge = (np.abs(np.diff(key, axis=0, prepend=key[:1])) > 0) | (np.abs(np.diff(key, axis=1, prepend=key[:, :1])) > 0)
    am = alpha > .5
    edge |= (am ^ ndimage.binary_erosion(am, iterations=1))
    gx, gy = ndimage.sobel(ndimage.gaussian_filter(L, 1.2), 1), ndimage.sobel(ndimage.gaussian_filter(L, 1.2), 0)
    edge |= np.hypot(gx, gy) > 1.15
    contour = ndimage.gaussian_filter(ndimage.binary_dilation(edge, iterations=1).astype(float), .7)
    n = smooth_noise(h, w, 40, .9, seed) + smooth_noise(h, w, 7, .25, seed + 1)
    s = 5.2; d = 1 - L
    def hatch(theta, width):
        u = (X * np.cos(theta) + Y * np.sin(theta)) / s + n / s * 1.6
        dist = np.abs((u % 1) - .5)
        return np.clip((width / 2 - dist) * s + .5, 0, 1)
    i1 = hatch(ang, np.clip(d * 1.05, 0, .92))
    i2 = hatch(ang + 1.15, np.clip((d - .42) * 1.7, 0, .85))
    i3 = hatch(ang - .55, np.clip((d - .74) * 2.4, 0, .8))
    ink = np.maximum.reduce([i1, i2, i3, np.clip(contour * 1.3, 0, 1)])
    out = base * (1 - ink[..., None]) + INK * ink[..., None]
    return out, alpha

def albumen(sh, ids, seed):
    h, w = sh.shape[:2]
    alpha = sh[..., 3] / 255; m = alpha > .5
    L = stretch((sh[..., :3] @ [.299, .587, .114]) / 255, m, lo=.5, hi=99.6, gamma=1.05)
    L = ndimage.gaussian_filter(L, .9)
    stops = [(0, (40, 26, 16)), (.45, (120, 90, 62)), (.8, (205, 182, 148)), (1, (240, 228, 204))]
    xs = [p for p, _ in stops]
    out = np.stack([np.interp(L, xs, [c[i] for _, c in stops]) for i in range(3)], -1)
    if ids is not None:
        key = ids[..., 0] * 65536 + ids[..., 1] * 256 + ids[..., 2]
        sel = key == 255 * 256 + 255
        out[sel] = out[sel] * .72 + np.array([96, 140, 148]) * .28
    out += np.random.default_rng(seed).normal(0, 6, (h, w))[..., None]
    return out, alpha

def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    for p in sorted(glob.glob(os.path.join(src, "*.png"))):
        name = os.path.basename(p)[:-4]
        if name.endswith("_id"):
            continue
        sh, ids = load(name, src)
        fn = albumen if name in ALBUMEN else engrave
        out, a = fn(sh, ids, abs(hash(name)) % 9999)
        img = Image.fromarray(np.dstack([np.clip(out, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8), "RGBA")
        img.save(os.path.join(dst, name + ".webp"), "WEBP", quality=90, method=5)
        print(name, end=" ", flush=True)
    print()

if __name__ == "__main__":
    main(*sys.argv[1:3])
