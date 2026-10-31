#!/usr/bin/env python3
"""Change the S13 time tag from '2:30 PM' to '2:15 PM' (AP: Hoffa called his wife about 2:15 p.m.).
Tracks the tag with template matching and repaints the two digits on its paper, frame by frame.
usage: python3 motion/lustig/fix_s13.py"""
import os, subprocess
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "video/S13.mp4"), os.path.join(HERE, "video/S13_fixed.mp4")
FONT = "/mnt/skills/examples/canvas-design/canvas-fonts/BigShoulders-Bold.ttf"

cap = cv2.VideoCapture(SRC); fps = cap.get(cv2.CAP_PROP_FPS); frames = []
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
ref = frames[int(4.5 * fps)]; g = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
txt = g[565:645, 505:625]; ink = txt < 110; ys, xs = np.where(ink); y0, y1 = ys.min() + 565, ys.max() + 565
TX, TY, TW, TH = 505, y0 - 4, 120, y1 - y0 + 8                 # template = the whole "2:30 PM" line
tmpl = g[TY:TY + TH, TX:TX + TW]
DX0, DX1 = 534, 571                                             # the digits "30" inside the frame
inkcol = ref[y0:y1, 536:568][ink[y0 - 565:y1 - 565, 31:63]].mean(0) if False else np.percentile(ref[y0:y1, 536:568].reshape(-1, 3), 3, axis=0)
# patch: paper sampled right of "M", digits "15" drawn to the same cap height
paper = ref[TY:TY + TH, 622:648]
patch = np.concatenate([paper] * 3, 1)[:, :DX1 - DX0].copy()
patch = cv2.GaussianBlur(patch, (0, 0), 1.2)
pil = Image.fromarray(cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil)
cap_h = y1 - y0; size = int(cap_h * 1.24); font = ImageFont.truetype(FONT, size)
bx = d.textbbox((0, 0), "15", font=font); tw = bx[2] - bx[0]
d.text(((DX1 - DX0 - tw) / 2 - bx[0], 4 - bx[1]), "15", font=font, fill=tuple(int(v) for v in inkcol[::-1]))
patch = cv2.GaussianBlur(cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR), (0, 0), .55)
mask = np.ones(patch.shape[:2], np.float32); mask[:, :2] = mask[:, -2:] = .5

h, w = ref.shape[:2]
vw = cv2.VideoWriter(OUT + ".tmp.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h)); hits = 0
for i, f in enumerate(frames):
    if i / fps > 2.6:
        gg = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        r = cv2.matchTemplate(gg[TY - 60:TY + TH + 60, TX - 120:TX + TW + 60], tmpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(r)
        if score > .6:
            ox, oy = loc[0] - 120, loc[1] - 60; x, y = DX0 + ox, TY + oy
            roi = f[y:y + TH, x:x + DX1 - DX0].astype(np.float32)
            f[y:y + TH, x:x + DX1 - DX0] = (roi * (1 - mask[..., None]) + patch * mask[..., None]).astype(np.uint8); hits += 1
    vw.write(f)
vw.release()
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", OUT + ".tmp.mp4", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", OUT], check=True)
os.remove(OUT + ".tmp.mp4"); print(f"patched {hits} frames of {len(frames)} -> {OUT}")
