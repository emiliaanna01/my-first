import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readRss, mapXResponse, markWatched } from '../server/feeds.js';

const rss = `<?xml version="1.0"?><rss version="2.0"><channel><title>ICS Advisories</title>
<item><title>Siemens SIMATIC S7-1500 CPU</title><link>https://example.com/a</link><guid>a</guid><pubDate>Thu, 23 Oct 2026 12:00:00 GMT</pubDate><description>&lt;p&gt;Details &lt;b&gt;here&lt;/b&gt;&lt;/p&gt;</description></item>
<item><title>Rockwell Automation FactoryTalk</title><link>https://example.com/b</link><guid>b</guid></item>
</channel></rss>`;

test('readRss parses items and strips markup from summaries', async () => {
  const items = await readRss('https://feed', 'CISA', async () => new Response(rss));
  assert.equal(items.length, 2);
  assert.equal(items[0].source, 'CISA');
  assert.equal(items[0].summary, 'Details here');
  assert.equal(items[0].date, '2026-10-23T12:00:00.000Z');
});

test('readRss surfaces HTTP errors', async () => {
  await assert.rejects(readRss('https://feed', 'x', async () => new Response('', { status: 403 })), /HTTP 403/);
});

test('markWatched flags whole-word keyword matches only', () => {
  const items = [{ title: 'Siemens SIMATIC S7-1500' }, { title: 'Siemensstrasse news' }, { title: 'ABB drives' }];
  const marked = markWatched(items, ['Siemens', 'ABB']);
  assert.deepEqual(marked.map((i) => i.watch), ['Siemens', undefined, 'ABB']);
  assert.equal(markWatched(items), items);
});

test('mapXResponse builds links from the author handle', () => {
  const posts = mapXResponse({
    data: [{ id: '42', text: 'New firmware out', author_id: 'u1', created_at: '2026-10-25T08:00:00.000Z' }],
    includes: { users: [{ id: 'u1', username: 'plc_news', name: 'PLC News' }] },
  });
  assert.deepEqual(posts, [{ id: '42', title: 'New firmware out', link: 'https://x.com/plc_news/status/42', date: '2026-10-25T08:00:00.000Z', source: '@plc_news' }]);
});
