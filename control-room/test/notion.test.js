import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createNotion, pickProperties, mapTask } from '../server/notion.js';

const properties = {
  Name: { type: 'title' },
  Status: { type: 'status' },
  'Due date': { type: 'date' },
  Priority: { type: 'select' },
  Created: { type: 'created_time' },
};

test('pickProperties guesses title, status, due and priority', () => {
  assert.deepEqual(pickProperties(properties), {
    title: 'Name',
    status: { name: 'Status', type: 'status' },
    due: 'Due date',
    priority: 'Priority',
  });
});

test('pickProperties falls back to a Done checkbox', () => {
  const s = pickProperties({ Task: { type: 'title' }, Done: { type: 'checkbox' } });
  assert.deepEqual(s.status, { name: 'Done', type: 'checkbox' });
});

test('mapTask flattens a Notion page', () => {
  const s = pickProperties(properties);
  const task = mapTask(
    {
      id: 'p1',
      url: 'https://www.notion.so/p1',
      properties: {
        Name: { title: [{ plain_text: 'Back up ' }, { plain_text: 'PLC-02' }] },
        Status: { type: 'status', status: { name: 'In progress' } },
        'Due date': { date: { start: '2026-10-25' } },
        Priority: { select: { name: 'High' } },
      },
    },
    s,
  );
  assert.deepEqual(task, { id: 'p1', title: 'Back up PLC-02', url: 'https://www.notion.so/p1', due: '2026-10-25', status: 'In progress', priority: 'High' });
});

test('client resolves the data source, filters out done tasks and completes tasks', async () => {
  const calls = [];
  const fetchImpl = async (url, init) => {
    calls.push({ url, method: init.method, body: init.body && JSON.parse(init.body), version: init.headers['Notion-Version'] });
    if (url.endsWith('/databases/0123456789abcdef0123456789abcdef')) return Response.json({ data_sources: [{ id: 'ds-1' }] });
    if (url.endsWith('/data_sources/ds-1')) return Response.json({ id: 'ds-1', properties });
    if (url.endsWith('/data_sources/ds-1/query')) return Response.json({ results: [] });
    if (url.includes('/pages/')) return Response.json({});
    return Response.json({ message: 'not found' }, { status: 404 });
  };
  const notion = createNotion({ token: 't', databaseId: 'https://www.notion.so/ws/0123456789abcdef0123456789abcdef?v=1', fetchImpl });
  await notion.listTasks();
  await notion.completeTask('page-9');

  const query = calls.find((c) => c.url.endsWith('/query'));
  assert.equal(query.version, '2025-09-03');
  assert.deepEqual(query.body.filter, { property: 'Status', status: { does_not_equal: 'Done' } });
  assert.deepEqual(query.body.sorts, [{ property: 'Due date', direction: 'ascending' }]);
  const patch = calls.find((c) => c.method === 'PATCH');
  assert.deepEqual(patch.body, { properties: { Status: { status: { name: 'Done' } } } });
  assert.equal(calls.filter((c) => c.url.endsWith('/data_sources/ds-1')).length, 1, 'schema is fetched once');
});

test('client reports Notion errors with their message', async () => {
  const fetchImpl = async () => Response.json({ message: 'API token is invalid.' }, { status: 401 });
  const notion = createNotion({ token: 'bad', databaseId: 'abc', fetchImpl });
  await assert.rejects(notion.listTasks(), /Notion 401: API token is invalid/);
});
