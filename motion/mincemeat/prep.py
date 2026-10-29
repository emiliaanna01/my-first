#!/usr/bin/env python3
"""Grade every still into one golden archival world, crop the photo-print borders, paint out AI glitches,
cut out the subjects, and build the matching 3D LUT for the clips.
usage: python3 motion/mincemeat/prep.py"""
import os
import numpy as np
from PIL import Image, ImageFilter
import cv2
from rembg import remove, new_session

HERE = os.path.dirname(os.path.abspath(__file__))
IMG, OUT = os.path.join(HERE, "images"), os.path.join(HERE, "layers")
# black -> olive-brown -> tobacco -> antique gold -> warm beige
STOPS = np.array([[0, 11, 10, 7], [.28, 58, 52, 36], [.55, 122, 90, 46], [.8, 217, 180, 90], [1, 235, 221, 184]], float)

def ramp(L):
    out = np.zeros(L.shape + (3,))
    for c in range(3): out[..., c] = np.interp(L, STOPS[:, 0], STOPS[:, c + 1])
    return out

def grade(a, mix=.86):
    """a: float RGB 0..255 -> graded float RGB 0..255"""
    L = (a @ [.299, .587, .114]) / 255
    L = np.clip(L, 0, 1); L = L * L * (3 - 2 * L) * .35 + L * .65          # gentle S-curve
    g = ramp(L)
    lum = a.mean(-1, keepdims=True)
    return np.clip(g * mix + (lum * .15 + a * .85) * (1 - mix) * np.array([1.04, 1, .9]), 0, 255)

def load(name, crop=(0, 0, 0, 0)):
    im = Image.open(os.path.join(IMG, name)).convert("RGB"); w, h = im.size; l, t, r, b = crop
    return im.crop((int(w * l), int(h * t), int(w * (1 - r)), int(h * (1 - b))))

def save_plate(key, im, size=(1188, 2112)):
    a = grade(np.asarray(im).astype(float)); im = Image.fromarray(a.astype(np.uint8))
    w, h = im.size; k = max(size[0] / w, size[1] / h); im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
    x, y = (im.width - size[0]) // 2, (im.height - size[1]) // 2; im = im.crop((x, y, x + size[0], y + size[1]))
    im = im.filter(ImageFilter.UnsharpMask(1.6, 60, 2)); im.save(f"{OUT}/{key}.webp", quality=90); print(key, im.size, flush=True)

BORDER = (.055, .035, .055, .035)
PLATES = {"P1": ("P1.jpg", (.02, .015, .02, .015)), "B1": ("B1.jpg", BORDER), "B2": ("B2.jpg", BORDER), "B3": ("B3.jpg", BORDER),
          "B4": ("B4.jpg", BORDER), "B5": ("B5.jpg", BORDER), "B6": ("B6.jpg", BORDER), "B7": ("B7.jpg", BORDER),
          "B8": ("B8.jpg", (0, 0, 0, 0)), "B9": ("B9.jpg", BORDER), "B10": ("B10.jpg", (.02, .015, .02, .015)),
          "B11": ("B11.jpg", (.02, .015, .02, .015)), "B12": ("B12.jpg", BORDER), "D1desk": ("D1-desk.jpg", (0, 0, 0, 0))}

def clean_b1(im):
    a = np.asarray(im).copy(); h, w = a.shape[:2]
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY); reg = np.zeros_like(g); reg[: int(h * .24), : int(w * .8)] = 1
    blur = cv2.medianBlur(g, 31); m = ((np.abs(g.astype(int) - blur.astype(int)) > 10) & (reg > 0)).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    return Image.fromarray(cv2.inpaint(a, m, 7, cv2.INPAINT_TELEA))

def cutout(key, name, model, sess, crop=(0, 0, 0, 0), maxw=1400):
    im = load(name, crop)
    cut = remove(im, session=sess.setdefault(model, new_session(model)), post_process_mask=True)
    rgb = Image.fromarray(grade(np.asarray(cut.convert("RGB")).astype(float), .8).astype(np.uint8))
    a = cut.split()[3].filter(ImageFilter.GaussianBlur(.7)); rgb.putalpha(a)
    rgb = rgb.crop(rgb.getbbox())
    if rgb.width > maxw: rgb = rgb.resize((maxw, round(rgb.height * maxw / rgb.width)), Image.LANCZOS)
    rgb.save(f"{OUT}/{key}.webp", quality=92); print(key, rgb.size, flush=True)

def lut(path, n=33):
    g = np.linspace(0, 255, n); r, gg, b = np.meshgrid(g, g, g, indexing="ij")
    a = np.stack([r, gg, b], -1).reshape(-1, 3); o = grade(a) / 255
    o = o.reshape(n, n, n, 3).transpose(2, 1, 0, 3).reshape(-1, 3)   # .cube order: red fastest
    with open(path, "w") as f:
        f.write(f"LUT_3D_SIZE {n}\n"); f.writelines(f"{x:.5f} {y:.5f} {z:.5f}\n" for x, y, z in o)

def main():
    os.makedirs(OUT, exist_ok=True)
    for key, (name, crop) in PLATES.items():
        im = load(name, crop)
        if key == "B1": im = clean_b1(im)
        save_plate(key, im)
    # P3 / P4 are used as photo prints: graded, border kept as the print's own edge
    for key, name, crop in (("P3", "P3.jpg", BORDER), ("P4print", "P4.jpg", (0, 0, 0, 0))):
        im = load(name, crop); a = grade(np.asarray(im).astype(float)); Image.fromarray(a.astype(np.uint8)).save(f"{OUT}/{key}.webp", quality=90); print(key, flush=True)
    sess = {}
    cutout("P2cut", "P2.webp", "u2net_human_seg", sess, (.03, .02, .03, .0))
    cutout("K1sub", "K1.webp", "isnet-general-use", sess, (.02, .04, .02, .04))
    cutout("K2tank", "K2.webp", "isnet-general-use", sess, (.02, .04, .02, .04))
    cutout("K3case", "K3.webp", "isnet-general-use", sess)
    cutout("D1paper", "D1.webp", "isnet-general-use", sess)
    cutout("D3tickets", "D3.webp", "isnet-general-use", sess)
    cutout("P4cut", "P4.jpg", "isnet-general-use", sess)
    lut(os.path.join(HERE, "grade.cube")); print("grade.cube")

if __name__ == "__main__":
    main()
