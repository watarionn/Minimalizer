// MinimalizerPublic-only, opt-in SVGPathCommander 2.3.3 observer.
// Generates SVG path strings from existing owner rings for diagnostics only.
// No path candidate is ever used for raster, SVG, owner masks or palette changes.
(function (root) {
  "use strict";
  const VERSION = "public-svgpath-owner-audit-v1";
  const MAX_SHAPES = 8;
  const MAX_RINGS = 64;
  const MAX_POINTS = 1800;
  const MAX_PATH_CHARS = 60000;
  const EPS = 1e-7;

  function ringsOf(shape) {
    if (!shape || typeof shape !== "object") return [];
    return Array.isArray(shape.rings) && shape.rings.length
      ? shape.rings : [shape.polygon];
  }

  function ringData(points) {
    if (!Array.isArray(points) || points.length < 3) return null;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    const commands = [];
    for (let i = 0; i < points.length; i += 1) {
      const p = points[i];
      if (!Array.isArray(p) || p.length !== 2 ||
          !Number.isFinite(p[0]) || !Number.isFinite(p[1])) return null;
      const [x, y] = p;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
      commands.push((i ? "L" : "M") + x + " " + y);
    }
    return {d: commands.join(" ") + " Z", minX, maxX, minY, maxY};
  }

  function auditShapes(shapes, width, height) {
    const PathCommander = root.SVGPathCommander;
    if (typeof PathCommander !== "function" ||
        typeof PathCommander.parsePathString !== "function") {
      return Object.freeze({version: VERSION, status: "unavailable",
        parsedRings: 0, bboxMatches: 0, geometryApplied: false});
    }
    if (!Array.isArray(shapes) || !Number.isInteger(width) ||
        !Number.isInteger(height) || width < 1 || height < 1 ||
        width * height > 160000) {
      return Object.freeze({version: VERSION, status: "invalid-input",
        parsedRings: 0, bboxMatches: 0, geometryApplied: false});
    }

    let shapesAudited = 0, parsedRings = 0, invalidRings = 0;
    let bboxMatches = 0, bboxMismatches = 0, sourcePathBytes = 0;
    let canonicalPathBytes = 0, sourceVertices = 0, measuredLength = 0;
    let truncated = false, status = "ok";
    try {
      for (const shape of shapes) {
        if (shapesAudited >= MAX_SHAPES || parsedRings >= MAX_RINGS) {
          truncated = true; break;
        }
        shapesAudited += 1;
        for (const ring of ringsOf(shape)) {
          if (parsedRings >= MAX_RINGS) {truncated = true; break;}
          const data = ringData(ring);
          if (!data) {invalidRings += 1; continue;}
          if (sourceVertices + ring.length > MAX_POINTS ||
              sourcePathBytes + data.d.length > MAX_PATH_CHARS) {
            truncated = true; break;
          }
          // Read-only geometry inspection: do not call transform/optimize on
          // render geometry and do not use canonical path to replace source.
          const path = new PathCommander(data.d);
          const bounds = path.getBBox();
          const length = path.getTotalLength();
          const parsed = PathCommander.parsePathString(data.d);
          const bboxExact = parsed.length >= 4 &&
            [bounds.x,bounds.y,bounds.x2,bounds.y2,length].every(Number.isFinite) &&
            Math.abs(bounds.x - data.minX) < EPS &&
            Math.abs(bounds.y - data.minY) < EPS &&
            Math.abs(bounds.x2 - data.maxX) < EPS &&
            Math.abs(bounds.y2 - data.maxY) < EPS;
          if (bboxExact) bboxMatches += 1;
          else bboxMismatches += 1;
          parsedRings += 1;
          sourceVertices += ring.length;
          sourcePathBytes += data.d.length;
          canonicalPathBytes += path.toString().length;
          measuredLength += length;
        }
        if (truncated) break;
      }
    } catch (_) {
      status = "error";
    }
    return Object.freeze({
      version: VERSION, status: status === "error" ? status : truncated ? "truncated" : "ok",
      shapesAudited, parsedRings, invalidRings, bboxMatches, bboxMismatches,
      sourceVertices, sourcePathBytes, canonicalPathBytes,
      measuredLength: Math.round(measuredLength * 1000) / 1000,
      geometryApplied: false,
    });
  }

  root.MinimalizerPublicSvgPathResearch = Object.freeze({VERSION, auditShapes});
  if (typeof module !== "undefined" && module.exports) {
    module.exports = root.MinimalizerPublicSvgPathResearch;
  }
}(typeof window !== "undefined" ? window : globalThis));
