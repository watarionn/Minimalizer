// Cache only the private app shell, never user images, outputs or API responses.
const CACHE = "minimalizer-local-shell-v1";
const ASSETS = ["/", "/static/styles.css", "/static/color-strip.css", "/static/app.js",
  "/static/browser-feature-palette.js", "/static/browser-color-strip.js",
  "/local-static/local-route.js", "/local-static/icon.svg"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key !== CACHE).map(key => caches.delete(key))
  )).then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || !ASSETS.includes(url.pathname)) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
