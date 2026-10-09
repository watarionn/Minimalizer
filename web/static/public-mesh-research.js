// Public-only opt-in Delaunator mesh feasibility observer.
// Delaunator triangulates original vertices; OpenCV-style owner mask authorizes
// each candidate triangle ONLY if all its rasterized pixels stay inside source.
// Never writes mesh triangles into image output, palette or shape ownership.
(function (root) {
  "use strict";
  const VERSION = "public-delaunator-owner-mesh-v1";
  const MAX_SHAPES = 8;
  const MAX_VERTICES = 180;
  const MAX_TRIANGLES = 48;
  const MAX_PIXELS = 160000;

  function shapeRings(shape) {
    if (!shape || typeof shape !== "object") return [];
    return Array.isArray(shape.rings) && shape.rings.length > 0
      ? shape.rings : [shape.polygon];
  }

  function originalVertices(rings) {
    const points = [];
    const seen = new Set();
    for (const ring of rings) {
      if (!Array.isArray(ring)) return null;
      for (const vertex of ring) {
        if (!Array.isArray(vertex) || vertex.length !== 2 ||
            !Number.isFinite(vertex[0]) || !Number.isFinite(vertex[1])) return null;
        const key = vertex[0] + "," + vertex[1];
        if (!seen.has(key)) {
          seen.add(key);
          points.push([vertex[0], vertex[1]]);
        }
        if (points.length > MAX_VERTICES) return null;
      }
    }
    return points;
  }

  function subsetMask(candidate, source) {
    if (!candidate || !source || candidate.length !== source.length) return false;
    for (let i = 0; i < candidate.length; i += 1) {
      if (candidate[i] && !source[i]) return false;
    }
    return true;
  }

  function signedDoubleArea(a, b, c) {
    return (b[0] - a[0]) * (c[1] - a[1]) -
      (b[1] - a[1]) * (c[0] - a[0]);
  }

  function auditShapes(shapes, width, height) {
    const Delaunator = root.Delaunator;
    const raster = root.MinimalizerOpenCvRaster;
    if (!Delaunator || typeof Delaunator.from !== "function" ||
        !raster || typeof raster.rasterizeLoops !== "function") {
      return Object.freeze({
        version: VERSION, status: "unavailable", shapesAudited: 0,
        acceptedTriangles: 0, rejectedTriangles: 0, geometryApplied: false,
      });
    }
    if (!Array.isArray(shapes) || !Number.isInteger(width) ||
        !Number.isInteger(height) || width < 1 || height < 1 ||
        width * height > MAX_PIXELS) {
      return Object.freeze({
        version: VERSION, status: "invalid-input", shapesAudited: 0,
        acceptedTriangles: 0, rejectedTriangles: 0, geometryApplied: false,
      });
    }

    let shapesAudited = 0;
    let candidateTriangles = 0;
    let acceptedTriangles = 0;
    let rejectedTriangles = 0;
    let skippedShapes = 0;
    let truncated = false;
    try {
      for (const shape of shapes) {
        if (shapesAudited >= MAX_SHAPES || candidateTriangles >= MAX_TRIANGLES) {
          truncated = true;
          break;
        }
        const rings = shapeRings(shape);
        const points = originalVertices(rings);
        if (!points || points.length < 3) {
          skippedShapes += 1;
          continue;
        }
        const original = raster.rasterizeLoops(rings, width, height, 2);
        const mesh = Delaunator.from(points);
        shapesAudited += 1;
        for (let t = 0; t < mesh.triangles.length; t += 3) {
          if (candidateTriangles >= MAX_TRIANGLES) {
            truncated = true;
            break;
          }
          const vertices = [
            points[mesh.triangles[t]],
            points[mesh.triangles[t + 1]],
            points[mesh.triangles[t + 2]],
          ];
          if (!vertices.every(Boolean) ||
              Math.abs(signedDoubleArea(...vertices)) < 1e-9) continue;
          candidateTriangles += 1;
          const triangle = raster.rasterizeLoops([vertices], width, height, 2);
          if (subsetMask(triangle, original)) {
            acceptedTriangles += 1;
          } else {
            rejectedTriangles += 1;
          }
        }
      }
    } catch (_) {
      return Object.freeze({
        version: VERSION, status: "error", shapesAudited,
        candidateTriangles, acceptedTriangles, rejectedTriangles, skippedShapes,
        geometryApplied: false,
      });
    }
    return Object.freeze({
      version: VERSION, status: truncated ? "truncated" : "ok",
      shapesAudited, candidateTriangles, acceptedTriangles, rejectedTriangles,
      skippedShapes, geometryApplied: false,
    });
  }

  root.MinimalizerPublicMeshResearch = Object.freeze({ VERSION, auditShapes });
  if (typeof module !== "undefined" && module.exports) {
    module.exports = root.MinimalizerPublicMeshResearch;
  }
}(typeof window !== "undefined" ? window : globalThis));
