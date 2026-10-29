"""Find real archive photos you are allowed to use: Wikimedia Commons, public domain and CC0 only by default.

  search "Harvard Mark II" sheet.png   -> numbered candidates + a contact sheet PNG to look at
  get "File:Harvard_Mark_II.jpg" out   -> downloads it and appends the credit line to CREDITS.txt

CC BY / CC BY-SA images are allowed with --allow-by; their author + licence go into the credits and must be shown.

Wikimedia rate-limits busy networks (HTTP 429 with a Retry-After). This module is built to get through that:
- it waits as long as Wikimedia asks (up to a budget) instead of giving up after a few seconds;
- metadata from a search is cached, and a film's photos are looked up in one batched request, so each photo costs
  one download and no extra API call;
- every download is kept in a shared cache (~/.papercut/cache), so no photo is ever fetched twice;
- it downloads from upload.wikimedia.org, falling back to the full-size original (resized here) when the
  thumbnail host is unreachable.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

import requests
from PIL import Image, ImageDraw, ImageFont

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "PapercutVideoEngine/1.0 (free paper-collage video engine)"}
FREE = re.compile(r"public domain|^pd|cc0|no restrictions", re.I)
BY = re.compile(r"^cc[ -]by", re.I)
CACHE = os.environ.get("PAPERCUT_CACHE") or os.path.join(os.path.expanduser("~"), ".papercut", "cache")
THUMB_W = 1280  # Wikimedia only serves standard thumbnail widths (…, 330, 500, 960, 1280, 1920); others are refused
SHEET_W = 330


class RateLimited(RuntimeError):
    pass


def _norm(title):
    t = title.strip().replace("_", " ")
    return t if t.startswith("File:") else "File:" + t


def _meta_path():
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, "meta.json")


def _load_meta():
    try:
        return json.load(open(_meta_path(), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_meta(meta):
    tmp = _meta_path() + ".tmp"
    json.dump(meta, open(tmp, "w", encoding="utf-8"), indent=0)
    os.replace(tmp, _meta_path())


def _wait(seconds, why, budget):
    """Sleep as Wikimedia asks, within what is left of the budget; returns the budget left."""
    if seconds > budget:
        raise RateLimited(f"Wikimedia asks to wait {seconds}s ({why}); waiting budget left is {budget:.0f}s")
    print(f"  Wikimedia is rate-limiting this network ({why}): waiting {seconds}s as asked", flush=True)
    time.sleep(seconds)
    return budget - seconds


def _get(params, budget=900):
    """One API call, honouring 429 Retry-After within the waiting budget (seconds)."""
    while True:
        r = requests.get(API, params=params, headers=UA, timeout=30)
        if r.status_code == 429:
            budget = _wait(int(r.headers.get("Retry-After", "30") or 30) + 1, "API", budget)
            continue
        r.raise_for_status()
        return r.json()


def _clean(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()


def _record(page):
    """A cache record from an API page with imageinfo."""
    ii = (page.get("imageinfo") or [{}])[0]
    md = ii.get("extmetadata", {})
    return {"license": _clean(md.get("LicenseShortName", {}).get("value")),
            "artist": _clean(md.get("Artist", {}).get("value"))[:120],
            "url": ii.get("url"), "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"),
            "w": ii.get("width"), "h": ii.get("height")}


def search(query, limit=24, allow_by=False):
    data = _get({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": THUMB_W,
    })
    meta, out = _load_meta(), []
    for p in sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        rec = _record(p)
        meta[_norm(p["title"])] = rec  # a later get() of this file needs no API call
        ok = bool(FREE.search(rec["license"])) or (allow_by and bool(BY.search(rec["license"])))
        if not ok or (rec["w"] or 0) < 500:
            continue
        out.append({"title": p["title"], "license": rec["license"], "w": rec["w"], "h": rec["h"],
                    "thumb": rec["thumb"] or rec["url"], "page": rec["page"], "artist": rec["artist"][:80]})
    _save_meta(meta)
    return out


def info(titles, budget=900):
    """Metadata for many files: from the cache, the rest in batched API calls (50 titles per request)."""
    meta = _load_meta()
    want = [_norm(t) for t in titles]
    missing = [t for t in want if t not in meta]
    for i in range(0, len(missing), 50):
        chunk = missing[i:i + 50]
        data = _get({"action": "query", "format": "json", "titles": "|".join(chunk), "prop": "imageinfo",
                     "iiprop": "url|size|extmetadata", "iiurlwidth": THUMB_W}, budget)
        norm = {n["to"]: n["from"] for n in data.get("query", {}).get("normalized", [])}
        for p in data.get("query", {}).get("pages", {}).values():
            if "imageinfo" in p:
                meta[_norm(norm.get(p["title"], p["title"]))] = _record(p)
                meta[_norm(p["title"])] = meta[_norm(norm.get(p["title"], p["title"]))]
        _save_meta(meta)
    return {t: meta.get(t) for t in want}


def _original_url(title):
    """The full-size file's address, computed the way Wikimedia stores it (no API call needed)."""
    name = _norm(title)[5:].replace(" ", "_")
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{name}"


def _candidates(rec, title):
    """Download addresses, best first: the 1280px thumb on upload.wikimedia.org, then the original there."""
    urls = []
    thumb = (rec or {}).get("thumb")
    if thumb:
        thumb = thumb.split("?")[0]
        urls.append(thumb.replace("://thumb.wikimedia.org/", "://upload.wikimedia.org/"))
    urls.append(((rec or {}).get("url") or _original_url(title)).split("?")[0])
    if thumb and "://thumb.wikimedia.org/" in thumb:
        urls.append(thumb)  # last: that host is often not allowed on locked-down networks
    return list(dict.fromkeys(urls))


def _download(url, out, budget):
    """curl (Wikimedia's edge rate-limits python's HTTP fingerprint), honouring Retry-After. Returns (ok, budget)."""
    hdr = out + ".hdr"
    while True:
        code = subprocess.run(["curl", "-s", "-L", "-o", out, "-D", hdr, "-w", "%{http_code}", "-A", UA["User-Agent"], url],
                              capture_output=True, text=True).stdout.strip()
        headers = open(hdr, encoding="latin-1").read() if os.path.exists(hdr) else ""
        if os.path.exists(hdr):
            os.remove(hdr)
        if code == "200":
            return True, budget
        if os.path.exists(out):
            os.remove(out)
        if code == "429":
            m = re.findall(r"(?im)^retry-after:\s*(\d+)", headers)
            budget = _wait(int(m[-1]) + 1 if m else 30, "download", budget)
            continue
        return False, budget  # 000 (host not reachable), 400/404 (no such size): try the next address


def _fit(path, max_side=1600):
    im = Image.open(path)
    if max(im.size) <= max_side:
        return
    im.thumbnail((max_side, max_side))
    if path.lower().endswith((".jpg", ".jpeg")):
        im.convert("RGB").save(path, quality=92)
    else:
        im.save(path)


def get(title, out, credits="CREDITS.txt", allow_by=False, budget=900):
    """Download one file (cached), check its licence, add its credit line."""
    title = _norm(title)
    rec = info([title], budget)[title]
    if not rec:
        raise SystemExit(f"not found on Wikimedia Commons: {title}")
    lic = rec["license"]
    if not (FREE.search(lic) or (allow_by and BY.search(lic))):
        raise SystemExit(f"refused: {title} is '{lic}', not public domain/CC0 (use allow_by / --allow-by for CC BY)")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cached = os.path.join(CACHE, "img", hashlib.md5(title.encode()).hexdigest() + os.path.splitext(title)[1].lower())
    if not os.path.exists(cached):
        os.makedirs(os.path.dirname(cached), exist_ok=True)
        tmp, ok = cached + ".part", False
        for url in _candidates(rec, title):
            ok, budget = _download(url, tmp, budget)
            if ok:
                break
        if not ok:
            raise SystemExit(f"download failed for {title}: every address refused or unreachable")
        os.replace(tmp, cached)
        _fit(cached)
        time.sleep(1.0)  # be gentle with a shared network
    shutil.copy(cached, out)
    line = f"{os.path.basename(out)}: {title} | {rec['artist'] or 'unknown'} | {lic} | {rec['page']}\n"
    existing = open(credits, encoding="utf-8").read() if os.path.exists(credits) else ""
    if line not in existing:
        open(credits, "a", encoding="utf-8").write(line)
    return out


def contact_sheet(cands, path, cols=4, tw=300):
    font = ImageFont.load_default()
    rows = (len(cands) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (tw + 40)), (30, 30, 30))
    from io import BytesIO
    for i, c in enumerate(cands):
        im = None
        for u in _candidates({"thumb": re.sub(r"/\d+px-", f"/{SHEET_W}px-", c["thumb"] or "")}, c["title"])[:1]:
            try:
                r = requests.get(u, headers=UA, timeout=30)
                if r.status_code == 200:
                    im = Image.open(BytesIO(r.content)).convert("RGB")
            except Exception:
                pass
            time.sleep(0.3)
        x, y = (i % cols) * tw, (i // cols) * (tw + 40)
        d = ImageDraw.Draw(sheet)
        if im is not None:
            im.thumbnail((tw - 8, tw - 8))
            sheet.paste(im, (x + 4, y + 4))
        else:
            d.text((x + 10, y + tw // 2), "(preview not available)", fill=(120, 120, 120), font=font)
        d.text((x + 6, y + tw + 2), f"{i + 1}. {c['title'][5:40]}", fill=(255, 255, 255), font=font)
        d.text((x + 6, y + tw + 18), f"{c['license'][:30]}  {c['w']}x{c['h']}", fill=(180, 180, 180), font=font)
    sheet.save(path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    allow = "--allow-by" in sys.argv
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    if cmd == "search":
        c = search(args[0], allow_by=allow)
        for i, x in enumerate(c, 1):
            print(f"{i:2d}. {x['title']}  [{x['license']}]  {x['w']}x{x['h']}")
        if len(args) > 1:
            contact_sheet(c, args[1])
            json.dump(c, open(args[1] + ".json", "w", encoding="utf-8"), indent=1)
            print("sheet:", args[1])
    elif cmd == "get":
        print(get(args[0], args[1], allow_by=allow))
