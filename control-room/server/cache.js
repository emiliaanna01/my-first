// Small TTL cache so a dashboard left open all day doesn't hammer the upstream APIs.
// Concurrent callers for the same key share one in-flight request.
export function createCache() {
  const entries = new Map();

  return async function cached(key, ttlMs, load, { force = false } = {}) {
    const entry = entries.get(key);
    const now = Date.now();
    if (entry && !force) {
      if (entry.pending) return entry.pending;
      if (now - entry.at < ttlMs) return entry.value;
    }
    const pending = Promise.resolve()
      .then(load)
      .then(
        (value) => {
          entries.set(key, { value, at: Date.now() });
          return value;
        },
        (error) => {
          entries.delete(key);
          throw error;
        },
      );
    entries.set(key, { ...entry, pending });
    return pending;
  };
}
