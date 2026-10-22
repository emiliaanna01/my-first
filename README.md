# Deck: a TweetDeck-style dashboard (free, website only)

One screen of side-by-side columns. It's a plain static website (HTML, CSS and JavaScript), with
no server and no paid APIs.

| Column | What it shows | Source | Cost |
|---|---|---|---|
| **Google Calendar** | Today's events, with the current one highlighted and Meet links | Google Calendar API, signed in from your browser | Free |
| **Calendar embed** | Google's agenda view | `calendar.google.com/embed` | Free, no setup |
| **Running tasks** | Tasks with start/pause timers, finish, delete, total time | Your browser (localStorage) | Free |
| **X profile** *(optional)* | One profile's timeline | X's free embed widget, no API | Free |

X's API is pay-per-read, so it isn't used. The optional X column is X's own embed widget, and X controls
what it shows: sometimes a sign-in prompt or older posts. For real-time X columns, X's own
**X Pro** (pro.x.com) is the official TweetDeck.

Add as many columns as you like with **+ Add column**. Rename and configure them with ⚙, move them with ← →, and remove them with ✕.
The layout and tasks are saved in your browser.

## Try it on your PC

Google sign-in won't work from a `file://` page, so serve the folder:

```bash
cd deck
python3 -m http.server 8080      # then open http://localhost:8080
```

## Put it on the web (free)

These are static files, so any free static host works:

- **GitHub Pages:** repo Settings → Pages → deploy from this branch. The site is then at
  `https://<user>.github.io/<repo>/deck/`.
- **Netlify Drop:** drag the `deck` folder onto https://app.netlify.com/drop.
- **Cloudflare Pages / Vercel:** connect the repo and set the root directory to `deck`. No build command is needed.

Whatever address you end up with, add it to the Google OAuth client's *Authorized JavaScript origins*
(next section). Only the origin goes there, e.g. `https://user.github.io`, without the path.

## Google Calendar setup (free, about 5 minutes)

1. https://console.cloud.google.com → create a project → **APIs & Services → Library** → enable **Google Calendar API**.
2. **OAuth consent screen**: choose External, fill in the app name, and add your Gmail as a **test user**.
3. **Credentials → Create credentials → OAuth client ID → Web application.**
   Under *Authorized JavaScript origins*, add `http://localhost:8080` and your hosted site's origin.
4. Copy the client ID (`….apps.googleusercontent.com`) into the calendar column's ⚙ settings and click **Sign in with Google**.

Access is read-only (`calendar.readonly`). The token is kept in browser memory for about an hour, and then the
column asks you to sign in again. A client ID isn't a secret, so it's fine for it to sit in a public website.
To show another calendar, put its ID in the column settings (Google Calendar → Settings → your calendar →
*Integrate calendar*).

If you don't want any setup, switch the column to **embed** mode and enter your Gmail address. It shows
Google's own agenda view while you're signed into Google in the same browser.

## Tasks

Type a task and press Enter. ▶ starts the timer and ❚❚ pauses it. More than one task can run at the same time.
✓ finishes a task and ↺ reopens it. Timers keep counting across reloads.
Tasks stay in the browser you use, so a different device or browser starts empty.

## Files
- `index.html`, `style.css`: the page and the column template
- `app.js`: column types (Calendar, Tasks, X embed) and the deck layout
