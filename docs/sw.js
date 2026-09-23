// Service Worker for Centinela Sísmico Offline PWA
const CACHE_NAME = 'centinela-cache-v9';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './seismic-core.js',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './og-image.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

async function cachedAppShell() {
  return (await caches.match('./index.html')) ||
         (await caches.match('./')) ||
         new Response('Centinela Sísmico: sin conexión.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}

self.addEventListener('fetch', (event) => {
  // Only GET requests are cacheable; let the browser handle everything else.
  if (event.request.method !== 'GET') return;

  // Bypass cache for live seismic feeds (USGS + EMSC/CSEM + SGC)
  if (event.request.url.includes('earthquake.usgs.gov') ||
      event.request.url.includes('seismicportal.eu') ||
      event.request.url.includes('sgc.gov.co') ||
      event.request.url.includes('bigdatacloud.net')) {
    return;
  }

  // Network-First for HTML navigation: users online get updates immediately, offline users get cached version
  if (event.request.mode === 'navigate' || event.request.destination === 'document') {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const resClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
          }
          return networkResponse;
        })
        .catch(() => cachedAppShell())
    );
    return;
  }

  // Stale-While-Revalidate for the app scripts: instant load, background refresh
  if (event.request.url.endsWith('/seismic-core.js')) {
    event.respondWith(
      caches.open(CACHE_NAME).then(async (cache) => {
        const cached = await cache.match(event.request);
        const network = fetch(event.request).then((res) => {
          if (res && res.status === 200) cache.put(event.request, res.clone());
          return res;
        }).catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // Cache-First for static assets (icons, images)
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch(() => cachedAppShell());
    })
  );
});

// ===========================================
// WEB PUSH NOTIFICATIONS (Client-side ready)
// PUSH_BACKEND_REQUIRED: This listener is activated by an external
// VAPID push server (e.g. Cloudflare Worker or Vercel Cron) that
// sends payloads when a significant earthquake is detected near
// subscribed users. The client subscription is managed in index.html.
// ===========================================
self.addEventListener('push', (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = { body: event.data ? event.data.text() : '' }; }
  const title = data.title || '🚨 Centinela Sísmico — Alerta Sísmica';
  const options = {
    body: data.body || 'Se ha detectado actividad sísmica cerca de tu ubicación.',
    icon: './icon-192.png',
    badge: './icon-192.png',
    vibrate: [400, 150, 400, 150, 800],
    tag: 'centinela-seismic-alert',
    renotify: true,
    requireInteraction: true,
    data: { url: data.url || './index.html' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || './index.html';
  const scope = self.registration.scope;
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url.startsWith(scope) && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow(targetUrl);
    })
  );
});
