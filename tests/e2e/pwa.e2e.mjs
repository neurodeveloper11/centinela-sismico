// End-to-end verification of the alert signal in a real Chrome (headless).
//
//   npm install && npm run test:e2e
//
// Seismic networks are simulated so every scenario is deterministic:
//   • EMSC live WebSocket  → page.routeWebSocket (we push events ourselves)
//   • USGS feeds / radial  → page.route fixtures
// Uses the locally installed Chrome (channel "chrome") or CHROME_PATH.

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'pwa');
const CALI = { lat: 3.4516, lon: -76.532 };
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.png': 'image/png' };

const results = [];
function check(name, ok, detail = '') {
  results.push({ name, ok: !!ok, detail });
  console.log(`${ok ? '✅' : '❌'} ${name}${detail ? ` — ${detail}` : ''}`);
}

function startServer() {
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const file = path.join(ROOT, urlPath === '/' ? 'index.html' : urlPath);
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404); res.end('not found'); return;
    }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

function emscMessage({ unid, lat, lon, depth, mag, timeMs, region }) {
  return JSON.stringify({
    action: 'create',
    data: {
      type: 'Feature', id: unid,
      geometry: { type: 'Point', coordinates: [lon, lat, -depth] },
      properties: { unid, lat, lon, depth, mag, magtype: 'mw', time: new Date(timeMs).toISOString(), flynn_region: region },
    },
  });
}

function usgsFeature({ id, lat, lon, depth, mag, timeMs, place }) {
  return {
    type: 'Feature', id,
    geometry: { type: 'Point', coordinates: [lon, lat, depth] },
    properties: { mag, time: timeMs, place, title: `M ${mag.toFixed(1)} - ${place}`, url: '' },
  };
}

async function launch() {
  const opts = { headless: true };
  if (process.env.CHROME_PATH) opts.executablePath = process.env.CHROME_PATH;
  else opts.channel = 'chrome';
  return chromium.launch(opts);
}

async function main() {
  const server = await startServer();
  const base = `http://127.0.0.1:${server.address().port}/`;
  const browser = await launch();
  let radialFeatures = [];

  try {
    // ------------------------------------------------------------------ deterministic context
    const context = await browser.newContext({ serviceWorkers: 'block', locale: 'es-ES', reducedMotion: 'reduce' });
    await context.addInitScript(([lat, lon]) => {
      if (sessionStorage.getItem('__seeded')) return;
      sessionStorage.setItem('__seeded', '1');
      localStorage.clear();
      localStorage.setItem('qm_user_lat', String(lat));
      localStorage.setItem('qm_user_lon', String(lon));
      localStorage.setItem('qm_user_city', 'Cali / Valle del Cauca');
      localStorage.setItem('qm_alert_mode', 'visual_only');
      localStorage.setItem('qm_lang', 'es');
    }, [CALI.lat, CALI.lon]);

    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(`pageerror: ${e.message}`));
    page.on('console', m => { if (m.type() === 'error') errors.push(`console: ${m.text()}`); });

    await page.route('https://earthquake.usgs.gov/**', route => {
      const url = route.request().url();
      const now = Date.now();
      let body;
      if (url.includes('all_day')) {
        body = { metadata: { generated: now }, features: [
          usgsFeature({ id: 'xss1', lat: 4.0, lon: -75.0, depth: 30, mag: 3.1, timeMs: now - 600000, place: '<img src=x onerror="window.__xss=1">Colombia' }),
        ] };
      } else if (url.includes('fdsnws')) {
        body = { metadata: { generated: now }, features: radialFeatures };
      } else {
        body = { metadata: { generated: now }, features: [] };
      }
      route.fulfill({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(body) });
    });
    await page.route('https://www.seismicportal.eu/fdsnws/**', route =>
      route.fulfill({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify({ features: [] }) }));
    await page.route('https://api.bigdatacloud.net/**', route => route.abort());

    let ws = null;
    await page.routeWebSocket('wss://www.seismicportal.eu/standing_order/websocket', socket => { ws = socket; socket.onMessage(() => {}); });

    const t0 = Date.now();
    await page.goto(base, { waitUntil: 'load' });
    const dcl = await page.evaluate(() => performance.getEntriesByType('navigation')[0].domContentLoadedEventEnd);
    check('Carga rápida (DOMContentLoaded < 1500 ms)', dcl < 1500, `${Math.round(dcl)} ms`);
    check('Núcleo científico cargado (SeismicCore)', await page.evaluate(() => typeof window.SeismicCore === 'object'));
    await page.waitForFunction(() => document.documentElement.lang === 'es');

    for (let i = 0; i < 50 && !ws; i++) await page.waitForTimeout(100);
    check('Canal en vivo EMSC (WebSocket) conectado', !!ws, `${Date.now() - t0} ms tras navegar`);

    // Instrument alert entry points (global function declarations are window properties)
    await page.evaluate(() => {
      window.__alerts = [];
      const fe = window.fireEarlyWarning, fn = window.showFeltNotice;
      window.fireEarlyWarning = function (...a) { window.__alerts.push(['incoming', a[0], a[3]]); return fe.apply(this, a); };
      window.showFeltNotice = function (...a) { window.__alerts.push(['felt', a[0].title]); return fn.apply(this, a); };
    });
    const bannerVisible = () => page.evaluate(() => getComputedStyle(document.getElementById('alertBanner')).display !== 'none');
    const alerts = () => page.evaluate(() => window.__alerts.slice());

    // 1) XSS in external place names
    await page.waitForFunction(() => document.getElementById('pulseListContainer').textContent.includes('Colombia'));
    const xss = await page.evaluate(() => ({ fired: window.__xss === 1, text: document.getElementById('pulseListContainer').textContent.includes('<img') }));
    check('Seguridad: nombres de lugar externos no ejecutan HTML (XSS)', !xss.fired && xss.text);

    // 2) Deep nearby event must NOT alarm (the old code read EMSC depth as −150 km → 1 km)
    ws.send(emscMessage({ unid: 'deep1', lat: 3.99, lon: -76.53, depth: 150, mag: 6.0, timeMs: Date.now() - 3000, region: 'COLOMBIA PROFUNDO' }));
    await page.waitForTimeout(600);
    const shield = await page.textContent('#shieldStatusTitle');
    check('Precisión: sismo profundo (150 km) cercano no genera falsa alarma', !(await bannerVisible()) && (await alerts()).length === 0 && shield.includes('Imperceptible'), shield.trim());

    // 3) Strong incoming event via WebSocket → countdown alert, fast
    const origin = Date.now() - 5000;
    const expected = Math.sqrt(120.9 ** 2 + 15 ** 2) / 3.5 - 5; // ≈ 29.8 s
    const sendAt = Date.now();
    ws.send(emscMessage({ unid: 'strong1', lat: 4.53, lon: -76.53, depth: 15, mag: 6.5, timeMs: origin, region: 'NEAR COAST OF COLOMBIA' }));
    await page.waitForFunction(() => getComputedStyle(document.getElementById('alertBanner')).display !== 'none', null, { timeout: 3000 });
    const latency = Date.now() - sendAt;
    check('Velocidad: alerta visible < 500 ms desde que llega el mensaje en vivo', latency < 500, `${latency} ms`);
    const shown = await page.evaluate(() => ({
      badge: document.getElementById('alertTypeBadge').textContent,
      count: parseInt(document.getElementById('countdownSec').textContent, 10),
      details: document.getElementById('alertDetails').textContent,
    }));
    check('Señal: alerta REAL con cuenta regresiva correcta (±2 s)', shown.badge.includes('REAL') && Math.abs(shown.count - expected) <= 2, `${shown.count}s vs ${expected.toFixed(1)}s esperado`);
    check('Señal: incluye distancia, magnitud e intensidad con rango', /Distancia: 1\d\d km/.test(shown.details) && shown.details.includes('M6.5') && /MMI \d\.\d \(rango [IVX]+–[IVX]+/.test(shown.details), shown.details);

    // 4) Same quake published by USGS radial query with another id → no duplicate alert
    radialFeatures = [usgsFeature({ id: 'us7000dup', lat: 4.55, lon: -76.51, depth: 12, mag: 6.4, timeMs: origin + 2000, place: 'near Cali, Colombia' })];
    await page.waitForTimeout(6500);
    const afterDup = await alerts();
    const countNow = await page.evaluate(() => parseInt(document.getElementById('countdownSec').textContent, 10));
    check('Sin duplicados: el mismo sismo por USGS (otro id) no repite la alerta', afterDup.length === 1, JSON.stringify(afterDup));
    check('Cuenta regresiva anclada al reloj (baja ~6–7 s en 6.5 s)', countNow <= shown.count - 5 && countNow >= shown.count - 8, `${shown.count}s → ${countNow}s`);
    radialFeatures = [];

    // 5) Strong nearby quake whose wave already passed → "felt" notice (not silence, not siren)
    await page.click('#btnDismissAlert');
    ws.send(emscMessage({ unid: 'felt1', lat: 3.1, lon: -76.9, depth: 20, mag: 6.0, timeMs: Date.now() - 180000, region: 'VALLE DEL CAUCA' }));
    await page.waitForFunction(() => document.getElementById('alertBanner').classList.contains('is-felt'), null, { timeout: 3000 }).catch(() => {});
    const felt = await page.evaluate(() => ({ cls: document.getElementById('alertBanner').className, title: document.getElementById('alertMainTitle').textContent }));
    check('Señal post-evento: sismo fuerte ya ocurrido se comunica (aviso "sentido")', felt.cls.includes('is-felt') && felt.title.includes('probablemente sentido'), felt.title);

    // 6) Distant strong quake → zero alarm fatigue
    await page.click('#btnDismissAlert');
    const before = (await alerts()).length;
    ws.send(emscMessage({ unid: 'tokyo1', lat: 35.68, lon: 139.65, depth: 30, mag: 6.9, timeMs: Date.now() - 2000, region: 'NEAR EAST COAST OF HONSHU, JAPAN' }));
    await page.waitForTimeout(600);
    check('Cero fatiga: sismo lejano (Japón) no alarma', (await alerts()).length === before && !(await bannerVisible()));

    // 7) Photosensitive safety of the rescue strobe (WCAG 2.3.1: ≤ 3 flashes/s)
    await page.click('#btnStrobe');
    const changes = await page.evaluate(async () => {
      const el = document.getElementById('strobeOverlay');
      let last = el.style.backgroundColor, n = 0;
      const end = performance.now() + 2000;
      while (performance.now() < end) {
        await new Promise(r => setTimeout(r, 10));
        if (el.style.backgroundColor !== last) { n++; last = el.style.backgroundColor; }
      }
      return n;
    });
    await page.click('#strobeOverlay');
    const flashesPerSec = changes / 2 / 2;
    check('Seguridad fotosensible: baliza ≤ 3 destellos/s', flashesPerSec <= 3, `${flashesPerSec.toFixed(2)} destellos/s`);

    // 8) Language persists across reloads and updates <html lang>
    await page.click('#langToggle');
    await page.reload({ waitUntil: 'load' });
    const lang = await page.evaluate(() => [document.documentElement.lang, document.getElementById('radarTitle').textContent]);
    check('Idioma persistente y <html lang> correcto tras recargar', lang[0] === 'en' && !lang[1].includes('Radar Sísmico Anticipado'), lang.join(' | '));

    check('Sin errores de JavaScript ni de consola', errors.length === 0, errors.slice(0, 3).join(' || '));
    await context.close();

    // ------------------------------------------------------------------ offline (Service Worker)
    const ctx2 = await browser.newContext();
    const p2 = await ctx2.newPage();
    await p2.route('https://**', r => r.abort());
    await p2.goto(base, { waitUntil: 'load' });
    await p2.evaluate(() => navigator.serviceWorker.ready);
    // clients.claim() must take control WITHOUT reloading the page on first install
    const navsBefore = await p2.evaluate(() => performance.getEntriesByType('navigation').length + ':' + performance.timeOrigin);
    const controlled = await p2.waitForFunction(() => !!navigator.serviceWorker.controller, null, { timeout: 5000 }).then(() => true).catch(() => false);
    await p2.waitForTimeout(500);
    const navsAfter = await p2.evaluate(() => performance.getEntriesByType('navigation').length + ':' + performance.timeOrigin);
    check('Primera instalación del Service Worker sin recarga inesperada', navsBefore === navsAfter);
    await ctx2.setOffline(true);
    let offlineOk = false;
    try {
      await p2.reload({ waitUntil: 'load' });
      offlineOk = await p2.evaluate(() => typeof window.SeismicCore === 'object' && !!document.getElementById('btnSound'));
    } catch (e) { offlineOk = false; }
    check('Offline: la app completa carga sin internet (Service Worker)', controlled && offlineOk);
    await ctx2.close();
  } finally {
    await browser.close();
    server.close();
  }

  if (process.env.E2E_REPORT) fs.writeFileSync(process.env.E2E_REPORT, JSON.stringify(results, null, 2));
  const failed = results.filter(r => !r.ok);
  console.log(`\n${failed.length === 0 ? '🟢 E2E OK' : '🔴 E2E FALLÓ'}: ${results.length - failed.length}/${results.length} verificaciones`);
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch(err => { console.error(err); process.exit(1); });
