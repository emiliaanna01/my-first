"""Send study-abroad deadline reminders to Telegram.

Reads data/opportunities.json and data/roadmap.json and posts:
  - an alert for anything due in exactly 30, 14, 7, 3 or 1 days (or today)
  - a full digest on Mondays, or whenever --digest is passed

Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment.
Standard library only, so the GitHub Action needs no pip install.
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
ALERT_DAYS = {30, 14, 7, 3, 1, 0}
DONE_STATUSES = {"applied", "accepted", "rejected", "dropped"}


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def open_items(today):
    """Yield (days_left, label, detail, link) for every dated, unfinished item."""
    for o in load("opportunities.json"):
        if not o.get("deadline") or o.get("status") in DONE_STATUSES:
            continue
        due = dt.date.fromisoformat(o["deadline"])
        flag = "" if o.get("verified") else " (unverified)"
        yield (due - today).days, o["name"], f"{o['funding']}{flag}", o.get("link")
    for s in load("roadmap.json"):
        if not s.get("due") or s.get("done"):
            continue
        due = dt.date.fromisoformat(s["due"])
        yield (due - today).days, f"Step: {s['title']}", s["detail"], None


def when(days):
    if days < 0:
        return f"OVERDUE {-days}d"
    if days == 0:
        return "TODAY"
    return f"in {days}d"


def line(days, label, detail, link):
    text = f"• <b>{when(days)}</b> — {label}\n  {detail}"
    return text + (f'\n  <a href="{link}">link</a>' if link else "")


def build_message(today, digest):
    items = sorted(open_items(today))
    alerts = [i for i in items if i[0] in ALERT_DAYS or i[0] < 0]
    parts = []
    if alerts:
        parts.append("⏰ <b>Deadline alerts</b>\n" + "\n".join(line(*i) for i in alerts))
    if digest:
        upcoming = [i for i in items if 0 <= i[0] <= 60]
        body = "\n".join(line(*i) for i in upcoming) or "Nothing due in the next 60 days."
        parts.append(f"📋 <b>Next 60 days</b> ({today:%d %b %Y})\n" + body)
    return "\n\n".join(parts)


def send(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=payload, timeout=30) as resp:
        if resp.status != 200:
            sys.exit(f"Telegram returned HTTP {resp.status}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", action="store_true", help="always include the 60-day digest")
    parser.add_argument("--dry-run", action="store_true", help="print instead of sending")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD) for testing")
    args = parser.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    digest = args.digest or today.weekday() == 0
    text = build_message(today, digest)
    if not text:
        print("Nothing to send today.")
        return
    if args.dry_run:
        print(text)
    else:
        send(text)
        print("Sent.")


if __name__ == "__main__":
    main()
