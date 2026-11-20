import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../../local_worker/frontend/sw.js", import.meta.url), "utf8");

function loadWorker({ response = new Response("pinned-shell") } = {}) {
  const handlers = new Map();
  const cache = {
    addAll: async () => {},
    match: async () => response,
  };
  const context = {
    URL,
    Request,
    Response,
    decodeURIComponent,
    Promise,
    Error,
    self: {
      location: { origin: "https://local.test" },
      addEventListener: (name, handler) => handlers.set(name, handler),
    },
    caches: {
      open: async () => cache,
    },
  };
  vm.runInNewContext(source, context, { filename: "sw.js" });
  return { handlers, cache };
}

test("query and encoded shell paths stay pinned to the installed generation", async () => {
  const { handlers } = loadWorker();
  const fetchHandler = handlers.get("fetch");
  let responsePromise;
  fetchHandler({
    request: new Request("https://local.test/%73tatic/app.js?v=newer"),
    respondWith: value => { responsePromise = value; },
  });
  assert.equal(await (await responsePromise).text(), "pinned-shell");
});

test("API and image requests are not intercepted", () => {
  const { handlers } = loadWorker();
  const fetchHandler = handlers.get("fetch");
  let intercepted = false;
  fetchHandler({
    request: new Request("https://local.test/api/zerobase2/minimalize"),
    respondWith: () => { intercepted = true; },
  });
  assert.equal(intercepted, false);
});

test("there is no activate cleanup handler that destroys rollback generations", () => {
  const { handlers } = loadWorker();
  assert.equal(handlers.has("activate"), false);
});
