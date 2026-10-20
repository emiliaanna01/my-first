"""Cut the speaker out of a video, relight them warm and place them in a new room.

Usage: python tools/compose.py CUT.mp4 BG.mp4 OUT.mp4 [--zoom "t0-t1:z,..."] [--downsample 0.25]
  - RobustVideoMatting (ONNX) alpha, recurrent so edges stay stable frame to frame
  - warm relight of the speaker (amber key, lifted shadows), light wrap from the background
  - window-blind light stripes drifting across the whole shot, vignette, light grain
  - optional punch-in zooms anchored at the eyes: "1.8-3.4:1.06" eases in/out over 6 frames
Audio is copied from CUT.
"""
import argparse, os, subprocess
import cv2, numpy as np, onnxruntime as ort

MODEL = os.path.expanduser("~/.cache/video-models/rvm_mobilenetv3_fp32.onnx")


def warm_curve():
    x = np.arange(256, dtype=np.float32) / 255
    lift = lambda v, g, gain, off: np.clip(off + gain * v ** g, 0, 1)
    # BGR: pull blue down, push red/green up a little, gentle S-curve on luma
    return np.stack([lift(x, 1.12, 0.86, 0.02), lift(x, 1.0, 0.98, 0.015), lift(x, 0.9, 1.06, 0.02)], 1) * 255


def blind_stripes(w, h, t):
    s = np.zeros((h * 2, w * 2), np.float32)
    off = int(18 * t) % 140
    for y in range(-140, h * 2, 140):
        cv2.rectangle(s, (0, y + off), (w * 2, y + off + 64), 1.0, -1)
    M = cv2.getRotationMatrix2D((w, h), -20, 1.0)
    s = cv2.warpAffine(s, M, (w * 2, h * 2))[h // 2:h // 2 + h, w // 2:w // 2 + w]
    return cv2.GaussianBlur(s, (0, 0), 18)


def zoom_at(t, zooms):
    z = 1.0
    for t0, t1, zz in zooms:
        ramp = 0.2
        if t0 - ramp <= t <= t1 + ramp:
            k = min(1, (t - t0 + ramp) / ramp, (t1 + ramp - t) / ramp)
            k = k * k * (3 - 2 * k)
            z = max(z, 1 + (zz - 1) * k)
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("bg"); ap.add_argument("out")
    ap.add_argument("--zoom", default="")
    ap.add_argument("--anchor-y", type=int, default=820, help="zoom anchor (eye line) in px")
    ap.add_argument("--downsample", type=float, default=0.25)
    a = ap.parse_args()
    zooms = [(float(r.split(":")[0].split("-")[0]), float(r.split(":")[0].split("-")[1]), float(r.split(":")[1]))
             for r in a.zoom.split(",") if r]

    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    cap, bgc = cv2.VideoCapture(a.inp), cv2.VideoCapture(a.bg)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps),
                            "-i", "-", "-i", a.inp, "-map", "0:v", "-map", "1:a?", "-c:a", "copy", "-c:v", "libx264",
                            "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    lut = warm_curve().astype(np.uint8)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vignette = (1 - 0.45 * (((xx - w / 2) / (w * 0.75)) ** 2 + ((yy - h * 0.45) / (h * 0.7)) ** 2)).clip(0.45, 1)[..., None]
    rng = np.random.default_rng(1)
    rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    ds = np.array([a.downsample], np.float32)
    i = 0
    ok, frame = cap.read()
    while ok:
        t = i / fps
        okb, bg = bgc.read()
        if not okb:
            bgc.set(cv2.CAP_PROP_POS_FRAMES, 0); _, bg = bgc.read()
        src = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255
        fgr, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                         "downsample_ratio": ds})
        alpha = cv2.GaussianBlur(pha[0, 0], (0, 0), 1.2)[..., None]
        fg = cv2.cvtColor((fgr[0].transpose(1, 2, 0) * 255).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        fg = cv2.LUT(fg, lut.reshape(256, 1, 3))  # warm relight
        hsv = cv2.cvtColor(fg, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] *= 1.18  # skin back to life after the upscale
        fg = cv2.cvtColor(hsv.clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        fg = (fg - 128) * 1.06 + 128
        bgf = bg.astype(np.float32)
        # light wrap: background glow bleeding onto the subject's edges
        edge = np.clip(cv2.GaussianBlur(1 - alpha[..., 0], (0, 0), 14) * alpha[..., 0], 0, 1)[..., None]
        fg = fg * (1 - 0.35 * edge) + cv2.GaussianBlur(bgf, (0, 0), 20) * 0.35 * edge
        comp = fg * alpha + bgf * (1 - alpha)
        # blind light across everything (stronger on the wall than on the speaker)
        st = blind_stripes(w, h, t)[..., None]
        comp = comp * (1 - 0.18 * st * (1 - 0.5 * alpha)) + np.array([30, 80, 140], np.float32) * 0.25 * st * alpha
        comp = comp * vignette + rng.normal(0, 3.0, (h, w, 1)).astype(np.float32)
        comp = np.clip(comp, 0, 255).astype(np.uint8)
        z = zoom_at(t, zooms)
        if z > 1.001:
            M = np.float32([[z, 0, (1 - z) * w / 2], [0, z, (1 - z) * a.anchor_y]])
            comp = cv2.warpAffine(comp, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        out.stdin.write(comp.tobytes())
        i += 1
        ok, frame = cap.read()
    out.stdin.close(); out.wait()


if __name__ == "__main__":
    main()
