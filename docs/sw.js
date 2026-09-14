// Service Worker for Centinela Sísmico Offline PWA
const CACHE_NAME = 'centinela-cache-v7';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
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

self.addEventListener('fetch', (event) => {
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
        .catch(() => {
          return caches.match('./index.html') || caches.match('./');
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
      return fetch(event.request).catch(() => {
        return caches.match('./index.html');
      });
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
  const data = event.data ? event.data.json() : {};
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
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url.includes('index.html') && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow(targetUrl);
    })
  );
});
