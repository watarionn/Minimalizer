# BrowserFallback v32: Source-Owned Contiguous Color Planes
Date: 2026-10-09
Status: **RESEARCH DIAGNOSTIC COMPLETE / BROWSER & SEMANTIC VISUAL-PROMOTION HOLD**
Branch: `research/browser-contiguous-planes-v32-20261009` based on held v31 PR #303.
Public Facet v15 / Local Worker: unchanged.

## Objective

V31's 8×8 independent tile medoids restored source garment color but introduced conspicuous checkerboard artifacts and altered 14 pixels of Kyoko's characteristic green tie. V32 fixes those blockers and tests connected irregular **source-color-following SLIC planes**, while keeping every unverified part/pose distinction UNBOUND. This is a Python offline diagnostic, NOT a production browser engine or SVG/Bezier renderer.

## Data and method

Three frozen original 340×340 Golden sources (Kyoko, Noel, Ririka) are verified with SHA-256. Model masks: cached original Kyoko AnimeSeg v3 and actual v30 Noel/Ririka CPU inference, each with exact mask SHA. Frozen original Facet PNGs are retrieved byte-for-byte from the canonical v27 stage archive. The model-class clothing mask is observational evidence, **not a source-annotated ground truth garment or arm mask**.

Use scikit-image SLIC masked by original source-opaque AnimeSeg clothing class. Build 4-connected subcomponents per irregular region, sample one medoid RGB from *actual source pixels in that component*, reject any component whose quantization worsens its source L1 error, and leave the original Facet unchanged outside the eligible source-supported mask. Preserve baseline alpha throughout. No generative pixels or RGB colors. Test coarse (260 requested SLIC areas) and fine (540 requested) variants. Skip tiny regions and preserve rejected original regions.

**Critical correction during v32:** first trial changed Kyoko's green tie color mass (1994 -> 1980 pixels) and significantly altered dark clothing color. That trial is **rejected/not shipped**. Final variant excludes every original Kyoko tie-color pixel RGB (149,211,27), exact Kyoko left-arm/sleeve ROI x90:112/y263:290, Noel staff RGB (68,37,36), and forbids assigning those protected colors to another plane. The final in-render RGB mass and protected pixels exactly match Facet. Kyoko 608 candidate garment pixels are excluded by these protections. This does NOT prove every arm region is semantically identified.

## Real 3-character metrics (after protection)

| Case | Variant | Accepted regions | Changed diagnostic pixels | Original-RGB MAE Facet | New MAE | Protected changes |
|---|---|---:|---:|---:|---:|---:|
| Kyoko | coarse | 132 | 14656 | 49.08868 | 21.89980 | 0 |
| Kyoko | fine | 313 | 14840 | 49.08868 | 18.50641 | 0 |
| Noel | coarse | 159 | 19388 | 32.97548 | 18.57842 | 0 |
| Noel | fine | 379 | 20502 | 32.97548 | 15.11356 | 0 |
| Ririka | coarse | 208 | 42657 | 19.10414 | 8.67298 | 0 |
| Ririka | fine | 453 | 43464 | 19.10414 | 7.18440 | 0 |

These per-model-garment RGB MAEs **exclude the protected pixels**; they are not global visual quality, model semantic accuracy or pose recall. All six outputs have **0** changes outside eligible original-source/AnimeSeg garment pixels and **0** alpha changes.

Visual comparison: v32 replaces the artificial v31 square-tile checker pattern with source-edge-following contiguous, faceted irregular color planes. Hair/face are mostly unchanged and imperfect, as expected. Noel's dark armor/gap and Ririka's sleeve still have class-boundary confusion, a true left/right arm decomposition is not proven, and small patches do not yet have shared-chain Bezier/vector contour quality. Fine variant has up to 2883 diagnostic contour vertices, so path simplification is required before release.

## Verification and explicit rollback decisions

- 6 synthetic v32 tests: connected source medoid palette, 4-neighbor topology, frozen alpha/mask/silhouette, no-gain/empty-mask fail closed, protected RGB no unintended assignment, no app route.
- Exact independently repeated local analysis: **9/9 PNG/JSON/CSV artifacts have byte-identical SHA-256** (six modes, montage, metrics json/csv). Initial unprotected trial rejected; reference final is `v32_metrics.json` with protected fields.
- All visible proposed PNGs are *offline diagnostics only*. Public v15, BrowserFallback app.js routes, production UI and Local Worker unchanged.
- No new model inference or RAM threshold reinstated. Existing v29 minimum-free-RAM policy remains revoked per user instruction; only simple CPU image segmentation in this step.

## Hold gate / next

**v32 source-plane research PASS; production promotion HOLD.** Need actual source-verified arm/garment/accessory masks, and clean shared-edge vector shapes without checker/seam artifacts; test all 3 Golden originals with user visible comparison and acceptable runtime. Do not merge this stacked research PR or claim the Python SLIC approach already runs in browser. For next stage, test topology-aware contiguous Bezier boundary simplification, mask-provenance uncertainty and browser implementability while retaining source RGB color samples, signature colors, silhouette and zero fabricated anatomy/facial internals.

Canonical Drive: `chatGPT及びCodex用/Minimalizer/ConnectedSourcePlanesV32_20261009` with full 3x5 comparison, six exact outputs, source/facet/mask provenance, replay SHA, source code, tests and handoff.
