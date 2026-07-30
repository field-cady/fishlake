// Service worker for the installable PWA / offline app shell.
//
// Strategy: NETWORK-FIRST for same-origin requests, falling back to cache when
// offline. Successful responses are cached so the app still works offline with
// the most recent version seen. This deliberately avoids the old cache-first
// approach, which froze returning visitors on a stale app shell (e.g. the
// pre-national "Pacific Northwest" build) because updates never propagated.
//
// Bump CACHE whenever the precached shell list changes to purge old caches.
var CACHE = 'fishlake-v2';
var SHELL = [
  './',
  'index.html',
  'all_scripts.js',
  'manifest.json',
  'trout.png',
  'icon-192.png',
  'icon-512.png'
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE).then(function(c) { return c.addAll(SHELL); })
      .then(function() { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.filter(function(k) { return k !== CACHE; })
        .map(function(k) { return caches.delete(k); }));
    }).then(function() { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(e) {
  if (e.request.method !== 'GET') return;
  // Network-first: always try the network so app + data stay fresh; cache each
  // successful same-origin response for offline; fall back to cache when the
  // network is unavailable.
  e.respondWith(
    fetch(e.request).then(function(resp) {
      if (resp && resp.ok && e.request.url.indexOf(self.location.origin) === 0) {
        var copy = resp.clone();
        caches.open(CACHE).then(function(c) { c.put(e.request, copy); });
      }
      return resp;
    }).catch(function() {
      return caches.match(e.request);
    })
  );
});
