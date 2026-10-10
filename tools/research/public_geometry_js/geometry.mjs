// Research-only geometry proposals. NEVER imported from MinimalizerPublic.
import paper from "paper";
import Delaunator from "delaunator";

const assert = (ok, msg) => { if (!ok) throw new Error(msg); };
const integer = (n) => Number.isSafeInteger(n) && n > 0;
const index = (x, y, width) => y * width + x;
const binary = (m, width, height) =>
  m && m.length === width * height && Array.from(m).every((v) => v === 0 || v === 1);

function validateImage(width, height, mask) {
  assert(integer(width) && integer(height) && width * height <= 4_000_000, "invalid image dimensions");
  assert(binary(mask, width, height), "verified binary part mask required");
}

function validPoints(points) {
  assert(Array.isArray(points) && points.length >= 3, "a polygon needs >=3 points");
  for (const p of points) {
    assert(Array.isArray(p) && p.length === 2 && p.every(Number.isFinite), "invalid contour point");
  }
}

function pointInPolygon(x, y, points) {
  let inside = false;
  for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
    const a = points[i], b = points[j];
    if ((a[1] > y) !== (b[1] > y) &&
        x < ((b[0] - a[0]) * (y - a[1])) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside;
}

export function rasterizePolygon(points, width, height) {
  validPoints(points);
  assert(integer(width) && integer(height), "invalid dimensions");
  const result = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    result[index(x, y, width)] = Number(pointInPolygon(x + 0.5, y + 0.5, points));
  }
  return result;
}

function exactAnchor(anchors, pt) {
  return anchors.some((p) => Math.hypot(p[0] - pt[0], p[1] - pt[1]) <= 1e-6);
}

/**
 * Independent Paper.js candidate only. sourceMask must be the upstream,
 * independently verified ORIGINAL part mask. A curve may be aesthetically
 * pleasing but is never accepted when it extends beyond original pixels,
 * drops required protected landmarks or exceeds the omission allowance.
 * Browser SVG rasterization needs a separate cross-browser release gate.
 */
export function proposePaperContour({ points, width, height, sourceMask, tolerance = 0.5,
  protectedIndices = [], maxMissingPixels = 0, flatness = 0.1 } = {}) {
  validateImage(width, height, sourceMask);
  validPoints(points);
  assert(Number.isFinite(tolerance) && tolerance >= 0 && tolerance <= 10, "invalid tolerance");
  assert(Number.isFinite(flatness) && flatness > 0 && flatness <= 1, "invalid flatness");
  assert(Number.isSafeInteger(maxMissingPixels) && maxMissingPixels >= 0, "invalid missing budget");
  assert(Array.isArray(protectedIndices) && protectedIndices.every((i) => Number.isInteger(i) && i >= 0 && i < points.length), "invalid landmarks");

  // Paper geometry functions do not require an SVG renderer or ML model.
  if (!paper.project) paper.setup([width, height]);
  const path = new paper.Path({ segments: points, closed: true, insert: false });
  try {
    const simplified = path.simplify(tolerance);
    const anchors = path.segments.map((s) => [s.point.x, s.point.y]);
    const protectedPreserved = protectedIndices.every((i) => exactAnchor(anchors, points[i]));
    const pathData = path.pathData;
    const flattened = path.clone({ insert: false });
    let polygon;
    try {
      flattened.flatten(flatness);
      polygon = flattened.segments.map((s) => [s.point.x, s.point.y]);
    } finally {
      flattened.remove();
    }
    assert(polygon.length >= 3, "Paper produced degenerate contour");
    const proposedMask = rasterizePolygon(polygon, width, height);
    let addedPixels = 0, missingPixels = 0, originalPixels = 0, proposedPixels = 0;
    for (let i = 0; i < proposedMask.length; i++) {
      if (proposedMask[i] && !sourceMask[i]) addedPixels++;
      if (!proposedMask[i] && sourceMask[i]) missingPixels++;
      originalPixels += sourceMask[i];
      proposedPixels += proposedMask[i];
    }
    const accepted = protectedPreserved && addedPixels === 0
      && missingPixels <= maxMissingPixels && anchors.length < points.length;
    return {
      accepted, source: "paper@0.12.18", candidateOnly: true,
      anchorCountBefore: points.length, anchorCountAfter: anchors.length,
      simplified, protectedPreserved, addedPixels, missingPixels,
      originalPixels, proposedPixels, pathData, anchors, flattenedPointCount: polygon.length,
    };
  } finally {
    path.remove();
  }
}

function triangleArea(a, b, c) {
  return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
}

function pointInTriangle(px, py, a, b, c) {
  const area = triangleArea(a, b, c);
  if (Math.abs(area) < 1e-8) return false;
  const s = triangleArea(a, b, [px, py]) / area;
  const t = triangleArea(b, c, [px, py]) / area;
  const u = triangleArea(c, a, [px, py]) / area;
  return s >= -1e-9 && t >= -1e-9 && u >= -1e-9;
}

function trianglePixels(vertices, width, height) {
  const minX = Math.max(0, Math.floor(Math.min(...vertices.map((p) => p[0]))));
  const maxX = Math.min(width - 1, Math.ceil(Math.max(...vertices.map((p) => p[0]))));
  const minY = Math.max(0, Math.floor(Math.min(...vertices.map((p) => p[1]))));
  const maxY = Math.min(height - 1, Math.ceil(Math.max(...vertices.map((p) => p[1]))));
  const inside = [];
  for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
    if (pointInTriangle(x + 0.5, y + 0.5, ...vertices)) inside.push([x, y]);
  }
  return inside;
}

/**
 * Draws ONLY candidate triangles whose every touched source-resolution pixel
 * belongs to ONE verified part mask. Source RGB is sampled verbatim from the
 * part for every fill. This is deliberately not a segmentation algorithm:
 * run separately per proven semantic part, not per whole-image foreground.
 */
export function proposeDelaunayPart({ width, height, partMask, sourceRGB, step = 4,
  maxPoints = 4096 } = {}) {
  validateImage(width, height, partMask);
  assert(sourceRGB && sourceRGB.length === width * height * 3, "source RGB required");
  assert(integer(step) && step <= 64, "invalid sample step");
  assert(integer(maxPoints) && maxPoints <= 20_000, "invalid point cap");

  const points = [];
  for (let y = 0; y < height; y += step) for (let x = 0; x < width; x += step) {
    const px = Math.min(width - 1, x + Math.floor(step / 2));
    const py = Math.min(height - 1, y + Math.floor(step / 2));
    if (partMask[index(px, py, width)]) points.push([px + 0.5, py + 0.5]);
    assert(points.length <= maxPoints, "point cap exceeded; abort instead of truncating");
  }
  if (points.length < 3) {
    return { source: "delaunator@5.1.0", candidateOnly: true, points, triangles: [],
      rejectedOutsideMask: 0, coveredPixels: 0, sourcePixels: partMask.reduce((a, b) => a + b, 0) };
  }
  const mesh = Delaunator.from(points);
  const triangles = [], covered = new Uint8Array(width * height);
  let rejectedOutsideMask = 0, rejectedEmpty = 0;
  for (let t = 0; t < mesh.triangles.length; t += 3) {
    const vertices = [points[mesh.triangles[t]], points[mesh.triangles[t + 1]],
      points[mesh.triangles[t + 2]]];
    const pixels = trianglePixels(vertices, width, height);
    if (!pixels.length) { rejectedEmpty++; continue; }
    if (pixels.some(([x, y]) => !partMask[index(x, y, width)])) {
      rejectedOutsideMask++; continue;
    }
    const [sampleX, sampleY] = pixels[0];
    const colorOffset = index(sampleX, sampleY, width) * 3;
    const rgb = Array.from(sourceRGB.slice(colorOffset, colorOffset + 3));
    for (const [x, y] of pixels) covered[index(x, y, width)] = 1;
    triangles.push({ vertices, rgb, colorSample: [sampleX, sampleY] });
  }
  let coveredPixels = 0, sourcePixels = 0, extraPixels = 0;
  for (let i = 0; i < covered.length; i++) {
    coveredPixels += covered[i]; sourcePixels += partMask[i];
    if (covered[i] && !partMask[i]) extraPixels++;
  }
  assert(extraPixels === 0, "invariant: triangulation exceeded source part mask");
  return { source: "delaunator@5.1.0", candidateOnly: true,
    points, triangles, rejectedOutsideMask, rejectedEmpty,
    coveredPixels, sourcePixels, extraPixels };
}

export function trianglesToSVG(proposal, width, height) {
  assert(proposal && Array.isArray(proposal.triangles), "triangle proposal required");
  const safe = (n) => Number(n.toFixed(4));
  const polygons = proposal.triangles.map((t) => {
    const xy = t.vertices.map((p) => p.map(safe).join(",")).join(" ");
    const fill = t.rgb.map((c) => { assert(Number.isInteger(c) && c >= 0 && c <= 255, "invalid RGB"); return c; }).join(",");
    return `<polygon points="${xy}" fill="rgb(${fill})"/>`;
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${polygons.join("")}</svg>`;
}
