import { esc, safeUrl, localDate, fmtTime, dayLabel, duration, ago } from './format.js';
import { computeAlarms, pruneAcks, PRIORITIES } from './alarms.js';
import { dayWindow, assignLanes, todaysTimedEvents, rollingWindow, labelRoom } from './trend.js';

const $ = (sel, root = document) => root.querySelector(sel);

// Per-browser conveniences only (theme, acknowledgements, chosen tab). Notes live on the server.
const store = {
  get(key, fallback) {
    try {
      const raw = localStorage.getItem(`control-room:${key}`);
      return raw == null ? fallback : JSON.parse(raw);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(`control-room:${key}`, JSON.stringify(value));
    } catch {}
  },
};

const state = {
  config: null,
  calendar: null,
  tasks: null,
  feeds: null,
  systems: null,
  notes: null,
  status: {},
  alarms: [],
  acks: store.get('acks', {}),
  feedTab: store.get('feedTab', 0),
  showAllAlarms: false,
  notified: new Set(),
  focus: store.get('focus', null),
};

const SOURCES = {
  calendar: { label: 'Calendar', path: '/api/calendar', every: 5 * 60_000, render: () => (renderTrend(), renderAgenda()) },
  tasks: { label: 'Notion', path: '/api/tasks', every: 2 * 60_000, render: () => renderTasks() },
  feeds: { label: 'Feeds', path: '/api/feeds', every: 10 * 60_000, render: () => renderFeeds() },
  systems: { label: 'Systems', path: '/api/systems', every: 30_000, render: () => renderSystems() },
};

async function api(path, options = {}) {
  const res = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
  return data;
}

async function load(name, { force = false } = {}) {
  const src = SOURCES[name];
  const previous = state.status[name];
  try {
    state[name] = await api(src.path + (force ? '?refresh' : ''));
    state.status[name] = { ok: true, at: new Date(), sample: state[name].source === 'sample', hint: state[name].hint };
  } catch (error) {
    // Keep showing the last good data, flagged as stale, like a bad-quality tag on an HMI.
    state.status[name] = { ...previous, ok: false, error: error.message, since: previous?.ok === false ? previous.since : new Date() };
  }
  src.render();
  renderStatus(name);
  updateAlarms();
}

/* ---------- Status lines ---------- */

function renderStatus(name) {
  const st = state.status[name];
  const el = $(`[data-status="${name}"]`);
  const hint = $(`[data-hint="${name}"]`);
  if (hint) {
    hint.hidden = !st?.hint;
    hint.innerHTML = st?.hint ? esc(st.hint).replace(/([A-Z_]{4,}|\.env|config\.json)/g, '<code>$1</code>') : '';
  }
  if (!el || !st) return;
  if (!st.ok) {
    el.dataset.state = 'offline';
    el.innerHTML = `${shape('diag')} Offline since ${fmtTime(st.since)}, retry`;
    el.title = st.error;
  } else if (st.sample) {
    el.dataset.state = 'sample';
    el.textContent = 'Sample data';
    el.title = st.hint ?? '';
  } else {
    el.dataset.state = 'live';
    el.textContent = `Updated ${fmtTime(st.at)}`;
    el.title = 'Refresh now';
  }
}

/* ---------- Alarms ---------- */

function shape(priority) {
  const glyph = { high: '1', medium: '2', low: '3', diag: '?' }[priority];
  return `<span class="shape shape-${priority}" aria-hidden="true">${glyph}</span>`;
}

function updateAlarms() {
  if (!state.config) return;
  const sourceErrors = [];
  for (const [name, st] of Object.entries(state.status)) {
    if (st && !st.ok) sourceErrors.push({ source: SOURCES[name].label, message: `Can't load: ${st.error}`, since: st.since.toISOString() });
  }
  if (state.calendar?.errors?.length) sourceErrors.push({ source: 'Calendar feed', message: state.calendar.errors.join('; ') });
  for (const tab of state.feeds?.tabs ?? []) {
    if (tab.errors.length) sourceErrors.push({ source: `Feed: ${tab.name}`, message: tab.errors.join('; ') });
  }

  state.alarms = computeAlarms({
    now: new Date(),
    events: state.calendar?.events,
    tasks: state.tasks?.tasks,
    systems: state.systems?.systems,
    feedItems: (state.feeds?.tabs ?? []).flatMap((t) => t.items),
    sourceErrors,
    meetingLeadMinutes: state.config.alarms.meetingLeadMinutes,
    advisoryDays: state.config.alarms.advisoryDays,
  });

  // Drop acknowledgements for cleared alarms, but only once every source has reported,
  // otherwise a page reload would forget acks for sources that haven't loaded yet.
  if (Object.keys(SOURCES).every((n) => state.status[n])) {
    state.acks = pruneAcks(state.acks, state.alarms);
    store.set('acks', state.acks);
  }
  notifyNewAlarms();
  renderAlarms();
}

function renderAlarms() {
  const el = $('#alarms');
  const alarms = [...state.alarms].sort((a, b) => Number(Boolean(state.acks[a.id])) - Number(Boolean(state.acks[b.id])));
  if (!alarms.length) {
    el.dataset.state = 'clear';
    el.innerHTML = '<p class="alarms-clear">No active alarms</p>';
    document.title = state.config?.title ?? 'Control room';
    return;
  }
  el.dataset.state = 'active';
  const unacked = alarms.filter((a) => !state.acks[a.id]);
  const counts = Object.keys(PRIORITIES)
    .map((p) => [p, alarms.filter((a) => a.priority === p).length])
    .filter(([, n]) => n);
  const shown = state.showAllAlarms ? alarms : alarms.slice(0, 3);
  document.title = `${unacked.length ? `(${unacked.length}) ` : ''}${state.config?.title ?? 'Control room'}`;

  el.innerHTML = `
    <div class="alarm-summary">
      ${counts.map(([p, n]) => `<span class="count">${shape(p)} ${n} ${esc(PRIORITIES[p].label.toLowerCase())}</span>`).join('')}
      <span class="unacked">${unacked.length ? `${unacked.length} not acknowledged` : 'All acknowledged'}</span>
      <span class="alarm-actions">
        ${alarms.length > 3 ? `<button type="button" data-action="toggle-alarms">${state.showAllAlarms ? 'Show fewer' : `Show all ${alarms.length}`}</button>` : ''}
        ${unacked.length > 1 ? '<button type="button" data-action="ack-all">Acknowledge all</button>' : ''}
      </span>
    </div>
    <ul class="alarm-list">${shown.map(alarmRow).join('')}</ul>`;
}

function alarmRow(alarm) {
  const acked = Boolean(state.acks[alarm.id]);
  const link = alarm.link && safeUrl(alarm.link.url);
  const since = alarm.since && alarm.since.length > 10 ? fmtTime(alarm.since) : '';
  return `
    <li class="alarm ${acked ? 'acked' : 'unacked'}" data-priority="${alarm.priority}">
      ${shape(alarm.priority)}<span class="sr">${esc(PRIORITIES[alarm.priority].label)} priority.</span>
      <span class="alarm-area">${esc(alarm.area)}</span>
      <span class="alarm-msg" title="${esc(alarm.message)}">${esc(alarm.message)}</span>
      <time>${since}</time>
      <span class="alarm-right">
        ${link ? `<a class="join" href="${esc(link)}" target="_blank" rel="noopener">${esc(alarm.link.label)}</a>` : ''}
        ${acked ? '<span class="acked-label">Acknowledged</span>' : `<button type="button" data-ack="${esc(alarm.id)}">Acknowledge</button>`}
      </span>
    </li>`;
}

function acknowledge(ids) {
  const at = new Date().toISOString();
  for (const id of ids) state.acks[id] = at;
  store.set('acks', state.acks);
  renderAlarms();
}

function notifyNewAlarms() {
  if (!store.get('notify', false) || !('Notification' in window) || Notification.permission !== 'granted') return;
  for (const alarm of state.alarms) {
    if (state.notified.has(alarm.id) || state.acks[alarm.id] || alarm.priority === 'diag') continue;
    state.notified.add(alarm.id);
    notify(`${PRIORITIES[alarm.priority].label} alarm: ${alarm.area}`, { body: alarm.message, tag: alarm.id });
  }
}

/* ---------- Day trend ---------- */

function renderTrend() {
  const now = new Date();
  const events = state.calendar?.events ?? [];
  const today = localDate(now);
  $('#trend-date').textContent = now.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' });

  const allDay = events.filter((ev) => ev.allDay && ev.date <= today && (ev.endDate ?? ev.date) >= today);
  $('#allday').innerHTML = allDay.map((ev) => `<span>All day: ${esc(ev.title)}</span>`).join('');

  const narrow = window.innerWidth < 720;
  const today_ = todaysTimedEvents(events, now);
  const { from, to } = narrow ? rollingWindow(now) : dayWindow(today_, now, state.config.dayWindow);
  const timed = today_.filter((ev) => Date.parse(ev.end) > from && Date.parse(ev.start) < to);
  const span = to - from;
  const plotWidth = Math.max($('#trend').clientWidth - 2, 1);
  const px = (t) => ((Math.min(Math.max(t, from.getTime()), to.getTime()) - from.getTime()) / span) * plotWidth;
  const { placed, lanes } = assignLanes(timed);
  const lead = state.config.alarms.meetingLeadMinutes * 60_000;

  const ticks = [];
  for (let t = from.getTime(); t <= to.getTime(); t += 3_600_000) ticks.push(t);
  const tickEvery = plotWidth < 500 ? 2 : 1;

  // Each event is a thin bar for its duration with its title underneath; the title may run
  // on to the right until the next event in the same row, so short meetings stay readable.
  const marks = labelRoom(placed, to).map((ev) => {
    const start = Date.parse(ev.start);
    const end = Date.parse(ev.end);
    const phase = end <= now ? 'past' : start <= now ? 'current' : start - now <= lead ? 'soon' : 'future';
    const left = px(start);
    const barWidth = Math.max(px(end) - left, 4);
    const room = Math.max(px(Date.parse(ev.roomEnd)) - left - 8, barWidth);
    const label = `${fmtTime(ev.start)} to ${fmtTime(ev.end)}, ${ev.title}${ev.location ? `, ${ev.location}` : ''}`;
    const join = safeUrl(ev.joinUrl);
    const attrs = `class="mark ${phase}" style="left:${left}px;width:${room}px;top:${ev.lane * 44 + 6}px" title="${esc(label)}"`;
    const inner = `<span class="bar" style="width:${barWidth}px"></span><span class="mark-title">${esc(ev.title)}</span>`;
    return join
      ? `<a ${attrs} href="${esc(join)}" target="_blank" rel="noopener" aria-label="${esc(`Join: ${label}`)}">${inner}</a>`
      : `<div ${attrs} tabindex="0" aria-label="${esc(label)}">${inner}</div>`;
  });

  $('#trend').innerHTML = `
    <div class="plot" style="--lanes:${lanes}">
      <div class="plot-past" style="width:${px(now.getTime())}px"></div>
      ${ticks
        .map((t, i) => `<span class="tick" style="left:${px(t)}px">${i % tickEvery === 0 ? `<span>${String(new Date(t).getHours()).padStart(2, '0')}</span>` : ''}</span>`)
        .join('')}
      ${marks.join('')}
      ${timed.length ? '' : `<p class="plot-empty">${today_.length ? 'Nothing else in this window' : 'Nothing scheduled today'}</p>`}
      <div class="cursor" style="left:${px(now.getTime())}px"><span>${fmtTime(now)}</span></div>
    </div>`;
}

/* ---------- Calendar ---------- */

function renderAgenda() {
  const now = new Date();
  const events = (state.calendar?.events ?? []).filter((ev) =>
    ev.allDay ? (ev.endDate ?? ev.date) >= localDate(now) : Date.parse(ev.end) > now,
  );
  renderNextUp(now);

  if (!events.length) {
    $('#agenda').innerHTML = `<p class="empty">Nothing in the next ${state.config.agendaDays ?? 7} days.</p>`;
    return;
  }
  const byDay = new Map();
  for (const ev of events) {
    const key = ev.allDay ? (ev.date < localDate(now) ? localDate(now) : ev.date) : localDate(new Date(ev.start));
    if (!byDay.has(key)) byDay.set(key, []);
    byDay.get(key).push(ev);
  }
  const showCalendar = (state.calendar?.calendars?.length ?? new Set(events.map((e) => e.calendar)).size) > 1;
  $('#agenda').innerHTML = [...byDay.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(
      ([day, list]) => `
      <h3 class="day">${esc(dayLabel(day, now))}</h3>
      <ul class="events">
        ${list
          .map((ev) => {
            const running = !ev.allDay && Date.parse(ev.start) <= now;
            const join = safeUrl(ev.joinUrl);
            return `
            <li class="event ${running ? 'running' : ''}">
              <span class="event-time">${ev.allDay ? 'All day' : running ? 'Now' : fmtTime(ev.start)}</span>
              <div>
                <div class="event-title">${esc(ev.title)}</div>
                <div class="event-meta">
                  ${ev.allDay ? '' : `<span>${duration(Date.parse(ev.end) - Date.parse(ev.start))}</span>`}
                  ${ev.location ? `<span>${esc(ev.location)}</span>` : ''}
                  ${showCalendar ? `<span>${esc(ev.calendar)}</span>` : ''}
                  ${join ? `<a class="join" href="${esc(join)}" target="_blank" rel="noopener">Join</a>` : ''}
                </div>
              </div>
            </li>`;
          })
          .join('')}
      </ul>`,
    )
    .join('');
}

function renderNextUp(now = new Date()) {
  const timed = (state.calendar?.events ?? []).filter((ev) => !ev.allDay && Date.parse(ev.end) > now);
  const current = timed.filter((ev) => Date.parse(ev.start) <= now);
  const next = timed.find((ev) => Date.parse(ev.start) > now);
  const block = (lead, ev, meta) => {
    const join = safeUrl(ev.joinUrl);
    return `<div class="next-up"><p class="lead">${lead}</p><p class="meta">${meta}${
      join ? ` <a class="join" href="${esc(join)}" target="_blank" rel="noopener">Join</a>` : ''
    }</p></div>`;
  };
  const html = [
    ...current.map((ev) => block(`Now: ${esc(ev.title)}`, ev, `<span>Ends at ${fmtTime(ev.end)}, ${duration(Date.parse(ev.end) - now)} left</span>`)),
    next ? block(`Next: ${esc(next.title)}`, next, `<span>${dayLabel(next.start, now)} at ${fmtTime(next.start)}, in ${duration(Date.parse(next.start) - now)}</span>`) : '',
  ].join('');
  $('#next-up').innerHTML = html;
}

/* ---------- Tasks ---------- */

function taskBucket(task, now) {
  if (!task.due) return 'someday';
  const today = localDate(now);
  if (task.due.length > 10 ? Date.parse(task.due) < now : task.due < today) return 'overdue';
  return task.due.slice(0, 10) === today ? 'today' : 'upcoming';
}

function renderTasks() {
  const now = new Date();
  const tasks = state.tasks?.tasks ?? [];
  const groups = { overdue: [], today: [], upcoming: [], someday: [] };
  for (const task of tasks) groups[taskBucket(task, now)].push(task);
  const names = { overdue: 'Overdue', today: 'Due today', upcoming: 'Coming up', someday: 'No date' };

  if (!tasks.length) {
    $('#tasks').innerHTML = '<p class="empty">No open tasks. Add one above.</p>';
    return;
  }
  $('#tasks').innerHTML = Object.entries(groups)
    .filter(([, list]) => list.length)
    .map(
      ([key, list]) => `
      <h3 class="task-group">${key === 'overdue' ? shape('medium') : ''}${names[key]} <span>${list.length}</span></h3>
      <ul class="task-list">${list.map((t) => taskRow(t, key, now)).join('')}</ul>`,
    )
    .join('');
}

function taskRow(task, bucket, now) {
  const url = safeUrl(task.url);
  const due = task.due
    ? `${dayLabel(task.due.slice(0, 10), now)}${task.due.length > 10 ? ` at ${fmtTime(task.due)}` : ''}`
    : '';
  return `
    <li class="task ${bucket}">
      <button type="button" class="check" data-done="${esc(task.id)}" aria-label="${esc(`Mark done: ${task.title}`)}" title="Mark done"></button>
      <div>
        <div class="task-title">${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(task.title)}</a>` : esc(task.title)}</div>
        <div class="task-meta">
          ${due ? `<span class="due">${bucket === 'overdue' ? 'Was due ' : ''}${esc(due)}</span>` : ''}
          ${task.priority ? `<span>${esc(task.priority)} priority</span>` : ''}
          ${task.status ? `<span>${esc(task.status)}</span>` : ''}
        </div>
      </div>
    </li>`;
}

async function addTask(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const title = form.title.value.trim();
  if (!title) return;
  const offset = form.due.value;
  let due = null;
  if (offset !== '') {
    const d = new Date();
    d.setDate(d.getDate() + Number(offset));
    due = localDate(d);
  }
  form.querySelector('button').disabled = true;
  try {
    await api('/api/tasks', { method: 'POST', body: JSON.stringify({ title, due }) });
    form.reset();
    toast(state.status.tasks?.sample ? 'Task added to the sample list' : 'Task added to Notion');
    await load('tasks');
  } catch (error) {
    toast(`Task not added: ${error.message}`);
  } finally {
    form.querySelector('button').disabled = false;
  }
}

async function completeTask(button) {
  button.setAttribute('aria-busy', 'true');
  try {
    await api('/api/tasks/done', { method: 'POST', body: JSON.stringify({ id: button.dataset.done }) });
    toast('Marked done');
    await load('tasks');
  } catch (error) {
    button.removeAttribute('aria-busy');
    toast(`Not marked done: ${error.message}`);
  }
}

/* ---------- Today's three and notes ---------- */

async function loadNotes() {
  try {
    state.notes = await api('/api/notes');
  } catch {
    state.notes = { top3: [], scratch: '' };
  }
  renderTop3();
  $('#scratch').value = state.notes.scratch ?? '';
}

function renderTop3() {
  const items = [...(state.notes.top3 ?? [])];
  while (items.length < 3) items.push({ text: '', done: false });
  $('#top3').innerHTML = items
    .map(
      (item, i) => `
      <li class="${item.done ? 'done' : ''}">
        <input type="checkbox" data-top3-done="${i}" ${item.done ? 'checked' : ''} aria-label="Done">
        <input type="text" data-top3="${i}" value="${esc(item.text)}" maxlength="200" placeholder="${['Most important thing today', 'Second', 'Third'][i]}" aria-label="Priority ${i + 1}">
      </li>`,
    )
    .join('');
}

let saveTimer;
function saveNotes() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    const top3 = [0, 1, 2].map((i) => ({
      text: $(`[data-top3="${i}"]`).value,
      done: $(`[data-top3-done="${i}"]`).checked,
    }));
    try {
      state.notes = await api('/api/notes', { method: 'PUT', body: JSON.stringify({ top3, scratch: $('#scratch').value }) });
    } catch (error) {
      toast(`Notes not saved: ${error.message}`);
    }
  }, 500);
}

/* ---------- Feeds ---------- */

let xWidgets;
function loadXWidgets() {
  if (window.twttr?.widgets) return window.twttr.widgets.load($('#feed-body'));
  if (xWidgets) return;
  xWidgets = document.createElement('script');
  xWidgets.src = 'https://platform.twitter.com/widgets.js';
  xWidgets.async = true;
  document.head.append(xWidgets);
}

function renderFeeds() {
  const tabs = state.feeds?.tabs ?? [];
  if (!tabs.length) {
    $('#feed-tabs').innerHTML = '';
    $('#feed-body').innerHTML = '<p class="empty">No feeds yet. Add some under "feeds" in config.json.</p>';
    return;
  }
  if (state.feedTab >= tabs.length) state.feedTab = 0;
  $('#feed-tabs').innerHTML = tabs
    .map((tab, i) => {
      const watched = tab.items.some((it) => it.watch);
      const failed = tab.errors.length > 0;
      return `<button type="button" role="tab" data-tab="${i}" aria-selected="${i === state.feedTab}" tabindex="${i === state.feedTab ? 0 : -1}">${esc(tab.name)}${
        failed ? shape('diag') : watched ? shape('low') : ''
      }</button>`;
    })
    .join('');

  const tab = tabs[state.feedTab];
  const hint = $('#feed-hint');
  hint.hidden = !tab.hint;
  hint.innerHTML = tab.hint ? esc(tab.hint).replace(/([A-Z_]{4,}|\.env|config\.json|"x-embed")/g, '<code>$1</code>') : '';

  const now = new Date();
  const theme = getComputedStyle(document.documentElement).colorScheme === 'dark' ? 'dark' : 'light';
  const embeds = tab.embeds
    .map(safeUrl)
    .filter(Boolean)
    .map((url) => `<div class="embed"><a class="twitter-timeline" data-height="560" data-dnt="true" data-theme="${theme}" href="${esc(url)}">Posts from ${esc(url)}</a></div>`)
    .join('');
  const posts = tab.items
    .map((item) => {
      const link = safeUrl(item.link);
      return `
      <li class="post">
        <div class="post-meta">
          <span>${esc(item.source)}</span>
          ${item.date ? `<time datetime="${esc(item.date)}">${ago(item.date, now)}</time>` : ''}
          ${item.watch ? `<span class="watch-tag">${shape('low')} Watching ${esc(item.watch)}</span>` : ''}
        </div>
        ${link ? `<a class="post-title" href="${esc(link)}" target="_blank" rel="noopener">${esc(item.title)}</a>` : `<span class="post-title">${esc(item.title)}</span>`}
        ${item.summary && item.summary !== item.title ? `<p>${esc(item.summary)}</p>` : ''}
      </li>`;
    })
    .join('');
  const errors = tab.errors.map((e) => `<p class="hint">${shape('diag')} ${esc(e)}</p>`).join('');
  $('#feed-body').innerHTML = `${errors}${embeds}${posts ? `<ul class="posts">${posts}</ul>` : embeds ? '' : '<p class="empty">Nothing new in this feed.</p>'}`;
  if (embeds) loadXWidgets();
}

/* ---------- Systems ---------- */

function renderSystems() {
  const systems = state.systems?.systems ?? [];
  if (!systems.length) {
    $('#systems').innerHTML = '<li class="empty">Add servers, gateways or PLCs under "systems" in config.json to watch them here.</li>';
    return;
  }
  $('#systems').innerHTML = systems
    .map(
      (s) => `
      <li class="sys ${s.up ? 'ok' : 'down'}">
        ${s.up ? '<span class="indicator ok" aria-hidden="true"></span>' : `<span class="indicator">${shape(s.critical ? 'high' : 'low')}</span>`}
        <span class="sys-name" title="${esc(s.name)}">${esc(s.name)}</span>
        <span class="sys-state">${s.up ? `OK, ${s.latencyMs} ms` : `Down: ${esc(s.detail)}`}</span>
        <span class="sys-target" title="${esc(s.target)}">${esc(s.target)}</span>
      </li>`,
    )
    .join('');
}

/* ---------- Work tabs ---------- */

function renderLaunchpad() {
  const groups = state.config.launchpad ?? [];
  $('#config-file').textContent = `Edit in ${state.config.configFile === 'config.json' ? 'config.json' : 'config.json (copy config.example.json)'}`;
  $('#launchpad').innerHTML = groups
    .map(
      (group, i) => `
      <section>
        <div class="group-head">
          <h3>${esc(group.name)}</h3>
          ${group.links.length > 1 ? `<button type="button" data-open-group="${i}">Open all ${group.links.length}</button>` : ''}
        </div>
        <ul class="links">
          ${group.links
            .map((link) => {
              const url = safeUrl(link.url);
              return url
                ? `<li><a href="${esc(url)}" target="_blank" rel="noopener">${esc(link.label)}</a><span class="host">${esc(new URL(url).host)}</span></li>`
                : '';
            })
            .join('')}
        </ul>
      </section>`,
    )
    .join('');
}

function openGroup(index) {
  const group = state.config.launchpad[index];
  const urls = group.links.map((l) => safeUrl(l.url)).filter(Boolean);
  urls.forEach((url) => window.open(url, '_blank', 'noopener'));
  toast(`Opened ${urls.length} tabs. If only one appeared, allow pop-ups for this page.`);
}

/* ---------- Weather ---------- */

async function loadWeather() {
  const el = $('#weather');
  const coords = state.config.weather ? null : store.get('coords', null);
  if (!state.config.weather && !coords) {
    el.innerHTML = '<button type="button" class="tool" data-action="locate">Show weather</button>';
    return;
  }
  try {
    const q = coords ? `?lat=${coords.lat}&lon=${coords.lon}` : '';
    const w = await api(`/api/weather${q}`);
    const label = state.config.weather?.label;
    el.innerHTML = `<span class="temp">${w.temperature}${esc(w.units)}</span><span>${esc(w.condition)}</span><span>High ${w.high}°, low ${w.low}°${
      w.rainChance != null ? `, rain ${w.rainChance}%` : ''
    }</span>${label ? `<span>${esc(label)}</span>` : ''}`;
  } catch {
    el.innerHTML = '<span>Weather unavailable</span>';
  }
}

function locate() {
  if (!navigator.geolocation) return toast('This browser cannot share your location. Set weather in config.json instead.');
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      store.set('coords', { lat: pos.coords.latitude.toFixed(2), lon: pos.coords.longitude.toFixed(2) });
      loadWeather();
    },
    () => toast('Location blocked. Set weather.latitude and weather.longitude in config.json instead.'),
  );
}

/* ---------- Focus timer, clock, theme, notifications ---------- */

function startFocus(minutes) {
  state.focus = { endsAt: Date.now() + minutes * 60_000, minutes };
  store.set('focus', state.focus);
  toast(`Focus block started: ${minutes} min`);
  tick();
}

function stopFocus(message) {
  state.focus = null;
  store.set('focus', null);
  if (message) toast(message);
  tick();
}

function tick() {
  const now = new Date();
  $('#clock-time').textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  $('#clock-date').textContent = now.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' });
  const btn = $('#focus-btn');
  if (state.focus) {
    const left = state.focus.endsAt - now;
    if (left <= 0) {
      if (store.get('notify', false) && window.Notification?.permission === 'granted') notify('Focus block done', { body: 'Take a break.' });
      return stopFocus('Focus block done. Take a break.');
    }
    const m = Math.floor(left / 60_000);
    const s = Math.floor((left % 60_000) / 1000);
    btn.textContent = `Focus ${m}:${String(s).padStart(2, '0')} left, stop`;
    btn.setAttribute('aria-pressed', 'true');
  } else {
    btn.textContent = 'Start focus';
    btn.setAttribute('aria-pressed', 'false');
  }
}

function applyTheme(theme) {
  if (theme) document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
  const dark = getComputedStyle(document.documentElement).colorScheme === 'dark';
  $('#theme-btn').textContent = dark ? 'Light theme' : 'Dark theme';
}

function toggleTheme() {
  const dark = getComputedStyle(document.documentElement).colorScheme === 'dark';
  const next = dark ? 'light' : 'dark';
  store.set('theme', next);
  applyTheme(next);
  if (state.feeds) renderFeeds();
}

// Some mobile browsers only allow notifications from a service worker and throw here.
function notify(title, options) {
  try {
    new Notification(title, options);
  } catch {}
}

function renderNotifyButton() {
  const on = store.get('notify', false) && window.Notification?.permission === 'granted';
  const btn = $('#notify-btn');
  btn.textContent = on ? 'Notifications on' : 'Turn on notifications';
  btn.setAttribute('aria-pressed', String(on));
  btn.hidden = !('Notification' in window);
}

async function toggleNotifications() {
  if (store.get('notify', false) && Notification.permission === 'granted') {
    store.set('notify', false);
  } else {
    const permission = await Notification.requestPermission();
    store.set('notify', permission === 'granted');
    if (permission !== 'granted') toast('Notifications are blocked for this page in your browser settings.');
  }
  renderNotifyButton();
}

let toastTimer;
function toast(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3500);
}

/* ---------- Search palette ---------- */

function paletteItems() {
  const items = [
    { kind: 'Action', label: 'Start a 25 minute focus block', run: () => startFocus(25) },
    { kind: 'Action', label: 'Start a 50 minute focus block', run: () => startFocus(50) },
    ...(state.focus ? [{ kind: 'Action', label: 'Stop focus block', run: () => stopFocus('Focus block stopped') }] : []),
    { kind: 'Action', label: 'Acknowledge all alarms', run: () => acknowledge(state.alarms.map((a) => a.id)) },
    { kind: 'Action', label: 'Refresh everything', run: () => refreshAll(true) },
    { kind: 'Action', label: 'Switch theme', run: toggleTheme },
    { kind: 'Action', label: 'Add a task', run: () => $('#task-title').focus() },
  ];
  (state.config.launchpad ?? []).forEach((group, i) => {
    if (group.links.length > 1) items.push({ kind: 'Open all', label: `${group.name} (${group.links.length} tabs)`, run: () => openGroup(i) });
    for (const link of group.links) {
      const url = safeUrl(link.url);
      if (url) items.push({ kind: 'Link', label: `${link.label}`, detail: group.name, run: () => window.open(url, '_blank', 'noopener') });
    }
  });
  const now = new Date();
  for (const ev of state.calendar?.events ?? []) {
    if (!ev.allDay && Date.parse(ev.end) < now) continue;
    const join = safeUrl(ev.joinUrl);
    items.push({
      kind: 'Event',
      label: `${ev.title}, ${dayLabel(ev.allDay ? ev.date : ev.start, now)}${ev.allDay ? '' : ` ${fmtTime(ev.start)}`}`,
      run: join ? () => window.open(join, '_blank', 'noopener') : () => document.querySelector('.agenda').scrollIntoView({ behavior: 'smooth' }),
    });
  }
  for (const task of state.tasks?.tasks ?? []) {
    const url = safeUrl(task.url);
    items.push({
      kind: 'Task',
      label: task.title,
      run: url ? () => window.open(url, '_blank', 'noopener') : () => document.querySelector('.tasks').scrollIntoView({ behavior: 'smooth' }),
    });
  }
  return items;
}

const palette = { items: [], shown: [], index: 0 };

function openPalette() {
  palette.items = paletteItems();
  $('#palette-input').value = '';
  filterPalette();
  $('#palette').showModal();
  $('#palette-input').focus();
}

function filterPalette() {
  const words = $('#palette-input').value.toLowerCase().split(/\s+/).filter(Boolean);
  palette.shown = palette.items.filter((item) => {
    const hay = `${item.kind} ${item.label} ${item.detail ?? ''}`.toLowerCase();
    return words.every((w) => hay.includes(w));
  }).slice(0, 50);
  palette.index = 0;
  renderPalette();
}

function renderPalette() {
  $('#palette-list').innerHTML = palette.shown.length
    ? palette.shown
        .map(
          (item, i) => `<li role="option" id="pal-${i}" data-pal="${i}" aria-selected="${i === palette.index}">
            <span class="kind">${esc(item.kind)}</span><span class="label">${esc(item.label)}${item.detail ? ` <span class="kind">${esc(item.detail)}</span>` : ''}</span></li>`,
        )
        .join('')
    : '<li class="empty">No matches</li>';
  $('#palette-input').setAttribute('aria-activedescendant', palette.shown.length ? `pal-${palette.index}` : '');
  document.getElementById(`pal-${palette.index}`)?.scrollIntoView({ block: 'nearest' });
}

function runPalette(i) {
  const item = palette.shown[i];
  if (!item) return;
  $('#palette').close();
  item.run();
}

/* ---------- Wiring ---------- */

function refreshAll(force = false) {
  for (const name of Object.keys(SOURCES)) load(name, { force });
  loadWeather();
}

function bind() {
  document.addEventListener('click', (e) => {
    const t = e.target.closest('button, [data-pal]');
    if (!t) return;
    if (t.dataset.ack) acknowledge([t.dataset.ack]);
    else if (t.dataset.action === 'ack-all') acknowledge(state.alarms.map((a) => a.id));
    else if (t.dataset.action === 'toggle-alarms') {
      state.showAllAlarms = !state.showAllAlarms;
      renderAlarms();
    } else if (t.dataset.action === 'locate') locate();
    else if (t.dataset.done) completeTask(t);
    else if (t.dataset.tab) {
      state.feedTab = Number(t.dataset.tab);
      store.set('feedTab', state.feedTab);
      renderFeeds();
    } else if (t.dataset.openGroup) openGroup(Number(t.dataset.openGroup));
    else if (t.dataset.status) load(t.dataset.status, { force: true });
    else if (t.dataset.pal) runPalette(Number(t.dataset.pal));
  });

  $('#feed-tabs').addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const count = state.feeds?.tabs.length ?? 0;
    state.feedTab = (state.feedTab + (e.key === 'ArrowRight' ? 1 : count - 1)) % count;
    store.set('feedTab', state.feedTab);
    renderFeeds();
    $(`[data-tab="${state.feedTab}"]`).focus();
  });

  $('#task-form').addEventListener('submit', addTask);
  $('#top3').addEventListener('input', (e) => {
    if (e.target.dataset.top3Done) e.target.closest('li').classList.toggle('done', e.target.checked);
    saveNotes();
  });
  $('#scratch').addEventListener('input', saveNotes);

  $('#focus-btn').addEventListener('click', () => (state.focus ? stopFocus('Focus block stopped') : startFocus(25)));
  $('#theme-btn').addEventListener('click', toggleTheme);
  $('#notify-btn').addEventListener('click', toggleNotifications);
  $('#palette-btn').addEventListener('click', openPalette);

  $('#palette-input').addEventListener('input', filterPalette);
  $('#palette-input').addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const n = palette.shown.length;
      if (!n) return;
      palette.index = (palette.index + (e.key === 'ArrowDown' ? 1 : n - 1)) % n;
      renderPalette();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      runPalette(palette.index);
    }
  });

  document.addEventListener('keydown', (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName);
    if ((e.key === 'k' && (e.ctrlKey || e.metaKey)) || (e.key === '/' && !typing)) {
      e.preventDefault();
      if (!$('#palette').open) openPalette();
    }
  });

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'visible') return;
    for (const [name, src] of Object.entries(SOURCES)) {
      const at = state.status[name]?.at;
      if (!at || Date.now() - at > src.every) load(name);
    }
  });

  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => state.calendar && renderTrend(), 150);
  });
}

async function start() {
  applyTheme(store.get('theme', null));
  bind();
  tick();
  setInterval(tick, 1000);
  renderNotifyButton();

  try {
    state.config = await api('/api/config');
  } catch (error) {
    $('#alarms').innerHTML = `<p class="alarms-clear">${shape('diag')} Can't reach the control room server: ${esc(error.message)}. Is <code>npm start</code> running?</p>`;
    return;
  }
  $('#title').textContent = state.config.title;
  renderLaunchpad();
  renderAlarms();
  loadNotes();
  refreshAll();

  for (const [name, src] of Object.entries(SOURCES)) setInterval(() => load(name), src.every);
  setInterval(loadWeather, 15 * 60_000);
  // Countdowns, the now cursor and meeting alarms move with the clock.
  setInterval(() => {
    if (!state.calendar) return;
    renderTrend();
    renderNextUp();
    updateAlarms();
  }, 15_000);
}

start();
