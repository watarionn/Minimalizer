# MinimalizerPublic R2: full color-group geometry observer and Chrome rollback

Date: 2026-10-10
Status: **R2 RESEARCH VERIFY PASS / ALL SIMPLIFICATION CANDIDATES REJECTED / PRODUCTION HOLD**

## Provenance and boundaries
- Repository `watarionn/Minimalizer`; R2 research branch `research/public-r2-source-owner-geometry-gate-20261010` is stacked on R1 Draft PR #353 (itself based on `main`). It does **not** merge v34 Draft PR #308 or its v33 parent #306.
- Immutable archived v34 source `chatGPT及びCodex用/Minimalizer/SvgLocalRollbackV34_20261009`, and independent original v32 Golden `chatGPT及びCodex用/Minimalizer/ConnectedSourcePlanesV32_20261009` both SHA-gated before output.
- No modifications to MinimalizerLocal, Python worker, Public route, live production renderer, image source content, or existing Golden.
- Three source-color-group SVG scenes remain v34 hybrid SVGs with frozen raster Facet background. Color groups **are not verified semantic arm/clothing/face owners**. The source material ownership and Stage8 budget HOLD are still binding.

## Algorithm: production-safe by isolation
- `scripts/public_r2_owner_geometry.cjs`: parses all exact v34 relative SVG path commands using pinned **SVGPathCommander**; rejects unsupported path commands, non-integer/out-of-bounds coordinates, unknown SVG group structures, malformed/over-budget rings; preserves entire source color-group, all loops, RGB order and painter order. **Simplify.js** proposes deleting only original vertices (0.35 / 0.85 / 1.25 tolerances) without adding geometry.
- Every nontrivial proposal is checked against the **entire source color-group even-odd polygon mask including holes** with the existing OpenCV-compatible browser mask implementation at scale 2. Whole-group comparison is mandatory, independent of the normal opt-in 8/12-shape diagnostic caps.
- Actual pinned **polygon-clipping** checks viewport intersections for every original ring (read-only). **Earcut** triangulates only unambiguous, bounded single-ring candidates for diagnostics; multi-ring groups are **not** falsely interpreted as one outer plus holes; no triangle is granted output ownership. Clipper2 alternative was not used because polygon-clipping sufficed for read-only diagnostics; VTracer remains HOLD.
- `scripts/verify_public_r2_chrome.py`: independent real **Chrome 154.0.8037.98** replay of original candidate and original frozen v32 Golden, at 340×340 native RGBA **and** 680×680 2x reference. Any mismatch rolls back **that individual color group** to the exact v34 source. The final SVG must be exact at both scales and must reject an intentionally painted black rectangle. Candidate search never bypasses the full source SHA gate.
- Mark output `productionPromoted:false` and `semanticOwnerAuthorized:false` regardless of Chrome success; no production route hook.

## Real three-Golden result
| Golden | Color groups fully visited | Original rings clipped without errors | Mask proposals tested | Mask rejected | Mask-accepted proposals / nominal vertices saved | Chrome-rejected groups | Final 340 / 680 diff |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kyoko | 238 | 271 | 471 | 469 | 2 / 7 | 2 | 0 / 0 |
| Noel | 371 | 377 | 727 | 719 | 8 / 17 | 8 | 0 / 0 |
| Ririka | 301 | 382 | 596 | 590 | 6 / 18 | 6 | 0 / 0 |
| **Total** | **910** | **1,030** | **1,794** | **1,778** | **16 / 42** | **16** | **all exact after rollback** |

All three cases had `candidateCoverageComplete:true`, source manifests passed, and unsourced black paint was detected on all 115,600 native pixels per case. Earcut single-ring diagnostics: Kyoko 219, Noel 365, Ririka 253; zero triangulation invocation errors. These counts do **not** certify triangulated replacement geometry.

**Significant finding:** a source-color-group proposal may be bit-for-bit identical in the existing scale-2 binary mask yet still cause genuine Chrome SVG output differences. Before rollback the grouped candidates showed 340px discrepancies of **18 / 27 / 26**, and 2x discrepancies **44 / 65 / 64** (Kyoko / Noel / Ririka). Even a single mask-safe Noel 2-vertex simplification caused 3/7 differing Chrome pixels in the earlier bounded run. No such candidate may be adopted; all 16 were automatically rolled back. **Actual source-vertex savings finally approved = 0.**

Final safe SVG output SHA-256 = exact frozen v34 original in all three cases, not a newly improved rendering. This is a correctness/safety infrastructure advance, not visual quality improvement.

## Test and verification record
- Genuine browser vendor JS synthetic suite `node tests/js/test_public_r2_owner_geometry.cjs`: 6 scenarios PASS (collinear positive, unsafe notch negative, detached rings, 12 group full coverage, invalid source, no mutation).
- `python -m pytest ...` R2 plus existing nine Public library integration and Local isolation tests: **46 PASS** (all existing 42 + four R2).
- `python -m py_compile` and `node --check` PASS.
- Real Chrome complete three-case pipeline **two independent executions PASS**.
- Direct byte comparison of the complete two-run files: **10/10 byte-exact** (3 raw rejected-candidate SVG, 3 Chrome-safe SVG, 3 full source-owner audit JSON, 1 top-level Chrome summary JSON).
- Local working directory was kept isolated in a detached worktree; pre-existing developer changes to the unrelated original local worktree must remain untouched.
- Real files and evidence: canonical Google Drive `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R2_20261010/` (see the actual uploaded data files).

## Decision and next phase
**R2 engineering and verification gate COMPLETE.** The new two-scale Chrome rollback is essential and demonstrated by a real negative case. No simplification, triangulation, polygon operation or inferred detail enters product rendering. The signed semantic garment/arm/neck-tie/staff protection and Stage8 original vertex budget are still HOLD, as are user Golden visual acceptance and Safari/iPhone DPR.

**R3:** bounded genuine geometric improvements preserving original source-color ownership without raster-visible changes, e.g. exact lattice co-linear reduction under anti-alias/double-resolution native Chrome, shared-edge constraints. If no candidate passes both full source-mask and Chrome, retain current source contours and formally record no improvement; do not relax thresholds, add face parts, infer RGB or silently promote HOLD research.
