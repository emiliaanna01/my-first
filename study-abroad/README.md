# Study abroad: scholarship & admissions tracker

Plan: Master's (Finance / Business Analytics / FinTech / Management), Germany first, Winter 2027 intake.

| Path | What it is |
|---|---|
| `data/opportunities.json` | Scholarships, programmes and visa items, with deadlines and status |
| `data/roadmap.json` | Step-by-step plan with due dates |
| `tracker.html` | Source of the tracker web page (published as a private claude.ai artifact) |
| `bot/telegram_digest.py` | Sends deadline alerts to Telegram |
| `../.github/workflows/telegram-digest.yml` | Runs the bot every day at 09:00 Dhaka time |

`verified: false` means the date or amount came from a third-party site. Check it on the official page before you rely on it.

## Telegram reminders: one-time setup

1. In Telegram, open **@BotFather**, send `/newbot`, and follow the prompts. Copy the **token** it gives you.
2. Send any message (for example "hi") to your new bot.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser. Find `"chat":{"id": ...}`. That number is your **chat id**.
4. On GitHub, go to the repo's **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `TELEGRAM_BOT_TOKEN` = the token
   - `TELEGRAM_CHAT_ID` = the chat id
5. Go to **Actions → Study-abroad Telegram reminders → Run workflow** to send a test digest now.

After that, the bot sends a message on days with an alert (30/14/7/3/1 days before a deadline, or overdue) and a full 60-day digest every Monday.
GitHub only runs scheduled workflows from the default branch, so merge this into `main` for the daily run to start.

Test locally without sending:

```bash
python3 study-abroad/bot/telegram_digest.py --dry-run --digest
```
