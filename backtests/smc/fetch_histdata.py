"""Download HistData.com free 1-minute ASCII bars (bid, EST without DST) as zips."""
import os, re, sys, time, urllib.parse, urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
UA = "Mozilla/5.0"
BASE = "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/%s/%s"


def get(url, data=None, ref=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **({"Referer": ref} if ref else {})})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def fetch(pair, year, month=None):
    tag = "%s_%d%s" % (pair, year, "" if month is None else "%02d" % month)
    path = os.path.join(OUT, tag + ".zip")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return "cached"
    page = BASE % (pair.lower(), year if month is None else "%d/%d" % (year, month))
    html = get(page).decode("utf-8", "replace")
    tk = re.search(r'id="tk" value="([^"]+)"', html)
    if not tk:
        return "no form"
    form = {"tk": tk.group(1), "date": str(year),
            "datemonth": str(year) if month is None else "%d%02d" % (year, month),
            "platform": "ASCII", "timeframe": "M1", "fxpair": pair}
    body = get("https://www.histdata.com/get.php", urllib.parse.urlencode(form).encode(), page)
    if body[:2] != b"PK":
        return "not a zip"
    open(path, "wb").write(body)
    return "%d bytes" % len(body)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for pair in sys.argv[1:] or ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]:
        for y in (2023, 2024, 2025):
            print(pair, y, fetch(pair, y), flush=True); time.sleep(1)
        for m in range(1, 13):
            r = fetch(pair, 2026, m)
            print(pair, 2026, m, r, flush=True); time.sleep(1)
            if r in ("no form", "not a zip"):
                break
