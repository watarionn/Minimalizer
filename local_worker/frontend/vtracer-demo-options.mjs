// Settings for the pinned VTracer vtracer-wasm@0.1.0 browser build.
// Matches controls in the classic visioncortex/vtracer web demo.
// IMPORTANT: this bundle does not expose the new VTracer 1.0-only options.
export const VTRACER_DEFAULTS = Object.freeze({
  binary: false,
  hierarchical: "stacked",
  mode: "spline",
  filterSpeckle: 4,
  colorPrecision: 6,
  layerDifference: 16,
  cornerThreshold: 60,
  lengthThreshold: 4,
  maxIterations: 10,
  spliceThreshold: 45,
  pathPrecision: 4
});
const LIMITS = Object.freeze({
  filterSpeckle: [1, 16, 1],
  colorPrecision: [1, 8, 1],
  layerDifference: [0, 255, 1],
  cornerThreshold: [0, 180, 1],
  lengthThreshold: [3.5, 10, 0.5],
  spliceThreshold: [0, 180, 1],
  pathPrecision: [0, 8, 1]
});
export function normalizeVTracerSettings(input = {}) {
  const result = {...VTRACER_DEFAULTS};
  if (typeof input !== "object" || input === null || Array.isArray(input))
    throw new TypeError("VTracer settings must be an object");
  result.binary = input.binary === true;
  if (input.hierarchical === "stacked" || input.hierarchical === "cutout")
    result.hierarchical = input.hierarchical;
  if (["pixel", "polygon", "spline"].includes(input.mode))
    result.mode = input.mode;
  for (const [key, [min, max, step]] of Object.entries(LIMITS)) {
    if (input[key] === undefined) continue;
    const n = Number(input[key]);
    if (!Number.isFinite(n) || n < min || n > max)
      throw new RangeError(key + " out of range");
    const snapped = Math.round((n - min) / step) * step + min;
    result[key] = Number(snapped.toFixed(6));
  }
  // Never send unknown API options to the pinned WASM; it may reject them.
  return result;
}
export function readVTracerControls(root = document) {
  const field = (id) => root.getElementById("vtracer-" + id);
  return normalizeVTracerSettings({
    binary: field("color-mode").value === "bw",
    hierarchical: field("hierarchical").value,
    mode: field("mode").value,
    filterSpeckle: field("filter-speckle").value,
    colorPrecision: field("color-precision").value,
    layerDifference: field("gradient-step").value,
    cornerThreshold: field("corner-threshold").value,
    lengthThreshold: field("segment-length").value,
    spliceThreshold: field("splice-threshold").value,
    pathPrecision: field("path-precision").value
  });
}
export function writeVTracerControls(root = document, options = VTRACER_DEFAULTS) {
  const s = normalizeVTracerSettings(options);
  const field = (id) => root.getElementById("vtracer-" + id);
  field("color-mode").value = s.binary ? "bw" : "color";
  field("hierarchical").value = s.hierarchical;
  field("mode").value = s.mode;
  for (const [id, name] of [
    ["filter-speckle", "filterSpeckle"], ["color-precision", "colorPrecision"],
    ["gradient-step", "layerDifference"], ["corner-threshold", "cornerThreshold"],
    ["segment-length", "lengthThreshold"], ["splice-threshold", "spliceThreshold"],
    ["path-precision", "pathPrecision"]
  ]) field(id).value = String(s[name]);
  return s;
}
