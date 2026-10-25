// Layout maths for the day trend: which hours to show and which row each event sits on.

export function dayWindow(events, now, { start = 7, end = 19 } = {}) {
  const midnight = new Date(now);
  midnight.setHours(0, 0, 0, 0);
  const hourOf = (iso) => (Date.parse(iso) - midnight.getTime()) / 3_600_000;
  let from = start;
  let to = end;
  const nowHour = hourOf(now.toISOString());
  from = Math.min(from, Math.floor(nowHour - 1));
  to = Math.max(to, Math.ceil(nowHour + 1));
  for (const ev of events) {
    if (ev.allDay) continue;
    from = Math.min(from, Math.floor(hourOf(ev.start)));
    to = Math.max(to, Math.ceil(hourOf(ev.end)));
  }
  from = Math.max(0, from);
  to = Math.min(24, Math.max(to, from + 4));
  return {
    from: new Date(midnight.getTime() + from * 3_600_000),
    to: new Date(midnight.getTime() + to * 3_600_000),
  };
}

// Greedy interval packing: each event takes the first row that is free at its start.
export function assignLanes(events) {
  const sorted = [...events].sort((a, b) => a.start.localeCompare(b.start) || b.end.localeCompare(a.end));
  const laneEnds = [];
  const placed = sorted.map((ev) => {
    let lane = laneEnds.findIndex((end) => end <= ev.start);
    if (lane === -1) lane = laneEnds.length;
    laneEnds[lane] = ev.end;
    return { ...ev, lane };
  });
  return { placed, lanes: Math.max(1, laneEnds.length) };
}

// Phone-width trend: an hour of history and the next few hours, like a short trend span.
export function rollingWindow(now, hours = 8) {
  const from = new Date(now);
  from.setMinutes(0, 0, 0);
  from.setHours(from.getHours() - 1);
  return { from, to: new Date(from.getTime() + hours * 3_600_000) };
}

// How far right each event's label may run: up to the next event in its row, or the window edge.
export function labelRoom(placed, windowEnd) {
  return placed.map((ev) => {
    const next = placed
      .filter((o) => o.lane === ev.lane && o.start >= ev.end && o !== ev)
      .reduce((min, o) => (min === null || o.start < min ? o.start : min), null);
    return { ...ev, roomEnd: next ?? windowEnd.toISOString() };
  });
}

export function todaysTimedEvents(events, now) {
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + 1);
  return events.filter((ev) => !ev.allDay && Date.parse(ev.end) > start.getTime() && Date.parse(ev.start) < end.getTime());
}
