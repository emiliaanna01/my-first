"""Background "sets" for the shot director: four warm rooms, rendered as large out-of-focus plates.

Usage: python tools/sets.py OUTDIR
Writes OUTDIR/<set>_far.png (room, depth-of-field blurred), OUTDIR/<set>_bokeh.png (additive highlights) for
sets lamp, desk, crt, window, plus OUTDIR/desk_fg.png (RGBA foreground desk for wide shots). Plates are 1.5x the frame
so the virtual camera can pan, push and pull with parallax.
"""
import os, sys
import cv2, numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cozy_bg import soft_blob, bokeh_disc, hue_safe_clip

PW, PH = 1620, 2880


def wall(top, glow, gx, gy):
    yy = np.linspace(0, 1, PH)[:, None, None]
    xx = np.linspace(0, 1, PW)[None, :, None]
    base = np.array(top, np.float32) + np.array(glow, np.float32) * np.exp(-((xx - gx) ** 2 / 0.18 + (yy - gy) ** 2 / 0.25))
    return np.broadcast_to(base, (PH, PW, 3)).copy()


def shelves(img, rng, x0, x1, ys, wood=(8, 14, 24)):
    for y in ys:
        Y = int(y * PH)
        cv2.rectangle(img, (int(x0 * PW), Y), (int(x1 * PW), Y + 30), wood, -1)
        for _ in range(rng.integers(4, 8)):
            bx = int((x0 + (x1 - x0 - 0.04) * rng.random()) * PW); bh = int(rng.integers(70, 180)); bw = int(rng.integers(20, 55))
            col = rng.choice([(30, 50, 110), (40, 70, 60), (25, 35, 70), (60, 90, 140), (90, 110, 150)])
            cv2.rectangle(img, (bx, Y - bh), (bx + bw, Y), tuple(int(c) for c in col), -1)


def plant(img, cx, cy, s=1.0):
    for ang in (-60, -35, -10, 15, 40, 65, -80, 85):
        cv2.ellipse(img, (int(cx + 2.4 * ang * s), int(cy - 200 * s + abs(ang) * 1.6 * s)), (int(42 * s), int(170 * s)), ang, 0, 360, (12, 26, 18), -1)
    cv2.rectangle(img, (int(cx - 70 * s), int(cy)), (int(cx + 70 * s), int(cy + 130 * s)), (20, 40, 72), -1)


def blinds(img, cx, cy, strength, angle=-18, gap=0.075, color=(40, 100, 170), spread=(0.05, 0.09)):
    s = np.zeros((PH, PW), np.float32)
    for i in range(14):
        y = int((0.0 + i * gap) * PH)
        cv2.rectangle(s, (0, y), (PW, y + 60), 1.0, -1)
    s = cv2.warpAffine(s, cv2.getRotationMatrix2D((PW * 0.5, PH * 0.4), angle, 1.0), (PW, PH))
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
    mask = np.exp(-(((xx / PW - cx) ** 2) / spread[0] + ((yy / PH - cy) ** 2) / spread[1]))
    img += (cv2.GaussianBlur(s, (0, 0), 8) * mask)[..., None] * np.array(color, np.float32) * strength


def bokeh(rng, n, colors, ymax=0.8):
    img = np.zeros((PH, PW, 3), np.float32)
    for _ in range(n):
        r = float(rng.uniform(22, 70))
        bokeh_disc(img, rng.uniform(0, PW), rng.uniform(0, PH * ymax), r, rng.choice(colors), float(rng.uniform(0.08, 0.24)))
    return cv2.GaussianBlur(img, (0, 0), 2)


def set_lamp(rng):
    img = wall((14, 26, 46), (20, 45, 85), 0.55, 0.35)
    shelves(img, rng, 0.04, 0.38, (0.22, 0.42, 0.62))
    cv2.rectangle(img, (int(0.70 * PW), int(0.70 * PH)), (PW, PH), (10, 18, 32), -1)
    plant(img, 0.88 * PW, 0.60 * PH)
    soft_blob(img, 0.80 * PW, 0.30 * PH, 230, (40, 110, 230), 0.55)
    soft_blob(img, 0.80 * PW, 0.30 * PH, 70, (90, 160, 240), 0.35)
    soft_blob(img, 0.15 * PW, 0.78 * PH, 190, (40, 120, 240), 0.5)
    blinds(img, 0.45, 0.40, 1.0)
    return img, [(80, 170, 255), (110, 200, 255), (60, 130, 240)]


def set_desk(rng):
    img = wall((16, 22, 34), (28, 52, 88), 0.30, 0.30)  # dark warm wall, teal monitor accent
    cv2.rectangle(img, (int(0.52 * PW), int(0.30 * PH)), (int(0.95 * PW), int(0.50 * PH)), (110, 95, 60), -1)  # monitor glow
    soft_blob(img, 0.74 * PW, 0.40 * PH, 260, (120, 95, 45), 0.30)  # teal spill
    shelves(img, rng, 0.05, 0.42, (0.18, 0.34))
    soft_blob(img, 0.18 * PW, 0.55 * PH, 220, (40, 120, 245), 0.75)  # warm desk lamp
    soft_blob(img, 0.18 * PW, 0.55 * PH, 60, (90, 170, 250), 0.4)
    plant(img, 0.10 * PW, 0.80 * PH, 0.9)
    cv2.rectangle(img, (0, int(0.82 * PH)), (PW, PH), (12, 16, 24), -1)
    blinds(img, 0.35, 0.25, 0.6, angle=-12)
    return img, [(90, 170, 255), (200, 170, 90), (70, 140, 240)]


def set_crt(rng):
    img = wall((18, 18, 40), (25, 35, 95), 0.50, 0.45)  # red-amber
    tv = (int(0.12 * PW), int(0.48 * PH), int(0.48 * PW), int(0.70 * PH))
    cv2.rectangle(img, (tv[0] - 30, tv[1] - 30), (tv[2] + 30, tv[3] + 30), (12, 14, 20), -1)
    noise = rng.uniform(60, 160, ((tv[3] - tv[1]) // 6, (tv[2] - tv[0]) // 6)).astype(np.float32)
    noise = cv2.resize(noise, (tv[2] - tv[0], tv[3] - tv[1]), interpolation=cv2.INTER_NEAREST)
    img[tv[1]:tv[3], tv[0]:tv[2]] = noise[..., None] * np.array([0.9, 0.75, 0.6], np.float32)
    soft_blob(img, 0.30 * PW, 0.59 * PH, 260, (110, 90, 70), 0.35)
    cv2.rectangle(img, (0, int(0.72 * PH)), (int(0.62 * PW), int(0.74 * PH)), (10, 20, 34), -1)  # TV console
    soft_blob(img, 0.82 * PW, 0.22 * PH, 160, (60, 60, 230), 0.55)  # red-orange sign glow
    soft_blob(img, 0.70 * PW, 0.80 * PH, 200, (30, 90, 200), 0.45)
    cv2.circle(img, (int(0.78 * PW), int(0.88 * PH)), 230, (20, 24, 90), -1)  # bean bag
    shelves(img, rng, 0.60, 0.96, (0.40,))
    return img, [(80, 120, 255), (60, 90, 230), (120, 180, 255)]


def set_window(rng):
    img = wall((24, 40, 64), (40, 90, 150), 0.40, 0.30)  # bright golden hour
    win = (int(0.20 * PW), int(0.08 * PH), int(0.75 * PW), int(0.48 * PH))
    cv2.rectangle(img, win[:2], win[2:], (120, 200, 250), -1)
    for i in range(win[1], win[3], 46):
        cv2.rectangle(img, (win[0], i), (win[2], i + 22), (40, 80, 130), -1)  # blinds slats
    plant(img, 0.85 * PW, 0.62 * PH, 1.2)
    cv2.rectangle(img, (0, int(0.68 * PH)), (int(0.55 * PW), PH), (14, 26, 44), -1)  # couch
    soft_blob(img, 0.48 * PW, 0.28 * PH, 420, (40, 110, 200), 0.35)
    blinds(img, 0.50, 0.65, 1.1, angle=-24, spread=(0.08, 0.06))
    return img, [(120, 200, 255), (150, 220, 255)]


def desk_fg():
    """Foreground desk with a laptop and a mug: hides where the cut-out body meets the source frame edge in wide shots."""
    w, h = 1080, 700
    rgb = np.zeros((h, w, 3), np.float32); a = np.zeros((h, w), np.float32)
    top = 160
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rng = np.random.default_rng(4)
    grain = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), sigmaX=40, sigmaY=1.5)
    wood = np.array([22, 44, 78], np.float32) * (1 + 0.25 * grain[..., None] / (np.abs(grain).max() + 1e-6))
    body = (yy >= top)
    rgb[body] = wood[body] * (1.0 - 0.55 * ((yy[body] - top) / (h - top)))[..., None]
    a[body] = 1
    edge = np.exp(-((yy - top) ** 2) / (2 * 7 ** 2))[..., None] * np.array([60, 120, 190], np.float32)
    rgb += edge * (xx / w * 0.6 + 0.4)[..., None]                        # lamp-lit front edge
    # laptop (seen from behind) with a soft glowing logo
    pts = np.array([[700, top + 4], [1010, top + 4], [985, top - 170], [725, top - 170]], np.int32)
    cv2.fillPoly(rgb, [pts], (46, 46, 52)); cv2.fillPoly(a, [pts], 1)
    cv2.rectangle(rgb, (680, top - 8), (1030, top + 14), (70, 72, 80), -1); cv2.rectangle(a, (680, top - 8), (1030, top + 14), 1, -1)
    glow = np.zeros((h, w), np.float32); cv2.circle(glow, (855, top - 90), 15, 1, -1)
    rgb += cv2.GaussianBlur(glow, (0, 0), 10)[..., None] * np.array([190, 210, 230], np.float32)
    # mug
    cv2.rectangle(rgb, (70, top - 95), (150, top + 6), (150, 170, 195), -1); cv2.rectangle(a, (70, top - 95), (150, top + 6), 1, -1)
    cv2.ellipse(rgb, (158, top - 45), (26, 30), 0, -90, 90, (150, 170, 195), 10); cv2.ellipse(a, (158, top - 45), (26, 30), 0, -90, 90, 1, 10)
    rgb[..., :] = cv2.GaussianBlur(rgb, (0, 0), 1.6); a = cv2.GaussianBlur(a, (0, 0), 1.6)
    return np.dstack([rgb, a * 255])


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for i, (name, fn) in enumerate((("lamp", set_lamp), ("desk", set_desk), ("crt", set_crt), ("window", set_window))):
        rng = np.random.default_rng(11 + i)
        far, cols = fn(rng)
        far = hue_safe_clip(cv2.GaussianBlur(far, (0, 0), 16))
        cv2.imwrite(os.path.join(out, f"{name}_far.png"), far.clip(0, 255).astype(np.uint8))
        cv2.imwrite(os.path.join(out, f"{name}_bokeh.png"), bokeh(rng, 20, cols).clip(0, 255).astype(np.uint8))
    cv2.imwrite(os.path.join(out, "desk_fg.png"), desk_fg().clip(0, 255).astype(np.uint8))


if __name__ == "__main__":
    main()
