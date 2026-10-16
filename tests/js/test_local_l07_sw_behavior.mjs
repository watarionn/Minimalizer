/** L07 synthetic Service Worker behavior, read-only; no production or Safari claim. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../../local_worker/frontend/sw.js', import.meta.url), 'utf8');
const ORIGIN = 'https://owner.example.ts.net';
const SHELL = Object.freeze(['/', '/static/styles.css', '/static/color-strip.css', '/static/app.js',
  '/static/browser-feature-palette.js', '/static/browser-color-strip.js',
  '/local-static/local-route.js', '/local-static/icon.svg']);

function harness({ networkFails = false, existingCaches = ['minimalizer-local-shell-v0', 'minimalizer-local-shell-v1'] } = {}) {
  const handlers = new Map();
  const actions = [];
  const self = {
    location: { origin: ORIGIN },
    addEventListener(type, fn) {
      assert.equal(typeof fn, 'function');
      assert.equal(handlers.has(type), false, 'unexpected duplicate handler');
      handlers.set(type, fn);
    },
    skipWaiting() { actions.push(['skipWaiting']); },
    clients: { claim() { actions.push(['claim']); } },
  };
  const caches = {
    async open(key) {
      actions.push(['open', key]);
      return { async addAll(paths) { actions.push(['addAll', Array.from(paths)]); } };
    },
    async keys() { actions.push(['keys']); return [...existingCaches]; },
    async delete(key) { actions.push(['delete', key]); return true; },
    async match(req) { actions.push(['match', req.url]); return { kind: 'cached-shell' }; },
  };
  async function fetch(req) {
    actions.push(['fetch', req.url]);
    if (networkFails) throw new Error('offline');
    return { kind: 'network-shell' };
  }
  vm.runInNewContext(script, { self, caches, fetch, URL }, { timeout: 1000, filename: 'sw.js' });
  function dispatch(type, request = undefined) {
    assert.ok(handlers.has(type), 'missing event handler');
    const waits = [], responses = [];
    handlers.get(type)({ request, waitUntil(p) { waits.push(p); }, respondWith(p) { responses.push(p); } });
    return { waits, responses };
  }
  return { actions, dispatch, handlers };
}
function req(path, method = 'GET', origin = ORIGIN) { return { method, url: new URL(path, origin).href }; }

test('L07 install caches exactly eight fixed shell assets, never image/API data', async () => {
  const h = harness();
  const event = h.dispatch('install');
  assert.equal(event.waits.length, 1);
  await Promise.all(event.waits);
  assert.deepEqual(h.actions.find(a => a[0] === 'addAll')[1], SHELL);
  assert.equal(h.actions.filter(a => a[0] === 'skipWaiting').length, 1);
  assert.ok(!h.actions.some(a => a[0] === 'put'));
});

test('L07 activation clears stale Local shell and claims clients', async () => {
  const h = harness();
  await Promise.all(h.dispatch('activate').waits);
  assert.ok(h.actions.some(a => a[0] === 'delete' && a[1] === 'minimalizer-local-shell-v0'));
  assert.ok(!h.actions.some(a => a[0] === 'delete' && a[1] === 'minimalizer-local-shell-v1'));
  assert.ok(h.actions.some(a => a[0] === 'claim'));
});

for (const path of SHELL) {
  test('L07 allowed shell ' + path + ' uses network-first without cache write', async () => {
    const h = harness();
    const e = h.dispatch('fetch', req(path));
    assert.equal(e.responses.length, 1);
    assert.equal((await e.responses[0]).kind, 'network-shell');
    assert.equal(h.actions.filter(a => a[0] === 'fetch').length, 1);
    assert.equal(h.actions.filter(a => a[0] === 'match').length, 0);
    assert.ok(!h.actions.some(a => a[0] === 'put' || a[0] === 'addAll'));
  });
}

test('L07 offline shell uses only existing cached shell response', async () => {
  const h = harness({ networkFails: true });
  const e = h.dispatch('fetch', req('/static/app.js'));
  assert.equal((await e.responses[0]).kind, 'cached-shell');
  assert.equal(h.actions.filter(a => a[0] === 'match').length, 1);
});

for (const [path, method, origin] of [
  ['/api/zerobase2/minimalize', 'GET', ORIGIN],
  ['/api/v2/minimalize', 'GET', ORIGIN],
  ['/health', 'GET', ORIGIN],
  ['/uploads/private.png', 'GET', ORIGIN],
  ['/artifacts/output.svg', 'GET', ORIGIN],
  ['/private/image.webp', 'GET', ORIGIN],
  ['/local-static/not-listed.js', 'GET', ORIGIN],
  ['/static/app.js', 'POST', ORIGIN],
  ['/static/app.js', 'GET', 'https://untrusted.example.invalid'],
]) {
  test('L07 bypass ' + method + ' ' + origin + ' ' + path + ' never intercepts', () => {
    const h = harness();
    const e = h.dispatch('fetch', req(path, method, origin));
    assert.equal(e.responses.length, 0);
    assert.equal(h.actions.length, 0);
  });
}

// The existing SW deletes all same-origin caches not matching CACHE, including unrelated
// namespaces. This test documents the blocker; it is not a release PASS.
test('L07 diagnostic: current activation deletes unrelated cache namespace; release HOLD', async () => {
  const h = harness({ existingCaches: ['minimalizer-local-shell-v1', 'unrelated-pwa-cache'] });
  await Promise.all(h.dispatch('activate').waits);
  assert.ok(h.actions.some(a => a[0] === 'delete' && a[1] === 'unrelated-pwa-cache'));
});
