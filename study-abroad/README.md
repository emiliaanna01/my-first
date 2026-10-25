# Study abroad: scholarship & admissions tracker

Plan: Master's (Finance / Business Analytics / FinTech / Management), Germany first, Winter 2027 intake.

| Path | What it is |
|---|---|
| `data/opportunities.json` | Scholarships, programmes and visa items, with deadlines and status |
| `data/roadmap.json` | Step-by-step plan with due dates |
| `data/daily_plan.json` | One 30–60 minute session per day (IELTS prep, then applications) |
| `data/documents.json`, `data/profile.json` | Papers checklist and your current status |
| `tracker.html` | Source of the tracker web page (published as a private claude.ai artifact) |
| `bot/telegram_digest.py` | Sends today's session and deadline alerts to Telegram |
| `bot/menu_bot.py` | The Path Abroad command menu (/today, /week, /deadlines …) |
| `bot/sync_from_tracker.py` | Copies what you tick on the page back into `data/`, so the bot stays current |
| `../.github/workflows/telegram-digest.yml` | Morning update, every day at 11:30 Dhaka time |
| `../.github/workflows/telegram-menu.yml` | Answers menu commands every 30 min, 6:00–23:30 Dhaka time |

`verified: false` means the date or amount came from a third-party site. Check it on the official page before you rely on it.

## Telegram reminders: one-time setup

1. In Telegram, open **@BotFather**, send `/newbot`, and follow the prompts. Copy the **token** it gives you.
2. Send any message (for example "hi") to your new bot.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser. Find `"chat":{"id": ...}`. That number is your **chat id**.
4. On GitHub, go to the repo's **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `TELEGRAM_BOT_TOKEN` = the token
   - `TELEGRAM_CHAT_ID` = the chat id
   - `TRACKER_URL` = your tracker link (optional; used by /tracker and /done)
5. Go to **Actions → Study-abroad Telegram reminders → Run workflow** to send a test digest now.

After that, the bot sends today's session every morning at 11:30, plus alerts (30/14/7/3/1 days before a deadline, or overdue) and a full 60-day digest every Monday.
GitHub only runs scheduled workflows from the default branch, so merge this into `main` for the daily run to start.

Test locally without sending:

```bash
python3 study-abroad/bot/telegram_digest.py --dry-run --digest
```

## Study Europe Compass (Germany, Italy, Hungary, France)

A four-country comparison for this profile: the recommendation for the self-funded and scholarship scenarios,
a ranking, factor scores with adjustable weights, two-year cost against the 15–25 lakh budget, cash needed before
the visa, a timeline to a September 2027 start, the latest signals and top opportunities.

| Path | What it is |
|---|---|
| `data/compass.json` | The data: scores, recommendation, signals, opportunities. The daily research run edits this file. |
| `bot/build_compass.py` | Checks `compass.json` and builds `site/data.js` and `compass.html` |
| `site/` | The website (no login): `index.html`, `data.js`, app manifest, offline worker, icons |
| `compass.html` | The same page with the data inlined, published to claude.ai (adds an "Ask Claude" box) |
| `open_compass.bat` | Windows: pulls the latest version and opens the page in your browser |

Ways to open it, none needing a Claude login:

- **Web link:** https://raw.githack.com/emiliaanna01/my-first/claude/friendly-cerf-x5ro5z/study-abroad/site/index.html
  (served straight from this branch; updates show within a few minutes of each push).
- **As a desktop app:** open the link in Chrome, then menu ⋮ → *Cast, save and share* → *Install page as app*
  (or the *Install as an app* button on the page). You get a desktop and taskbar icon that opens in its own window.
- **Offline / on your PC:** with this repo cloned, double-click `study-abroad/open_compass.bat`.
- **Inside claude.ai:** https://claude.ai/artifact/ToiYYKs82G9wXLUcNGBysR

To rebuild after editing the data: `python3 study-abroad/bot/build_compass.py`.

## Daily research run

A scheduled Claude task runs every morning. It searches for new scholarships and programme
updates, adds them to the tracker, posts a short note under **Today → Research updates**, syncs
the tracker into `data/` and pushes to `claude/friendly-cerf-x5ro5z`. The Telegram job reads that
branch, so the 11:30 message includes the same day's changes.

## Menu commands

`/today` `/week` `/deadlines` `/apply` `/ielts` `/papers` `/done` `/tracker` `/help`. The buttons show
under the chat box. The bot only answers your own chat id.

There are two ways to run it, and both can be on at once:

- **GitHub (always on, slower):** the *Path Abroad menu replies* workflow checks for commands every
  30 minutes between 6:00 and 23:30 Dhaka time. Answers can take up to about 30 minutes, longer when GitHub is busy.
- **Your PC (instant, while it's on):** install Python 3 and clone this repo. Copy
  `study-abroad/bot/.env.example` to `study-abroad/bot/.env` and fill it in, then double-click
  `study-abroad/bot/start_menu_bot.bat` (Windows), or run `python3 study-abroad/bot/menu_bot.py --listen`.
  It pulls fresh tracker data from GitHub every 30 minutes.

Ticking things happens on the tracker page. `/done` sends you there, because the bot can't change the tracker itself.
