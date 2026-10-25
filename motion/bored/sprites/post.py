#!/usr/bin/env python3
"""Turn raw 3D renders into reel cutouts: duotone grade, contrast stretch, film grain, trim.
usage: python3 post.py raw out"""
import glob, os, sys
import numpy as np
from PIL import Image

GRAY = [(0, "#14162e"), (.45, "#7d7f99"), (.8, "#d4d5e2"), (1, "#fafaff")]      # people, furniture, clocks
LAV = [(0, "#1e2366"), (.5, "#8e95e0"), (.82, "#d3d6fb"), (1, "#f6f6ff")]        # props
LAVISH = {"bulb", "bulbLit", "puzzle", "phone", "kettle", "scale0", "scaleT", "lift", "busstop", "shower"}

def hexrgb(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)

def ramp(L, stops):
    out = np.zeros(L.shape + (3,))
    xs = [s[0] for s in stops]; cs = [hexrgb(s[1]) for s in stops]
    for c in range(3):
        out[..., c] = np.interp(L, xs, [col[c] for col in cs])
    return out

def grade(im, name):
    a = np.asarray(im.convert("RGBA")).astype(float)
    rgb, al = a[..., :3], a[..., 3]
    L = (rgb @ [0.299, 0.587, 0.114]) / 255
    m = al > 128
    lo, hi = np.percentile(L[m], 1.5), np.percentile(L[m], 99.2)
    L = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1) ** 1.12
    col = ramp(L, LAV if name in LAVISH else GRAY)
    rng = np.random.default_rng(abs(hash(name)) % 2**32)
    col += rng.normal(0, 7, L.shape)[..., None]
    out = np.dstack([np.clip(col, 0, 255), al]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    bb = img.getbbox(); pad = 24
    img = img.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(img.width, bb[2] + pad), min(img.height, bb[3] + pad)))
    img.thumbnail((900, 900), Image.LANCZOS)
    return img

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
for p in sorted(glob.glob(os.path.join(src, "*.png"))):
    n = os.path.basename(p)[:-4]
    grade(Image.open(p), n).save(os.path.join(dst, n + ".webp"), "WEBP", quality=88, method=6)
    print(n, end=" ")
print()
