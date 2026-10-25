import fs from 'node:fs/promises';
import path from 'node:path';

// "Today's three" and the scratchpad, kept in data/notes.json next to the app.
// Unfinished items roll over to the next day.
export function createNotes(dir) {
  const file = path.join(dir, 'notes.json');

  async function read(today) {
    let saved = { date: today, top3: [], scratch: '' };
    try {
      saved = JSON.parse(await fs.readFile(file, 'utf8'));
    } catch {}
    if (saved.date !== today) {
      saved = { ...saved, date: today, top3: (saved.top3 ?? []).filter((t) => !t.done) };
    }
    return saved;
  }

  async function write(today, { top3 = [], scratch = '' }) {
    const clean = {
      date: today,
      top3: top3.slice(0, 3).map((t) => ({ text: String(t.text ?? '').slice(0, 200), done: Boolean(t.done) })),
      scratch: String(scratch).slice(0, 20_000),
    };
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(file, JSON.stringify(clean, null, 2));
    return clean;
  }

  return { read, write };
}
