# MinimalizerPublic Paper.js / Delaunator Geometry PoC (2026-10-09)

**Status: IMPLEMENTED / SYNTHETIC TEST PASS / REAL-IMAGE VISUAL GATE HOLD / NOT IN PRODUCTION**

## Scope and current boundary

- Purpose: isolated opt-in research for browser-only MinimalizerPublic, preserving existing MinimalizerPublic Local/Public separation.
- Code: `tools/research/public_geometry_js/{package.json,package-lock.json,geometry.mjs,geometry.test.mjs,demo.mjs,README.md}`.
- No `web/static`, LocalWorker, RRM, API, deployment pipeline, or canonical engine changes.
- No image synthesis, img2img, or generation of missing character parts.
- Only original-source mask/RGB evidence is permitted in this PoC. Synthetic masks are *test fixtures*, not claimed real-image evidence.
- Paper.js 0.12.18 (MIT), Delaunator 5.1.0 (ISC), robust-predicates 3.0.3 (Unlicense). Exact versions and integrity hashes are in lockfile. Install only inside the isolated research directory.

## Reproducible verification

Verification performed against immutable GitHub commit
`706af37ccd1c1399112b8fadaede871f842a508f`
(after discovering that the branch-name raw file URL temporarily returned a stale CDN-cached version).

1. Download the four research files and package-lock from that exact commit to an isolated temporary work directory.
2. Run `npm ci --ignore-scripts --no-audit --no-fund`: **PASS**, installed 3 packages.
3. Run `npm test`: **6 passed, 0 failed, 0 skipped** (Node.js v26.3.0, Windows).
4. Run `npm run demo -- ./out`: **exit 0**, producing source-independent synthetic SVGs and a JSON metric artifact.

The 6 tests cover Paper stable proposals, Paper overshoot hard rejection, Paper invalid evidence rejection, Delaunator separate-part color provenance, masked-hole triangle rejection, malformed evidence/point budget fail-closed.

## Observed synthetic metrics

| Trial | Metric | Result |
|---|---|---|
| Paper | contour anchors | 12 → 11 |
| Paper | protected source anchors | retained |
| Paper | new source-external pixels after cubic simplification | **148**, hence `accepted=false` |
| Paper | missing original pixels | 0 |
| Delaunator | proposed accepted triangles | 122 |
| Delaunator | triangles rejected for leaving observed part mask | 14 |
| Delaunator | accepted triangle covered source pixels | 1660 / 2319 |
| Delaunator | extra outside pixels at audited source resolution | **0** |
| Visibility | full source subject visual quality | **not evaluated, HOLD** |

**Interpretation:** Paper can reduce anchors but Bézier handles bulge beyond original silhouette even when protected source anchors remain unchanged. Do not interpret fewer anchors as better fidelity. Delaunay candidates avoid observed other-part pixels on this single-resolution raster gate, but they leave 659 test pixels uncovered and cannot represent clean connected colored masses by themselves.

## Risks and limitations

- Paper `pathData` is not interchangeable with pixel-centre tests of flattened curves: SVG antialiasing, coordinate precision, thin sub-pixel excursions, and viewer differences require stronger tests.
- Delaunator is not a constrained polygon mesher. Triangles are rejected whenever their rasterized footprint intersects holes/other parts; this may leave large coverage gaps. It does not perform semantic decomposition or invent disconnected structures.
- 0 outside **source-resolution raster pixel-centers** is not a 0 continuous geometry/supersampled footprint guarantee.
- Ingested mask must be tied to independently verified original-source data. ML observer guidance cannot be elevated to visible drawing authority.
- Color sample is an original source RGB triplet inside the same independently verified part; triangle fill is a simplified approximation, not pixelwise source identity.
- Existing Public is still the production source of truth, and no regression, Golden full-image, cross-browser or Diagnostic-2 visual QA was run in this research stage.

## Decision / next phase

- **ACCEPT as research-only PoC.**
- **DO NOT merge as a production feature or deploy.** Review research-only code separately.
- Next: original GC001/Kyoko and Raden multi-image, SHA-bound evidence masks. Use existing canonical output side-by-side with Paper and Delaunator candidate-only output. Keep tie/arm/hair protected. Run optical/structural/source RGB and pixel-footprint gates, supersampled SVG comparison and visual review. If Paper overshoots, retain canonical. If Delaunator leaves large gaps or changes important color features, retain existing internal face/facet reconstruction.
