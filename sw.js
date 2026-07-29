// Minimal service worker so the map is an installable PWA and its shell works
// offline. The app shell is precached; the large data file and map tiles are
// fetched from the network (falling back to cache if present).
var CACHE = 'fishlake-v1';
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
  // Cache-first for anything we have; otherwise go to the network.
  e.respondWith(
    caches.match(e.request).then(function(cached) {
      return cached || fetch(e.request).catch(function() { return cached; });
    })
  );
});
