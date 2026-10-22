// Deck: TweetDeck-style columns. Each column type is a small module with
// defaults(), settings(col) -> form HTML, and render(col, el) which may return a cleanup fn.
// Static site, no server and no paid APIs: layout, settings and tasks live in
// localStorage; the only outside calls are X's embed widget and Google, with your own sign-in.

const STORE = "deck.columns.v1";
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const uid = () => Math.random().toString(36).slice(2, 10);

function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function save(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); } catch { /* private mode: run without saving */ }
}

const hms = (ms) => {
  const t = Math.floor(ms / 1000);
  return [Math.floor(t / 3600), Math.floor(t / 60) % 60, t % 60].map((n) => String(n).padStart(2, "0")).join(":");
};

/* ---------------- X / Twitter (free embed, no API) ---------------- */

// X's API is pay-per-read, so this column uses X's own free timeline widget instead.
// X decides what the widget shows: sometimes a sign-in prompt or older posts.
const X = {
  icon: "𝕏",
  defaults: () => ({ title: "X", query: "" }),
  title: (c) => c.title,
  settings: (c) => `
    <label>@username <input name="query" value="${esc(c.query)}" placeholder="@username"></label>
    <p class="hint">Free embed widget, no API key. If it stays blank, sign in to x.com in this browser.</p>`,
  render(c, body, status) {
    const user = (c.query || "").replace(/^@/, "").replace(/[^A-Za-z0-9_]/g, "");
    if (!user) { body.innerHTML = `<div class="empty">Set a @username in ⚙.</div>`; return; }
    const draw = () => {
      body.innerHTML = `<a class="twitter-timeline" data-theme="dark" data-dnt="true" data-chrome="noheader nofooter transparent" href="https://twitter.com/${user}">Posts by @${user}</a>
        <div class="empty"><a href="https://x.com/${user}" target="_blank" rel="noopener">Open @${esc(user)} on x.com</a></div>`;
      if (window.twttr?.widgets) window.twttr.widgets.load(body);
      else if (!$("#twttr-js")) {
        const s = Object.assign(document.createElement("script"), { id: "twttr-js", src: "https://platform.twitter.com/widgets.js", async: true });
        s.onload = () => window.twttr?.widgets?.load(body);
        document.head.append(s);
      } else $("#twttr-js").addEventListener("load", () => window.twttr?.widgets?.load(body));
    };
    draw();
    return { refresh: draw };
  },
};

/* ---------------- Google Calendar ---------------- */

// One Google token shared by all calendar columns (read-only scope, held in memory only).
const google = { token: null, exp: 0, client: null, waiting: [] };

function googleToken(clientId, interactive) {
  if (google.token && Date.now() < google.exp) return Promise.resolve(google.token);
  if (!interactive) return Promise.reject(new Error("Google sign-in expired — sign in again"));
  if (!window.google?.accounts?.oauth2) return Promise.reject(new Error("Google sign-in script not loaded yet — try again in a second"));
  return new Promise((resolve, reject) => {
    if (!google.client || google.client.clientId !== clientId) {
      google.client = window.google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: "https://www.googleapis.com/auth/calendar.readonly",
        callback: (r) => {
          const w = google.waiting.splice(0);
          if (r.error) return w.forEach((p) => p.reject(new Error(r.error)));
          google.token = r.access_token;
          google.exp = Date.now() + (r.expires_in - 60) * 1000;
          w.forEach((p) => p.resolve(google.token));
        },
      });
      google.client.clientId = clientId;
    }
    google.waiting.push({ resolve, reject });
    google.client.requestAccessToken({ prompt: "" });
  });
}

function loadGis() {
  if ($("#gis-js")) return;
  document.head.append(Object.assign(document.createElement("script"), { id: "gis-js", src: "https://accounts.google.com/gsi/client", async: true }));
}

const CAL = {
  icon: "📅",
  defaults: () => ({ title: "Today", mode: "api", clientId: "", calendarId: "primary", embedSrc: "" }),
  title: (c) => c.title,
  settings: (c) => `
    <label>Mode
      <select name="mode">
        <option value="api" ${c.mode === "api" ? "selected" : ""}>Live list via Calendar API (free)</option>
        <option value="embed" ${c.mode === "embed" ? "selected" : ""}>Google's embedded agenda (no setup)</option>
      </select>
    </label>
    <label>OAuth client ID (API mode) <input name="clientId" value="${esc(c.clientId)}" placeholder="xxxx.apps.googleusercontent.com"></label>
    <label>Calendar ID (API mode) <input name="calendarId" value="${esc(c.calendarId)}"></label>
    <label>Calendar email / ID (embed mode) <input name="embedSrc" value="${esc(c.embedSrc)}" placeholder="you@gmail.com"></label>
    <p class="hint">See deck/README.md for the 5-minute Google Cloud setup.</p>`,
  render(c, body, status) {
    if (c.mode === "embed") {
      if (!c.embedSrc) { body.innerHTML = `<div class="empty">Put your calendar email in ⚙.</div>`; return; }
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      body.innerHTML = `<iframe class="cal-frame" src="https://calendar.google.com/calendar/embed?src=${encodeURIComponent(c.embedSrc)}&mode=AGENDA&ctz=${encodeURIComponent(tz)}&showTitle=0&showPrint=0&showTabs=0&showCalendars=0"></iframe>`;
      return;
    }
    if (!c.clientId) { body.innerHTML = `<div class="empty">Add your Google OAuth client ID in ⚙, or switch to embed mode.</div>`; return; }
    loadGis();
    let events = [];

    const draw = () => {
      if (!events.length) { body.innerHTML = `<div class="empty">Nothing on the calendar today.</div>`; return; }
      const now = Date.now();
      body.innerHTML = events.map((e) => {
        const allDay = !e.start.dateTime;
        const s = new Date(e.start.dateTime || e.start.date), en = new Date(e.end.dateTime || e.end.date);
        const cls = allDay ? "" : now >= s && now < en ? "now" : now >= en ? "past" : "";
        const fmt = (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        return `<div class="card ev ${cls}">
          <time>${allDay ? "All day" : `${fmt(s)}<br>${fmt(en)}`}</time>
          <div><div class="ev-title">${esc(e.summary || "(no title)")}</div>
          ${e.location ? `<div class="ev-where">${esc(e.location)}</div>` : ""}
          ${e.hangoutLink ? `<div class="ev-where"><a href="${esc(e.hangoutLink)}" target="_blank" rel="noopener">Join Meet</a></div>` : ""}</div>
        </div>`;
      }).join("");
    };

    const fetchEvents = async (interactive) => {
      try {
        const token = await googleToken(c.clientId, interactive);
        const start = new Date(); start.setHours(0, 0, 0, 0);
        const end = new Date(start); end.setDate(end.getDate() + 1);
        const q = new URLSearchParams({ timeMin: start.toISOString(), timeMax: end.toISOString(), singleEvents: "true", orderBy: "startTime", maxResults: "50" });
        const r = await fetch(`https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(c.calendarId || "primary")}/events?${q}`, { headers: { Authorization: `Bearer ${token}` } });
        const d = await r.json();
        if (!r.ok) {
          if (r.status === 401) google.token = null;
          throw new Error(d.error?.message || r.statusText);
        }
        events = d.items || [];
        status(`Updated ${new Date().toLocaleTimeString()}`);
        draw();
      } catch (e) {
        status(e.message, true);
        body.innerHTML = `<div class="empty"><button class="signin">Sign in with Google</button></div>`;
        $(".signin", body).onclick = () => fetchEvents(true);
      }
    };

    // Google's sign-in popup needs a click, so start with a button unless we already hold a token.
    const signIn = () => {
      body.innerHTML = `<div class="empty"><button class="signin">Sign in with Google</button></div>`;
      $(".signin", body).onclick = () => fetchEvents(true);
    };
    if (google.token && Date.now() < google.exp) fetchEvents(false);
    else signIn();
    const poll = setInterval(() => google.token && fetchEvents(false), 5 * 60 * 1000);
    const redraw = setInterval(() => events.length && draw(), 60 * 1000); // move the "now" highlight along
    return { stop: () => [poll, redraw].forEach(clearInterval), refresh: () => (google.token ? fetchEvents(false) : signIn()) };
  },
};

/* ---------------- Running tasks ---------------- */

const TASKS = {
  icon: "✓",
  defaults: () => ({ title: "Running tasks", hideDone: false }),
  title: (c) => c.title,
  settings: (c) => `<label><span><input type="checkbox" name="hideDone" ${c.hideDone ? "checked" : ""} style="width:auto"> Hide finished tasks</span></label>`,
  render(c, body, status) {
    const key = `deck.tasks.${c.id}`;
    let tasks = load(key, []);
    const persist = () => save(key, tasks);
    const elapsed = (t) => t.elapsedMs + (t.runningSince ? Date.now() - t.runningSince : 0);

    const draw = () => {
      const list = c.hideDone ? tasks.filter((t) => !t.done) : tasks;
      const total = tasks.reduce((n, t) => n + elapsed(t), 0);
      body.innerHTML = `
        <form class="task-add"><input name="text" placeholder="Add a task and press Enter" autocomplete="off"><button>Add</button></form>
        ${list.length ? "" : `<div class="empty">No tasks.</div>`}
        ${list.map((t) => `
          <div class="card task ${t.runningSince ? "running" : ""} ${t.done ? "done" : ""}" data-id="${t.id}">
            <button data-t="toggle" title="${t.runningSince ? "Pause" : "Start"}" ${t.done ? "disabled" : ""}>${t.runningSince ? "❚❚" : "▶"}</button>
            <span class="t-text">${esc(t.text)}</span>
            <span class="t-time">${hms(elapsed(t))}</span>
            <button data-t="done" title="${t.done ? "Reopen" : "Finish"}">${t.done ? "↺" : "✓"}</button>
            <button data-t="del" title="Delete">✕</button>
          </div>`).join("")}
        <div class="task-total">Total time ${hms(total)} · ${tasks.filter((t) => t.runningSince).length} running</div>`;
      const input = $("input", body);
      $("form", body).onsubmit = (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        tasks.unshift({ id: uid(), text, done: false, elapsedMs: 0, runningSince: null, created: Date.now() });
        persist(); draw();
        $("input", body).focus();
      };
    };

    body.onclick = (e) => {
      const btn = e.target.closest("button[data-t]");
      if (!btn) return;
      const t = tasks.find((x) => x.id === btn.closest(".task").dataset.id);
      if (btn.dataset.t === "toggle") {
        if (t.runningSince) { t.elapsedMs += Date.now() - t.runningSince; t.runningSince = null; }
        else t.runningSince = Date.now();
      } else if (btn.dataset.t === "done") {
        if (t.runningSince) { t.elapsedMs += Date.now() - t.runningSince; t.runningSince = null; }
        t.done = !t.done;
      } else if (btn.dataset.t === "del") {
        tasks = tasks.filter((x) => x !== t);
      }
      persist(); draw();
    };

    draw();
    // Tick only the timer text so typing in the input isn't interrupted.
    const tick = setInterval(() => {
      body.querySelectorAll(".task.running").forEach((row) => {
        const t = tasks.find((x) => x.id === row.dataset.id);
        if (t) $(".t-time", row).textContent = hms(elapsed(t));
      });
      const total = tasks.reduce((n, t) => n + elapsed(t), 0);
      const tot = $(".task-total", body);
      if (tot) tot.textContent = `Total time ${hms(total)} · ${tasks.filter((t) => t.runningSince).length} running`;
    }, 1000);
    return { stop: () => clearInterval(tick), refresh: draw, destroy: () => { try { localStorage.removeItem(key); } catch {} } };
  },
};

/* ---------------- Deck ---------------- */

const TYPES = { x: X, calendar: CAL, tasks: TASKS };
let columns = load(STORE, null) || [
  { id: uid(), type: "calendar", ...CAL.defaults() },
  { id: uid(), type: "tasks", ...TASKS.defaults() },
];
save(STORE, columns); // pin default column ids so per-column data (tasks) survives reloads
const live = new Map(); // column id -> { stop, refresh, destroy }

function mount(c) {
  const T = TYPES[c.type];
  const el = $("#colTpl").content.firstElementChild.cloneNode(true);
  el.dataset.id = c.id;
  $(".col-icon", el).textContent = T.icon;
  $(".col-title", el).textContent = T.title(c);
  const statusEl = $(".col-status", el);
  const status = (msg, err) => { statusEl.textContent = msg; statusEl.classList.toggle("err", !!err); };

  const form = $(".col-settings", el);
  form.innerHTML = `<label>Column title <input name="title" value="${esc(c.title)}"></label>${T.settings(c)}<button>Save</button>`;
  form.onsubmit = (e) => {
    e.preventDefault();
    const f = new FormData(form);
    for (const input of form.elements) {
      if (!input.name) continue;
      c[input.name] = input.type === "checkbox" ? input.checked : input.type === "number" ? Number(f.get(input.name)) : String(f.get(input.name)).trim();
    }
    save(STORE, columns);
    renderAll();
  };

  el.querySelector(".col-tools").onclick = (e) => {
    const act = e.target.closest("button")?.dataset.act;
    const i = columns.indexOf(c);
    if (act === "refresh") live.get(c.id)?.refresh?.();
    if (act === "settings") form.hidden = !form.hidden;
    if (act === "left" && i > 0) [columns[i - 1], columns[i]] = [columns[i], columns[i - 1]];
    if (act === "right" && i < columns.length - 1) [columns[i + 1], columns[i]] = [columns[i], columns[i + 1]];
    if (act === "remove") {
      if (!confirm(`Remove "${c.title}"?`)) return;
      live.get(c.id)?.destroy?.();
      columns.splice(i, 1);
    }
    if (act === "left" || act === "right" || act === "remove") { save(STORE, columns); renderAll(); }
  };

  $("#deck").append(el);
  live.set(c.id, T.render(c, $(".col-body", el), status) || {});
}

function renderAll() {
  live.forEach((h) => h.stop?.());
  live.clear();
  $("#deck").innerHTML = "";
  columns.forEach(mount);
}

$("#addBtn").onclick = () => {
  const type = $("#addType").value;
  columns.push({ id: uid(), type, ...TYPES[type].defaults() });
  save(STORE, columns);
  renderAll();
  $("#deck").lastElementChild.scrollIntoView({ behavior: "smooth", inline: "end" });
  $("#deck").lastElementChild.querySelector(".col-settings").hidden = false;
};

const clock = () => ($("#clock").textContent = new Date().toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }));
clock();
setInterval(clock, 15000);
renderAll();
