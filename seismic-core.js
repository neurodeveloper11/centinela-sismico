/*!
 * seismic-core.js — Núcleo científico único de Centinela Sísmico.
 *
 * Funciones puras (sin DOM ni red) compartidas por la PWA y las pruebas en Node.
 * El motor Python (quakemind_engine.py) replica exactamente estas fórmulas y una
 * prueba de paridad garantiza que ambos devuelven los mismos valores.
 *
 * Intensidad: Allen, Wald & Worden (2012), "Intensity attenuation for active
 * crustal regions", J. Seismology 16:409-433 — modelo con distancia hipocentral
 * (coeficientes verificados contra openquake.hazardlib.gsim.allen_2012_ipe).
 *
 * License: MIT
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.SeismicCore = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const EARTH_RADIUS_KM = 6371.0;
  const V_P_KM_S = 6.0;   // Velocidad cortical de la onda primaria
  const V_S_KM_S = 3.5;   // Velocidad cortical de la onda secundaria (destructiva)

  // Allen, Wald & Worden (2012) — Rhypo model
  const AWW12 = { c0: 2.085, c1: 1.428, c2: -1.402, c4: 0.078, m1: -0.209, m2: 2.042, s1: 0.82, s2: 0.37, s3: 22.9 };

  const LEVEL_RANK = { none: -1, calm: 0, felt: 1, incoming: 2 };

  function toRad(deg) { return deg * Math.PI / 180; }

  /** Distancia de gran círculo en km. */
  function haversine(lat1, lon1, lat2, lon2) {
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return EARTH_RADIUS_KM * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  /** Distancia hipocentral 3D: R = sqrt(D² + h²), con h ≥ 1 km. */
  function hypocentralDistance(epicentralKm, depthKm) {
    const h = Math.max(Number.isFinite(depthKm) ? depthKm : 10.0, 1.0);
    return Math.sqrt(epicentralKm * epicentralKm + h * h);
  }

  /** MMI media sin recortar (Allen et al. 2012, Rhypo). */
  function allen2012MmiRaw(magnitude, hypoKm) {
    const r = Math.max(hypoKm, 1.0);
    const rm = AWW12.m1 + AWW12.m2 * Math.exp(magnitude - 5.0);
    let mmi = AWW12.c0 + AWW12.c1 * magnitude + AWW12.c2 * Math.log(Math.sqrt(r * r + rm * rm));
    if (r > 50.0) mmi += AWW12.c4 * Math.log(r / 50.0);
    return mmi;
  }

  /** MMI estimada, recortada al rango físico I–XII. */
  function estimateMMI(magnitude, hypoKm) {
    return Math.min(12.0, Math.max(1.0, allen2012MmiRaw(magnitude, hypoKm)));
  }

  /** Desviación estándar total de la IPE (en unidades MMI), depende de la distancia. */
  function mmiSigma(hypoKm) {
    return AWW12.s1 + AWW12.s2 / (1.0 + (hypoKm / AWW12.s3) ** 2);
  }

  /** Tiempos de viaje (s) de las ondas P y S a lo largo del rayo hipocentral. */
  function waveTravelTimes(hypoKm) {
    return { p: hypoKm / V_P_KM_S, s: hypoKm / V_S_KM_S };
  }

  /** Segundos enteros restantes hasta la llegada (nunca negativo). */
  function countdownSeconds(arrivalMs, nowMs) {
    return Math.max(0, Math.ceil((arrivalMs - nowMs) / 1000));
  }

  /**
   * Corrección conservadora del reloj del dispositivo.
   * Si el servidor generó datos "en el futuro" respecto al teléfono, el reloj local
   * está atrasado: eso haría creer que queda más tiempo del real (peligroso).
   * Solo se corrige ese caso; un reloj adelantado ya da un margen del lado seguro.
   * Devuelve drift = cliente − servidor (≤ 0).
   */
  function estimateClockDriftMs(clientNowMs, serverMs) {
    if (!Number.isFinite(serverMs) || !Number.isFinite(clientNowMs)) return 0;
    return serverMs > clientNowMs + 1000 ? clientNowMs - serverMs : 0;
  }

  function toFiniteNumber(v, fallback) {
    const n = typeof v === 'number' ? v : parseFloat(v);
    return Number.isFinite(n) ? n : fallback;
  }

  function parseUtcMs(value) {
    if (typeof value === 'number') return value;
    if (!value) return NaN;
    const s = String(value);
    const hasZone = /([zZ]|[+-]\d\d:?\d\d)$/.test(s);
    return new Date(hasZone ? s : s + 'Z').getTime();
  }

  /** Normaliza un Feature GeoJSON del USGS (feeds o fdsnws). */
  function normalizeUSGSFeature(feat, source) {
    const p = (feat && feat.properties) || {};
    const c = (feat && feat.geometry && feat.geometry.coordinates) || [];
    const mag = toFiniteNumber(p.mag, NaN);
    return {
      id: feat && feat.id,
      title: p.title || (Number.isFinite(mag) ? `M ${mag.toFixed(1)}` : 'Earthquake'),
      place: p.place || p.title || 'Unknown location',
      mag: mag,
      time: toFiniteNumber(p.time, NaN),
      lat: toFiniteNumber(c[1], NaN),
      lon: toFiniteNumber(c[0], NaN),
      depth: Math.max(0, toFiniteNumber(c[2], 10.0)),
      url: p.url || '',
      source: source || 'USGS'
    };
  }

  /**
   * Normaliza un Feature de EMSC (fdsnws JSON o mensaje WebSocket `data`).
   * EMSC codifica la coordenada Z como −profundidad; la profundidad real
   * está en properties.depth (positiva). Usarla evita tratar sismos profundos
   * como superficiales y sobreestimar su intensidad.
   */
  function normalizeEMSCFeature(feat, source) {
    const p = (feat && feat.properties) || {};
    const c = (feat && feat.geometry && feat.geometry.coordinates) || [];
    const mag = toFiniteNumber(p.mag, NaN);
    const depth = Number.isFinite(parseFloat(p.depth))
      ? Math.abs(parseFloat(p.depth))
      : Math.abs(toFiniteNumber(c[2], 10.0));
    const timeMs = parseUtcMs(p.time);
    const region = p.flynn_region || p.place || 'Unknown region';
    return {
      id: p.unid || (feat && feat.id) || `emsc-${timeMs}`,
      title: `M ${Number.isFinite(mag) ? mag.toFixed(1) : '?'} - ${region}`,
      place: region,
      mag: mag,
      time: timeMs,
      lat: toFiniteNumber(p.lat, toFiniteNumber(c[1], NaN)),
      lon: toFiniteNumber(p.lon, toFiniteNumber(c[0], NaN)),
      depth: depth,
      url: p.unid ? `https://www.seismicportal.eu/eventdetails.html?unid=${encodeURIComponent(p.unid)}` : '',
      source: source || 'EMSC'
    };
  }

  function isValidEvent(e) {
    return !!e && Number.isFinite(e.mag) && e.mag > -2 &&
      Number.isFinite(e.lat) && Number.isFinite(e.lon) && Number.isFinite(e.time);
  }

  /** ¿Dos reportes (posiblemente de agencias distintas) describen el mismo sismo? */
  function isSameEvent(a, b, maxKm, maxSec) {
    if (a.id && b.id && a.id === b.id) return true;
    const km = maxKm === undefined ? 50 : maxKm;
    const sec = maxSec === undefined ? 120 : maxSec;
    return Math.abs((a.time || 0) - (b.time || 0)) / 1000 < sec &&
      haversine(a.lat, a.lon, b.lat, b.lon) < km;
  }

  /** Une dos listas eliminando duplicados; devuelve orden descendente por tiempo. */
  function deduplicate(eventsA, eventsB) {
    const merged = eventsA.slice();
    for (const b of eventsB) {
      if (!merged.some(a => isSameEvent(a, b))) merged.push(b);
    }
    return merged.sort((x, y) => (y.time || 0) - (x.time || 0));
  }

  /**
   * Evaluación completa de un sismo para el usuario.
   * level:
   *   'incoming' → intensidad ≥ umbral y la onda S aún no llega (cuenta regresiva)
   *   'felt'     → intensidad ≥ umbral, la onda S ya pasó hace ≤ feltWindowSec (aviso post-evento)
   *   'calm'     → sismo regional (≤ calmRadiusKm) por debajo del umbral (tranquilidad)
   *   'none'     → irrelevante para el usuario
   */
  function assessEvent(evt, userLat, userLon, opts) {
    const o = opts || {};
    const nowMs = Number.isFinite(o.nowMs) ? o.nowMs : Date.now();
    const threshold = Number.isFinite(o.thresholdMmi) ? o.thresholdMmi : 4.0;
    const calmRadiusKm = o.calmRadiusKm || 750;
    const feltWindowSec = o.feltWindowSec || 900;

    const distKm = haversine(userLat, userLon, evt.lat, evt.lon);
    const hypoKm = hypocentralDistance(distKm, evt.depth);
    const mmi = estimateMMI(evt.mag, hypoKm);
    const sigma = mmiSigma(hypoKm);
    const tt = waveTravelTimes(hypoKm);
    const pArrivalMs = evt.time + tt.p * 1000;
    const sArrivalMs = evt.time + tt.s * 1000;
    const remainingSec = (sArrivalMs - nowMs) / 1000;
    const ageSec = (nowMs - evt.time) / 1000;

    let level = 'none';
    if (mmi >= threshold) {
      if (remainingSec > 0) level = 'incoming';
      else if (ageSec <= feltWindowSec + tt.s) level = 'felt';
    } else if (distKm <= calmRadiusKm) {
      level = 'calm';
    }

    return {
      distKm, hypoKm, mmi,
      mmiSigma: sigma,
      mmiLow: Math.max(1, mmi - sigma),
      mmiHigh: Math.min(12, mmi + sigma),
      pArrivalMs, sArrivalMs, remainingSec, ageSec, level
    };
  }

  /**
   * Registro de alertas emitidas: garantiza UNA sola alerta por sismo aunque
   * llegue por WebSocket EMSC, feed USGS y consulta radial con IDs distintos.
   * Solo permite repetir si el nivel escala (p. ej. 'felt' → 'incoming' no
   * es posible, pero 'calm' → 'incoming' sí tras una revisión de magnitud).
   */
  class AlertRegistry {
    constructor(opts) {
      const o = opts || {};
      this.maxKm = o.maxKm || 100;
      this.maxSec = o.maxSec || 90;
      this.ttlMs = o.ttlMs || 3600 * 1000;
      this.records = [];
    }
    _find(evt) {
      return this.records.find(r => isSameEvent(r, evt, this.maxKm, this.maxSec));
    }
    shouldNotify(evt, level, nowMs) {
      this.prune(nowMs);
      const prev = this._find(evt);
      if (!prev) return true;
      return LEVEL_RANK[level] > LEVEL_RANK[prev.level];
    }
    record(evt, level) {
      const prev = this._find(evt);
      if (prev) {
        if (LEVEL_RANK[level] > LEVEL_RANK[prev.level]) prev.level = level;
        return;
      }
      this.records.push({ id: evt.id, lat: evt.lat, lon: evt.lon, time: evt.time, level });
    }
    prune(nowMs) {
      const now = Number.isFinite(nowMs) ? nowMs : Date.now();
      this.records = this.records.filter(r => now - r.time < this.ttlMs);
    }
  }

  const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'];
  function mmiToRoman(mmi) {
    const i = Math.min(12, Math.max(1, Math.round(mmi))) - 1;
    return ROMAN[i];
  }

  const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  function escapeHtml(value) {
    return String(value === undefined || value === null ? '' : value).replace(/[&<>"']/g, ch => HTML_ESCAPES[ch]);
  }

  return {
    V_P_KM_S, V_S_KM_S, AWW12,
    haversine, hypocentralDistance, allen2012MmiRaw, estimateMMI, mmiSigma,
    waveTravelTimes, countdownSeconds, estimateClockDriftMs, parseUtcMs,
    normalizeUSGSFeature, normalizeEMSCFeature, isValidEvent,
    isSameEvent, deduplicate, assessEvent, AlertRegistry,
    mmiToRoman, escapeHtml
  };
});
