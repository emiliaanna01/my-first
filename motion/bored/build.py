#!/usr/bin/env python3
"""Inline fonts, cutout sprites, voice-over timings (and optionally the soundtrack) into the reel HTML.
usage: python3 motion/bored/build.py <out.html> [soundtrack.m4a]"""
import base64, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONTDIR = os.path.join(HERE, "sprites/node_modules/@fontsource/barlow-condensed/files")
FONTS = {"BCB": "barlow-condensed-latin-800-normal.woff2", "BCBI": "barlow-condensed-latin-800-italic.woff2", "BCL": "barlow-condensed-latin-300-italic.woff2"}
b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()

def main(out, audio=None):
    html = open(os.path.join(HERE, "src/bored-reel.html"), encoding="utf-8").read()
    faces = "\n".join(f'@font-face{{font-family:"{n}";src:url(data:font/woff2;base64,{b64(os.path.join(FONTDIR, f))}) format("woff2");font-display:block;}}' for n, f in FONTS.items())
    spr = {os.path.basename(p)[:-5]: "data:image/webp;base64," + b64(p) for p in sorted(glob.glob(os.path.join(HERE, "sprites/cut/*.webp")))}
    vo = json.load(open(os.path.join(HERE, "vo.json")))
    html = html.replace("/*FONTS*/", faces).replace("/*SPRITES*/", "const SPR = " + json.dumps(spr) + ";").replace("/*VO*/", "const VO_META = " + json.dumps(vo) + ";")
    if audio:
        html = html.replace("__AUDIO__", "data:audio/mp4;base64," + b64(audio))
    open(out, "w", encoding="utf-8").write(html)
    print(f"wrote {out} ({os.path.getsize(out) // 1024} KB)")

if __name__ == "__main__":
    main(*sys.argv[1:3])
