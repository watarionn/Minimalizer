import fs from "node:fs";
import path from "node:path";
import { rasterizePolygon, proposePaperContour, proposeDelaunayPart, trianglesToSVG } from "./geometry.mjs";

// Synthetic-only fixture. Never substitute synthetic masks for verified images.
const W = 80, H = 60;
const ring = [[6, 6], [20, 6], [40, 6], [58, 6], [66, 6],
  [66, 18], [66, 30], [66, 52], [40, 52], [20, 52], [6, 52], [6, 30]];
const sourceMask = rasterizePolygon(ring, W, H);
const partMask = sourceMask.slice();
for (let y = 19; y < 40; y++) for (let x = 27; x < 48; x++) partMask[y * W + x] = 0;
const rgb = new Uint8Array(W * H * 3);
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
  const i = (y * W + x) * 3;
  rgb[i] = x < 40 ? 24 : 165;
  rgb[i + 1] = y < 30 ? 120 : 80;
  rgb[i + 2] = 210;
}
const paper = proposePaperContour({ points: ring, width: W, height: H,
  sourceMask, protectedIndices: [0, 4, 7, 10], tolerance: 0.1 });
const delaunay = proposeDelaunayPart({ width: W, height: H,
  partMask, sourceRGB: rgb, step: 5 });
const report = {
  status: "SYNTHETIC_ONLY_NO_PRODUCTION_INTEGRATION",
  paper: { ...paper, pathData: paper.pathData },
  delaunay: { ...delaunay, points: undefined, triangles: undefined },
  previewTriangles: delaunay.triangles.length,
};
const out = process.argv[2];
if (out) {
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, "synthetic-triangles.svg"),
    trianglesToSVG(delaunay, W, H), "utf8");
  fs.writeFileSync(path.join(out, "metrics.json"), JSON.stringify(report, null, 2) + "\n", "utf8");
  fs.writeFileSync(path.join(out, "synthetic-paper-path.svg"),
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}"><path d="${paper.pathData}" fill="rgb(24,120,210)"/></svg>`, "utf8");
}
console.log(JSON.stringify(report, null, 2));
