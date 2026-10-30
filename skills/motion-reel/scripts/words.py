#!/usr/bin/env python3
"""Estimate word onset times inside each voice-over clip: letter-count guess snapped to energy dips.
usage: python3 motion/anderson/words.py <vo_dir> <out_json>"""
import json, sys, re
import numpy as np, soundfile as sf

def onsets(path, text):
    x, sr = sf.read(path); x = x.mean(1) if x.ndim > 1 else x
    hop = int(.01 * sr); e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    e = np.convolve(e, np.ones(3) / 3, "same"); thr = e.max() * .12
    dips = [i for i in range(1, len(e) - 1) if e[i] <= e[i - 1] and e[i] <= e[i + 1] and e[i] < thr]
    words = text.split(); wt = [len(re.sub(r"[^a-z0-9']", "", w.lower())) + 1.4 for w in words]
    dur = len(x) / sr; first = next((i for i in range(len(e)) if e[i] > thr), 0) * .01
    res, cum = [], 0
    for k, w in enumerate(words):
        g = first + (dur - first - .12) * cum / sum(wt)
        if k and dips:
            near = min(dips, key=lambda i: abs(i * .01 - g))
            if abs(near * .01 - g) < .16: g = near * .01 + .02
        res.append(round(max(g, res[-1] + .06 if res else 0), 3)); cum += wt[k]
    return res

def main(vo_dir, out):
    meta = json.load(open(f"{vo_dir}/vo.json"))
    for m in meta:
        m["words"] = [round(m["t"] + o, 3) for o in onsets(m["file"], m["text"])]
        m.pop("file", None)
    json.dump(meta, open(out, "w"), indent=1)
    for m in meta: print(m["id"], list(zip(m["text"].split(), m["words"]))[:6])

if __name__ == "__main__":
    main(*sys.argv[1:3])
