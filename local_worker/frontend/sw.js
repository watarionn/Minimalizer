// Cache only the private app shell, never user images, outputs or API responses.
const GENERATION = "minimalizer-local-20261107-1";
const CACHE_PREFIX = "minimalizer-local-shell-";
const CACHE = CACHE_PREFIX + GENERATION;
const ASSETS = ["/", "/static/styles.css", "/static/color-strip.css", "/static/app.js",
  "/static/browser-feature-palette.js", "/static/browser-color-strip.js",
  "/local-static/local-route.js", "/local-static/icon.svg"];
self.addEventListener("install", event => {
  // Keep the old generation in control of already-open pages.  The new
  // generation becomes active on the browser's normal next-navigation
  // lifecycle, so one page cannot mix old JS with a new shell cache.
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE)
      .map(key => caches.delete(key))
  )));
});
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || !ASSETS.includes(url.pathname)) return;
  // Query strings are allowed on shell requests, but the installed cache is
  // keyed by the generation's canonical pathname.  Never let an offline
  // query miss that generation's cached shell.
  const cacheRequest = new Request(new URL(url.pathname, self.location.origin).href);
  event.respondWith(fetch(event.request).catch(() => caches.match(cacheRequest)));
});
