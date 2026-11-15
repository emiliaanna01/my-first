"""Restore data/compass.json from the published Compass page.

The morning research run updates the claude.ai copy of the Compass every day,
but it cannot push to GitHub. This copies that day's data back into the repo:
pass the HTML saved by the Artifact tool's read of the Compass artifact.

Usage: python3 study-abroad/bot/restore_compass.py <saved-compass.html>
"""

import json
import pathlib
import re
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "data" / "compass.json"


def main():
    html = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    m = re.search(r"window\.COMPASS = (\{.*?\});</script>", html, re.S)
    if not m:
        sys.exit("No Compass data found in that file.")
    live = json.loads(m.group(1))
    for key in ("builtAt", "tracker"):  # rebuilt by build_compass.py
        live.pop(key, None)
    repo = json.loads(SRC.read_text(encoding="utf-8"))
    if live["updated"] < repo["updated"]:
        sys.exit(f"Published copy ({live['updated']}) is older than the repo ({repo['updated']}); nothing to restore.")
    SRC.write_text(json.dumps(live, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"restored compass.json: updated {live['updated']}, {len(live['signals'])} signals, {len(live['picks'])} picks")


if __name__ == "__main__":
    main()
