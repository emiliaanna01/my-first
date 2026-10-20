"""Rebuild data/*.json from a tracker database export.

The daily research run exports each tracker collection with
ArtifactData (out_dir=EXPORT), which writes EXPORT/<collection>/<doc_id>.json.
This script turns those files back into the JSON lists the Telegram bot reads,
so ticks and status changes made on the page reach the bot.

Usage: python3 study-abroad/bot/sync_from_tracker.py EXPORT_DIR
"""

import json
import pathlib
import sys

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
# collection name in the tracker -> file the bot reads, and the sort key
FILES = {
    "opportunities": ("opportunities.json", "deadline"),
    "roadmap": ("roadmap.json", "order"),
    "plan": ("daily_plan.json", "date"),
    "documents": ("documents.json", "category"),
}


def main():
    export = pathlib.Path(sys.argv[1])
    for collection, (filename, key) in FILES.items():
        folder = export / collection
        if not folder.is_dir():
            print(f"skip {collection}: not exported")
            continue
        rows = []
        for f in folder.glob("*.json"):
            doc = json.loads(f.read_text(encoding="utf-8"))
            rows.append({"id": f.stem, **doc})
        rows.sort(key=lambda r: (r.get(key) is None, str(r.get(key)), r["id"]))
        (DATA / filename).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{filename}: {len(rows)} rows")
    profile = export / "profile" / "main.json"
    if profile.exists():
        (DATA / "profile.json").write_text(profile.read_text(encoding="utf-8"), encoding="utf-8")
        print("profile.json: updated")


if __name__ == "__main__":
    main()
