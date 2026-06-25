/* RT Image Matching Trainer — service worker (PWA install shell + offline fallback).
 *
 * PAYWALL-SAFE BY DESIGN. This worker NEVER caches:
 *   - the gated pages (/trainer, /account, /subscribe),
 *   - the case data (*_data.js) or DRR images (/drr/),
 *   - any /api/* request, or any cross-origin request (Clerk, future R2).
 * Those always go straight to the network, so the client auth gate and the
 * Phase-2 server-side paywall are completely unaffected by this worker.
 *
 * What it DOES: caches the PUBLIC static shell (landing, guides, legal pages,
 * fonts, icons) with a network-first strategy — always fresh when online, with
 * a cache fallback (and an offline page for failed navigations) when offline,
 * plus the installability the manifest needs.
 *
 * Bump VERSION to invalidate the old cache on the next deploy.
 */
var VERSION = 'rt-pwa-v1';
var SHELL = ['/', '/offline.html', '/favicon.svg', '/manifest.webmanifest'];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(VERSION)
      .then(function (c) { return c.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== VERSION) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

// Requests the worker must never touch: always network-only, never stored.
function bypass(url) {
  if (url.origin !== self.location.origin) return true;        // cross-origin (Clerk, R2, ...)
  var p = url.pathname;
  return p.indexOf('/api/') === 0 ||
         p.indexOf('/drr/') === 0 ||
         /_data\.js$/.test(p) ||
         p === '/trainer' || p === '/trainer.html' ||
         p === '/account' || p === '/account.html' ||
         p === '/subscribe' || p === '/subscribe.html';
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (bypass(url)) return;                                      // browser handles it, uncached

  // Network-first for the public shell; cache fallback, then offline page.
  e.respondWith(
    fetch(req).then(function (res) {
      if (res && res.ok && res.type === 'basic') {
        var copy = res.clone();
        caches.open(VERSION).then(function (c) { c.put(req, copy); });
      }
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) {
        if (hit) return hit;
        if (req.mode === 'navigate') return caches.match('/offline.html');
        return Response.error();
      });
    })
  );
});
