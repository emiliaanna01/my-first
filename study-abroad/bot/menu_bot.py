"""Path Abroad Telegram menu: answers /today, /week, /deadlines and more.

Two ways to run it, same code:
  --once    read waiting messages, answer them, exit (GitHub Actions, every 30 min)
  --listen  keep running and answer instantly (your PC, while it's on)

Telegram holds unanswered messages for 24 hours, and asking for updates
after the last one we handled marks them read, so no state file is needed.
Only messages from TELEGRAM_CHAT_ID get an answer; everyone else is ignored.

Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID. TRACKER_URL is optional.
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import time
import urllib.parse
import urllib.request

from telegram_digest import ALERT_DAYS, DONE_STATUSES, line, load, open_items, todays_session

REPO = pathlib.Path(__file__).resolve().parents[2]

# On your PC, keys can live in study-abroad/bot/.env (KEY=value per line, git-ignored).
ENV_FILE = pathlib.Path(__file__).with_name(".env")
if ENV_FILE.exists():
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, sep, value = raw.strip().partition("=")
        if sep and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip('"'))

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", ""))
TRACKER_URL = os.environ.get("TRACKER_URL", "")
DHAKA = dt.timezone(dt.timedelta(hours=6))

COMMANDS = [
    ("today", "Today's session"),
    ("week", "Next 7 days of sessions"),
    ("deadlines", "Deadlines in the next 60 days"),
    ("apply", "Applications to work on now"),
    ("ielts", "IELTS countdown and plan"),
    ("papers", "Documents still missing"),
    ("done", "Mark today's session done"),
    ("tracker", "Open the tracker page"),
    ("help", "Show this menu"),
]
KEYBOARD = {
    "keyboard": [["/today", "/week", "/deadlines"], ["/apply", "/ielts", "/papers"], ["/done", "/tracker", "/help"]],
    "resize_keyboard": True,
    "is_persistent": True,
}


def api(method, **params):
    data = urllib.parse.urlencode({k: json.dumps(v) if isinstance(v, (dict, list)) else v
                                   for k, v in params.items()}).encode()
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    with urllib.request.urlopen(url, data=data, timeout=70) as resp:
        body = json.load(resp)
    if not body.get("ok"):
        raise RuntimeError(f"{method} failed: {body}")
    return body["result"]


def reply(text):
    api("sendMessage", chat_id=CHAT_ID, text=text[:4000], parse_mode="HTML",
        disable_web_page_preview="true", reply_markup=KEYBOARD)


def today():
    return dt.datetime.now(DHAKA).date()


# ---------- answers ----------

def cmd_today(_):
    return todays_session(today()) or "No session planned for today. The morning research run adds new days."


def cmd_week(_):
    plan = {p["date"]: p for p in load("daily_plan.json")}
    rows = []
    for k in range(7):
        d = today() + dt.timedelta(days=k)
        p = plan.get(d.isoformat())
        if p:
            tick = "✅" if p.get("done") else "▫️"
            rows.append(f"{tick} <b>{d:%a %d %b}</b> · {p['minutes']}m · {p['focus']}\n   {p['task']}")
    return "🗓 <b>Next 7 days</b>\n" + ("\n".join(rows) or "Nothing planned yet.")


def cmd_deadlines(_):
    items = [i for i in sorted(open_items(today())) if i[0] <= 60]
    return "⏰ <b>Next 60 days</b>\n" + ("\n".join(line(*i) for i in items) or "Nothing due.")


def cmd_apply(_):
    opps = [o for o in load("opportunities.json")
            if o.get("deadline") and o.get("status") not in DONE_STATUSES and o.get("status") != "later"]
    opps.sort(key=lambda o: o["deadline"])
    rows = []
    for o in opps[:6]:
        days = (dt.date.fromisoformat(o["deadline"]) - today()).days
        if days < 0:
            continue
        check = "" if o.get("verified") else " ⚠️ verify date"
        rows.append(f"• <b>{o['name']}</b>\n  {days}d left ({o['deadline']}) · {o['status']}{check}")
    return "📝 <b>Applications to work on</b>\n" + ("\n".join(rows) or "No open applications with dates.")


def cmd_ielts(_):
    prof = load("profile.json")
    if prof.get("ieltsScore"):
        return f"🎯 IELTS result logged: <b>{prof['ieltsScore']}</b> (target {prof.get('ieltsTarget', 7)})."
    if not prof.get("ieltsDate"):
        return "🎯 No test date yet. Book IELTS Academic and set the date in the tracker's Readiness tab."
    days = (dt.date.fromisoformat(prof["ieltsDate"]) - today()).days
    plan = load("daily_plan.json")
    upcoming = [p for p in plan if p["date"] >= today().isoformat() and p["focus"].startswith("IELTS")][:3]
    nxt = "\n".join(f"• {dt.date.fromisoformat(p['date']):%a %d %b}: {p['focus']}" for p in upcoming)
    return (f"🎯 <b>IELTS in {days} days</b> ({prof['ieltsDate']}) · target {prof.get('ieltsTarget', 7)}\n"
            f"Score your essays in the tracker's IELTS tab.\n{nxt}")


def cmd_papers(_):
    docs = load("documents.json")
    ready = sum(1 for d in docs if d.get("status") == "ready")
    missing = [d for d in docs if d.get("status") == "missing"]
    rows = "\n".join(f"• {d['name']}" for d in missing[:8])
    more = f"\n…and {len(missing) - 8} more" if len(missing) > 8 else ""
    return f"📁 <b>{ready}/{len(docs)} documents ready</b>\nStill missing:\n{rows or 'Nothing. Well done.'}{more}"


def cmd_done(_):
    link = f'\n<a href="{TRACKER_URL}">Open the tracker</a>' if TRACKER_URL else ""
    return ("Tick today's session in the tracker's Today tab so your streak counts. "
            "The bot reads it after the morning sync." + link)


def cmd_tracker(_):
    return f'🧭 <a href="{TRACKER_URL}">Open Path Abroad tracker</a>' if TRACKER_URL else \
        "Add a TRACKER_URL secret with your tracker link and I'll show it here."


def cmd_help(_):
    return "🧭 <b>Path Abroad</b>\n" + "\n".join(f"/{c} — {d}" for c, d in COMMANDS)


HANDLERS = {f"/{c}": globals()[f"cmd_{c}"] for c, _ in COMMANDS}
HANDLERS["/start"] = cmd_help


def handle(update):
    msg = update.get("message") or {}
    if str(msg.get("chat", {}).get("id")) != CHAT_ID:
        return
    word = (msg.get("text") or "").strip().split()[0:1]
    cmd = word[0].split("@")[0].lower() if word else ""
    fn = HANDLERS.get(cmd, cmd_help)
    try:
        reply(fn(msg))
    except FileNotFoundError:
        reply("Tracker data isn't synced yet. Try again after the morning run.")


def poll(timeout, offset):
    updates = api("getUpdates", offset=offset, timeout=timeout, allowed_updates=["message"])
    for u in updates:
        handle(u)
        offset = u["update_id"] + 1
    return offset


def git_pull():
    if (REPO / ".git").exists():
        subprocess.run(["git", "-C", str(REPO), "pull", "--ff-only", "-q"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="answer waiting messages, then exit")
    mode.add_argument("--listen", action="store_true", help="keep running and answer instantly")
    args = parser.parse_args()
    if not TOKEN or not CHAT_ID:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first.")

    api("setMyCommands", commands=[{"command": c, "description": d} for c, d in COMMANDS])
    if args.once:
        offset = None
        while True:  # drain everything waiting, then stop
            before = offset
            offset = poll(0, offset)
            if offset == before:
                break
        return

    print("Path Abroad menu bot is running. Press Ctrl+C to stop.")
    offset, last_pull = None, 0.0
    while True:
        if time.time() - last_pull > 1800:  # refresh tracker data every 30 min
            git_pull()
            last_pull = time.time()
        try:
            offset = poll(50, offset)
        except Exception as e:  # network blips on a home connection: wait and retry
            print(f"retrying after error: {e}")
            time.sleep(15)


if __name__ == "__main__":
    main()
