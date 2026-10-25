import net from 'node:net';

const REASONS = {
  ECONNREFUSED: 'Connection refused',
  ENOTFOUND: 'Host not found',
  EHOSTUNREACH: 'Host unreachable',
  ENETUNREACH: 'Network unreachable',
  ECONNRESET: 'Connection reset',
  CERT_HAS_EXPIRED: 'Certificate expired',
};

// Reachability checks: HTTP(S) endpoints, or a raw TCP port (Modbus 502, EtherNet/IP 44818, OPC UA 4840, ...).
export async function checkSystem(system, { timeoutMs = 4000 } = {}) {
  const started = performance.now();
  const done = (up, detail) => ({
    name: system.name,
    target: system.url ?? `${system.host}:${system.port}`,
    critical: Boolean(system.critical),
    up,
    detail,
    latencyMs: up ? Math.round(performance.now() - started) : null,
    checkedAt: new Date().toISOString(),
  });

  try {
    if (system.type === 'tcp') {
      await tcpConnect(system.host, Number(system.port), timeoutMs);
      return done(true, 'Port open');
    }
    const res = await fetch(system.url, { redirect: 'follow', signal: AbortSignal.timeout(timeoutMs) });
    await res.body?.cancel().catch(() => {});
    const expected = system.expectStatus ?? null;
    const up = expected ? res.status === expected : res.status < 500;
    return done(up, `HTTP ${res.status}`);
  } catch (error) {
    const code = error.cause?.code ?? error.code;
    const reason = error.name === 'TimeoutError' ? `No answer in ${timeoutMs / 1000} s` : REASONS[code] ?? code ?? error.message;
    return done(false, reason);
  }
}

function tcpConnect(host, port, timeoutMs) {
  return new Promise((resolve, reject) => {
    const socket = net.connect({ host, port });
    const fail = (error) => {
      socket.destroy();
      reject(error);
    };
    socket.setTimeout(timeoutMs, () => fail(Object.assign(new Error('timeout'), { name: 'TimeoutError' })));
    socket.once('connect', () => {
      socket.end();
      resolve();
    });
    socket.once('error', fail);
  });
}

// A cloud server can't see your plant or home network, so hosted copies skip these.
export function isPrivateTarget(system) {
  let host = system.host;
  try {
    host ??= new URL(system.url).hostname;
  } catch {
    return false;
  }
  return /^(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|169\.254\.|\[?::1\]?$)|\.local$/i.test(host);
}

export function checkAll(systems) {
  return Promise.all(systems.map((s) => checkSystem(s)));
}
