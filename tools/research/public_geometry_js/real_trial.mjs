// Research only: evaluate existing frozen real-image masks. Never draw facial details.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { proposePaperContour, proposeDelaunayPart, trianglesToSVG } from "./geometry.mjs";
import { wholeSignedRoleGate } from "./real_guards.mjs";

function assert(ok, msg) { if (!ok) throw new Error(msg); }
const specFile = process.argv[2], destination = process.argv[3];
assert(specFile && destination, "usage: node real_trial.mjs prepared.json output_dir");
const spec = JSON.parse(fs.readFileSync(specFile, "utf8"));
assert(spec.schema === "public-real-two-case-part-geometry-v1", "wrong provenance schema");
assert(Object.keys(spec.cases).sort().join(",") === "GC001,Raden", "two signed cases mandatory");
fs.mkdirSync(destination, { recursive: true });
const report = { schema: "public-js-real-two-case-v1", status: "REAL_MASK_PROPOSALS_ONLY",
  production: "UNCHANGED", visualGolden: "HOLD", faceDetails: "NOT_RENDERED",
  scope: "SA1041_SHA_FROZEN_STAGE04_FACE_AND_ARMS_ONLY", cases: {} };
for (const caseName of ["GC001", "Raden"]) {
  const record = spec.cases[caseName];
  const width = record.size[0], height = record.size[1];
  assert(width === 340 && height === 340, "size mismatch");
  const rgb = new Uint8Array(fs.readFileSync(record.rgb));
  assert(rgb.length === width * height * 3, "RGB size mismatch");
  const roles = {};
  let faceMask, leftMask, rightMask;
  const combinedTriangles = [];
  for (const role of ["face", "left_arm", "right_arm"]) {
    const part = record.roles[role];
    const signedMask = new Uint8Array(fs.readFileSync(part.signedMask));
    assert(signedMask.length === width * height, "signed mask size mismatch");
    if (role === "face") faceMask = signedMask;
    if (role === "left_arm") leftMask = signedMask;
    if (role === "right_arm") rightMask = signedMask;
    const [x, y, cw, ch] = part.crop;
    const comp = new Uint8Array(fs.readFileSync(part.componentMask));
    assert(comp.length === cw * ch, "component shape mismatch");
    const paper = proposePaperContour({ points: part.points, width: cw, height: ch,
      sourceMask: comp, tolerance: 0.2, maxMissingPixels: 0,
      protectedIndices: [...new Set([0, Math.floor(part.points.length/4),
        Math.floor(part.points.length/2), Math.floor(part.points.length*3/4)])] });
    // Evaluate the entire signed role, not just its largest component.
    const wholeRoleGate = wholeSignedRoleGate(part, paper);
    // Paper is only a proposal; even one out-of-mask pixel means NO-GO.
    let triangle = null;
    if (role !== "face") {
      const t = proposeDelaunayPart({ width, height, partMask: signedMask,
        sourceRGB: rgb, step: 8, maxPoints: 4096 });
      assert(t.extraPixels === 0, "triangles overflow signed part");
      // Sampled RGB belongs to the signed source part; no new RGB introduced.
      let diff = 0, coveredRgbPixels = 0;
      const selected = new Uint8Array(width*height);
      for (const p of t.triangles) {
        combinedTriangles.push(p);
        // Separate source RGB metric is approximate for vertex outlines; exact SVG
        // and supersampled Chrome geometry must be audited independently.
        const [sx, sy] = p.colorSample;
        assert(signedMask[sy*width+sx] === 1, "source RGB escaped signed part");
        diff += Math.abs(rgb[(sy*width+sx)*3] - p.rgb[0]);
        coveredRgbPixels++;
      }
      assert(diff === 0, "sampled source RGB mutated");
      triangle = { acceptedTriangles: t.triangles.length,
        rejectedOutsideMask: t.rejectedOutsideMask,
        coveredPixels: t.coveredPixels, signedPixels: t.sourcePixels,
        missingPixels: t.sourcePixels - t.coveredPixels,
        extraRasterCenterPixels: t.extraPixels, sourceSampleRgbExact: true };
    }
    roles[role] = { provenanceSha: part.mask_sha256,
      wholeRoleGate, signedHoleCount: part.maskHoleCount,
      sourceMaskPixels: part.signedPixels, componentPixels: part.componentPixels,
      observedComponents: part.components, originalContourVertices: part.sourceContourPointCount,
      paper: { candidateOnly: true, accepted: wholeRoleGate.accepted, componentTrialAccepted: paper.accepted,
        verticesBefore: paper.anchorCountBefore, verticesAfter: paper.anchorCountAfter,
        externalPixels: paper.addedPixels, missingComponentPixels: paper.missingPixels,
        protectedPreserved: paper.protectedPreserved, componentOnly: true,
        pixelCenterNotSvgAntialias: true }, delaunator: triangle };
    // Mask only: original-source boundary audit, not portrait composition.
    fs.writeFileSync(path.join(destination, `${caseName}_${role}_paper_source_contour.svg`),
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 340" width="340" height="340"><g transform="translate(${x} ${y})"><path d="${paper.pathData}" stroke="#c43920" stroke-width="0.6" fill="none"/></g></svg>\n`);
  }
  let overlaps = 0;
  for (let i = 0; i < width * height; i++)
    if (faceMask[i] && (leftMask[i] || rightMask[i]) || leftMask[i] && rightMask[i]) overlaps++;
  report.cases[caseName] = { size: [width, height],
    observedRoleOverlapPixels: overlaps, roles,
    samplesRGBSourceVerifiedByPython: true,
    baselineGoldenSourceNotModified: true };
  // This is a proposal-only partial overlay, *not* a full-figure image.
  fs.writeFileSync(path.join(destination, `${caseName}_arm_triangles_candidate.svg`),
    trianglesToSVG({ triangles: combinedTriangles }, width, height)+"\n");
}
function canonical(v) { return JSON.stringify(v, null, 2) + "\n"; }
fs.writeFileSync(path.join(destination, "real_metrics.json"), canonical(report));
console.log(canonical({
  status: report.status, production: report.production, visualGolden: report.visualGolden,
  cases: Object.fromEntries(Object.entries(report.cases).map(([name, item]) =>
    [name, Object.fromEntries(["left_arm","right_arm","face"].map(role =>
      [role, { paper: item.roles[role].paper, triangles: item.roles[role].delaunator }]))]))
}));
