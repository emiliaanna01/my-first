"""Cut the speaker out once and save reusable layers for the shot director.

Usage: python tools/matte_layers.py CUT.mp4 OUTDIR [--downsample 0.25]
Writes OUTDIR/fg_warm.mp4 (relit speaker), OUTDIR/fg_flat.mp4 (original colors) and OUTDIR/alpha.mp4 (matte as gray).
"""
import argparse, os, subprocess, sys
import cv2, numpy as np, onnxruntime as ort

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import MODEL, warm_curve


def writer(path, w, h, fps, crf):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps),
                             "-i", "-", "-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv444p", path],
                            stdin=subprocess.PIPE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("outdir"); ap.add_argument("--downsample", type=float, default=0.25)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    cap = cv2.VideoCapture(a.inp)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ow, of, oa = (writer(os.path.join(a.outdir, n), w, h, fps, c) for n, c in
                  (("fg_warm.mp4", 14), ("fg_flat.mp4", 14), ("alpha.mp4", 10)))
    lut = warm_curve().astype(np.uint8).reshape(256, 1, 3)
    rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    ds = np.array([a.downsample], np.float32)
    ok, frame = cap.read()
    while ok:
        src = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255
        fgr, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                         "downsample_ratio": ds})
        fg = cv2.cvtColor((fgr[0].transpose(1, 2, 0) * 255).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        warm = cv2.LUT(fg, lut)
        hsv = cv2.cvtColor(warm, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] *= 1.18
        warm = ((cv2.cvtColor(hsv.clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) - 128) * 1.06 + 128)
        ow.stdin.write(warm.clip(0, 255).astype(np.uint8).tobytes())
        of.stdin.write(fg.tobytes())
        al = (cv2.GaussianBlur(pha[0, 0], (0, 0), 1.2) * 255).clip(0, 255).astype(np.uint8)
        oa.stdin.write(cv2.cvtColor(al, cv2.COLOR_GRAY2BGR).tobytes())
        ok, frame = cap.read()
    for p in (ow, of, oa):
        p.stdin.close(); p.wait()


if __name__ == "__main__":
    main()
