// PICU BoardIQ service worker
// Strategy: cache-first for app shell + HTML pages, network update in background
// Bump CACHE_VERSION whenever you want browsers to refetch everything.

const CACHE_VERSION = 'biq-v31-2026-05-15-bulletproof-networkfirst';
const RUNTIME_CACHE = 'biq-runtime-v1';

// Pre-cache the core shell so the app launches fully offline after first visit.
// Keep this list short — additional pages are added on demand.
const PRECACHE_URLS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './99_PICU_BoardIQ/00_APP/PICU_BoardIQ_v2.html',
  './99_PICU_BoardIQ/00_APP/_SAFE_MODE.html',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      // Add files one-by-one so a single missing file doesn't kill the whole install
      return Promise.all(
        PRECACHE_URLS.map((url) =>
          cache.add(url).catch((err) => console.warn('[SW] precache miss:', url, err))
        )
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_VERSION && k !== RUNTIME_CACHE).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  // Only handle GET
  if (req.method !== 'GET') return;
  // Skip cross-origin requests (e.g., CDN fonts) — pass through to network
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // For HTML navigation: try network first, fall back to cache, then index
  if (req.mode === 'navigate' || req.destination === 'document') {
    event.respondWith(
      fetch(req).then((resp) => {
        const copy = resp.clone();
        caches.open(RUNTIME_CACHE).then((c) => c.put(req, copy));
        return resp;
      }).catch(() =>
        caches.match(req).then((cached) => cached || caches.match('./index.html'))
      )
    );
    return;
  }

  // For HTML files (main app, content pages): network-first so updates land immediately
  if (url.pathname.endsWith('.html')) {
    event.respondWith(
      fetch(req).then((resp) => {
        const copy = resp.clone();
        caches.open(RUNTIME_CACHE).then((c) => c.put(req, copy));
        return resp;
      }).catch(() => caches.match(req).then((cached) => cached || caches.match('./index.html')))
    );
    return;
  }

  // For other assets (icons, manifest, etc.): cache-first with background refresh
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) {
        fetch(req).then((resp) => {
          caches.open(RUNTIME_CACHE).t