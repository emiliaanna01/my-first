"""Replace the background of a talking-head video using RobustVideoMatting (ONNX, CPU).

Usage: python tools/matte.py IN.mp4 BACKGROUND.(jpg|png|mp4) OUT.mp4 [--downsample 0.25] [--alpha-out ALPHA.mp4]
Audio from IN is copied to OUT.
"""
import argparse, os, subprocess
import cv2, numpy as np, onnxruntime as ort

MODEL = os.path.expanduser("~/.cache/video-models/rvm_mobilenetv3_fp32.onnx")


def bg_frames(path, w, h):
    if path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        img = cover(cv2.imread(path), w, h)
        while True:
            yield img
    while True:
        cap = cv2.VideoCapture(path)
        ok, f = cap.read()
        while ok:
            yield cover(f, w, h)
            ok, f = cap.read()


def cover(img, w, h):
    s = max(w / img.shape[1], h / img.shape[0])
    img = cv2.resize(img, (round(img.shape[1] * s), round(img.shape[0] * s)), interpolation=cv2.INTER_AREA)
    y, x = (img.shape[0] - h) // 2, (img.shape[1] - w) // 2
    return img[y:y + h, x:x + w]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("bg"); ap.add_argument("out")
    ap.add_argument("--downsample", type=float, default=0.25, help="0.25 for 1080p, 0.4 for 720p")
    ap.add_argument("--alpha-out")
    a = ap.parse_args()

    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    cap = cv2.VideoCapture(a.inp)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def enc(path):
        return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                                 "-r", str(fps), "-i", "-", "-i", a.inp, "-map", "0:v", "-map", "1:a?", "-c:a", "copy",
                                 "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", path],
                                stdin=subprocess.PIPE)
    out = enc(a.out)
    aout = enc(a.alpha_out) if a.alpha_out else None

    rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    ds = np.array([a.downsample], np.float32)
    bgs = bg_frames(a.bg, w, h)
    ok, frame = cap.read()
    while ok:
        src = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255
        fgr, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                         "downsample_ratio": ds})
        alpha = pha[0, 0][..., None]
        fg = cv2.cvtColor((fgr[0].transpose(1, 2, 0) * 255).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        comp = (fg * alpha + next(bgs) * (1 - alpha)).astype(np.uint8)
        out.stdin.write(comp.tobytes())
        if aout:
            aout.stdin.write(cv2.cvtColor((alpha * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR).tobytes())
        ok, frame = cap.read()
    for p in filter(None, [out, aout]):
        p.stdin.close(); p.wait()


if __name__ == "__main__":
    main()
