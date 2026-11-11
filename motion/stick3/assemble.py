#!/usr/bin/env python3
"""Billionaire-confidence reel: fit the 8 scenes to the cast dialogue (S08 is split so its punchline lands on White
Shirt's line) and burn one-word captions at the top.
usage: python3 motion/stick3/assemble.py <out.mp4>"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); TAIL = 1.6
FONT = "/mnt/skills/examples/canvas-design/canvas-fonts/WorkSans-BoldItalic.ttf"
ZOOM = {}
PUNCH = 1.65                                                   # S08 source time where the "YOU DON'T EVEN HAVE A CAR" frame starts
GREEN = {"DOLLAR", "BILLIONAIRE", "MONEY", "FIVE", "BUCKS", "LEVERAGING", "ASSETS", "FINEST", "LAMBORGHINI", "FIFTY", "FANCY"}
RED = {"TWELVE", "TWELVE?!", "OCEAN?!", "DECLINED", "BORROWED", "CAR!!", "PARKING?"}

def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)

def main(out):
    meta = json.load(open(os.path.join(HERE, "vo.json"))); n = len(meta)
    starts = [0] + [m["t"] for m in meta[1:]]
    durs = [starts[i + 1] - starts[i] for i in range(n - 1)] + [meta[-1]["t"] + meta[-1]["dur"] + TAIL - starts[-1]]
    os.makedirs(os.path.join(HERE, "clips"), exist_ok=True)
    for i in range(1, n + 1):
        src = os.path.join(HERE, f"video/S{i:02d}.mp4"); L = dur(src) - .05; d = durs[i - 1]
        sp = 1.0 if d <= L else max(.85, L / d)                    # never slower than 0.85x; hold the last frame for the rest
        z, cy = ZOOM.get(i, (1.0, .5))
        crop = f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:ih*{cy}-ih/{z}/2," if z > 1 else ""
        vf = (f"{crop}setpts=PTS/{sp:.4f},scale=1080:1920:flags=lanczos,unsharp=5:5:0.4,fps=30,"
              f"tpad=stop_mode=clone:stop_duration=4,trim=duration={d:.4f},setpts=PTS-STARTPTS,format=yuv420p")
        if i == 8:   # hold the "borrow fifty bucks" bubble under Red's lines, then play the punchline on White's line
            lines = json.load(open(os.path.join(HERE, "lines.json"))); wt = [l["t"] for l in lines if l["scene"] == 8 and l["who"] == "WHITE"][0]
            da = max(.5, wt - .1 - starts[i - 1]); spa = PUNCH / da
            vf = (f"split[a][b];[a]trim=0:{PUNCH},setpts=(PTS-STARTPTS)/{spa:.4f}[a1];[b]trim={PUNCH}:{L:.3f},setpts=PTS-STARTPTS[b1];"
                  f"[a1][b1]concat=n=2:v=1,scale=1080:1920:flags=lanczos,unsharp=5:5:0.4,fps=30,"
                  f"tpad=stop_mode=clone:stop_duration=4,trim=duration={d:.4f},setpts=PTS-STARTPTS,format=yuv420p")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-an", "-vf", vf, "-c:v", "libx264", "-crf", "15",
                        "-preset", "medium", os.path.join(HERE, f"clips/S{i:02d}.mp4")], check=True)
        print(f"S{i:02d} {d:.2f}s speed {sp:.2f}")
    lst = os.path.join(HERE, "clips/list.txt"); open(lst, "w").write("".join(f"file 'S{i:02d}.mp4'\n" for i in range(1, n + 1)))
    joined = os.path.join(HERE, "clips/joined.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    # captions: the word being spoken, big, at the top; pops in over 0.12 s
    f = []
    for m in meta:
        ws = m["text"].split()
        for k, (w, t0) in enumerate(zip(ws, m["words"])):
            t1 = m["words"][k + 1] if k + 1 < len(ws) else m["t"] + m["dur"] + .25
            word = re.sub(r"[^A-Za-z0-9!$'’]", "", w).upper().replace("'", "’")
            col = "0x1FA83A" if word.rstrip("!") in GREEN or word in GREEN else "0xE0342B" if word in RED else "0x111111"
            txt = word.replace("’", "\\’").replace(":", "\\:")
            f.append(f"drawtext=fontfile={FONT}:text='{txt}':fontcolor={col}:borderw=7:bordercolor=white:"
                     f"fontsize='96*(1+0.28*max(0\\,1-(t-{t0:.3f})/0.12))':x=(w-text_w)/2:y={1700 if m['id'] == 'S08' else 250}-text_h/2:"
                     f"enable='between(t\\,{t0:.3f}\\,{t1 - .02:.3f})'")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", joined, "-vf", ",".join(f), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                    "-pix_fmt", "yuv420p", out], check=True)
    json.dump({"starts": starts, "durs": durs}, open(os.path.join(HERE, "cut.json"), "w"), indent=1)
    print("wrote", out, sum(durs))

if __name__ == "__main__":
    main(*sys.argv[1:2])
