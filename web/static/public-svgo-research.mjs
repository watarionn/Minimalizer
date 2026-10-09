// MinimalizerPublic opt-in SVGO 4.1.0 experiment. Never applied to production geometry.
// This module loads ONLY after ?publicSvgoResearch=1; it is not a renderer.
import { optimize } from "./vendor/svgo/svgo.browser.js";

export const VERSION = "public-svgo-pixel-audit-v1";
const MAX_SHAPES = 8;
const MAX_RINGS = 48;
const MAX_POINTS = 1600;
const MAX_PIXELS = 160000;
const MAX_CHARS = 60000;
const UTF8 = new TextEncoder();

const byteLength = (s) => UTF8.encode(s).byteLength;
const invalid = (status) => Object.freeze({
  version: VERSION, status, shapesAudited: 0, ownerRings: 0,
  sourceBytes: 0, optimizedBytes: 0, savedBytes: 0,
  rasterDifferentPixels: null, rasterExact: false, applied: false,
});

function pathFor(points) {
  if (!Array.isArray(points) || points.length < 3) return null;
  const commands = [];
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (!Array.isArray(p) || p.length !== 2 ||
        !Number.isFinite(p[0]) || !Number.isFinite(p[1]) ||
        Math.abs(p[0]) > 1000000 || Math.abs(p[1]) > 1000000) return null;
    commands.push((i === 0 ? "M" : "L") + p[0] + " " + p[1]);
  }
  return commands.join(" ") + " Z";
}

// Build a NEW SVG from a bounded copy of already-computed source-owner rings.
// Nothing below reads the user's original file or changes the production canvas.
export function buildSourceSvg(shapes, width, height) {
  if (!Array.isArray(shapes) || !Number.isInteger(width) ||
      !Number.isInteger(height) || width < 1 || height < 1 ||
      width * height > MAX_PIXELS) return {status: "invalid-input"};
  const entries = [];
  let rings = 0, points = 0, chars = 0, truncated = false;
  let shapesAudited = 0;
  for (const shape of shapes) {
    if (shapesAudited >= MAX_SHAPES) {truncated = true; break;}
    if (!shape || !Array.isArray(shape.rgb) ||
        shape.rgb.length !== 3 ||
        !shape.rgb.every(v => Number.isInteger(v) && v >= 0 && v <= 255)) {
      return {status: "invalid-shape"};
    }
    const loops = Array.isArray(shape.rings) && shape.rings.length
      ? shape.rings : [shape.polygon];
    if (!loops.length || loops.some(loop => !Array.isArray(loop))) {
      return {status: "invalid-shape"};
    }
    // A whole owner is accepted or skipped. Never measure a partial hole set.
    const nextPoints = loops.reduce((n, p) => n + p.length, 0);
    if (rings + loops.length > MAX_RINGS || points + nextPoints > MAX_POINTS) {
      truncated = true; break;
    }
    const ds = loops.map(pathFor);
    if (ds.some(d => d === null)) return {status: "invalid-ring"};
    const d = ds.join(" ");
    if (chars + d.length > MAX_CHARS) {truncated = true; break;}
    const fill = "rgb(" + shape.rgb.join(",") + ")";
    entries.push('<path fill="' + fill + '" fill-rule="evenodd" d="' + d + '"/>');
    shapesAudited++;
    rings += loops.length;
    points += nextPoints;
    chars += d.length;
  }
  if (!shapesAudited) return {status: truncated ? "bounded" : "empty"};
  // Comment is deliberately inert but optimizable; viewBox, fill rule, paint
  // order and original absolute path coordinates are preserved in the source.
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + width +
    '" height="' + height + '" viewBox="0 0 ' + width + ' ' + height +
    '"><!-- SVGO source-owner diagnostic only --><g>' +
    entries.join("") + '</g></svg>';
  return {status: truncated ? "truncated" : "ok", svg,
    shapesAudited, ownerRings: rings, vertices: points, truncated};
}

export function makeCandidate(svg) {
  if (typeof svg !== "string" || svg.length > MAX_CHARS * 2 ||
      svg.length < 20) throw new Error("SVG source out of bounds");
  // Conservative serializer work only. No transform, polygon approximation,
  // shape merge, palette changes, or automatic SVG replacement.
  const result = optimize(svg, {
    multipass: false,
    plugins: ["removeComments", "removeMetadata", "removeDesc",
      "removeDoctype", "removeXMLProcInst", "cleanupAttrs"],
  });
  if (!result || typeof result.data !== "string" ||
      result.data.length > MAX_CHARS * 2) throw new Error("Invalid SVGO output");
  return result.data;
}

export function rgbaDiffPixels(a, b) {
  if (!a || !b || a.length !== b.length || a.length % 4 !== 0) return null;
  let pixels = 0;
  for (let i = 0; i < a.length; i += 4) {
    if (a[i] !== b[i] || a[i+1] !== b[i+1] ||
        a[i+2] !== b[i+2] || a[i+3] !== b[i+3]) pixels++;
  }
  return pixels;
}

async function raster(svg, width, height) {
  const url = URL.createObjectURL(new Blob([svg], {type: "image/svg+xml"}));
  try {
    const img = await new Promise((resolve, reject) => {
      const item = new Image();
      item.onload = () => resolve(item);
      item.onerror = () => reject(new Error("SVG raster decode failed"));
      item.src = url;
    });
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d", {willReadFrequently: true});
    if (!ctx) throw new Error("Canvas context unavailable");
    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(img, 0, 0, width, height);
    return ctx.getImageData(0, 0, width, height).data;
  } finally {
    URL.revokeObjectURL(url);
  }
}

export async function auditShapes(shapes, width, height) {
  const built = buildSourceSvg(shapes, width, height);
  if (!built.svg) return invalid(built.status);
  const base = {version: VERSION, shapesAudited: built.shapesAudited,
    ownerRings: built.ownerRings, vertices: built.vertices,
    sourceBytes: byteLength(built.svg), applied: false};
  try {
    const optimized = makeCandidate(built.svg);
    const repeat = makeCandidate(built.svg);
    if (repeat !== optimized) return Object.freeze({...base,
      status: "non-deterministic", optimizedBytes: byteLength(optimized),
      savedBytes: 0, rasterDifferentPixels: null, rasterExact: false});
    const [before, after] = await Promise.all([
      raster(built.svg, width, height), raster(optimized, width, height),
    ]);
    const changed = rgbaDiffPixels(before, after);
    const optimizedBytes = byteLength(optimized);
    const exact = changed === 0;
    return Object.freeze({...base, status: !exact ? "pixel-mismatch"
      : built.truncated ? "truncated" : "ok",
      optimizedBytes, savedBytes: exact
        ? Math.max(0, base.sourceBytes - optimizedBytes) : 0,
      rasterDifferentPixels: changed, rasterExact: exact});
  } catch (_) {
    return Object.freeze({...base, status: "error", optimizedBytes: 0,
      savedBytes: 0, rasterDifferentPixels: null, rasterExact: false});
  }
}
