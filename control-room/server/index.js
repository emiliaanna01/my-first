import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { ROOT, loadEnv, loadConfig, parseCalendarEnv } from './config.js';
import { createCache } from './cache.js';
import { getAgenda } from './calendar.js';
import { createNotion } from './notion.js';
import { readRss, createX, markWatched } from './feeds.js';
import { checkAll } from './systems.js';
import { getWeather } from './weather.js';
import { createNotes } from './notes.js';
import { demoEvents, demoTasks, demoPosts } from './demo.js';

loadEnv();
const config = loadConfig();
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
    integrations: {
      calendar: calendars.length ? 'live' : 'sample',
      notion: notion ? 'live' : 'sample',
      x: readX ? 'live' : 'off',
    },
  }),

  'GET /api/calendar': async ({ force }) => {
    if (!calendars.length) {
      return { source: 'sample', events: demoEvents(), errors: [], hint: 'Add your Google Calendar secret iCal address to CALENDAR_ICS_URLS in .env.' };
    }
    const agenda = await cache('calendar', 5 * 60_000, () => getAgenda({ calendars, days: config.agendaDays }), { force });
    return { source: 'live', ...agenda };
  },

  'GET /api/tasks': async ({ force }) => {
    if (!notion) {
      return { source: 'sample', tasks: sampleTasks, hint: 'Add NOTION_TOKEN and NOTION_DATABASE_ID to .env to load your Notion tasks.' };
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
    systems: await cache('systems', 20_000, () => checkAll(config.systems), { force }),
  }),

  'GET /api/weather': async ({ query }) => {
    const latitude = Number(query.get('lat') ?? config.weather?.latitude);
    const longitude = Number(query.get('lon') ?? config.weather?.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) throw httpError(400, 'Set weather.latitude and weather.longitude in config.json.');
    const key = `weather:${latitude.toFixed(2)},${longitude.toFixed(2)}`;
    return cache(key, 15 * 60_000, () => getWeather({ latitude, longitude }));
  },

  'GET /api/notes': () => notes.read(today()),
  'PUT /api/notes': ({ body }) => notes.write(today(), body),
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
    hint: sample ? 'Add X_BEARER_TOKEN to .env, or an "x-embed" source in config.json, to see real posts.' : undefined,
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

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const route = routes[`${req.method} ${url.pathname}`];
  if (!route) {
    if (req.method === 'GET' && !url.pathname.startsWith('/api/')) return serveStatic(url.pathname, res);
    return send(res, 404, JSON.stringify({ error: 'Unknown endpoint' }), 'application/json');
  }
  try {
    const body = req.method === 'POST' || req.method === 'PUT' ? await readBody(req) : {};
    const result = await route({ body, query: url.searchParams, force: url.searchParams.has('refresh') });
    send(res, 200, JSON.stringify(result), 'application/json');
  } catch (error) {
    const status = error.status && error.status < 500 && error.status >= 400 ? error.status : 502;
    send(res, status, JSON.stringify({ error: error.message }), 'application/json');
  }
});

const port = Number(process.env.PORT ?? 4300);
const host = process.env.HOST ?? '127.0.0.1';
server.listen(port, host, () => {
  console.log(`Control room running at http://${host === '0.0.0.0' ? 'localhost' : host}:${port}`);
  console.log(`  config: ${config.source}`);
  console.log(`  calendar: ${calendars.length ? `${calendars.length} calendar(s)` : 'sample data'}`);
  console.log(`  notion: ${notion ? 'connected' : 'sample data'}`);
  console.log(`  x api: ${readX ? 'connected' : 'off'}`);
});
