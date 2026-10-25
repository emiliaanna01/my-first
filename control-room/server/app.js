import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { ROOT, loadEnv, loadConfig, parseCalendarEnv } from './config.js';
import { createCache } from './cache.js';
import { getAgenda } from './calendar.js';
import { createNotion } from './notion.js';
import { readRss, createX, markWatched } from './feeds.js';
import { checkAll, isPrivateTarget } from './systems.js';
import { getWeather } from './weather.js';
import { createNotes } from './notes.js';
import { demoEvents, demoTasks, demoPosts } from './demo.js';

loadEnv();
const config = loadConfig();
// On Vercel the filesystem is read-only and the page is reachable from the internet.
export const HOSTED = Boolean(process.env.VERCEL);
const ENV_FILE = HOSTED ? 'your Vercel environment variables' : '.env';
const cache = createCache();
const notes = createNotes(path.join(ROOT, 'data'));

const calendars = parseCalendarEnv(process.env.CALENDAR_ICS_URLS);
const notionDatabase = process.env.NOTION_DATABASE_ID || config.notion.databaseId;
const notion =
  process.env.NOTION_TOKEN && notionDatabase
    ? createNotion({ ...config.notion, token: process.env.NOTION_TOKEN, databaseId: notionDatabase })
    : null;
const readX = process.env.X_BEARER_TOKEN ? createX({ token: process.env.X_BEARER_TOKEN }) : null;
let sampleTasks = demoTasks();

const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

const routes = {
  'GET /api/config': () => ({
    title: config.title,
    dayWindow: config.dayWindow,
    alarms: config.alarms,
    launchpad: config.launchpad,
    weather: config.weather ? { label: config.weather.label ?? null } : null,
    feeds: config.feeds.map((f) => f.name),
    configFile: config.source,
    hosted: HOSTED,
    integrations: {
      calendar: calendars.length ? 'live' : 'sample',
      notion: notion ? 'live' : 'sample',
      x: readX ? 'live' : 'off',
    },
  }),

  'GET /api/calendar': async ({ force }) => {
    if (!calendars.length) {
      return { source: 'sample', events: demoEvents(), errors: [], hint: `Add your Google Calendar secret iCal address to CALENDAR_ICS_URLS in ${ENV_FILE}.` };
    }
    const agenda = await cache('calendar', 5 * 60_000, () => getAgenda({ calendars, days: config.agendaDays }), { force });
    return { source: 'live', ...agenda };
  },

  'GET /api/tasks': async ({ force }) => {
    if (!notion) {
      return { source: 'sample', tasks: sampleTasks, hint: `Add NOTION_TOKEN and NOTION_DATABASE_ID to ${ENV_FILE} to load your Notion tasks.` };
    }
    return { source: 'live', tasks: await cache('tasks', 2 * 60_000, () => notion.listTasks(), { force }) };
  },

  'POST /api/tasks': async ({ body }) => {
    const title = String(body.title ?? '').trim();
    if (!title) throw httpError(400, 'Write a task title first.');
    const due = /^\d{4}-\d{2}-\d{2}$/.test(body.due ?? '') ? body.due : null;
    if (!notion) {
      const task = { id: `sample-${Date.now()}`, title, due, status: 'Not started', priority: null, url: null };
      sampleTasks = [...sampleTasks, task];
      return task;
    }
    const task = await notion.addTask({ title, due });
    await cache('tasks', 0, () => notion.listTasks(), { force: true });
    return task;
  },

  'POST /api/tasks/done': async ({ body }) => {
    const id = String(body.id ?? '');
    if (!notion) {
      sampleTasks = sampleTasks.filter((t) => t.id !== id);
      return { ok: true };
    }
    await notion.completeTask(id);
    await cache('tasks', 0, () => notion.listTasks(), { force: true });
    return { ok: true };
  },

  'GET /api/feeds': async ({ force }) => ({
    tabs: await Promise.all(config.feeds.map((tab) => cache(`feed:${tab.name}`, 10 * 60_000, () => loadTab(tab), { force }))),
  }),

  'GET /api/systems': async ({ force }) => ({
    systems: await cache('systems', 20_000, () => checkAll(HOSTED ? config.systems.filter((s) => !isPrivateTarget(s)) : config.systems), { force }),
  }),

  'GET /api/weather': async ({ query }) => {
    const latitude = Number(query.get('lat') ?? config.weather?.latitude);
    const longitude = Number(query.get('lon') ?? config.weather?.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) throw httpError(400, 'Set weather.latitude and weather.longitude in config.json.');
    const key = `weather:${latitude.toFixed(2)},${longitude.toFixed(2)}`;
    return cache(key, 15 * 60_000, () => getWeather({ latitude, longitude }));
  },

  // Hosted: notes stay in the browser instead (see app.js).
  'GET /api/notes': () => (HOSTED ? { storage: 'browser' } : notes.read(today())),
  'PUT /api/notes': ({ body }) => (HOSTED ? { storage: 'browser' } : notes.write(today(), body)),
};

async function loadTab(tab) {
  const items = [];
  const errors = [];
  const embeds = [];
  let wantsX = false;
  await Promise.all(
    (tab.sources ?? []).map(async (src) => {
      try {
        if (src.type === 'rss') items.push(...markWatched(await readRss(src.url, src.label), src.watch));
        else if (src.type === 'x-embed') embeds.push(src.url);
        else if (src.type === 'x') {
          wantsX = true;
          if (readX) items.push(...(await readX(src)));
        }
      } catch (error) {
        errors.push(`${src.label ?? src.user ?? src.list ?? src.url}: ${error.message}`);
      }
    }),
  );
  const sample = wantsX && !readX && items.length === 0 && embeds.length === 0;
  items.sort((a, b) => (b.date ?? '').localeCompare(a.date ?? ''));
  return {
    name: tab.name,
    source: sample ? 'sample' : 'live',
    items: sample ? demoPosts() : items.slice(0, 40),
    embeds,
    errors,
    hint: sample ? `Add X_BEARER_TOKEN to ${ENV_FILE}, or an "x-embed" source in config.json, to see real posts.` : undefined,
  };
}

function httpError(status, message) {
  return Object.assign(new Error(message), { status });
}

async function readBody(req) {
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 100_000) throw httpError(413, 'Request body is too large.');
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw httpError(400, 'Request body is not valid JSON.');
  }
}

const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.json': 'application/json', '.png': 'image/png' };
const PUBLIC = path.join(ROOT, 'public');

async function serveStatic(pathname, res) {
  const file = path.normalize(path.join(PUBLIC, pathname === '/' ? 'index.html' : decodeURIComponent(pathname)));
  if (!file.startsWith(PUBLIC + path.sep)) return send(res, 403, 'Forbidden', 'text/plain');
  try {
    const body = await fs.readFile(file);
    send(res, 200, body, `${TYPES[path.extname(file)] ?? 'application/octet-stream'}; charset=utf-8`);
  } catch {
    send(res, 404, 'Not found', 'text/plain');
  }
}

function send(res, status, body, type) {
  res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(body);
}

// Password gate: required when hosted, optional locally (set APP_PASSWORD).
const PASSWORD = process.env.APP_PASSWORD ?? '';
const SESSION = PASSWORD ? crypto.createHmac('sha256', PASSWORD).update('control-room-session').digest('hex') : '';

function authorized(req) {
  if (!PASSWORD) return !HOSTED;
  const cookie = (req.headers.cookie ?? '').split(';').map((c) => c.trim()).find((c) => c.startsWith('cr_session='));
  const value = cookie?.slice('cr_session='.length) ?? '';
  return value.length === SESSION.length && crypto.timingSafeEqual(Buffer.from(value), Buffer.from(SESSION));
}

async function login(req, res) {
  if (!PASSWORD) return send(res, 503, JSON.stringify({ error: 'Set APP_PASSWORD to turn on sign-in.' }), 'application/json');
  const body = await readBody(req).catch(() => ({}));
  const given = crypto.createHash('sha256').update(String(body.password ?? '')).digest();
  const expected = crypto.createHash('sha256').update(PASSWORD).digest();
  if (!crypto.timingSafeEqual(given, expected)) {
    await new Promise((r) => setTimeout(r, 600));
    return send(res, 401, JSON.stringify({ error: 'Wrong password.' }), 'application/json');
  }
  const secure = HOSTED || req.headers['x-forwarded-proto'] === 'https' ? '; Secure' : '';
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Set-Cookie': `cr_session=${SESSION}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${60 * 60 * 24 * 60}${secure}`,
  });
  res.end('{"ok":true}');
}

export async function handler(req, res) {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/api/login' && req.method === 'POST') return login(req, res);
  const route = routes[`${req.method} ${url.pathname}`];
  if (!route) {
    if (req.method === 'GET' && !url.pathname.startsWith('/api/')) return serveStatic(url.pathname, res);
    return send(res, 404, JSON.stringify({ error: 'Unknown endpoint' }), 'application/json');
  }
  if (!authorized(req)) {
    const error = PASSWORD ? 'Sign in to see your dashboard.' : 'Set APP_PASSWORD in your Vercel environment variables, then redeploy.';
    return send(res, PASSWORD ? 401 : 503, JSON.stringify({ error, login: Boolean(PASSWORD) }), 'application/json');
  }
  try {
    const body = req.method === 'POST' || req.method === 'PUT' ? await readBody(req) : {};
    const result = await route({ body, query: url.searchParams, force: url.searchParams.has('refresh') });
    send(res, 200, JSON.stringify(result), 'application/json');
  } catch (error) {
    const status = error.status && error.status < 500 && error.status >= 400 ? error.status : 502;
    send(res, status, JSON.stringify({ error: error.message }), 'application/json');
  }
}

export const summary = {
  config: config.source,
  calendar: calendars.length ? `${calendars.length} calendar(s)` : 'sample data',
  notion: notion ? 'connected' : 'sample data',
  x: readX ? 'connected' : 'off',
  password: PASSWORD ? 'on' : 'off',
};
