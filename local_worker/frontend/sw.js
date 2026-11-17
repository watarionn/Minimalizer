// Cache only the private app shell, never user images, outputs or API responses.
// This generation is immutable after install.  A later generation gets a new
// name and waits for the browser's normal navigation lifecycle.
const GENERATION = "minimalizer-local-20261117-2";
const CACHE_PREFIX = "minimalizer-local-shell-";
const CACHE = CACHE_PREFIX + GENERATION;
const ASSETS = ["/", "/static/styles.css", "/static/color-strip.css", "/static/app.js",
  "/static/browser-feature-palette.js", "/static/browser-color-strip.js",
  "/local-static/local-route.js", "/local-static/icon.svg"];

function canonicalShellPath(pathname) {
  if (ASSETS.includes(pathname)) return pathname;
  if (!pathname.includes("%")) return null;
  let candidate = pathname;
  for (let i = 0; i < 4; i++) {
    try { candidate = decodeURIComponent(candidate); }
    catch (_) { return null; }
    if (candidate.includes("?") || candidate.includes("#") || !candidate.startsWith("/")) return null;
    const normalized = new URL(
      self.location.origin + candidate.replace(/\/{2,}/g, "/")
    ).pathname;
    if (ASSETS.includes(normalized)) return normalized;
    if (!candidate.includes("%")) break;
  }
  return null;
}

self.addEventListener("install", event => {
  // Keep the old generation in control of already-open pages.  The new
  // generation becomes active on the browser's normal next-navigation
  // lifecycle, so one page cannot mix old JS with a new shell cache.
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
});

self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin) return;
  const canonical = canonicalShellPath(url.pathname);
  if (canonical === null || !ASSETS.includes(canonical)) return;
  // Cache-first is intentional: a controlled page must never mix a newer
  // online shell with the generation that controls it.  Missing cache bytes
  // fail closed; they are never replaced by a network response.
  const cacheRequest = new Request(new URL(canonical, self.location.origin).href);
  event.respondWith(caches.open(CACHE).then(cache => cache.match(cacheRequest)).then(response => {
    if (!response) throw new Error("Local shell generation is unavailable.");
    return response;
  }));
});
