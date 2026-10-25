// Notion tasks through the data-source API (Notion-Version 2025-09-03).
const API = 'https://api.notion.com/v1';
const VERSION = '2025-09-03';

const plain = (rich = []) => rich.map((r) => r.plain_text).join('');

export function createNotion({ token, databaseId, titleProperty, statusProperty, doneValue = 'Done', dueProperty, fetchImpl = fetch }) {
  let schema; // resolved once: { dataSourceId, title, status: {name, type}, due, priority }

  async function call(method, path, body) {
    const res = await fetchImpl(`${API}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        'Notion-Version': VERSION,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(10_000),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(`Notion ${res.status}: ${data.message ?? res.statusText}`);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  // Accepts a database ID (from the database URL) or a data source ID.
  async function resolveSchema() {
    if (schema) return schema;
    const id = databaseId.replace(/-/g, '').match(/[0-9a-f]{32}/i)?.[0] ?? databaseId;
    let dataSourceId = id;
    try {
      const db = await call('GET', `/databases/${id}`);
      dataSourceId = db.data_sources?.[0]?.id ?? id;
    } catch (error) {
      if (error.status !== 404 && error.status !== 400) throw error;
    }
    const ds = await call('GET', `/data_sources/${dataSourceId}`);
    schema = { dataSourceId: ds.id, ...pickProperties(ds.properties, { titleProperty, statusProperty, dueProperty }) };
    return schema;
  }

  async function listTasks() {
    const s = await resolveSchema();
    const body = { page_size: 100 };
    if (s.status?.type === 'status') body.filter = { property: s.status.name, status: { does_not_equal: doneValue } };
    else if (s.status?.type === 'select') body.filter = { property: s.status.name, select: { does_not_equal: doneValue } };
    else if (s.status?.type === 'checkbox') body.filter = { property: s.status.name, checkbox: { equals: false } };
    if (s.due) body.sorts = [{ property: s.due, direction: 'ascending' }];
    const data = await call('POST', `/data_sources/${s.dataSourceId}/query`, body);
    return data.results.map((page) => mapTask(page, s));
  }

  async function addTask({ title, due }) {
    const s = await resolveSchema();
    const properties = { [s.title]: { title: [{ text: { content: title } }] } };
    if (due && s.due) properties[s.due] = { date: { start: due } };
    const page = await call('POST', '/pages', {
      parent: { type: 'data_source_id', data_source_id: s.dataSourceId },
      properties,
    });
    return mapTask(page, s);
  }

  async function completeTask(pageId) {
    const s = await resolveSchema();
    if (!s.status) throw new Error('No status or checkbox property found to mark tasks done.');
    const value =
      s.status.type === 'checkbox'
        ? { checkbox: true }
        : { [s.status.type]: { name: doneValue } };
    await call('PATCH', `/pages/${pageId}`, { properties: { [s.status.name]: value } });
  }

  return { listTasks, addTask, completeTask };
}

// Use the configured property names, otherwise guess from the database's schema.
export function pickProperties(properties, wanted = {}) {
  const entries = Object.entries(properties);
  const byType = (type, pattern) =>
    entries.find(([name, p]) => p.type === type && (!pattern || pattern.test(name)))?.[0];

  const title = wanted.titleProperty || byType('title');
  let status;
  const statusName =
    wanted.statusProperty ||
    byType('status') ||
    byType('checkbox', /done|complete|finished/i) ||
    byType('select', /status|state/i);
  if (statusName && properties[statusName]) status = { name: statusName, type: properties[statusName].type };
  const due = wanted.dueProperty || byType('date', /due|deadline|date|when/i) || byType('date');
  const priority = byType('select', /priority|prio/i);
  return { title, status, due, priority };
}

export function mapTask(page, s) {
  const props = page.properties ?? {};
  const statusProp = s.status ? props[s.status.name] : undefined;
  const status =
    statusProp?.type === 'checkbox'
      ? statusProp.checkbox ? 'Done' : 'Open'
      : statusProp?.[statusProp?.type]?.name;
  return {
    id: page.id,
    title: plain(props[s.title]?.title) || 'Untitled',
    url: page.url,
    due: s.due ? props[s.due]?.date?.start ?? null : null,
    status: status ?? null,
    priority: s.priority ? props[s.priority]?.select?.name ?? null : null,
  };
}
