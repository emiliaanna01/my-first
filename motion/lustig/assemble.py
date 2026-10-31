#!/usr/bin/env python3
"""Cut each 6 s scene clip to the length of its voice line and join them.
For clip i (duration d = next line start - this line start), take the source window that shows its animation:
it ends just after the motion settles and is sped up (max 1.25x) when the animation is longer than d.
usage: python3 motion/lustig/assemble.py <vo_dir> <out.mp4>"""
import json, os, subprocess, sys
import cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); TAIL = 2.6     # last clip holds for the ending
SRC = {13: "video/S13_fixed.mp4"}                                 # tag repainted to 2:15 PM
CROP = {12: "crop=710:1262:5:9,"}                                 # thin white edge
MINSTART = {25: .46}                                              # S25 opens on its own last frame for 0.4 s
WEND = {27: 4.7}                                                  # let the FOUND stamp land fully

def motion(path):
    c = cv2.VideoCapture(path); prev = None; d = []
    while True:
        ok, f = c.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f, (90, 160)), cv2.COLOR_BGR2GRAY).astype(float)
        if prev is not None: d.append(np.abs(g - prev).mean())
        prev = g
    d = np.convolve(np.array(d), np.ones(5) / 5, "same"); fps = 24
    act = np.where(d > max(.8, np.percentile(d, 60) * .6))[0]; big = np.where(d > d.max() * .35)[0]
    return act[0] / fps, big[-1] / fps, act[-1] / fps

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json")); n = len(meta)
    starts = [0] + [m["t"] for m in meta[1:]]
    durs = [starts[i + 1] - starts[i] for i in range(n - 1)] + [meta[-1]["dur"] + TAIL + meta[-1]["t"] - starts[-1]]
    os.makedirs(os.path.join(HERE, "clips"), exist_ok=True); plan = []
    for i in range(1, n + 1):
        src = os.path.join(HERE, SRC.get(i, f"video/S{i:02d}.mp4")); d = durs[i - 1]
        first, settle, last = motion(os.path.join(HERE, f"video/S{i:02d}.mp4"))
        we = WEND.get(i) or min(6.0, max(settle + 1.0, min(last + .6, settle + 1.8)))   # end on a held, readable frame
        ws = max(MINSTART.get(i, 0), first - .1)
        sp = (we - ws) / d
        if sp > 1.25: ws = we - 1.25 * d; sp = 1.25          # never faster than 1.25x: the viewer must catch each element
        if sp < 1.0:                                              # clip longer than its animation: hold real time, start a bit earlier
            ws = max(MINSTART.get(i, 0), we - d); sp = max(1.0, (we - ws) / d)
            if we - ws < d: we = min(6.0, ws + d); sp = 1.0
        plan.append((i, round(ws, 2), round(we, 2), round(sp, 2), round(d, 2)))
        vf = (f"{CROP.get(i, '')}trim={ws:.3f}:{we:.3f},setpts=(PTS-STARTPTS)/{sp:.4f},scale=1080:1920:flags=lanczos,unsharp=5:5:0.5,"
              f"fps=30,tpad=stop_mode=clone:stop_duration=3,trim=duration={d:.4f},setpts=PTS-STARTPTS,format=yuv420p")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-an", "-vf", vf, "-c:v", "libx264", "-crf", "15", "-preset", "medium",
                        os.path.join(HERE, f"clips/S{i:02d}.mp4")], check=True)
    for p in plan: print("S%02d window %.2f-%.2f speed %.2fx -> %.2f s" % p)
    lst = os.path.join(HERE, "clips/list.txt"); open(lst, "w").write("".join(f"file 'S{i:02d}.mp4'\n" for i in range(1, n + 1)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    json.dump({"starts": starts, "durs": durs, "plan": plan}, open(os.path.join(HERE, "cut.json"), "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
