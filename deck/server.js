// Deck server: serves the static page and proxies X API v2 reads.
// The browser can't call api.x.com directly (CORS + the token must stay secret),
// so X columns go through /api/x/*. Zero dependencies — Node 18+.
//
// Env:
//   X_BEARER_TOKEN    app-only token: search + user timelines + lists
//   X_USER_TOKEN      OAuth 2.0 user token (optional): home timeline + bookmarks
//   X_MIN_POLL_SEC    cache each feed at least this long (default 300)
//   X_DAILY_READ_CAP  stop calling X after this many posts read today (default 500)
//   PORT              default 8080

const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = Number(process.env.PORT || 8080);
const BEARER = process.env.X_BEARER_TOKEN || "";
const USER_TOKEN = process.env.X_USER_TOKEN || "";
const MIN_POLL_MS = Number(process.env.X_MIN_POLL_SEC || 300) * 1000;
const DAILY_CAP = Number(process.env.X_DAILY_READ_CAP || 500);
const ROOT = __dirname;
const API = "https://api.x.com/2";

const FIELDS =
  "tweet.fields=created_at,public_metrics,author_id&expansions=author_id" +
  "&user.fields=name,username,profile_image_url";

// Pay-per-use bills every post returned, so we cache per feed and keep a daily counter.
const cache = new Map(); // key -> { at, sinceId, posts }
const usage = { day: today(), reads: 0 };
let userIdCache = new Map(); // username -> id
let meId = null;

function today() {
  return new Date().toISOString().slice(0, 10);
}

async function xGet(url, token) {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = body.detail || body.title || (body.errors && body.errors[0]?.message) || res.statusText;
    throw Object.assign(new Error(`X API ${res.status}: ${msg}`), { status: res.status });
  }
  return body;
}

async function userId(username) {
  if (userIdCache.has(username)) return userIdCache.get(username);
  const r = await xGet(`${API}/users/by/username/${encodeURIComponent(username)}`, BEARER);
  userIdCache.set(username, r.data.id);
  return r.data.id;
}

async function myId() {
  if (meId) return meId;
  const r = await xGet(`${API}/users/me`, USER_TOKEN);
  meId = r.data.id;
  return meId;
}

// Build the X endpoint for a feed. Returns { url, token, supportsSince }.
async function feedUrl(kind, q) {
  switch (kind) {
    case "search":
      return { url: `${API}/tweets/search/recent?query=${encodeURIComponent(q)}&max_results=10&${FIELDS}`, token: BEARER, supportsSince: true };
    case "user":
      return { url: `${API}/users/${await userId(q.replace(/^@/, ""))}/tweets?max_results=10&${FIELDS}`, token: BEARER, supportsSince: true };
    case "list":
      return { url: `${API}/lists/${encodeURIComponent(q)}/tweets?max_results=10&${FIELDS}`, token: BEARER, supportsSince: false };
    case "home":
      return { url: `${API}/users/${await myId()}/timelines/reverse_chronological?max_results=10&${FIELDS}`, token: USER_TOKEN, supportsSince: true };
    case "bookmarks":
      return { url: `${API}/users/${await myId()}/bookmarks?max_results=10&${FIELDS}`, token: USER_TOKEN, supportsSince: false };
    default:
      throw Object.assign(new Error(`unknown feed kind: ${kind}`), { status: 400 });
  }
}

function normalize(body) {
  const users = new Map((body.includes?.users || []).map((u) => [u.id, u]));
  return (body.data || []).map((t) => {
    const u = users.get(t.author_id) || {};
    return {
      id: t.id,
      text: t.text,
      createdAt: t.created_at,
      metrics: t.public_metrics || {},
      author: { name: u.name, username: u.username, avatar: u.profile_image_url },
    };
  });
}

async function handleX(kind, q) {
  const needsUser = kind === "home" || kind === "bookmarks";
  if (needsUser ? !USER_TOKEN : !BEARER) {
    throw Object.assign(new Error(needsUser ? "X_USER_TOKEN not set on the server" : "X_BEARER_TOKEN not set on the server"), { status: 503 });
  }
  if (usage.day !== today()) Object.assign(usage, { day: today(), reads: 0 });

  const key = `${kind}:${q}`;
  const hit = cache.get(key);
  const fresh = hit && Date.now() - hit.at < MIN_POLL_MS;
  if (fresh || usage.reads >= DAILY_CAP) {
    return { posts: hit?.posts || [], cached: true, capped: usage.reads >= DAILY_CAP, usage, nextPollSec: MIN_POLL_MS / 1000 };
  }

  const { url, token, supportsSince } = await feedUrl(kind, q);
  const full = supportsSince && hit?.sinceId ? `${url}&since_id=${hit.sinceId}` : url;
  const newPosts = normalize(await xGet(full, token));
  usage.reads += newPosts.length;

  // Merge new posts on top of what we already have, newest first, keep 50.
  const seen = new Set(newPosts.map((p) => p.id));
  const posts = [...newPosts, ...(hit?.posts || []).filter((p) => !seen.has(p.id))].slice(0, 50);
  cache.set(key, { at: Date.now(), sinceId: posts[0]?.id || hit?.sinceId, posts });
  return { posts, cached: false, capped: false, usage, nextPollSec: MIN_POLL_MS / 1000 };
}

const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };

function send(res, status, body, type = "application/json") {
  res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(typeof body === "string" || Buffer.isBuffer(body) ? body : JSON.stringify(body));
}

http
  .createServer(async (req, res) => {
    const u = new URL(req.url, `http://${req.headers.host}`);
    try {
      if (u.pathname === "/api/x/status") {
        return send(res, 200, { bearer: !!BEARER, user: !!USER_TOKEN, minPollSec: MIN_POLL_MS / 1000, dailyCap: DAILY_CAP, usage });
      }
      const m = u.pathname.match(/^\/api\/x\/(search|user|list|home|bookmarks)$/);
      if (m) return send(res, 200, await handleX(m[1], u.searchParams.get("q") || ""));

      const file = path.normalize(path.join(ROOT, u.pathname === "/" ? "index.html" : u.pathname));
      if (!file.startsWith(ROOT) || path.basename(file) === "server.js") return send(res, 404, "not found", "text/plain");
      fs.readFile(file, (err, data) => {
        if (err) return send(res, 404, "not found", "text/plain");
        send(res, 200, data, TYPES[path.extname(file)] || "application/octet-stream");
      });
    } catch (e) {
      send(res, e.status || 500, { error: e.message });
    }
  })
  .listen(PORT, () => console.log(`Deck on http://localhost:${PORT}  (X bearer: ${BEARER ? "yes" : "no"}, user token: ${USER_TOKEN ? "yes" : "no"})`));
