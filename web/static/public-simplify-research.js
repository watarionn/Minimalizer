// Browser-only research observer: Simplify.js 1.2.4 (BSD-2-Clause).
// Proposes vertex reductions but NEVER writes proposed geometry into rendered output.
// A proposal counts only if the existing Public rasterizer reproduces each owner mask bit-for-bit.
(function (root) {
  "use strict";

  const VERSION = "public-simplify-lossless-v1";
  const TOLERANCES = Object.freeze([0.25, 0.5, 0.75, 1.0, 1.5]);
  const MAX_SHAPES = 12;
  const MAX_TRIALS = 48;
  const MAX_PIXELS = 160000;
  const MAX_RING_POINTS = 1200;

  function rawRings(shape) {
    if (!shape || typeof shape !== "object") return [];
    return Array.isArray(shape.rings) && shape.rings.length > 0
      ? shape.rings : [shape.polygon];
  }

  function sameMask(left, right) {
    if (!left || !right || left.length !== right.length) return false;
    for (let i = 0; i < left.length; i += 1) {
      if (left[i] !== right[i]) return false;
    }
    return true;
  }

  function validRing(ring) {
    return Array.isArray(ring) && ring.length >= 3 &&
      ring.length <= MAX_RING_POINTS &&
      ring.every(p => Array.isArray(p) && p.length === 2 &&
        Number.isFinite(p[0]) && Number.isFinite(p[1]));
  }

  function auditShapes(shapes, width, height) {
    const simplify = root.simplify;
    const raster = root.MinimalizerOpenCvRaster;
    if (typeof simplify !== "function" ||
        !raster || typeof raster.rasterizeLoops !== "function") {
      return Object.freeze({ version: VERSION, status: "unavailable", safeSavedVertices: 0, proposals: 0 });
    }
    if (!Array.isArray(shapes) || !Number.isInteger(width) || !Number.isInteger(height) ||
        width < 1 || height < 1 || width * height > MAX_PIXELS) {
      return Object.freeze({ version: VERSION, status: "invalid-input", safeSavedVertices: 0, proposals: 0 });
    }

    let safeSavedVertices = 0;
    let proposals = 0;
    let rejectedProposals = 0;
    let auditedShapes = 0;
    let skippedShapes = 0;
    let truncated = false;
    let reason = "";

    try {
      for (const shape of shapes) {
        if (auditedShapes >= MAX_SHAPES || proposals >= MAX_TRIALS) {
          truncated = true;
          break;
        }
        const rings = rawRings(shape);
        if (rings.length === 0 || !rings.every(validRing)) {
          skippedShapes += 1;
          continue;
        }
        const original = raster.rasterizeLoops(rings, width, height, 2);
        // A shape's hole/fill interaction must be preserved as a WHOLE; no single-ring
        // area comparison is permitted to approve any candidate.
        let candidateRings = rings.map(r => r.map(p => p.slice()));
        auditedShapes += 1;
        for (let i = 0; i < candidateRings.length; i += 1) {
          const sourceRing = candidateRings[i];
          if (sourceRing.length <= 3) continue;
          for (const tolerance of TOLERANCES) {
            if (proposals >= MAX_TRIALS) {
              truncated = true;
              break;
            }
            const source = candidateRings[i];
            // Closed loops are represented without duplicate endpoint in the Public engine.
            // Only remove original vertices: Simplify.js must never synthesize new coordinates.
            const points = source.map(p => ({ x: p[0], y: p[1] }));
            const proposal = simplify(points, tolerance, true);
            if (proposal.length < 3 || proposal.length >= source.length) continue;
            const reduced = proposal.map(p => [p.x, p.y]);
            const proposedRings = candidateRings.slice();
            proposedRings[i] = reduced;
            proposals += 1;
            if (sameMask(original, raster.rasterizeLoops(proposedRings, width, height, 2))) {
              safeSavedVertices += source.length - reduced.length;
              candidateRings = proposedRings;
            } else {
              rejectedProposals += 1;
            }
          }
        }
      }
    } catch (err) {
      reason = "raster-error";
    }

    return Object.freeze({
      version: VERSION,
      status: reason ? "error" : truncated ? "truncated" : "ok",
      auditedShapes, skippedShapes, proposals, rejectedProposals,
      safeSavedVertices, geometryApplied: false,
    });
  }

  root.MinimalizerPublicSimplifyResearch = Object.freeze({ VERSION, auditShapes });
  if (typeof module !== "undefined" && module.exports) {
    module.exports = root.MinimalizerPublicSimplifyResearch;
  }
}(typeof window !== "undefined" ? window : globalThis));
