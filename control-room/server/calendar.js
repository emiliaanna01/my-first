import ical from 'node-ical';

const JOIN_LINK = /https:\/\/(?:meet\.google\.com|[\w-]+\.zoom\.us|teams\.microsoft\.com|teams\.live\.com)\/[^\s<>"')]+/i;

const text = (value) => (value && typeof value === 'object' ? value.val ?? '' : value ?? '');

function localDate(d) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// Expand every VEVENT in an .ics body into concrete instances between `from` and `to`.
export function eventsFromICS(body, { from, to, calendar = 'Calendar' }) {
  const parsed = ical.sync.parseICS(body);
  const events = [];
  for (const component of Object.values(parsed)) {
    if (component.type !== 'VEVENT' || component.status === 'CANCELLED') continue;
    const instances = ical.expandRecurringEvent(component, { from, to, expandOngoing: true });
    for (const inst of instances) {
      const ev = inst.event;
      if (ev.status === 'CANCELLED') continue;
      const start = new Date(inst.start);
      const end = new Date(inst.end ?? inst.start);
      const description = text(ev.description);
      const location = text(ev.location);
      const join = (text(ev.url).match(JOIN_LINK) || location.match(JOIN_LINK) || description.match(JOIN_LINK) || [])[0];
      events.push({
        id: `${ev.uid}@${start.toISOString()}`,
        title: text(inst.summary) || '(no title)',
        start: start.toISOString(),
        end: end.toISOString(),
        allDay: inst.isFullDay,
        date: inst.isFullDay ? localDate(start) : undefined,
        endDate: inst.isFullDay ? localDate(new Date(end.getTime() - 1)) : undefined,
        location: location || undefined,
        joinUrl: join,
        calendar,
      });
    }
  }
  return events;
}

export async function getAgenda({ calendars, days = 7, now = new Date(), fetchImpl = fetch }) {
  // Start a day early: a hosted server runs on UTC, and the browser trims to its own local day.
  const from = new Date(now);
  from.setHours(0, 0, 0, 0);
  from.setDate(from.getDate() - 1);
  const to = new Date(from);
  to.setDate(to.getDate() + days + 2);

  const results = await Promise.allSettled(
    calendars.map(async (cal) => {
      const res = await fetchImpl(cal.url, { signal: AbortSignal.timeout(10_000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return eventsFromICS(await res.text(), { from, to, calendar: cal.name });
    }),
  );

  const events = [];
  const errors = [];
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') events.push(...r.value);
    else errors.push(`${calendars[i].name}: ${r.reason?.message ?? r.reason}`);
  });
  if (errors.length === calendars.length) throw new Error(errors.join('; '));

  events.sort((a, b) => a.start.localeCompare(b.start));
  return { events, errors, calendars: calendars.map((c) => c.name) };
}
