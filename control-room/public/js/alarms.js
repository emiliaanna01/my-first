import { localDate } from './format.js';

// Alarm philosophy borrowed from ISA-18.2: few alarms, each one actionable,
// floods collapsed into one line, and comms failures kept apart from process alarms.
export const PRIORITIES = {
  high: { rank: 1, label: 'High' },
  medium: { rank: 2, label: 'Medium' },
  low: { rank: 3, label: 'Low' },
  diag: { rank: 4, label: 'Data source' },
};

export function computeAlarms({
  now = new Date(),
  events = [],
  tasks = [],
  systems = [],
  feedItems = [],
  sourceErrors = [],
  meetingLeadMinutes = 10,
  advisoryDays = 7,
}) {
  const alarms = [];
  const nowMs = now.getTime();
  const today = localDate(now);

  for (const ev of events) {
    if (ev.allDay) continue;
    const minutes = (Date.parse(ev.start) - nowMs) / 60_000;
    if (minutes > 0 && minutes <= meetingLeadMinutes) {
      alarms.push({
        id: `event:${ev.id}`,
        priority: 'medium',
        area: 'Calendar',
        message: `${ev.title} starts in ${Math.ceil(minutes)} min`,
        since: ev.start,
        link: ev.joinUrl ? { label: 'Join', url: ev.joinUrl } : null,
      });
    }
  }

  for (const task of tasks) {
    if (!task.due) continue;
    const overdue = task.due.length > 10 ? Date.parse(task.due) < nowMs : task.due < today;
    if (overdue) {
      alarms.push({
        id: `task:${task.id}:overdue`,
        priority: task.priority && /high|urgent|p1/i.test(task.priority) ? 'high' : 'medium',
        area: 'Tasks',
        message: `Overdue: ${task.title}`,
        since: task.due,
        link: task.url ? { label: 'Open', url: task.url } : null,
      });
    }
  }

  for (const system of systems) {
    if (system.up) continue;
    alarms.push({
      id: `system:${system.name}`,
      priority: system.critical ? 'high' : 'low',
      area: 'Systems',
      message: `${system.name} not responding (${system.detail})`,
      since: system.checkedAt,
      link: null,
    });
  }

  // One alarm per watched keyword, however many advisories match it.
  const cutoff = nowMs - advisoryDays * 86_400_000;
  const groups = new Map();
  for (const item of feedItems) {
    if (!item.watch || (item.date && Date.parse(item.date) < cutoff)) continue;
    const group = groups.get(item.watch) ?? [];
    group.push(item);
    groups.set(item.watch, group);
  }
  for (const [keyword, items] of groups) {
    items.sort((a, b) => (b.date ?? '').localeCompare(a.date ?? ''));
    const latest = items[0];
    alarms.push({
      id: `watch:${keyword}:${latest.id}`,
      priority: 'low',
      area: 'Advisories',
      message: items.length === 1 ? latest.title : `${items.length} new ${keyword} advisories, latest: ${latest.title}`,
      since: latest.date,
      link: latest.link ? { label: 'Read', url: latest.link } : null,
    });
  }

  for (const err of sourceErrors) {
    alarms.push({
      id: `comms:${err.source}`,
      priority: 'diag',
      area: err.source,
      message: err.message,
      since: err.since ?? now.toISOString(),
      link: null,
    });
  }

  return alarms.sort(
    (a, b) => PRIORITIES[a.priority].rank - PRIORITIES[b.priority].rank || (b.since ?? '').localeCompare(a.since ?? ''),
  );
}

// Acknowledgements survive reloads but are dropped once their alarm clears,
// so a condition that comes back alarms again.
export function pruneAcks(acks, alarms) {
  const active = new Set(alarms.map((a) => a.id));
  return Object.fromEntries(Object.entries(acks).filter(([id]) => active.has(id)));
}
