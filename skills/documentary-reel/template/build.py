#!/usr/bin/env python3
"""Inline fonts, graded plates, voice-over timings, clips (and optionally the soundtrack) into the reel HTML.
usage: python3 motion/<slug>/build.py render                    -> motion/<slug>/render.html (reads clips/ from disk, for export)
       python3 motion/<slug>/build.py <out.html> [soundtrack.m4a] -> standalone page with the small clips embedded"""
import base64, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CF = "/mnt/skills/examples/canvas-design/canvas-fonts"
FONTS = {"ISR": f"{CF}/InstrumentSerif-Regular.ttf", "ISI": f"{CF}/InstrumentSerif-Italic.ttf", "GL": f"{CF}/Gloock-Regular.ttf",
         "HND": f"{CF}/NothingYouCouldDo-Regular.ttf", "LB": f"{CF}/LibreBaskerville-Regular.ttf", "TW": f"{CF}/IBMPlexMono-Regular.ttf"}
b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()

def main(out, audio=None):
    html = open(os.path.join(HERE, "src/reel.html"), encoding="utf-8").read()
    faces = "\n".join(f'@font-face{{font-family:"{n}";src:url(data:font/ttf;base64,{b64(p)}) format("truetype");font-display:block;}}' for n, p in FONTS.items())
    spr = {os.path.basename(p)[:-5]: "data:image/webp;base64," + b64(p) for p in sorted(glob.glob(os.path.join(HERE, "layers/*.webp")))}
    if out == "render":
        out = os.path.join(HERE, "render.html")
        clips = {os.path.basename(p)[:-5]: "clips/" + os.path.basename(p) for p in sorted(glob.glob(os.path.join(HERE, "clips/*.webm")))}
    else:
        clips = {os.path.basename(p)[:-5]: "data:video/webm;base64," + b64(p) for p in sorted(glob.glob(os.path.join(HERE, "clips_lo/*.webm")))}
    vo = json.load(open(os.path.join(HERE, "vo.json")))
    html = (html.replace("/*FONTS*/", faces).replace("/*SPRITES*/", "const SPR = " + json.dumps(spr) + ";")
                .replace("/*CLIPS*/", "const CLIPS = " + json.dumps(clips) + ";").replace("/*VO*/", "const VO_META = " + json.dumps(vo) + ";"))
    if audio:
        html = html.replace("__AUDIO__", "data:audio/mp4;base64," + b64(audio))
    open(out, "w", encoding="utf-8").write(html)
    print(f"wrote {out} ({os.path.getsize(out) // 1024} KB)")

if __name__ == "__main__":
    main(*sys.argv[1:3])
