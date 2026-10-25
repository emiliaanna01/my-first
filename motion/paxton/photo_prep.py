#!/usr/bin/env python3
"""Prepare the generated scene images for the photographic version of the reel.

For each scene: pick the source image, crop card borders, grade it into one archival
world (warm, slightly faded, restrained saturation), enlarge to 1200x2134 with sharpening,
and for scenes with people/objects cut the subject out (rembg) and fill the background
behind it (OpenCV inpaint) so parallax never reveals a duplicate.

usage: python3 motion/paxton/photo_prep.py <out_dir> [chatgpt]
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
import cv2
from rembg import remove, new_session

HERE = os.path.dirname(os.path.abspath(__file__))
G, C = os.path.join(HERE, "images/gemini"), os.path.join(HERE, "images/chatgpt")
W, H = 1200, 2134

# key: (file, crop fraction (l, t, r, b), saturation, cutout model or None)
SCENES = {
    "girl":      (f"{G}/01.webp", (0, 0, 0, 0), .78, "u2net_human_seg"),
    "bloom":     (f"{C}/02.webp", (0, 0, 0, 0), .55, None),
    "portrait":  (f"{G}/03.webp", (.02, .02, .02, .02), .8, "u2net_human_seg"),
    "tank":      (f"{G}/04.webp", (.02, .02, .02, .02), .8, "u2net_human_seg"),
    "underside": (f"{C}/05.webp", (0, 0, 0, 0), .55, None),
    "park":      (f"{G}/06.webp", (.03, .03, .03, .03), .8, None),
    "designs":   (f"{C}/07.webp", (0, 0, 0, 0), .55, None),
    "boardroom": (f"{G}/08.webp", (.02, .02, .02, .02), .82, "u2net_human_seg"),
    "sketch":    (f"{G}/09.webp", (0, 0, 0, 0), .85, None),
    "build":     (f"{G}/10.webp", (.02, .02, .02, .02), .8, None),
    "sappers":   (f"{G}/11.webp", (.02, .02, .02, .02), .78, None),
    "opening":   (f"{G}/12.webp", (.035, .045, .035, .025), .62, None),
    "towers":    (f"{G}/13.png", (0, 0, 0, 0), .9, None),
    "london":    (f"{G}/14.png", (.05, .04, .05, .04), .9, None),
}

def grade(img, sat):
    a = np.asarray(img.convert("RGB")).astype(float) / 255
    L = a @ [.299, .587, .114]
    a = L[..., None] + (a - L[..., None]) * sat                 # restrain saturation
    a = a * [1.03, 1.0, .93]                                     # warm, aged
    a = .055 + a * .9                                            # lifted blacks, softened whites
    a = np.clip(a, 0, 1) ** 1.04
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def crop(img, f):
    w, h = img.size; l, t, r, b = f
    img = img.crop((int(w * l), int(h * t), int(w * (1 - r)), int(h * (1 - b))))
    # cover-crop to 9:16
    w, h = img.size; tw = min(w, int(h * 9 / 16)); th = min(h, int(w * 16 / 9))
    return img.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th))

def enlarge(img):
    img = img.resize((W, H), Image.LANCZOS)
    return img.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))

# all-ChatGPT set: same scenes, ChatGPT files, a little more desaturation (they are glossier)
SCENES_CHATGPT = {
    "girl":      (f"{C}/01.webp", (0, 0, 0, 0), .5, "u2net_human_seg"),
    "bloom":     (f"{C}/02.webp", (0, 0, 0, 0), .55, None),
    "portrait":  (f"{C}/03.webp", (0, 0, 0, 0), .55, "u2net_human_seg"),
    "tank":      (f"{C}/04.webp", (0, 0, 0, 0), .5, "u2net_human_seg"),
    "underside": (f"{C}/05.webp", (0, 0, 0, 0), .55, None),
    "park":      (f"{C}/06.webp", (0, 0, 0, 0), .5, None),
    "designs":   (f"{C}/07.webp", (0, 0, 0, 0), .55, None),
    "boardroom": (f"{C}/08.webp", (0, 0, 0, 0), .55, "u2net_human_seg"),
    "sketch":    (f"{C}/09.webp", (0, 0, 0, 0), .6, None),
    "build":     (f"{C}/10.webp", (0, 0, 0, 0), .5, None),
    "sappers":   (f"{C}/11.webp", (0, 0, 0, 0), .5, None),
    "opening":   (f"{C}/12.webp", (0, 0, 0, 0), .5, None),
    "towers":    (f"{C}/13.webp", (0, 0, 0, 0), .6, None),
    "london":    (f"{C}/14.webp", (0, 0, 0, 0), .7, None),
}

def main(out, which="gemini"):
    global SCENES
    if which == "chatgpt":
        SCENES = SCENES_CHATGPT
    os.makedirs(out, exist_ok=True)
    sessions = {}
    for key, (src, cf, sat, model) in SCENES.items():
        img = enlarge(grade(crop(Image.open(src), cf), sat))
        if model:
            sess = sessions.setdefault(model, new_session(model))
            cut = remove(img, session=sess, post_process_mask=True)
            alpha = np.asarray(cut)[..., 3]
            mask = cv2.dilate((alpha > 40).astype(np.uint8) * 255, np.ones((15, 15), np.uint8))
            small = cv2.resize(np.asarray(img), (W // 3, H // 3)); msmall = cv2.resize(mask, (W // 3, H // 3))
            filled = cv2.inpaint(small, msmall, 9, cv2.INPAINT_TELEA)
            filled = cv2.GaussianBlur(cv2.resize(filled, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 3)
            bg = np.asarray(img).copy(); m = (mask > 0)[..., None]
            bg = np.where(m, filled, bg)
            Image.fromarray(bg).save(f"{out}/{key}_bg.webp", quality=90)
            a = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(.8))
            fg = img.convert("RGBA"); fg.putalpha(a); fg.save(f"{out}/{key}_fg.webp", quality=92)
            print(key, "bg+fg", f"{(alpha > 40).mean() * 100:.0f}% subject", flush=True)
        else:
            img.save(f"{out}/{key}_bg.webp", quality=90)
            print(key, "bg", flush=True)

if __name__ == "__main__":
    main(*sys.argv[1:3])
