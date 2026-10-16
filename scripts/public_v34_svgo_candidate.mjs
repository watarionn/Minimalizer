/**
 * MinimalizerPublic: compare frozen v34 lossless SVG against genuine SVGO.
 * Research-only candidate. No UI route or Local Worker hook.
 * node scripts/public_v34_svgo_candidate.mjs INPUT.svg OUTPUT.svg
 */
import {readFileSync, writeFileSync} from "node:fs";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
import {optimize} from "../web/static/vendor/svgo/svgo.browser.js";

export function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}
export function serializerCandidate(source) {
  if (typeof source !== "string" || source.length < 100 ||
      Buffer.byteLength(source, "utf8") > 2_000_000 ||
      !source.startsWith("<svg ") || !source.endsWith("</svg>") ||
      !source.includes('fill-rule="evenodd"') ||
      !source.includes("data:image/png;base64,")) {
    throw new Error("invalid or over-budget frozen v34 hybrid SVG");
  }
  // Allowlist only: no preset-default, convertPathData, transforms or shape edits.
  const options = {multipass: false, plugins: [
    "removeComments", "removeMetadata", "removeDesc",
    "removeDoctype", "removeXMLProcInst", "cleanupAttrs",
  ]};
  const first = optimize(source, options);
  const second = optimize(source, options);
  if (typeof first?.data !== "string" || first.data !== second?.data ||
      !first.data.includes("<svg") || !first.data.includes("</svg>") ||
      Buffer.byteLength(first.data, "utf8") > 2_000_000) {
    throw new Error("SVGO candidate non-deterministic, malformed or oversized");
  }
  return first.data;
}
function cli() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output || resolve(input) === resolve(output)) {
    throw new Error("usage: node scripts/public_v34_svgo_candidate.mjs INPUT.svg OUTPUT.svg");
  }
  const original = readFileSync(input, "utf8");
  const candidate = serializerCandidate(original);
  writeFileSync(output, candidate, {flag: "wx"});
  process.stdout.write(JSON.stringify({
    sourceSHA256: sha256(Buffer.from(original, "utf8")),
    candidateSHA256: sha256(Buffer.from(candidate, "utf8")),
    originalBytes: Buffer.byteLength(original, "utf8"),
    candidateBytes: Buffer.byteLength(candidate, "utf8"),
    savedBytes: Buffer.byteLength(original, "utf8") - Buffer.byteLength(candidate, "utf8"),
    appliedToProduction: false,
  }) + "\n");
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) cli();
