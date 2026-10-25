"""Send study-abroad deadline reminders to Telegram.

Reads data/opportunities.json, data/roadmap.json and data/daily_plan.json and posts:
  - today's study / application session (every day)
  - an alert for anything due in exactly 30, 14, 7, 3 or 1 days (or today)
  - a full digest on Mondays, or whenever --digest is passed
  - what the morning research run added to the Study Europe Compass today (data/compass.json)

Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment.
Standard library only, so the GitHub Action needs no pip install.
"""

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
ALERT_DAYS = {30, 14, 7, 3, 1, 0}
DONE_STATUSES = {"applied", "accepted", "rejected", "dropped"}
COMPASS_URL = "https://raw.githack.com/emiliaanna01/my-first/claude/friendly-cerf-x5ro5z/study-abroad/site/index.html"
FLAGS = {"de": "🇩🇪", "it": "🇮🇹", "hu": "🇭🇺", "fr": "🇫🇷", "eu": "🇪🇺"}


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


def todays_session(today):
    plan = {p["date"]: p for p in load("daily_plan.json")}
    p = plan.get(today.isoformat())
    if not p:
        return ""
    week = [plan.get((today - dt.timedelta(days=k)).isoformat()) for k in range(1, 8)]
    done = sum(1 for w in week if w and w.get("done"))
    text = f"📚 <b>Today · {p['minutes']} min · {p['focus']}</b>\n{p['task']}"
    if p.get("resource"):
        text += f"\n<i>Use: {p['resource']}</i>"
    return text + f"\nLast 7 days: {done}/7 sessions done."


def compass_news(today):
    """Signals, opportunities and a recommendation change logged today, or "" when there are none."""
    path = DATA / "compass.json"
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    day = today.isoformat()
    lines = []
    analysis = data.get("analysis", {})
    if analysis.get("changedOn") == day:
        lines.append(f"• <b>Recommendation changed:</b> {html.escape(analysis.get('changeNote', ''), quote=False)}")
    for s in data.get("signals", []):
        if s.get("added") == day:
            lines.append(f"• {FLAGS.get(s.get('country'), '')} {html.escape(s['title'], quote=False)}")
    for p in data.get("picks", []):
        if p.get("added") == day:
            lines.append(f"• {FLAGS.get(p.get('country'), '')} New opportunity: {html.escape(p['name'], quote=False)}")
    if not lines:
        return ""
    more = f"\n…and {len(lines) - 8} more" if len(lines) > 8 else ""
    return "🆕 <b>Study Europe Compass updated</b>\n" + "\n".join(lines[:8]) + more + f'\n<a href="{COMPASS_URL}">Open the compass</a>'


def build_message(today, digest):
    items = sorted(open_items(today))
    alerts = [i for i in items if i[0] in ALERT_DAYS or i[0] < 0]
    parts = [f"🧭 <b>Path Abroad</b> · {today:%a %d %b}"]
    session = todays_session(today)
    if session:
        parts.append(session)
    news = compass_news(today)
    if news:
        parts.append(news)
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
        # same buttons as menu_bot.py, so the menu shows under the chat box
        "reply_markup": json.dumps({
            "keyboard": [["/today", "/week", "/deadlines"], ["/apply", "/ielts", "/papers"], ["/done", "/tracker", "/help"]],
            "resize_keyboard": True, "is_persistent": True,
        }),
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
