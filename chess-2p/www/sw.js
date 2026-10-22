// Offline cache for the browser (PWA) version. The Android app loads the
// same files from its bundled assets and does not use this.
var CACHE = 'p2p-chess-v1';
var FILES = ['./', 'index.html', 'css/style.css', 'js/pieces.js', 'js/chess.js', 'js/sound.js', 'js/app.js',
  'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    // The player photo is optional, so cache it without failing the install.
    return c.addAll(FILES).then(function () { return c.add('img/ayman.jpg').catch(function () {}); });
  }));
  self.skipWaiting();
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});
self.addEventListener('fetch', function (e) {
  e.respondWith(caches.match(e.request).then(function (hit) { return hit || fetch(e.request); }));
});
