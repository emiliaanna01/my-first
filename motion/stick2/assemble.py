#!/usr/bin/env python3
"""D.B. Cooper reel: fit each scene to its narration (stretch slow, then hold), add a cross-fade through black where the
scene itself fades, and burn one-word captions (cream, key words gold) at the top.
usage: python3 motion/stick2/assemble.py <out.mp4>"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); TAIL = 2.4
FONT = "/mnt/skills/examples/canvas-design/canvas-fonts/WorkSans-BoldItalic.ttf"
NUM = {"TWO HUNDRED THOUSAND DOLLARS": "$200,000", "FIVE THOUSAND EIGHT HUNDRED DOLLARS": "$5,800"}
ZOOM = {}
GOLD = {"HIJACKED", "TWO", "HUNDRED", "THOUSAND", "DOLLARS", "DARKNESS", "FBI", "NOVEMBER", "TWENTY-FOURTH", "NINETEEN", "SEVENTY-ONE", "DAN", "COOPER", "NOTE", "BOMB",
        "PARACHUTES", "FOUR", "THIRTY-SIX", "MONEY", "EIGHT", "DISAPPEARS", "NINE", "FIVE", "RANSOM", "COLUMBIA", "TRACE", "SIXTEEN", "SURVIVE", "WILDERNESS", "NOBODY", "KNOWS"}

def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)

def main(out):
    meta = json.load(open(os.path.join(HERE, "vo.json"))); n = len(meta)
    starts = [0] + [m["t"] for m in meta[1:]]
    durs = [starts[i + 1] - starts[i] for i in range(n - 1)] + [meta[-1]["t"] + meta[-1]["dur"] + TAIL - starts[-1]]
    os.makedirs(os.path.join(HERE, "clips"), exist_ok=True)
    for i in range(1, n + 1):
        src = os.path.join(HERE, f"video/S{i:02d}.mp4"); L = dur(src) - .05; d = durs[i - 1]
        sp = 1.0 if d <= L else max(.7, L / d)                     # dark slow scenes: stretch down to 0.7x, then hold
        z, cy = ZOOM.get(i, (1.0, .5))
        crop = f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:ih*{cy}-ih/{z}/2," if z > 1 else ""
        vf = (f"{crop}setpts=PTS/{sp:.4f},scale=1080:1920:flags=lanczos,unsharp=5:5:0.4,fps=30,"
              f"tpad=stop_mode=clone:stop_duration=4,trim=duration={d:.4f},setpts=PTS-STARTPTS,format=yuv420p")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-an", "-vf", vf, "-c:v", "libx264", "-crf", "15",
                        "-preset", "medium", os.path.join(HERE, f"clips/S{i:02d}.mp4")], check=True)
        print(f"S{i:02d} {d:.2f}s speed {sp:.2f}")
    lst = os.path.join(HERE, "clips/list.txt"); open(lst, "w").write("".join(f"file 'S{i:02d}.mp4'\n" for i in range(1, n + 1)))
    joined = os.path.join(HERE, "clips/joined.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    # captions: the word being spoken, big, at the top; pops in over 0.12 s
    # numbers are shown as figures: the whole spoken number becomes one caption ("$200,000", "1971")
    NUMS = [("TWO HUNDRED THOUSAND DOLLARS", "$200,000"), ("FIVE THOUSAND EIGHT HUNDRED DOLLARS", "$5,800"),
            ("NINETEEN SEVENTY-ONE", "1971"), ("TWENTY SIXTEEN", "2016"), ("THIRTY-SIX", "36"), ("NINE YEARS", "9 YEARS"), ("FOUR PARACHUTES", "4 PARACHUTES")]
    f = []
    for m in meta:
        ws = [re.sub(r"[^A-Za-z0-9!$'’-]", "", w).upper().replace("'", "\u2019") for w in m["text"].split()]
        ts = m["words"]; end = m["t"] + m["dur"] + .25; k = 0; caps = []
        while k < len(ws):
            hit = None
            for ph, rep in NUMS:
                p = ph.split()
                if [re.sub(r"[^A-Z0-9-]", "", x) for x in ws[k:k + len(p)]] == p: hit = (rep, len(p)); break
            word, n = hit if hit else (ws[k], 1)
            caps.append((word, ts[k], hit is not None)); k += n
        for j, (word, t0, isnum) in enumerate(caps):
            t1 = caps[j + 1][1] if j + 1 < len(caps) else end
            if not word: continue
            col = "0xE8C25A" if isnum or word.rstrip("?.,!") in GOLD else "0xF2EBDD"
            txt = word.replace("\u2019", "\\\u2019").replace(":", "\\:").replace("$", "\\$").replace(",", "\\,")
            size = 112 if isnum else 96
            f.append(f"drawtext=fontfile={FONT}:text='{txt}':fontcolor={col}:borderw=6:bordercolor=0x111111:"
                     f"fontsize='{size}*(1+0.28*max(0\\,1-(t-{t0:.3f})/0.12))':x=(w-text_w)/2:y=250-text_h/2:"
                     f"enable='between(t\\,{t0:.3f}\\,{t1 - .02:.3f})'")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", joined, "-vf", ",".join(f), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                    "-pix_fmt", "yuv420p", out], check=True)
    json.dump({"starts": starts, "durs": durs}, open(os.path.join(HERE, "cut.json"), "w"), indent=1)
    print("wrote", out, sum(durs))

if __name__ == "__main__":
    main(*sys.argv[1:2])
