#!/usr/bin/env python3
"""Inline fonts, engraved plates, voice-over timings (and optionally the soundtrack) into the reel HTML.
usage: python3 motion/paxton/build_photo.py <out.html> [soundtrack.m4a|-] [chatgpt]"""
import base64, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {"ISI": "/mnt/skills/examples/canvas-design/canvas-fonts/InstrumentSerif-Italic.ttf",
         "ISR": "/mnt/skills/examples/canvas-design/canvas-fonts/InstrumentSerif-Regular.ttf"}
SKIP = {"paxton"}
b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()

def main(out, audio=None, variant=""):
    html = open(os.path.join(HERE, f"src/paxton-photo{variant and '-' + variant}.html"), encoding="utf-8").read()
    faces = "\n".join(f'@font-face{{font-family:"{n}";src:url(data:font/ttf;base64,{b64(p)}) format("truetype");font-display:block;}}' for n, p in FONTS.items())
    spr = {os.path.basename(p)[:-5]: "data:image/webp;base64," + b64(p) for p in sorted(glob.glob(os.path.join(HERE, f"layers{variant and '_' + variant}/*.webp"))) }
    vo = json.load(open(os.path.join(HERE, "vo.json")))
    html = html.replace("/*FONTS*/", faces).replace("/*SPRITES*/", "const SPR = " + json.dumps(spr) + ";").replace("/*VO*/", "const VO_META = " + json.dumps(vo) + ";")
    if audio:
        html = html.replace("__AUDIO__", "data:audio/mp4;base64," + b64(audio))
    open(out, "w", encoding="utf-8").write(html)
    print(f"wrote {out} ({os.path.getsize(out) // 1024} KB)")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None, sys.argv[3] if len(sys.argv) > 3 else "")
