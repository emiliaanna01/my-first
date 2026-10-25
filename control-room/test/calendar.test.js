import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { eventsFromICS, getAgenda } from '../server/calendar.js';
import { parseCalendarEnv } from '../server/config.js';

const ics = fs.readFileSync(new URL('./fixtures/work.ics', import.meta.url), 'utf8');
const week = { from: new Date('2026-10-26T00:00:00Z'), to: new Date('2026-11-02T00:00:00Z'), calendar: 'Work' };

test('expands weekly events, honouring EXDATE and moved occurrences', () => {
  const standups = eventsFromICS(ics, week).filter((e) => e.title.startsWith('Daily stand-up'));
  const starts = standups.map((e) => e.start).sort();
  assert.deepEqual(starts, [
    '2026-10-26T08:00:00.000Z',
    '2026-10-27T08:00:00.000Z',
    '2026-10-29T09:00:00.000Z', // moved from 09:00 to 10:00 Berlin
    '2026-10-30T08:00:00.000Z',
  ]);
  assert.equal(standups.find((e) => e.start === '2026-10-29T09:00:00.000Z').title, 'Daily stand-up (moved)');
});

test('pulls the meeting link out of the description', () => {
  const ev = eventsFromICS(ics, week).find((e) => e.title === 'Daily stand-up');
  assert.equal(ev.joinUrl, 'https://meet.google.com/abc-defg-hij');
});

test('skips cancelled events and keeps all-day dates', () => {
  const events = eventsFromICS(ics, week);
  assert.equal(events.some((e) => e.title === 'Cancelled review'), false);
  const shutdown = events.find((e) => e.title === 'Plant shutdown');
  assert.equal(shutdown.allDay, true);
  assert.equal(shutdown.date, '2026-10-30');
  assert.equal(shutdown.endDate, '2026-10-31');
});

test('getAgenda keeps working when one of several calendars fails', async () => {
  const fetchImpl = async (url) =>
    url.includes('good') ? new Response(ics) : new Response('nope', { status: 404 });
  const agenda = await getAgenda({
    calendars: [{ name: 'Work', url: 'https://good' }, { name: 'Broken', url: 'https://bad' }],
    now: new Date('2026-10-26T06:00:00Z'),
    fetchImpl,
  });
  assert.ok(agenda.events.length > 0);
  assert.deepEqual(agenda.errors, ['Broken: HTTP 404']);
});

test('getAgenda throws when every calendar fails', async () => {
  const fetchImpl = async () => new Response('', { status: 500 });
  await assert.rejects(getAgenda({ calendars: [{ name: 'Work', url: 'https://x' }], fetchImpl }));
});

test('parseCalendarEnv reads named and unnamed URLs', () => {
  assert.deepEqual(parseCalendarEnv('Work=https://a/basic.ics; webcal://b/basic.ics'), [
    { name: 'Work', url: 'https://a/basic.ics' },
    { name: 'Calendar 2', url: 'https://b/basic.ics' },
  ]);
  assert.deepEqual(parseCalendarEnv(''), []);
});
