import http from 'node:http';
import { handler, summary } from './app.js';

const port = Number(process.env.PORT ?? 4300);
const host = process.env.HOST ?? '127.0.0.1';
http.createServer(handler).listen(port, host, () => {
  console.log(`Control room running at http://${host === '0.0.0.0' ? 'localhost' : host}:${port}`);
  for (const [key, value] of Object.entries(summary)) console.log(`  ${key}: ${value}`);
});
