// Public-only, non-authoritative polygon clipping diagnostic.
// Uses the vendored polygon-clipping 0.15.7 UMD build (MIT).
// Does not modify output geometry, color, masks, or render order.
(function (root) {
  "use strict";

  const VERSION = "public-polygon-clipping-v1";
  const MAX_RINGS = 160;
  const MAX_VERTICES = 12000;

  function area(ring) {
    let twiceArea = 0;
    for (let i = 0; i < ring.length - 1; i += 1) {
      twiceArea += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
    }
    return twiceArea / 2;
  }

  function clippedArea(multipolygon) {
    let sum = 0;
    for (const polygon of multipolygon) {
      for (let i = 0; i < polygon.length; i += 1) {
        const signed = Math.abs(area(polygon[i]));
        sum += i === 0 ? signed : -signed;
      }
    }
    return sum;
  }

  function normalizedRing(points) {
    if (!Array.isArray(points) || points.length < 3) return null;
    const ring = [];
    for (const point of points) {
      if (!Array.isArray(point) || point.length !== 2 ||
          !Number.isFinite(point[0]) || !Number.isFinite(point[1])) return null;
      ring.push([point[0], point[1]]);
    }
    if (ring[0][0] !== ring[ring.length - 1][0] ||
        ring[0][1] !== ring[ring.length - 1][1]) {
      ring.push(ring[0].slice());
    }
    return ring;
  }

  function auditShapes(shapes, width, height) {
    const clip = root.polygonClipping;
    if (!clip || typeof clip.intersection !== "function") {
      return { version: VERSION, status: "unavailable", testedRings: 0, invalidRings: 0 };
    }
    if (!Array.isArray(shapes) || !Number.isFinite(width) || !Number.isFinite(height) ||
        width <= 0 || height <= 0) {
      return { version: VERSION, status: "invalid-input", testedRings: 0, invalidRings: 0 };
    }
    const viewport = [[[0, 0], [width, 0], [width, height], [0, height], [0, 0]]];
    let testedRings = 0;
    let invalidRings = 0;
    let clipErrors = 0;
    let visibleRingCount = 0;
    let sumClippedArea = 0;
    let vertices = 0;
    let truncated = false;

    for (const shape of shapes) {
      const rings = shape && Array.isArray(shape.rings) && shape.rings.length
        ? shape.rings : [shape && shape.polygon];
      for (const points of rings) {
        if (!points || vertices + points.length > MAX_VERTICES || testedRings >= MAX_RINGS) {
          truncated = true;
          break;
        }
        vertices += points.length;
        const ring = normalizedRing(points);
        if (!ring) {
          invalidRings += 1;
          continue;
        }
        try {
          // Diagnostic only: never use this result to replace the official renderer.
          const intersection = clip.intersection([ring], viewport);
          testedRings += 1;
          if (intersection.length) {
            visibleRingCount += 1;
            sumClippedArea += clippedArea(intersection);
          }
        } catch (_) {
          clipErrors += 1;
        }
      }
      if (truncated) break;
    }
    return Object.freeze({
      version: VERSION,
      status: clipErrors ? "error" : truncated ? "truncated" : "ok",
      testedRings, invalidRings, clipErrors, visibleRingCount,
      clippedAreaSum: Math.round(sumClippedArea * 1000) / 1000,
    });
  }

  root.MinimalizerPublicPolygonGeometry = Object.freeze({ VERSION, auditShapes });
  if (typeof module !== "undefined" && module.exports) {
    module.exports = root.MinimalizerPublicPolygonGeometry;
  }
}(typeof window !== "undefined" ? window : globalThis));
