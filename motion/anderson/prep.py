#!/usr/bin/env python3
"""Grade the scene images into one archival look and cut out the studio shots.
usage: python3 motion/anderson/prep.py <out_dir>"""
import os, sys
import numpy as np
from PIL import Image
from rembg import remove, new_session

HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, "images")
PLATES = ["A1", "A2", "A3", "A4", "A5", "A6", "A8", "A10", "A12", "A13", "A14"]
CUTS = ["A4-cut", "A9-cut", "A10-cut"]

def grade(img, sat=.82, warm=(1.03, 1.0, .94), lift=.035):
    a = np.asarray(img.convert("RGB")).astype(float) / 255
    L = a @ [.299, .587, .114]
    a = L[..., None] + (a - L[..., None]) * sat
    a = lift + a * (1 - lift * 1.6) * np.array(warm)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def main(out):
    os.makedirs(out, exist_ok=True)
    for n in PLATES:
        grade(Image.open(f"{IMG}/{n}.jpg")).save(f"{out}/{n}.webp", quality=90); print(n, end=" ", flush=True)
    sess = new_session("isnet-general-use")
    for n in CUTS:
        src = Image.open(f"{IMG}/{n}.jpg")
        cut = remove(src, session=sess, post_process_mask=True)
        g = grade(src).convert("RGBA"); g.putalpha(cut.split()[3])
        g = g.crop(g.getbbox()); g.save(f"{out}/{n}.webp", quality=92); print(n, g.size, end=" ", flush=True)
    print()

if __name__ == "__main__":
    main(sys.argv[1])
