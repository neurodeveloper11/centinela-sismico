// Live smoke test against the REAL USGS / EMSC services (network required, not run in CI).
//   node tests/e2e/live-smoke.mjs
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'pwa');
const server = http.createServer((req, res) => {
  const p = new URL(req.url, 'http://x').pathname;
  const file = path.join(ROOT, p === '/' ? 'index.html' : p);
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript' : file.endsWith('.html') ? 'text/html; charset=utf-8' : 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' });
const ctx = await browser.newContext({ serviceWorkers: 'block' });
await ctx.addInitScript(() => { localStorage.setItem('qm_user_lat', '3.4516'); localStorage.setItem('qm_user_lon', '-76.532'); localStorage.setItem('qm_alert_mode', 'visual_only'); });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto(`http://127.0.0.1:${server.address().port}/`, { waitUntil: 'load' });
await page.waitForFunction(() => /Última revisión|Last review/.test(document.getElementById('lastFeedCheck').textContent), null, { timeout: 20000 });
await page.waitForFunction(() => document.querySelectorAll('.pulse-card').length > 0, null, { timeout: 20000 });
const info = await page.evaluate(() => ({
  feed: document.getElementById('lastFeedCheck').textContent.trim(),
  cards: document.querySelectorAll('.pulse-card').length,
  count: document.getElementById('pulseCountText').textContent,
  shield: document.getElementById('shieldStatusTitle').textContent.trim(),
}));
console.log(JSON.stringify(info, null, 1));
console.log(errors.length ? `❌ errores: ${errors.join(' | ')}` : '✅ sin errores de consola ni violaciones CSP con APIs reales');
await browser.close(); server.close();
process.exit(errors.length ? 1 : 0);
