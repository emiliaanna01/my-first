import Parser from 'rss-parser';

const parser = new Parser();

const clip = (s = '', n = 220) => {
  const flat = s.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  return flat.length > n ? `${flat.slice(0, n - 1)}…` : flat;
};

export async function readRss(url, label, fetchImpl = fetch) {
  const res = await fetchImpl(url, {
    headers: { 'User-Agent': 'control-room/0.1 (personal dashboard)', Accept: 'application/rss+xml, application/atom+xml, text/xml;q=0.9, */*;q=0.5' },
    signal: AbortSignal.timeout(10_000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const feed = await parser.parseString(await res.text());
  return feed.items.slice(0, 20).map((item) => ({
    id: item.guid || item.link,
    title: clip(item.title, 200) || '(untitled)',
    summary: clip((item.contentSnippet || item.content || '').replace(/^\s*View CSAF\s+Summary\s*/i, '')),
    link: item.link,
    date: item.isoDate || null,
    source: label || feed.title,
  }));
}

// X API v2. Reading posts needs a paid API plan; without a token the tab
// falls back to the official embedded timeline or RSS sources.
export function createX({ token, fetchImpl = fetch }) {
  const userIds = new Map();

  async function call(path) {
    const res = await fetchImpl(`https://api.x.com/2${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(10_000),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(`X ${res.status}: ${data.title ?? data.detail ?? res.statusText}`);
    return data;
  }

  async function userId(username) {
    if (!userIds.has(username)) {
      const { data } = await call(`/users/by/username/${encodeURIComponent(username)}`);
      userIds.set(username, data.id);
    }
    return userIds.get(username);
  }

  return async function readX({ user, list }) {
    const fields = 'max_results=15&tweet.fields=created_at&expansions=author_id&user.fields=username,name';
    const path = list
      ? `/lists/${encodeURIComponent(list)}/tweets?${fields}`
      : `/users/${await userId(user.replace(/^@/, ''))}/tweets?exclude=replies&${fields}`;
    return mapXResponse(await call(path));
  };
}

export function mapXResponse({ data = [], includes = {} }) {
  const users = new Map((includes.users ?? []).map((u) => [u.id, u]));
  return data.map((post) => {
    const author = users.get(post.author_id);
    const handle = author?.username ?? 'i';
    return {
      id: post.id,
      title: post.text,
      link: `https://x.com/${handle}/status/${post.id}`,
      date: post.created_at ?? null,
      source: author ? `@${author.username}` : 'X',
    };
  });
}

// Flag items whose title names a watched keyword (e.g. a vendor in an ICS advisory feed).
export function markWatched(items, keywords = []) {
  if (!keywords.length) return items;
  const patterns = keywords.map((k) => [k, new RegExp(`\\b${k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')]);
  return items.map((item) => {
    const hit = patterns.find(([, re]) => re.test(item.title));
    return hit ? { ...item, watch: hit[0] } : item;
  });
}
