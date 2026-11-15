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


TRACKER_URL = "https://claude.ai/artifact/YD31RbVmBQgdeK1tZFsJv7"
DHAKA = datetime.timezone(datetime.timedelta(hours=6))
SUBMITTED = {"applied", "accepted", "rejected"}
CLOSED = SUBMITTED | {"dropped"}
# Compass pick ids whose tracker entry has a different id
PICK_ALIASES = {"hu-sh": "stipendium-hungaricum", "it-unipv-finance": "it-pavia-msc-finance",
                "fr-campus-bd": "fr-etudes-en-france"}


def load_data(name, default):
    path = ROOT / "data" / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def tracker_snapshot(picks):
    """Summarise the tracker's synced data (data/*.json) for the Compass's progress panel."""
    today = datetime.datetime.now(DHAKA).date()
    iso = today.isoformat()
    opps = load_data("opportunities.json", [])
    plan = {p["date"]: p for p in load_data("daily_plan.json", [])}
    docs = load_data("documents.json", [])
    steps = load_data("roadmap.json", [])
    prof = load_data("profile.json", {})

    streak, day = 0, today
    if not plan.get(iso, {}).get("done"):
        day -= datetime.timedelta(days=1)
    while plan.get(day.isoformat(), {}).get("done"):
        streak += 1
        day -= datetime.timedelta(days=1)
    week = [plan.get((today - datetime.timedelta(days=k)).isoformat()) for k in range(1, 8)]

    deadlines = sorted(
        [{"name": o["name"], "date": o["deadline"], "link": o.get("link", ""), "status": o.get("status", "")}
         for o in opps if o.get("deadline") and o["deadline"] >= iso and o.get("status") not in CLOSED]
        + [{"name": s["title"], "date": s["due"], "link": "", "status": "step"}
           for s in steps if s.get("due") and s["due"] >= iso and not s.get("done")],
        key=lambda x: x["date"])[:5]

    by_id = {o["id"]: o for o in opps}
    by_link = {o.get("link"): o for o in opps if o.get("link")}
    status = {}
    for p in picks:
        pid = p["id"]
        o = (by_id.get(pid) or by_id.get(PICK_ALIASES.get(pid, "")) or by_id.get(pid.split("-", 1)[-1])
             or by_link.get(p.get("link")))
        if o:
            status[pid] = o.get("status", "to-check")

    today_task = plan.get(iso)
    return {
        "url": TRACKER_URL,
        "asOf": iso,
        "ielts": {"date": prof.get("ieltsDate"), "score": prof.get("ieltsScore"), "target": prof.get("ieltsTarget", 7)},
        "today": {k: today_task[k] for k in ("focus", "minutes", "task", "done")} if today_task else None,
        "sessions": {"last7": sum(1 for w in week if w and w.get("done")),
                     "doneTotal": sum(1 for p in plan.values() if p["date"] <= iso and p.get("done")),
                     "pastTotal": sum(1 for p in plan.values() if p["date"] <= iso),
                     "streak": streak},
        "docs": {"ready": sum(1 for d in docs if d.get("status") == "ready"), "total": len(docs),
                 "missing": [d["name"] for d in docs if d.get("status") == "missing"][:4]},
        "steps": {"done": sum(1 for s in steps if s.get("done")), "total": len(steps)},
        "apps": {"submitted": sum(1 for o in opps if o.get("status") in SUBMITTED),
                 "preparing": sum(1 for o in opps if o.get("status") == "preparing"),
                 "target": prof.get("appsTarget", 6)},
        "deadlines": deadlines,
        "pickStatus": status,
    }


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    check(data)
    data["tracker"] = tracker_snapshot(data["picks"])
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
