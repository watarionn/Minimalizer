// Public-only, opt-in Earcut polygon-with-holes triangulation observer.
// Never applies triangles to PNG/SVG. A proposed triangle is counted only when
// ALL of its OpenCV-compatible raster pixels belong to the original owner.
(function (root) {
  "use strict";
  const VERSION = "public-earcut-hole-aware-v1";
  const MAX_SHAPES = 8;
  const MAX_RINGS = 24;
  const MAX_VERTICES = 180;
  const MAX_TRIANGLES = 64;
  const MAX_PIXELS = 160000;

  function sourceRings(shape) {
    if (!shape || typeof shape !== "object") return [];
    return Array.isArray(shape.rings) && shape.rings.length
      ? shape.rings : [shape.polygon];
  }

  function normalizedRing(source) {
    if (!Array.isArray(source) || source.length < 3) return null;
    const ring = [];
    for (const p of source) {
      if (!Array.isArray(p) || p.length !== 2 ||
          !Number.isFinite(p[0]) || !Number.isFinite(p[1])) return null;
      ring.push([p[0], p[1]]);
    }
    if (ring.length > 3 && ring[0][0] === ring[ring.length - 1][0] &&
        ring[0][1] === ring[ring.length - 1][1]) {
      ring.pop();
    }
    return ring.length >= 3 ? ring : null;
  }

  function asEarcutInput(rings) {
    if (!rings.length || rings.length > MAX_RINGS) return null;
    let count = 0;
    const flat = [];
    const holes = [];
    const vertices = [];
    for (let i = 0; i < rings.length; i += 1) {
      const ring = normalizedRing(rings[i]);
      if (!ring || count + ring.length > MAX_VERTICES) return null;
      if (i > 0) holes.push(count);
      for (const p of ring) {
        vertices.push(p);
        flat.push(p[0], p[1]);
      }
      count += ring.length;
    }
    return { flat, holes, vertices };
  }

  function maskIsSubset(candidate, original) {
    if (!candidate || !original || candidate.length !== original.length) return false;
    for (let i = 0; i < candidate.length; i += 1) {
      if (candidate[i] && !original[i]) return false;
    }
    return true;
  }

  function sameMask(first, second) {
    if (!first || !second || first.length !== second.length) return false;
    for (let i = 0; i < first.length; i += 1) {
      if (first[i] !== second[i]) return false;
    }
    return true;
  }

  function area2(tri) {
    const [a, b, c] = tri;
    return (b[0] - a[0]) * (c[1] - a[1]) -
      (b[1] - a[1]) * (c[0] - a[0]);
  }

  function auditShapes(shapes, width, height) {
    const library = root.earcut;
    const triangulate = library && (library.default || library);
    const raster = root.MinimalizerOpenCvRaster;
    if (typeof triangulate !== "function" ||
        !raster || typeof raster.rasterizeLoops !== "function") {
      return Object.freeze({
        version: VERSION, status: "unavailable", acceptedTriangles: 0,
        rejectedTriangles: 0, fullyReconstructedShapes: 0,
        geometryApplied: false,
      });
    }
    if (!Array.isArray(shapes) || !Number.isInteger(width) ||
        !Number.isInteger(height) || width < 1 || height < 1 ||
        width * height > MAX_PIXELS) {
      return Object.freeze({
        version: VERSION, status: "invalid-input", acceptedTriangles: 0,
        rejectedTriangles: 0, fullyReconstructedShapes: 0,
        geometryApplied: false,
      });
    }

    let auditedShapes = 0;
    let skippedShapes = 0;
    let holeGroups = 0;
    let candidateTriangles = 0;
    let acceptedTriangles = 0;
    let rejectedTriangles = 0;
    let fullyReconstructedShapes = 0;
    let truncated = false;
    try {
      for (const shape of shapes) {
        if (auditedShapes >= MAX_SHAPES || candidateTriangles >= MAX_TRIANGLES) {
          truncated = true;
          break;
        }
        const rings = sourceRings(shape);
        const input = asEarcutInput(rings);
        if (!input) {
          skippedShapes += 1;
          continue;
        }
        // Multiple rings are an experimental "outer + holes" interpretation.
        // Independent source-mask replay, not ring index, is the authority.
        const original = raster.rasterizeLoops(rings, width, height, 2);
        const ids = triangulate(input.flat, input.holes, 2);
        if (!ids || ids.length % 3 !== 0) {
          skippedShapes += 1;
          continue;
        }
        auditedShapes += 1;
        if (input.holes.length) holeGroups += 1;
        const union = new Uint8Array(original.length);
        let allAccepted = true;
        let completelyExamined = true;
        for (let j = 0; j < ids.length; j += 3) {
          if (candidateTriangles >= MAX_TRIANGLES) {
            truncated = true;
            completelyExamined = false;
            break;
          }
          const tri = [
            input.vertices[ids[j]],
            input.vertices[ids[j + 1]],
            input.vertices[ids[j + 2]],
          ];
          if (tri.some(p => !p) || Math.abs(area2(tri)) <= 1e-9) {
            allAccepted = false;
            rejectedTriangles += 1;
            continue;
          }
          const candidate = raster.rasterizeLoops([tri], width, height, 2);
          candidateTriangles += 1;
          if (maskIsSubset(candidate, original)) {
            acceptedTriangles += 1;
            for (let k = 0; k < union.length; k += 1) {
              if (candidate[k]) union[k] = 1;
            }
          } else {
            rejectedTriangles += 1;
            allAccepted = false;
          }
        }
        if (completelyExamined && allAccepted && sameMask(original, union)) {
          fullyReconstructedShapes += 1;
        }
      }
    } catch (_) {
      return Object.freeze({
        version: VERSION, status: "error", auditedShapes, skippedShapes,
        holeGroups, candidateTriangles, acceptedTriangles,
        rejectedTriangles, fullyReconstructedShapes, geometryApplied: false,
      });
    }
    return Object.freeze({
      version: VERSION, status: truncated ? "truncated" : "ok",
      auditedShapes, skippedShapes, holeGroups, candidateTriangles,
      acceptedTriangles, rejectedTriangles, fullyReconstructedShapes,
      geometryApplied: false,
    });
  }

  root.MinimalizerPublicEarcutResearch = Object.freeze({ VERSION, auditShapes });
  if (typeof module !== "undefined" && module.exports) {
    module.exports = root.MinimalizerPublicEarcutResearch;
  }
}(typeof window !== "undefined" ? window : globalThis));
