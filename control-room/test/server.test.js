import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createCache } from '../server/cache.js';
import { createNotes } from '../server/notes.js';

test('cache shares in-flight loads and respects force', async () => {
  const cached = createCache();
  let calls = 0;
  const load = async () => ++calls;
  const [a, b] = await Promise.all([cached('k', 60_000, load), cached('k', 60_000, load)]);
  assert.equal(a, 1);
  assert.equal(b, 1);
  assert.equal(await cached('k', 60_000, load), 1);
  assert.equal(await cached('k', 60_000, load, { force: true }), 2);
});

test('cache does not keep failures', async () => {
  const cached = createCache();
  await assert.rejects(cached('k', 60_000, async () => { throw new Error('down'); }));
  assert.equal(await cached('k', 60_000, async () => 'up'), 'up');
});

test('notes roll unfinished items over to the next day', async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'control-room-'));
  const notes = createNotes(dir);
  await notes.write('2026-10-24', { top3: [{ text: 'Finish FAT report', done: false }, { text: 'Call vendor', done: true }], scratch: 'hi' });
  const next = await notes.read('2026-10-25');
  assert.deepEqual(next.top3, [{ text: 'Finish FAT report', done: false }]);
  assert.equal(next.scratch, 'hi');
  await fs.rm(dir, { recursive: true });
});

test('isPrivateTarget spots plant and home network addresses', async () => {
  const { isPrivateTarget } = await import('../server/systems.js');
  assert.equal(isPrivateTarget({ type: 'tcp', host: '192.168.1.10', port: 502 }), true);
  assert.equal(isPrivateTarget({ type: 'http', url: 'http://localhost:8088/StatusPing' }), true);
  assert.equal(isPrivateTarget({ type: 'http', url: 'http://172.20.0.5' }), true);
  assert.equal(isPrivateTarget({ type: 'http', url: 'http://historian.local' }), true);
  assert.equal(isPrivateTarget({ type: 'http', url: 'https://github.com' }), false);
  assert.equal(isPrivateTarget({ type: 'http', url: 'http://172.32.0.1' }), false);
});
