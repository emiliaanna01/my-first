"""Telegram remote for opencode: drive the coding agent on your PC from your phone.

Send any message, or a voice note, and it goes to opencode as a prompt; the answer comes back
with the tools it ran and the files it changed. When opencode wants to run a
command or edit a file, you get Allow / Always / Reject buttons. When it asks
a question, you get its options as buttons (or type your own answer).

How it runs (on your PC):
  1. If no opencode server answers on OPENCODE_URL, the bot starts
     `opencode serve` in OPENCODE_PROJECT_DIR, locked with a random password,
     listening on 127.0.0.1 only. Closing the bot stops it.
  2. The bot long-polls Telegram, so no port is opened to the internet.

Only messages from TELEGRAM_CHAT_ID get an answer; everyone else is ignored.
That matters: whoever controls this chat can run commands on your PC.

Voice notes are transcribed on your PC with faster-whisper (pip install
faster-whisper). The first one downloads the model, then it works offline.

Keys live in opencode-bot/.env (KEY=value per line, git-ignored).
Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID; see .env.example for the rest.
"""

import atexit
import base64
import html
import json
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent

ENV_FILE = HERE / ".env"
if ENV_FILE.exists():
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, sep, value = raw.strip().partition("=")
        if sep and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip('"'))

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", ""))
OC_URL = os.environ.get("OPENCODE_URL", "http://127.0.0.1:4096").rstrip("/")
PROJECT_DIR = os.environ.get("OPENCODE_PROJECT_DIR", "")
OC_USER = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
OC_PASSWORD = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
MODEL = os.environ.get("OPENCODE_MODEL", "")  # e.g. anthropic/claude-sonnet-4-5; empty = opencode's default
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")  # tiny, base, small, medium, large-v3: bigger is slower and better
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "") or None  # e.g. en; empty = detect per message

# Sessions made here always ask before these tools, whatever opencode's own config allows.
ASK_FIRST = [t.strip() for t in os.environ.get("OPENCODE_ASK", "bash,edit").split(",") if t.strip()]
STATE_FILE = HERE / ".state.json"  # remembers the current session and agent across restarts
WATCH_SECONDS = 2

COMMANDS = [
    ("new", "Start a fresh opencode session"),
    ("sessions", "List recent sessions"),
    ("use", "Switch session: /use 2"),
    ("stop", "Abort the running prompt"),
    ("status", "What opencode is doing now"),
    ("diff", "Files changed in the project"),
    ("agent", "Switch agent: /agent plan or /agent build"),
    ("help", "Show this menu"),
]
KEYBOARD = {
    "keyboard": [["/status", "/diff", "/stop"], ["/new", "/sessions", "/help"]],
    "resize_keyboard": True,
    "is_persistent": True,
}

state = {"session": None, "agent": "build", "listed": []}
busy = threading.Event()
announced = set()   # permission / question ids already sent to Telegram
questions = {}      # question id -> {"req": request, "answers": [...], "msg": telegram message id}
lock = threading.Lock()
voice_lock = threading.Lock()  # one transcription at a time; also guards loading the model
whisper = None


# ---------- Telegram ----------

def api(method, **params):
    data = urllib.parse.urlencode({k: json.dumps(v) if isinstance(v, (dict, list)) else v
                                   for k, v in params.items()}).encode()
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    with urllib.request.urlopen(url, data=data, timeout=70) as resp:
        body = json.load(resp)
    if not body.get("ok"):
        raise RuntimeError(f"{method} failed: {body}")
    return body["result"]


def reply(text, buttons=None):
    """Send HTML text, split into Telegram-sized pieces. Buttons go on the last piece."""
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or ["(empty)"]
    sent = None
    for n, chunk in enumerate(chunks):
        markup = {"inline_keyboard": buttons} if buttons and n == len(chunks) - 1 else KEYBOARD
        try:
            sent = api("sendMessage", chat_id=CHAT_ID, text=chunk, parse_mode="HTML",
                       disable_web_page_preview="true", reply_markup=markup)
        except (RuntimeError, urllib.error.HTTPError):
            # A cut through an HTML tag makes Telegram refuse the piece; send it plain instead.
            sent = api("sendMessage", chat_id=CHAT_ID, text=chunk, reply_markup=markup)
    return sent


def esc(text):
    return html.escape(str(text), quote=False)


# ---------- opencode server ----------

def oc(method, path, body=None, timeout=60, **query):
    if PROJECT_DIR:
        query.setdefault("directory", PROJECT_DIR)
    url = OC_URL + path + ("?" + urllib.parse.urlencode(query) if query else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if OC_PASSWORD:
        token = base64.b64encode(f"{OC_USER}:{OC_PASSWORD}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"opencode {method} {path}: {err.code} {err.read()[:300].decode(errors='replace')}")
    return json.loads(raw) if raw else None


def server_up():
    try:
        oc("GET", "/session", timeout=3, limit=1)
        return True
    except (OSError, RuntimeError):
        return False


def start_server():
    """Start `opencode serve` on 127.0.0.1 with a fresh password unless one is already running."""
    global OC_PASSWORD
    if server_up():
        print(f"using the opencode server already running at {OC_URL}")
        return
    exe = shutil.which("opencode")
    if not exe:
        raise SystemExit("opencode isn't on PATH. Install it: npm install -g opencode-ai")
    port = urllib.parse.urlparse(OC_URL).port or 4096
    OC_PASSWORD = OC_PASSWORD or secrets.token_urlsafe(24)
    env = dict(os.environ, OPENCODE_SERVER_PASSWORD=OC_PASSWORD, OPENCODE_SERVER_USERNAME=OC_USER)
    cwd = PROJECT_DIR or None
    print(f"starting opencode serve on port {port} in {cwd or os.getcwd()}")
    proc = subprocess.Popen([exe, "serve", "--hostname", "127.0.0.1", "--port", str(port)], cwd=cwd, env=env)
    atexit.register(proc.terminate)
    for _ in range(60):
        if proc.poll() is not None:
            raise SystemExit("opencode serve stopped right away; run it by hand to see why.")
        if server_up():
            return
        time.sleep(1)
    raise SystemExit("opencode serve didn't answer within 60 seconds.")


def load_state():
    if STATE_FILE.exists():
        state.update(json.loads(STATE_FILE.read_text(encoding="utf-8")))


def save_state():
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def new_session(title):
    rules = [{"permission": t, "pattern": "*", "action": "ask"} for t in ASK_FIRST]
    sess = oc("POST", "/session", {"title": title, "permission": rules})
    state["session"] = sess["id"]
    save_state()
    return sess


def current_session():
    if state["session"]:
        try:
            oc("GET", f"/session/{state['session']}")
            return state["session"]
        except RuntimeError:
            pass  # deleted or from another project; start a new one
    return new_session("Telegram")["id"]


# ---------- prompts ----------

def tool_line(part):
    st = part.get("state", {})
    inp = st.get("input") or {}
    what = st.get("title") or inp.get("command") or inp.get("filePath") or inp.get("pattern") or ""
    mark = {"completed": "✓", "error": "✗"}.get(st.get("status"), "…")
    line = f"{mark} <b>{esc(part['tool'])}</b> {esc(what)[:120]}"
    if st.get("status") == "error":
        line += f"\n   {esc(st.get('error', ''))[:200]}"
    return line


def format_result(res):
    info, parts = res.get("info", {}), res.get("parts", [])
    text = "\n\n".join(p["text"] for p in parts if p.get("type") == "text" and p.get("text"))
    tools = [tool_line(p) for p in parts if p.get("type") == "tool"]
    files = sorted({f for p in parts if p.get("type") == "patch" for f in p.get("files", [])})
    out = []
    if tools:
        out.append("🔧 " + "\n".join(tools[-15:]) + (f"\n…{len(tools) - 15} earlier" if len(tools) > 15 else ""))
    if files:
        out.append("📝 <b>Changed</b>\n" + "\n".join(f"• {esc(f)}" for f in files[:20]))
    if text:
        out.append(esc(text))
    err = info.get("error")
    if err:
        msg = (err.get("data") or {}).get("message") or err.get("name", "unknown error")
        out.append(f"⚠️ {esc(msg)[:500]}")
    return "\n\n".join(out) or "Done (no text reply)."


def run_prompt(text):
    try:
        sid = current_session()
        body = {"parts": [{"type": "text", "text": text}], "agent": state["agent"]}
        if MODEL:
            provider, _, model = MODEL.partition("/")
            body["model"] = {"providerID": provider, "modelID": model}
        # Blocks until opencode finishes, which can take many minutes on a big task.
        res = oc("POST", f"/session/{sid}/message", body, timeout=4 * 3600)
        # The answer holds only the last step; gather every step of this turn for the tool list.
        turn = [m for m in oc("GET", f"/session/{sid}/message", limit=100)
                if m["info"].get("role") == "assistant" and m["info"].get("parentID") == res["info"].get("parentID")]
        parts = [p for m in turn for p in m["parts"]] or res.get("parts", [])
        reply(format_result({"info": res["info"], "parts": parts}))
    except Exception as err:  # keep the bot alive whatever opencode does
        reply(f"⚠️ {esc(err)[:800]}")
    finally:
        busy.clear()


# ---------- permissions and questions (polled while the bot runs) ----------

def announce_permission(p):
    what = ", ".join(p.get("patterns") or []) or json.dumps(p.get("metadata", {}))[:300]
    pid = p["id"]
    reply(f"🔐 opencode wants <b>{esc(p['permission'])}</b>\n<code>{esc(what)[:1500]}</code>",
          buttons=[[{"text": "✅ Allow", "callback_data": f"p:{pid}:once"},
                    {"text": "♾ Always", "callback_data": f"p:{pid}:always"},
                    {"text": "⛔ Reject", "callback_data": f"p:{pid}:reject"}]])


def ask_next_question(qid):
    q = questions[qid]
    i = len(q["answers"])
    info = q["req"]["questions"][i]
    opts = "\n".join(f"• <b>{esc(o['label'])}</b>: {esc(o.get('description', ''))}" for o in info["options"])
    rows = [[{"text": o["label"][:60], "callback_data": f"q:{qid}:{k}"}] for k, o in enumerate(info["options"])]
    rows.append([{"text": "⛔ Skip question", "callback_data": f"q:{qid}:x"}])
    reply(f"❓ <b>{esc(info['header'])}</b>\n{esc(info['question'])}\n{opts}\n<i>Tap an option or type your own answer.</i>",
          buttons=rows)


def answer_question(qid, answer):
    """Record one answer; send them all to opencode once every question has one."""
    q = questions[qid]
    q["answers"].append(answer)
    if len(q["answers"]) < len(q["req"]["questions"]):
        ask_next_question(qid)
        return "Next question…"
    del questions[qid]
    oc("POST", f"/question/{qid}/reply", {"answers": q["answers"]})
    return "Answer sent."


def watch():
    last_typing = 0
    while True:
        try:
            for p in oc("GET", "/permission", timeout=10):
                if p["id"] not in announced:
                    announced.add(p["id"])
                    announce_permission(p)
            for q in oc("GET", "/question", timeout=10):
                if q["id"] not in announced:
                    announced.add(q["id"])
                    with lock:
                        questions[q["id"]] = {"req": q, "answers": []}
                    ask_next_question(q["id"])
            if busy.is_set() and time.time() - last_typing > 5:
                api("sendChatAction", chat_id=CHAT_ID, action="typing")
                last_typing = time.time()
        except Exception as err:
            print(f"watch: {err}")
        time.sleep(WATCH_SECONDS)


def handle_button(cb):
    if str(cb.get("message", {}).get("chat", {}).get("id")) != CHAT_ID:
        return
    kind, rid, choice = (cb.get("data") or "::").split(":", 2)
    note = "Done."
    try:
        if kind == "p":
            oc("POST", f"/permission/{rid}/reply", {"reply": choice})
            note = {"once": "✅ Allowed once", "always": "♾ Allowed always", "reject": "⛔ Rejected"}[choice]
        elif kind == "q":
            with lock:
                if rid not in questions:
                    note = "That question is already closed."
                elif choice == "x":
                    del questions[rid]
                    oc("POST", f"/question/{rid}/reject")
                    note = "⛔ Question skipped"
                else:
                    info = questions[rid]["req"]["questions"][len(questions[rid]["answers"])]
                    label = info["options"][int(choice)]["label"]
                    note = f"✅ {label}. " + answer_question(rid, [label])
    except Exception as err:
        note = f"⚠️ {err}"[:190]
    api("answerCallbackQuery", callback_query_id=cb["id"], text=note[:190])
    msg = cb["message"]
    try:  # swap the buttons for what was chosen, so nobody taps twice
        api("editMessageText", chat_id=CHAT_ID, message_id=msg["message_id"],
            text=(msg.get("text") or "")[:3800] + f"\n\n→ {note}")
    except Exception:
        pass


# ---------- voice notes ----------

def transcribe(path):
    global whisper
    if whisper is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError("Voice needs faster-whisper on this PC: pip install faster-whisper")
        print(f"loading whisper model {WHISPER_MODEL} (first time downloads it)")
        whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = whisper.transcribe(str(path), language=WHISPER_LANGUAGE, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()


def run_voice(file_id):
    try:
        api("sendChatAction", chat_id=CHAT_ID, action="typing")
        file_path = api("getFile", file_id=file_id)["file_path"]
        with tempfile.TemporaryDirectory() as tmp:
            audio = pathlib.Path(tmp) / pathlib.Path(file_path).name
            urllib.request.urlretrieve(f"https://api.telegram.org/file/bot{TOKEN}/{file_path}", audio)
            with voice_lock:
                text = transcribe(audio)
    except Exception as err:
        reply(f"⚠️ Couldn't transcribe that: {esc(err)[:500]}")
        return
    if not text:
        reply("🎙 I couldn't hear any words in that one.")
        return
    reply(f"🎙 <i>{esc(text)}</i>")
    handle_text(spoken_command(text) or text)


def spoken_command(text):
    """Turn a short voice note like "stop", "status" or "slash new session" into its command."""
    words = re.sub(r"[^\w\s]", " ", text.lower()).split()
    if words[:1] == ["slash"]:
        words = words[1:]
    if not words or len(words) > 3 or words[0] not in {c for c, _ in COMMANDS}:
        return None
    if words[0] == "new" and words[1:] == ["session"]:
        words = ["new"]
    return "/" + " ".join(words)


# ---------- commands ----------

def cmd_new(arg):
    sess = new_session(arg or "Telegram")
    return f"🆕 New session <b>{esc(sess.get('title', ''))}</b>. Send your first prompt."


def cmd_sessions(_):
    rows = [s for s in oc("GET", "/session", roots="true", limit=8) if not s.get("parentID")][:8]
    state["listed"] = [s["id"] for s in rows]
    save_state()
    lines = []
    for n, s in enumerate(rows, 1):
        mark = "👉 " if s["id"] == state["session"] else ""
        when = time.strftime("%d %b %H:%M", time.localtime(s["time"]["updated"] / 1000))
        lines.append(f"{n}. {mark}<b>{esc(s.get('title', s['id']))}</b> · {when}")
    return "🗂 <b>Recent sessions</b>\n" + ("\n".join(lines) or "None yet.") + "\n\nSwitch with /use 2"


def cmd_use(arg):
    if not arg.isdigit() or not 1 <= int(arg) <= len(state["listed"]):
        return "Run /sessions first, then /use with a number from that list."
    state["session"] = state["listed"][int(arg) - 1]
    save_state()
    s = oc("GET", f"/session/{state['session']}")
    return f"👉 Now on <b>{esc(s.get('title', s['id']))}</b>."


def cmd_stop(_):
    if not state["session"]:
        return "No session yet."
    oc("POST", f"/session/{state['session']}/abort")
    return "🛑 Abort sent."


def cmd_status(_):
    status = oc("GET", "/session/status")
    mine = status.get(state["session"] or "", {}).get("type", "idle")
    title = oc("GET", f"/session/{state['session']}").get("title", "") if state["session"] else "(none yet)"
    pending = len(oc("GET", "/permission")) + len(oc("GET", "/question"))
    return (f"📡 Session <b>{esc(title)}</b>: {mine}\nAgent: {state['agent']} · Model: {esc(MODEL or 'opencode default')}\n"
            f"Waiting on you: {pending}\nProject: {esc(PROJECT_DIR or 'where opencode was started')}")


def cmd_diff(_):
    files = oc("GET", "/file/status")
    if not files:
        return "No changed files."
    icon = {"added": "🟢", "deleted": "🔴", "modified": "🟡"}
    lines = [f"{icon.get(f['status'], '•')} {esc(f['path'])} <i>+{f['added']} −{f['removed']}</i>" for f in files[:30]]
    more = f"\n…and {len(files) - 30} more" if len(files) > 30 else ""
    return "📝 <b>Changed files</b>\n" + "\n".join(lines) + more


def cmd_agent(arg):
    names = [a["name"] for a in oc("GET", "/agent") if a.get("mode") != "subagent" and not a.get("hidden")]
    if arg not in names:
        return f"Agent is <b>{state['agent']}</b>. Choose one of: {', '.join(names)}\nExample: /agent plan"
    state["agent"] = arg
    save_state()
    return f"🤖 Agent set to <b>{arg}</b>."


def cmd_help(_):
    return ("🧑‍💻 <b>opencode remote</b>\nSend any message to prompt opencode.\n"
            + "\n".join(f"/{c} — {d}" for c, d in COMMANDS)
            + "\n\n🎙 Voice notes work too. Say just \"stop\", \"status\" or \"diff\" to run that command.")


HANDLERS = {f"/{c}": globals()[f"cmd_{c}"] for c, _ in COMMANDS}
HANDLERS["/start"] = cmd_help


def handle(update):
    if "callback_query" in update:
        handle_button(update["callback_query"])
        return
    msg = update.get("message") or {}
    if str(msg.get("chat", {}).get("id")) != CHAT_ID:
        print("ignored a message from a chat that isn't TELEGRAM_CHAT_ID")
        return
    voice = msg.get("voice") or msg.get("audio")
    if voice:
        print("transcribing a voice note")
        threading.Thread(target=run_voice, args=(voice["file_id"],), daemon=True).start()
        return
    text = (msg.get("text") or "").strip()
    if text:
        handle_text(text)


def handle_text(text):
    """A typed or transcribed message: a command, an answer to an open question, or a prompt."""
    if text.startswith("/"):
        word, _, arg = text.partition(" ")
        fn = HANDLERS.get(word.split("@")[0].lower(), cmd_help)
        print(f"answering {word}")
        try:
            reply(fn(arg.strip()))
        except Exception as err:
            reply(f"⚠️ {esc(err)[:800]}")
        return
    with lock:  # a typed reply answers an open question before anything else
        open_q = next(iter(questions), None)
        if open_q:
            try:
                reply("✅ " + answer_question(open_q, [text]))
            except Exception as err:
                reply(f"⚠️ {esc(err)[:800]}")
            return
    with lock:  # voice notes arrive on their own thread, so check and claim together
        if busy.is_set():
            reply("⏳ Still working on the last prompt. Wait for it, or /stop it.")
            return
        busy.set()
    print("sending a prompt to opencode")
    threading.Thread(target=run_prompt, args=(text,), daemon=True).start()


def main():
    if not TOKEN or not CHAT_ID:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in opencode-bot/.env first.")
    load_state()
    start_server()
    api("setMyCommands", commands=[{"command": c, "description": d} for c, d in COMMANDS])
    hook = api("getWebhookInfo").get("url")
    if hook:
        raise SystemExit(f"This bot has a webhook set ({hook}); remove it to use polling.")
    threading.Thread(target=watch, daemon=True).start()  # also sends permissions already waiting
    reply("🟢 opencode remote is online. Send a prompt, or /help.")
    print("listening; press Ctrl+C to stop")
    offset = None
    while True:
        try:
            updates = api("getUpdates", offset=offset, timeout=50,
                          allowed_updates=["message", "callback_query"])
            for u in updates:
                offset = u["update_id"] + 1
                handle(u)
        except KeyboardInterrupt:
            break
        except Exception as err:  # network blips: wait and keep going
            print(f"poll error: {err}")
            time.sleep(5)


if __name__ == "__main__":
    main()
