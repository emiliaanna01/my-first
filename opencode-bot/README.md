# opencode Telegram remote

Drive [opencode](https://opencode.ai) on your PC from Telegram: type or speak a
prompt, approve commands and file edits with buttons, check what changed.

## Setup (once, on the PC)
1. Install opencode and log in to your model provider:
   `npm install -g opencode-ai`, then run `opencode` once and use `/connect`.
2. For voice notes: `pip install faster-whisper` (the first voice note downloads the model).
3. Make a new bot with @BotFather, copy `.env.example` to `.env`, and fill in the token,
   your chat id and `OPENCODE_PROJECT_DIR`.
4. Double-click `start_opencode_bot.bat`. You should get "opencode remote is online".

The bot starts `opencode serve` itself (127.0.0.1 only, random password) and stops it
when you close the window. If an opencode server is already running on `OPENCODE_URL`
(default `http://127.0.0.1:4096`), it uses that one instead.

## Using it
| You send | What happens |
|---|---|
| any text | prompt to opencode; the reply lists the tools it ran, files changed and its answer |
| a voice note | transcribed, shown back to you, then handled like text |
| "stop", "status", "diff" (spoken) | runs that command |
| /new, /sessions, /use 2 | start or switch sessions |
| /stop | abort the running prompt |
| /status, /diff | what opencode is doing, which files changed |
| /agent plan, /agent build | plan = talk it through without editing; build = do the work |

When opencode wants to run a command or edit a file, you get **Allow / Always / Reject**.
Questions from opencode arrive as buttons, or you can type your own answer.

## Safety
Whoever controls `TELEGRAM_CHAT_ID` can run commands on this PC. Messages from any other
chat are ignored. opencode itself runs commands without asking by default, so sessions the
bot creates always ask first for `bash` and `edit`; each one reaches you as a button.
Change the list with `OPENCODE_ASK` in `.env` (e.g. `bash,edit,webfetch`).
