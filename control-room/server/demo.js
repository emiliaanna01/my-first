// Sample data shown until an integration is connected, built around the current time
// so the timeline, countdown and alarms all have something to show.
const MIN = 60_000;

function at(base, minutes) {
  return new Date(base.getTime() + minutes * MIN);
}

function localDate(d) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function demoEvents(now = new Date()) {
  const base = new Date(Math.round(now.getTime() / (5 * MIN)) * 5 * MIN);
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(9, 0, 0, 0);
  const shutdown = new Date(now);
  shutdown.setDate(shutdown.getDate() + 3);

  const ev = (id, title, start, minutes, extra = {}) => ({
    id: `demo-${id}`,
    title,
    start: start.toISOString(),
    end: at(start, minutes).toISOString(),
    allDay: false,
    calendar: 'Work',
    ...extra,
  });

  return [
    ev('standup', 'Daily stand-up', at(base, -150), 15, { joinUrl: 'https://meet.google.com/' }),
    ev('mcr', 'Review PLC change request MCR-214', at(base, -75), 45),
    ev('fat', 'Line 3 FAT prep', at(base, -20), 30, { location: 'Plant B, panel room' }),
    ev('vendor', 'Call with drive vendor', at(base, 8), 30, { joinUrl: 'https://meet.google.com/' }),
    ev('ignition', 'Ignition gateway upgrade review', at(base, 120), 60),
    ev('gym', 'Gym', at(base, 300), 60, { calendar: 'Personal' }),
    ev('site', 'Site visit: Plant B', tomorrow, 180, { location: 'Plant B' }),
    {
      id: 'demo-shutdown',
      title: 'Planned shutdown, Line 2',
      start: shutdown.toISOString(),
      end: shutdown.toISOString(),
      allDay: true,
      date: localDate(shutdown),
      endDate: localDate(shutdown),
      calendar: 'Work',
    },
  ];
}

export function demoTasks(now = new Date()) {
  const day = (offset) => {
    const d = new Date(now);
    d.setDate(d.getDate() + offset);
    return localDate(d);
  };
  return [
    { id: 'demo-1', title: 'Send FAT punch list to vendor', due: day(-1), status: 'In progress', priority: 'High' },
    { id: 'demo-2', title: 'Update I/O list to rev C', due: day(0), status: 'Not started', priority: 'Medium' },
    { id: 'demo-3', title: 'Back up PLC-02 program before upgrade', due: day(0), status: 'Not started', priority: 'High' },
    { id: 'demo-4', title: 'Order spare 24 V power supply', due: day(3), status: 'Not started', priority: 'Low' },
    { id: 'demo-5', title: 'Read ISA-18.2 alarm rationalization notes', due: null, status: 'Not started', priority: null },
  ].map((t) => ({ ...t, url: null }));
}

export function demoPosts(now = new Date()) {
  return [
    'Sample post: connect the X API or add an embedded timeline to see real posts here.',
    'Sample post: lists work best. Make an X list of the controls engineers you follow and add its ID to config.json.',
    'Sample post: no X API plan? Point an RSS source at a feed service instead; any RSS or Atom URL works.',
  ].map((text, i) => ({
    id: `demo-x-${i}`,
    title: text,
    link: null,
    date: at(now, -(i + 1) * 47).toISOString(),
    source: 'Sample',
  }));
}
