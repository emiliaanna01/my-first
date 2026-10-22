# Deck: a TweetDeck-style dashboard

One screen of side-by-side columns. Each column is one feed:

| Column | What it shows | Data source | Cost |
|---|---|---|---|
| **X / Twitter** | Search, a user's posts, a list, your home timeline, your bookmarks | X API v2 through `server.js` | Paid, per post read (see below) |
| **X embed** | A profile's timeline | X's own embed widget | Free, but X may show a sign-in prompt or older posts |
| **Google Calendar** | Today's events, with the current one highlighted | Google Calendar API, signed in from your browser | Free |
| **Calendar embed** | Google's agenda view in an iframe | `calendar.google.com/embed` | Free, no setup |
| **Running tasks** | Tasks with start/pause timers, finish, delete | Saved in your browser | Free |

You can add as many columns as you like, and rename, reorder and remove them. The layout is saved in your browser.

## Run it

```bash
cd deck
node server.js              # Node 18+, no npm install needed
# open http://localhost:8080
```

The tasks and calendar-embed columns work right away. The other two need the keys below.

## X / Twitter API: the honest picture (October 2026)

- **There's no useful free tier anymore.** Since February 2026, X API access is **pay-per-use** by default.
  Third-party trackers put reads at about **$0.005 per post** returned, and you top up credits in the
  X Developer Console. The old $200/month Basic and Pro plans have been moved over to pay-per-use.
  X changes these terms often, so check the current prices in the console.
- **What that means for a live column:** fetching 10 posts a minute all day is about 14,000 reads, or
  roughly **$70 a day**. That's why `server.js`:
  - caches each feed for `X_MIN_POLL_SEC` (default **300 s**), so 5 browser tabs don't cost 5×;
  - asks only for posts newer than the last one it has (`since_id`), so you pay just for new posts;
  - stops calling X once it has read `X_DAILY_READ_CAP` posts today (default **500**, about $2.50 a day at most).
- **The free option:** set a column's source to *Embedded profile*. It uses X's own widget with no API and no
  cost, but X may show a login wall or a stale feed.
- **The official option:** TweetDeck still exists as **X Pro** (pro.x.com). It's included with X Premium
  (paid monthly) and gives real-time columns with no developer work.

### Setup
1. Go to https://developer.x.com, create a project and an app, and add credits.
2. Copy the app's **Bearer Token**. This covers search, user posts and lists.
3. *(Optional)* For **home timeline** and **bookmarks** you need an OAuth 2.0 **user** access token with
   the scopes `tweet.read users.read bookmark.read`. Generate one with the PKCE flow on the app's
   "Keys and tokens" page or with any OAuth 2.0 tool. These tokens expire after 2 hours unless you
   also request `offline.access` and refresh them.
4. Start the server:
   ```bash
   X_BEARER_TOKEN=xxxx X_USER_TOKEN=yyyy X_MIN_POLL_SEC=300 X_DAILY_READ_CAP=500 node server.js
   ```
   The tokens stay on the server and never reach the browser.

Search query examples: `PLC OR SCADA -is:retweet lang:en`, `from:elonmusk`, `#automation has:media`.

## Google Calendar: free (about 5 minutes)

1. https://console.cloud.google.com → create a project → **APIs & Services → Library** → enable **Google Calendar API**.
2. **OAuth consent screen**: choose External, fill in the app name, and add yourself as a **test user**.
3. **Credentials → Create credentials → OAuth client ID → Web application.**
   Under *Authorized JavaScript origins*, add `http://localhost:8080`, plus your real domain if you host it.
4. Copy the client ID (`….apps.googleusercontent.com`) into the calendar column's ⚙ settings and click **Sign in with Google**.

Access is read-only (`calendar.readonly`). The token lives in browser memory for about an hour, and then the
column asks you to sign in again. To see a different calendar, put its ID in the column settings
(Google Calendar → Settings → your calendar → *Integrate calendar*).

If you don't want any setup, switch the column to **embed** mode and enter your Gmail address. It shows
Google's own agenda view, as long as you're signed into Google in the same browser.

## Tasks

Type a task and press Enter. ▶ starts the timer and ❚❚ pauses it. More than one task can run at the same time.
✓ finishes a task and ↺ reopens it. Timers keep counting across reloads because the start time is saved.
Tasks are stored in this browser only (localStorage). To sync them across devices, the next step would be a
small database on the server.

## Hosting

- **Your own PC only:** `node server.js`. You can also run it on startup with Task Scheduler, a systemd service or pm2.
- **On the web:** any Node host works (Render, Railway, Fly.io, a VPS). Set the env vars there and add the
  site's URL to the Google OAuth origins. Put it behind a login, because anyone who can open the page can
  spend your X credits.
- **As a desktop app:** the same files can go inside Electron or Tauri if you want a window instead of a browser tab.

## Files
- `index.html`, `style.css`: the page and the column template
- `app.js`: column types (X, Calendar, Tasks) and the deck layout
- `server.js`: static server plus the X API proxy with caching and the daily cap
