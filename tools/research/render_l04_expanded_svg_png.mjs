import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { Resvg, initWasm } from "../../web/static/vendor/resvg-wasm/index.mjs";

const [svgArg, pngArg] = process.argv.slice(2);
if (!svgArg || !pngArg || process.argv.length !== 4) {
  console.error("usage: node render_l04_expanded_svg_png.mjs <expanded.svg> <output.png>");
  process.exit(2);
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const wasmPath = path.resolve(scriptDir, "../../web/static/vendor/resvg-wasm/index_bg.wasm");
const packagePath = path.resolve(scriptDir, "../../web/static/vendor/resvg-wasm/package.json");
const [wasm, packageBytes, svg] = await Promise.all([
  readFile(wasmPath),
  readFile(packagePath),
  readFile(path.resolve(svgArg)),
]);
const packageJson = JSON.parse(packageBytes.toString("utf8"));
await initWasm(wasm);

const renderer = new Resvg(new Uint8Array(svg), { fitTo: { mode: "original" } });
const image = renderer.render();
try {
  if (!Number.isSafeInteger(image.width) || !Number.isSafeInteger(image.height)
      || image.width < 1 || image.height < 1) {
    throw new Error("invalid SVG raster dimensions");
  }
  const png = image.asPng();
  await writeFile(path.resolve(pngArg), png);
  const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
  console.log(JSON.stringify({
    schema: "minimalizer/local-l04/svg-raster/v1",
    source_svg_sha256: sha256(svg),
    png_sha256: sha256(png),
    renderer: packageJson.name,
    version: packageJson.version,
    wasm_sha256: sha256(wasm),
    fit: "original",
    preserve_alpha: true,
    width: image.width,
    height: image.height,
    bytes: png.length,
  }));
} finally {
  image.free();
  renderer.free();
}
