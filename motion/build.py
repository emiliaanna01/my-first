#!/usr/bin/env python3
"""Inline subset fonts into the reel HTML so the delivered file is self-contained.

usage: python3 motion/build.py motion/src/control-reel.html exports/control-reel.html
"""
import base64
import io
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

FONTS = {
    "IDBlack": "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "IDBold": "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
    "IDLight": "/usr/share/fonts/opentype/inter/InterDisplay-Light.otf",
    "ISerif": "/mnt/skills/examples/canvas-design/canvas-fonts/InstrumentSerif-Italic.ttf",
    "Mono": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf",
}
# Basic Latin + Latin-1 + common punctuation, bullets and arrows.
UNICODES = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + list(range(0x2010, 0x2028)) + [0x2022, 0x2190, 0x2191, 0x2192, 0x2193, 0x2122]


def woff2_b64(path):
    font = TTFont(path)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "tnum", "case"]
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=UNICODES)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def main(src, dst):
    html = open(src, encoding="utf-8").read()
    faces = "\n".join(
        f'@font-face{{font-family:"{name}";src:url(data:font/woff2;base64,{woff2_b64(path)}) format("woff2");font-display:block;}}'
        for name, path in FONTS.items()
    )
    open(dst, "w", encoding="utf-8").write(html.replace("/*FONTS*/", faces))
    print(f"wrote {dst} ({len(html) // 1024} KB source, fonts inlined)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
