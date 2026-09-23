// Pruebas del núcleo científico compartido (node --test tests/js)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const core = require('../../pwa/seismic-core.js');

const CALI = { lat: 3.4516, lon: -76.532 };

test('haversine: Cali–Bogotá ≈ 300 km y distancia nula', () => {
  const d = core.haversine(3.4516, -76.532, 4.711, -74.0721);
  assert.ok(d > 280 && d < 320, `got ${d}`);
  assert.equal(core.haversine(10, 20, 10, 20), 0);
});

test('distancia hipocentral pitagórica y profundidad mínima 1 km', () => {
  assert.equal(core.hypocentralDistance(30, 40), 50);
  assert.equal(core.hypocentralDistance(0, -7), 1);
});

test('IPE Allen 2012 reproduce los valores de referencia de OpenQuake', () => {
  // Valores calculados a mano con los coeficientes de allen_2012_ipe.AllenEtAl2012Rhypo
  const cases = [
    [7.0, 10, 8.0293],
    [7.0, 100, 5.6632],
    [5.0, 20, 5.0182],
    [6.0, 50, 5.1604],
  ];
  for (const [m, r, expected] of cases) {
    const rm = -0.209 + 2.042 * Math.exp(m - 5);
    let ref = 2.085 + 1.428 * m - 1.402 * Math.log(Math.sqrt(r * r + rm * rm));
    if (r > 50) ref += 0.078 * Math.log(r / 50);
    assert.ok(Math.abs(core.allen2012MmiRaw(m, r) - ref) < 1e-9);
    assert.ok(Math.abs(core.allen2012MmiRaw(m, r) - expected) < 0.01, `M${m} R${r}: ${core.allen2012MmiRaw(m, r)}`);
  }
});

test('MMI recortada a I–XII, decrece con la distancia, sigma decrece con la distancia', () => {
  assert.equal(core.estimateMMI(1.0, 5000), 1);
  assert.ok(core.estimateMMI(9.5, 1) <= 12);
  assert.ok(core.estimateMMI(7, 20) > core.estimateMMI(7, 300));
  assert.ok(core.mmiSigma(5) > core.mmiSigma(200));
  assert.ok(Math.abs(core.mmiSigma(0) - 1.19) < 1e-9);
});

test('EMSC: la profundidad se toma positiva aunque la coordenada Z sea negativa', () => {
  const feat = {
    id: '20260923_0000277',
    geometry: { type: 'Point', coordinates: [-66.9338, 17.9448, -150.0] },
    properties: { time: '2026-09-23T20:55:51.8Z', depth: 150.0, mag: 6.1, flynn_region: 'PUERTO RICO', unid: '20260923_0000277' },
  };
  const e = core.normalizeEMSCFeature(feat);
  assert.equal(e.depth, 150);
  assert.equal(e.time, Date.UTC(2026, 8, 23, 20, 55, 51, 800));
  assert.equal(e.place, 'PUERTO RICO');
  // Sin properties.depth → valor absoluto de Z
  const e2 = core.normalizeEMSCFeature({ geometry: { coordinates: [0, 0, -33] }, properties: { time: '2026-01-01T00:00:00', mag: 4 } });
  assert.equal(e2.depth, 33);
  assert.equal(e2.time, Date.UTC(2026, 0, 1));
});

test('USGS: normalización y profundidad sobre el nivel del mar recortada a 0', () => {
  const e = core.normalizeUSGSFeature({
    id: 'us7000abcd',
    geometry: { coordinates: [-76.6, 4.9, -1.5] },
    properties: { mag: 5.2, time: 1790000000000, place: 'X', title: 'M 5.2 - X', url: 'u' },
  });
  assert.equal(e.depth, 0);
  assert.equal(e.mag, 5.2);
  assert.ok(core.isValidEvent(e));
  assert.equal(core.isValidEvent({ mag: NaN, lat: 0, lon: 0, time: 0 }), false);
});

test('decisión: sismo fuerte cercano aún en camino → incoming con cuenta regresiva', () => {
  const now = 1_800_000_000_000;
  const evt = { id: 'a', lat: 4.53, lon: -76.53, depth: 15, mag: 6.5, time: now - 10_000 };
  const a = core.assessEvent(evt, CALI.lat, CALI.lon, { nowMs: now, thresholdMmi: 4 });
  assert.equal(a.level, 'incoming');
  assert.ok(a.mmi >= 4 && a.mmi < 6, `mmi ${a.mmi}`);
  assert.ok(a.remainingSec > 20 && a.remainingSec < 30, `remaining ${a.remainingSec}`);
  assert.equal(core.countdownSeconds(a.sArrivalMs, now), Math.ceil(a.remainingSec));
});

test('decisión: sismo fuerte cuya onda ya pasó → felt (aviso post-evento, no silencio)', () => {
  const now = 1_800_000_000_000;
  const evt = { id: 'b', lat: 3.6, lon: -76.5, depth: 20, mag: 6.0, time: now - 180_000 };
  const a = core.assessEvent(evt, CALI.lat, CALI.lon, { nowMs: now, thresholdMmi: 4 });
  assert.equal(a.level, 'felt');
  const old = core.assessEvent({ ...evt, time: now - 3_600_000 }, CALI.lat, CALI.lon, { nowMs: now, thresholdMmi: 4 });
  assert.equal(old.level, 'none');
});

test('cero fatiga: sismo lejano/débil nunca dispara alarma', () => {
  const now = 1_800_000_000_000;
  const small = { id: 'c', lat: 5.7, lon: -76.53, depth: 30, mag: 3.0, time: now - 2000 };
  assert.equal(core.assessEvent(small, CALI.lat, CALI.lon, { nowMs: now }).level, 'calm');
  const tokyo = { id: 'd', lat: 35.68, lon: 139.65, depth: 30, mag: 6.8, time: now - 2000 };
  assert.equal(core.assessEvent(tokyo, CALI.lat, CALI.lon, { nowMs: now }).level, 'none');
});

test('profundidad importa: el mismo sismo a 150 km de profundidad es menos intenso', () => {
  const now = 1_800_000_000_000;
  const base = { lat: 3.6, lon: -76.5, mag: 6.0, time: now };
  const shallow = core.assessEvent({ ...base, depth: 10 }, CALI.lat, CALI.lon, { nowMs: now });
  const deep = core.assessEvent({ ...base, depth: 150 }, CALI.lat, CALI.lon, { nowMs: now });
  assert.ok(shallow.mmi - deep.mmi > 1.5, `${shallow.mmi} vs ${deep.mmi}`);
});

test('una sola alerta por sismo aunque llegue por EMSC y USGS con IDs distintos', () => {
  const now = 1_800_000_000_000;
  const reg = new core.AlertRegistry();
  const emsc = { id: '20260923_0000999', lat: 4.95, lon: -76.65, time: now - 5000 };
  const usgs = { id: 'us7000zzzz', lat: 5.02, lon: -76.70, time: now - 3000 };
  assert.equal(reg.shouldNotify(emsc, 'incoming', now), true);
  reg.record(emsc, 'incoming');
  assert.equal(reg.shouldNotify(usgs, 'incoming', now), false);
  assert.equal(reg.shouldNotify(usgs, 'felt', now), false);
  // Réplica distinta (otro momento) sí alerta
  assert.equal(reg.shouldNotify({ id: 'x', lat: 4.95, lon: -76.65, time: now + 300_000 }, 'incoming', now), true);
  // Escalada de nivel permitida
  const r2 = new core.AlertRegistry();
  r2.record(emsc, 'felt');
  assert.equal(r2.shouldNotify(usgs, 'incoming', now), true);
});

test('deduplicación de listas: cercanos se funden, lejanos se conservan', () => {
  const a = [{ id: 'u1', lat: 3.45, lon: -76.53, time: 1_700_000_000_000 }];
  assert.equal(core.deduplicate(a, [{ id: 'e1', lat: 3.46, lon: -76.54, time: 1_700_000_060_000 }]).length, 1);
  assert.equal(core.deduplicate(a, [{ id: 'e2', lat: 35, lon: 139, time: 1_700_000_060_000 }]).length, 2);
});

test('reloj: solo se corrige el atraso del teléfono (lado seguro)', () => {
  assert.equal(core.estimateClockDriftMs(1000, 500), 0);
  assert.equal(core.estimateClockDriftMs(1000, 11_000), -10_000);
  assert.equal(core.estimateClockDriftMs(1000, NaN), 0);
});

test('escapeHtml neutraliza HTML de fuentes externas', () => {
  assert.equal(core.escapeHtml('<img src=x onerror=alert(1)>"\''), '&lt;img src=x onerror=alert(1)&gt;&quot;&#39;');
  assert.equal(core.escapeHtml(null), '');
});

test('números romanos MMI', () => {
  assert.equal(core.mmiToRoman(0.4), 'I');
  assert.equal(core.mmiToRoman(4.4), 'IV');
  assert.equal(core.mmiToRoman(13), 'XII');
});

test('velocidad: evaluar 10 000 sismos tarda < 200 ms', () => {
  const now = Date.now();
  const events = Array.from({ length: 10_000 }, (_, i) => ({
    id: String(i), lat: -60 + (i % 120), lon: -180 + (i % 360), depth: i % 300, mag: 2 + (i % 70) / 10, time: now - i * 1000,
  }));
  const t0 = performance.now();
  for (const e of events) core.assessEvent(e, CALI.lat, CALI.lon, { nowMs: now });
  const ms = performance.now() - t0;
  assert.ok(ms < 200, `took ${ms.toFixed(1)} ms`);
});
