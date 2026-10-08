/* Experimental geometry-only contour candidate.
 * Algorithm inspired by weighted Visvalingam simplification; no third-party source copied.
 * Candidate acceptance and topology validation remain in canonical-contour.js.
 */
(function (root) {
  "use strict";
  const VERSION = "weighted-visvalingam-v1";

  function simplifyOpen(points, epsilon, options) {
    if (!Array.isArray(points) || points.length < 3 || !(epsilon > 0)) {
      return Array.isArray(points) ? points.map((p) => p.slice()) : [];
    }
    const opts = options || {};
    const weight = Number.isFinite(opts.weight) ? Math.max(0, Math.min(2, opts.weight)) : 0.7;
    const areaScale = Number.isFinite(opts.areaScale) ? Math.max(0, Math.min(8, opts.areaScale)) : 1;
    const threshold = 0.5 * epsilon * epsilon * areaScale;
    if (threshold <= 0) return points.map((p) => p.slice());
    const n = points.length;
    const prev = new Int32Array(n);
    const next = new Int32Array(n);
    const active = new Uint8Array(n);
    const generations = new Int32Array(n);
    const heap = [];
    for (let i = 0; i < n; i += 1) {
      prev[i] = i - 1;
      next[i] = i + 1;
      active[i] = 1;
    }
    function less(a, b) {
      return a.area < b.area || (a.area === b.area && a.index < b.index);
    }
    function push(item) {
      heap.push(item);
      let i = heap.length - 1;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (!less(heap[i], heap[p])) break;
        [heap[i], heap[p]] = [heap[p], heap[i]];
        i = p;
      }
    }
    function pop() {
      const item = heap[0];
      const last = heap.pop();
      if (heap.length) {
        heap[0] = last;
        let i = 0;
        while (true) {
          const l = 2 * i + 1, r = l + 1;
          let child = l;
          if (r < heap.length && less(heap[r], heap[l])) child = r;
          if (child >= heap.length || !less(heap[child], heap[i])) break;
          [heap[i], heap[child]] = [heap[child], heap[i]];
          i = child;
        }
      }
      return item;
    }
    function weightedArea(i) {
      const a = points[prev[i]], b = points[i], c = points[next[i]];
      const ux = a[0] - b[0], uy = a[1] - b[1];
      const vx = c[0] - b[0], vy = c[1] - b[1];
      const cross = Math.abs(ux * vy - uy * vx);
      const denominator = Math.hypot(ux, uy) * Math.hypot(vx, vy);
      if (!(denominator > 0)) return 0;
      const cosine = Math.max(-1, Math.min(1, (ux * vx + uy * vy) / denominator));
      const halfAngle = Math.sqrt((1 - cosine) / 2);
      return (cross / 2) * Math.pow(Math.max(0.05, halfAngle), weight);
    }
    function schedule(i) {
      if (i <= 0 || i >= n - 1 || !active[i]) return;
      const area = weightedArea(i);
      generations[i] += 1;
      push({ index: i, area, generation: generations[i] });
    }
    for (let i = 1; i < n - 1; i += 1) schedule(i);
    while (heap.length) {
      const item = pop();
      const i = item.index;
      if (!active[i] || item.generation !== generations[i]) continue;
      if (item.area > threshold) break;
      active[i] = 0;
      next[prev[i]] = next[i];
      prev[next[i]] = prev[i];
      schedule(prev[i]);
      schedule(next[i]);
    }
    const output = [];
    for (let i = 0; i < n; i += 1) {
      if (active[i]) output.push(points[i].slice());
    }
    return output;
  }

  const api = Object.freeze({ VERSION, simplifyOpen });
  root.MinimalizerWeightedVisvalingam = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : globalThis));
