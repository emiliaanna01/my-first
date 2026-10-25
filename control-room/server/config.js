import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const DEFAULTS = {
  title: 'Control room',
  dayWindow: { start: 7, end: 19 },
  agendaDays: 7,
  alarms: { meetingLeadMinutes: 10 },
  weather: null,
  notion: { databaseId: '', titleProperty: '', statusProperty: '', doneValue: 'Done', dueProperty: '' },
  feeds: [],
  systems: [],
  launchpad: [],
};

// Secrets live in .env; everything else in config.json (falls back to config.example.json).
export function loadEnv() {
  const file = path.join(ROOT, '.env');
  if (fs.existsSync(file)) process.loadEnvFile(file);
}

export function loadConfig() {
  const own = path.join(ROOT, 'config.json');
  const file = fs.existsSync(own) ? own : path.join(ROOT, 'config.example.json');
  const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  const config = { ...DEFAULTS, ...raw };
  config.notion = { ...DEFAULTS.notion, ...raw.notion };
  config.alarms = { ...DEFAULTS.alarms, ...raw.alarms };
  config.dayWindow = { ...DEFAULTS.dayWindow, ...raw.dayWindow };
  config.source = path.basename(file);
  return config;
}

// CALENDAR_ICS_URLS="Work=https://...basic.ics; Home=https://...basic.ics" (names optional)
export function parseCalendarEnv(value = '') {
  return value
    .split(/[;\n]/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part, i) => {
      const eq = part.indexOf('=');
      const named = eq > 0 && !part.slice(0, eq).includes('://');
      return {
        name: named ? part.slice(0, eq).trim() : `Calendar ${i + 1}`,
        url: (named ? part.slice(eq + 1) : part).trim().replace(/^webcal:/, 'https:'),
      };
    });
}
