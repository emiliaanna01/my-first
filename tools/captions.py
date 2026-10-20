"""Transcribe a video and write word-by-word captions + glowing titles as an ASS subtitle file.

Usage:
  python tools/captions.py IN.mp4 OUT.ass [--title "There are 5 levels@0-2.2"] [--title "Level one@9-11"]
Burn in with:
  ffmpeg -i IN.mp4 -vf "ass=OUT.ass" -c:a copy OUT.mp4
English speech recognition: NVIDIA Parakeet TDT 0.6B (sherpa-onnx, CPU), word timestamps.
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asr import transcribe

W, H = 1080, 1920
TITLE_COLOR = "&H8FD6FF&"  # #FFD68F warm cream fill (ASS is BGR)
TITLE_GLOW = "&H349BF9&"  # #F99B34 orange glow
FILLERS = {"um", "uh", "uhm", "erm", "hmm"}


def ts(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def phrases(words, max_words=3):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == max_words or w[0][-1:] in ".,!?" or (cur and w is words[-1]):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--title", action="append", default=[], help='"text@start-end" seconds')
    ap.add_argument("--caption-y", type=int, default=1350)
    ap.add_argument("--title-y", type=int, default=520)
    ap.add_argument("--caption-y-at", action="append", default=[],
                    help='"start-end:y" caption height for a span (e.g. when the chin drops lower)')
    a = ap.parse_args()

    ev = []
    spans = [(*map(float, r.split(":")[0].split("-")), int(r.split(":")[1])) for r in a.caption_y_at]
    cap_y = lambda t: next((y for s0, s1, y in spans if s0 <= t < s1), a.caption_y)
    words = [w for w in transcribe(a.video) if w[0].lower().strip(",.!?") not in FILLERS]
    for ph in phrases(words):
        for i, w in enumerate(ph):  # whole phrase visible, active word highlighted with a pop
            end = ph[i + 1][1] if i + 1 < len(ph) else w[2]
            parts = []
            for j, x in enumerate(ph):
                txt = x[0].upper()
                parts.append(r"{\c&H34E1FF&\t(0,80,\fscx112\fscy112)\t(80,160,\fscx100\fscy100)}" + txt + r"{\c&HFFFFFF&}"
                             if j == i else txt)
            ev.append(f"Dialogue: 1,{ts(w[1])},{ts(end)},Cap,,0,0,0,,{{\\pos({W // 2},{cap_y(ph[0][1])})}}" + " ".join(parts))
    for t in a.title:
        text, rng = t.rsplit("@", 1)
        s, e = map(float, rng.split("-"))
        fs = min(130, int(1900 / max(1, len(text))))  # fit ~950 px of width
        anim = r"\fscx70\fscy70\t(0,180,\fscx106\fscy106)\t(180,300,\fscx100\fscy100)\fad(80,150)"
        ev.append(f"Dialogue: 2,{ts(s)},{ts(e)},TitleGlow,,0,0,0,,{{\\pos({W // 2},{a.title_y})\\fs{fs}{anim}}}{text}")
        ev.append(f"Dialogue: 3,{ts(s)},{ts(e)},Title,,0,0,0,,{{\\pos({W // 2},{a.title_y})\\fs{fs}{anim}}}{text}")

    with open(a.out, "w") as f:
        f.write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Poppins ExtraBold,92,&HFFFFFF&,&HFFFFFF&,&H000000&,&H80000000&,0,0,0,0,100,100,0,0,1,6,3,5,60,60,0,1
Style: Title,DM Serif Display,130,{TITLE_COLOR},{TITLE_COLOR},&H06142E&,&H96000000&,0,0,0,0,100,100,1,0,1,3,4,5,60,60,0,1
Style: TitleGlow,DM Serif Display,130,{TITLE_GLOW},{TITLE_GLOW},{TITLE_GLOW},&H00000000&,0,0,0,0,100,100,1,0,1,14,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        for e in ev:
            if ",TitleGlow," in e:
                e = e.replace("{\\pos", "{\\blur18\\alpha&H60&\\pos", 1)
            f.write(e + "\n")


if __name__ == "__main__":
    main()
