import { test } from 'node:test';
import assert from 'node:assert/strict';
import { computeAlarms, pruneAcks } from '../public/js/alarms.js';
import { assignLanes, dayWindow, labelRoom, rollingWindow } from '../public/js/trend.js';
import { esc, safeUrl, duration } from '../public/js/format.js';

const now = new Date('2026-10-25T10:00:00');
const iso = (minutes) => new Date(now.getTime() + minutes * 60_000).toISOString();

test('meetings alarm only inside the lead time', () => {
  const events = [
    { id: 'a', title: 'Soon', start: iso(8), end: iso(30), allDay: false, joinUrl: 'https://meet.google.com/x' },
    { id: 'b', title: 'Later', start: iso(45), end: iso(60), allDay: false },
    { id: 'c', title: 'Running', start: iso(-5), end: iso(20), allDay: false },
  ];
  const alarms = computeAlarms({ now, events, meetingLeadMinutes: 10 });
  assert.equal(alarms.length, 1);
  assert.equal(alarms[0].message, 'Soon starts in 8 min');
  assert.equal(alarms[0].priority, 'medium');
  assert.equal(alarms[0].link.label, 'Join');
});

test('overdue tasks alarm; high-priority ones alarm high', () => {
  const tasks = [
    { id: 1, title: 'Late', due: '2026-10-24' },
    { id: 2, title: 'Late and urgent', due: '2026-10-20', priority: 'High' },
    { id: 3, title: 'Today', due: '2026-10-25' },
    { id: 4, title: 'Past deadline today', due: iso(-30) },
    { id: 5, title: 'No date', due: null },
  ];
  const alarms = computeAlarms({ now, tasks });
  assert.deepEqual(alarms.map((a) => [a.id, a.priority]), [
    ['task:2:overdue', 'high'],
    ['task:4:overdue', 'medium'],
    ['task:1:overdue', 'medium'],
  ]);
});

test('down systems alarm by criticality; data-source errors sort last', () => {
  const alarms = computeAlarms({
    now,
    systems: [
      { name: 'PLC-01', up: false, critical: false, detail: 'No answer in 4 s', checkedAt: iso(0) },
      { name: 'Gateway', up: false, critical: true, detail: 'Connection refused', checkedAt: iso(0) },
      { name: 'GitHub', up: true },
    ],
    sourceErrors: [{ source: 'Notion', message: "Can't load" }],
  });
  assert.deepEqual(alarms.map((a) => a.priority), ['high', 'low', 'diag']);
  assert.equal(alarms[0].message, 'Gateway not responding (Connection refused)');
});

test('watched advisories collapse into one alarm per keyword', () => {
  const feedItems = [
    { id: 'a1', title: 'Siemens SCALANCE', watch: 'Siemens', date: iso(-60) },
    { id: 'a2', title: 'Siemens SIMATIC', watch: 'Siemens', date: iso(-30) },
    { id: 'a3', title: 'Siemens old', watch: 'Siemens', date: iso(-60 * 24 * 30) },
    { id: 'b1', title: 'Rockwell FactoryTalk', watch: 'Rockwell', date: iso(-10) },
    { id: 'c1', title: 'Unwatched', date: iso(-10) },
  ];
  const alarms = computeAlarms({ now, feedItems, advisoryDays: 7 });
  assert.equal(alarms.length, 2);
  const siemens = alarms.find((a) => a.id.startsWith('watch:Siemens'));
  assert.equal(siemens.id, 'watch:Siemens:a2');
  assert.equal(siemens.message, '2 new Siemens advisories, latest: Siemens SIMATIC');
});

test('pruneAcks forgets acknowledgements of cleared alarms', () => {
  assert.deepEqual(pruneAcks({ a: 't', b: 't' }, [{ id: 'b' }]), { b: 't' });
});

test('assignLanes stacks overlapping events and reuses free rows', () => {
  const ev = (id, s, e) => ({ id, start: iso(s), end: iso(e) });
  const { placed, lanes } = assignLanes([ev('a', 0, 60), ev('b', 30, 90), ev('c', 60, 120), ev('d', 95, 100)]);
  assert.equal(lanes, 2);
  assert.deepEqual(Object.fromEntries(placed.map((p) => [p.id, p.lane])), { a: 0, b: 1, c: 0, d: 1 });
});

test('dayWindow widens to include early events and the current time', () => {
  const early = new Date(now);
  early.setHours(5, 30);
  const { from, to } = dayWindow([{ start: early.toISOString(), end: iso(0), allDay: false }], now, { start: 7, end: 19 });
  assert.equal(from.getHours(), 5);
  assert.equal(to.getHours(), 19);
});

test('format helpers escape markup and refuse non-web links', () => {
  assert.equal(esc('<img src=x onerror="a">'), '&lt;img src=x onerror=&quot;a&quot;&gt;');
  assert.equal(safeUrl('javascript:alert(1)'), null);
  assert.equal(safeUrl('https://x.com/a'), 'https://x.com/a');
  assert.equal(duration(80 * 60_000), '1 h 20 min');
});

test('labelRoom lets a label run until the next event in its row', () => {
  const ev = (id, s, e) => ({ id, start: iso(s), end: iso(e) });
  const { placed } = assignLanes([ev('a', 0, 15), ev('b', 60, 90), ev('c', 5, 20)]);
  const end = new Date(now.getTime() + 8 * 3_600_000);
  const rooms = Object.fromEntries(labelRoom(placed, end).map((p) => [p.id, p.roomEnd]));
  assert.equal(rooms.a, iso(60));
  assert.equal(rooms.b, end.toISOString());
  assert.equal(rooms.c, end.toISOString());
});

test('rollingWindow starts on the hour before now and spans eight hours', () => {
  const { from, to } = rollingWindow(new Date('2026-10-25T10:40:00'));
  assert.equal(from.getHours(), 9);
  assert.equal(from.getMinutes(), 0);
  assert.equal((to - from) / 3_600_000, 8);
});
