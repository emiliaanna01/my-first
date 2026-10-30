#!/usr/bin/env python3
"""Cut a recorded (ElevenLabs) narration into the reel's voice-over clips, tighten it to the reference's pace
(faster delivery via rubberband time-stretch with formants preserved, short punchy pauses), and write vo.json.
usage: python3 scripts/vo_el.py <narration.mp3> <out_dir> [tempo]"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf

SR = 48000
# the recording's phrases in order (one per pause), grouped into the clips the film keys on.
# (id, text, phrases in this clip, pause after) — pauses follow the reference: ~0.2 s, longer only on the beats
CLIPS = [
    ("hook",     "What if I told you...", 1, .22),
    ("hook2",    "the windshield wiper was invented by a woman riding a streetcar?", 2, .38),
    ("ny",       "New York, nineteen-oh-two.", 2, .18),
    ("crawl",    "A streetcar crawls through the sleet.", 1, .18),
    ("cantsee",  "The driver can't see the road.", 1, .28),
    ("only",     "So he does the only thing he can.", 1, .12),
    ("opens",    "He opens the window, and leans into the storm.", 2, .36),
    ("watch",    "One passenger can't stop watching.", 1, .24),
    ("name",     "Her name is Mary Anderson.", 1, .12),
    ("visiting", "She's visiting from Alabama.", 1, .24),
    ("engineer", "She isn't an engineer.", 1, .3),
    ("follows",  "But the problem follows her home.", 1, .26),
    ("sketch",   "She sketches an idea.", 1, .18),
    ("lever",    "A lever inside the car.", 1, .1),
    ("blade",    "A rubber blade outside.", 1, .24),
    ("turn",     "One turn of the handle...", 1, .1),
    ("clear",    "and the glass is clear.", 1, .4),
    ("patent",   "In nineteen-oh-three, she's granted a patent.", 1, .2),
    ("sell",     "Then she tries to sell it.", 1, .18),
    ("canada",   "A company in Canada tells her it isn't worth making.", 1, .26),
    ("nobody",   "Nobody buys it.", 1, .45),
    ("expire",   "Her patent runs out in nineteen-twenty,", 1, .08),
    ("roads",    "just as cars are filling the roads.", 1, .2),
    ("standard", "Within a few years, wipers are standard.", 1, .26),
    ("profit",   "She never profits from it.", 1, .45),
    ("every",    "But every time yours sweeps the rain away...", 1, .12),
    ("still",    "that's her idea, still moving.", 2, 0),
]
INNER = .2   # pause kept inside a two-phrase clip

def phrases(x, min_gap=.18):
    hop = int(.01 * SR); e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(e + 1e-9); sil = db < np.percentile(db, 95) - 38
    out, i, start = [], 0, None
    while i < len(sil):
        if not sil[i]:
            start = i if start is None else start; i += 1; continue
        j = i
        while j < len(sil) and sil[j]: j += 1
        if start is not None and ((j - i) * .01 >= min_gap or j == len(sil)): out.append((start, i)); start = None
        i = j
    if start is not None: out.append((start, len(sil)))
    pad = int(.03 * SR)   # keep breath edges
    return [x[max(0, a * hop - pad): min(len(x), b * hop + pad)] for a, b in out]

def stretch(x, tempo, tmp):
    sf.write(tmp + ".in.wav", x, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp + ".in.wav", "-af", f"rubberband=tempo={tempo}:formant=preserved:pitchq=quality:transients=mixed",
                    tmp + ".out.wav"], check=True)
    y, _ = sf.read(tmp + ".out.wav"); return y

def main(src, out_dir, tempo="1.1"):
    tempo = float(tempo); os.makedirs(out_dir, exist_ok=True); tmp = os.path.join(out_dir, "_tmp")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR), tmp + ".src.wav"], check=True)
    x, _ = sf.read(tmp + ".src.wav")
    ph = phrases(x); need = sum(c[2] for c in CLIPS)
    if len(ph) != need: sys.exit(f"found {len(ph)} phrases, script expects {need}: adjust min_gap")
    t, meta, k = .15, [], 0
    for cid, text, n, gap in CLIPS:
        parts = [stretch(p, tempo, tmp) for p in ph[k:k + n]]; k += n
        clip = parts[0]
        for p in parts[1:]: clip = np.concatenate([clip, np.zeros(int(INNER * SR)), p])
        path = f"{out_dir}/{cid}.wav"; sf.write(path, clip, SR); d = len(clip) / SR
        meta.append({"id": cid, "text": text, "t": round(t, 3), "dur": round(d, 3), "file": path})
        print(f"{cid:<9} {t:6.2f}  {d:4.2f}s  {text}"); t += d + gap
    for f in (".src.wav", ".in.wav", ".out.wav"):
        if os.path.exists(tmp + f): os.remove(tmp + f)
    print(f"total {t:.2f}s"); json.dump(meta, open(f"{out_dir}/vo.json", "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
