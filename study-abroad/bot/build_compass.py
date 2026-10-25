"""Build the Study Europe Compass from data/compass.json.

Writes two files:
  site/data.js   - loaded by site/index.html (GitHub Pages, or opened straight from disk)
  compass.html   - the same page with the data inlined, for the claude.ai artifact

Usage: python3 study-abroad/bot/build_compass.py
"""

import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "compass.json"
SITE = ROOT / "site"
DATA_TAG = '<script src="data.js"></script>'

REQUIRED_SIGNAL = {"id", "date", "country", "title", "detail", "impact", "link"}
REQUIRED_PICK = {"id", "name", "country", "funding", "fit", "link"}
COUNTRIES = {"de", "it", "hu", "fr", "eu"}


def check(data):
    ids = {c["id"] for c in data["countries"]}
    for f in data["factors"]:
        for sc in ("self", "sch"):
            for c in ids:
                v = f[sc][c]
                if not (isinstance(v, (int, float)) and 0 <= v <= 10):
                    raise ValueError(f"factor {f['id']} {sc} {c}: score {v!r} must be 0-10")
    for kind, rows, need in (("signal", data["signals"], REQUIRED_SIGNAL), ("pick", data["picks"], REQUIRED_PICK)):
        seen = set()
        for r in rows:
            missing = need - r.keys()
            if missing:
                raise ValueError(f"{kind} {r.get('id')}: missing {sorted(missing)}")
            if r["country"] not in COUNTRIES:
                raise ValueError(f"{kind} {r['id']}: country must be one of {sorted(COUNTRIES)}")
            if r["id"] in seen:
                raise ValueError(f"{kind} {r['id']}: duplicate id")
            seen.add(r["id"])


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    check(data)
    for row in data["signals"] + data["picks"]:
        row.setdefault("added", data["updated"])  # the day it was logged; drives the NEW highlights
    data["builtAt"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (SITE / "data.js").write_text(f"window.COMPASS = {payload};\n", encoding="utf-8")

    # The artifact gets the page body only (the publisher adds its own skeleton) with the data inlined.
    html = (SITE / "index.html").read_text(encoding="utf-8")
    page = html.split("<!--page-->", 1)[1].split("<!--/page-->", 1)[0]
    page = page.replace("<!--/head-->\n</head>\n<body>\n", "")
    page = page.replace(DATA_TAG, f"<script>window.COMPASS = {payload};</script>")
    (ROOT / "compass.html").write_text(page.lstrip(), encoding="utf-8")
    print(f"built: {len(data['signals'])} signals, {len(data['picks'])} picks, updated {data['updated']}")


if __name__ == "__main__":
    main()
