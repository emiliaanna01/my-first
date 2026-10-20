"""Procedural warm "cozy room" background: dark wood wall, out-of-focus lamps, bokeh, window-blind light.

Usage: python tools/cozy_bg.py OUT.mp4 --seconds 16 [--seed 7]
Renders 1080x1920 at 30 fps with a slow parallax drift, so it reads as a shallow-depth-of-field room
behind a cut-out speaker.
"""
import argparse, subprocess
import cv2, numpy as np

W, H, FPS = 1080, 1920, 30
PAD = 160  # parallax margin


def soft_blob(canvas, x, y, r, color, strength):
    """Add a gaussian light blob (additive, linear-ish)."""
    h, w = canvas.shape[:2]
    x0, x1, y0, y1 = max(0, int(x - 3 * r)), min(w, int(x + 3 * r)), max(0, int(y - 3 * r)), min(h, int(y + 3 * r))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    g = np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r)))[..., None]
    canvas[y0:y1, x0:x1] += g * np.array(color, np.float32) * strength


def bokeh_disc(canvas, x, y, r, color, strength):
    """Out-of-focus highlight: flat disc with a slightly brighter rim, softened."""
    size = int(r * 2 + 8)
    d = np.zeros((size, size), np.float32)
    c = size // 2
    cv2.circle(d, (c, c), int(r), 1.0, -1, cv2.LINE_AA)
    cv2.circle(d, (c, c), int(r), 1.4, max(1, int(r * 0.12)), cv2.LINE_AA)
    d = cv2.GaussianBlur(d, (0, 0), max(1.0, r * 0.08))
    x0, y0 = int(x) - c, int(y) - c
    h, w = canvas.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    ex, ey = min(size, w - x0), min(size, h - y0)
    if sx0 >= ex or sy0 >= ey:
        return
    canvas[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] += d[sy0:ey, sx0:ex, None] * np.array(color, np.float32) * strength


def far_layer(rng):
    w, h = W + 2 * PAD, H + 2 * PAD
    yy = np.linspace(0, 1, h)[:, None, None]
    xx = np.linspace(0, 1, w)[None, :, None]
    # warm wall: deep brown at the bottom/edges, amber in the upper middle (BGR)
    base = np.array([14, 26, 46], np.float32) + np.array([20, 45, 85], np.float32) * np.exp(-((xx - 0.55) ** 2 / 0.18 + (yy - 0.35) ** 2 / 0.25))
    img = np.broadcast_to(base, (h, w, 3)).copy()
    # shelves and furniture silhouettes (dark, will be blurred out of focus)
    for y in (0.22, 0.42, 0.62):
        cv2.rectangle(img, (int(0.04 * w), int(y * h)), (int(0.36 * w), int(y * h) + 26), (8, 14, 24), -1)
        for k in range(rng.integers(3, 7)):  # books / objects on the shelf
            bx = int((0.05 + 0.29 * rng.random()) * w); bh = int(rng.integers(60, 150)); bw = int(rng.integers(18, 45))
            col = rng.choice([(30, 50, 110), (40, 70, 60), (25, 35, 70), (60, 90, 140)])
            cv2.rectangle(img, (bx, int(y * h) - bh), (bx + bw, int(y * h)), tuple(int(c) for c in col), -1)
    cv2.rectangle(img, (int(0.70 * w), int(0.70 * h)), (w, h), (10, 18, 32), -1)        # sofa
    for ang in (-50, -25, 0, 25, 50, 75, -75):  # plant: leaves fanning out of a pot
        cv2.ellipse(img, (int(0.88 * w + 2.2 * ang), int(0.56 * h - 180 + abs(ang) * 1.5)), (38, 150), ang, 0, 360, (16, 34, 22), -1)
    cv2.rectangle(img, (int(0.84 * w), int(0.62 * h)), (int(0.93 * w), int(0.70 * h)), (20, 40, 70), -1)
    cv2.rectangle(img, (0, int(0.86 * h)), (w, h), (6, 12, 22), -1)                      # floor shadow
    # lamps: big warm glows
    soft_blob(img, 0.80 * w, 0.30 * h, 170, (40, 110, 230), 0.55)
    soft_blob(img, 0.80 * w, 0.30 * h, 50, (90, 160, 240), 0.35)
    soft_blob(img, 0.15 * w, 0.78 * h, 140, (40, 120, 240), 0.6)
    soft_blob(img, 0.48 * w, 0.12 * h, 260, (40, 110, 220), 0.35)
    # window-blind light falling diagonally across the wall
    stripes = np.zeros((h, w), np.float32)
    for i in range(9):
        y = int((0.05 + i * 0.075) * h)
        cv2.rectangle(stripes, (0, y), (w, y + 46), 1.0, -1)
    M = cv2.getRotationMatrix2D((w * 0.5, h * 0.4), -18, 1.0)
    stripes = cv2.warpAffine(stripes, M, (w, h))
    mask = np.exp(-(((xx[..., 0] - 0.45) ** 2) / 0.05 + ((yy[..., 0] - 0.40) ** 2) / 0.09))
    img += (cv2.GaussianBlur(stripes, (0, 0), 7) * mask)[..., None] * np.array([40, 100, 170], np.float32)
    img = cv2.GaussianBlur(img, (0, 0), 14)  # shallow depth of field
    return hue_safe_clip(img)


def hue_safe_clip(img):
    """Scale down over-bright pixels as a whole so lamps stay amber instead of clipping to yellow-green."""
    peak = img.max(axis=2, keepdims=True)
    return img * np.minimum(1.0, 245.0 / np.maximum(peak, 1e-3))


def bokeh_layer(rng):
    w, h = W + 2 * PAD, H + 2 * PAD
    img = np.zeros((h, w, 3), np.float32)
    for _ in range(16):
        r = float(rng.uniform(18, 60))
        col = rng.choice([(80, 170, 255), (110, 200, 255), (60, 130, 240), (150, 220, 255)])
        bokeh_disc(img, rng.uniform(0, w), rng.uniform(0, h * 0.75), r, col, float(rng.uniform(0.08, 0.25)))
    return cv2.GaussianBlur(img, (0, 0), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--seconds", type=float, default=16); ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    far, bok = far_layer(rng), bokeh_layer(rng)
    n = int(a.seconds * FPS) + 1
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        fx, fy = PAD + 40 * np.sin(t * 0.25), PAD + 25 * np.sin(t * 0.18)          # far layer drifts slowly
        bx, by = PAD + 90 * np.sin(t * 0.25 + 0.5), PAD + 50 * np.sin(t * 0.18)   # bokeh drifts more (parallax)
        flicker = 1.0 + 0.03 * np.sin(t * 2.1)
        f = far[int(fy):int(fy) + H, int(fx):int(fx) + W]
        b = bok[int(by):int(by) + H, int(bx):int(bx) + W]
        frame = np.clip(hue_safe_clip(f * flicker + b), 0, 255).astype(np.uint8)
        p.stdin.write(frame.tobytes())
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    main()
