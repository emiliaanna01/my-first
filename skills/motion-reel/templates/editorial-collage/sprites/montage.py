# Contact sheet of a sprite folder with names. usage: python3 montage.py <dir> <out.png> [cols]
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 7
fs = sorted(glob.glob(os.path.join(d, "*.png")) + glob.glob(os.path.join(d, "*.webp"))); S = 300
rows = (len(fs) + cols - 1) // cols; sheet = Image.new("RGB", (cols * S, rows * S), (205, 210, 248))
f = ImageFont.truetype("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf", 18)
for i, p in enumerate(fs):
    im = Image.open(p).convert("RGBA"); im.thumbnail((S - 10, S - 30)); x, y = (i % cols) * S, (i // cols) * S
    sheet.paste(im, (x + (S - im.width) // 2, y + 26 + (S - 30 - im.height) // 2), im)
    ImageDraw.Draw(sheet).text((x + 6, y + 4), os.path.basename(p).rsplit(".", 1)[0], fill=(20, 20, 60), font=f)
sheet.save(out)
