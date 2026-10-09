# MinimalizerPublic R4: Whole-scene Chrome vs resvg independent Golden matrix

2026-10-10 | **R4 research complete / native agreement PASS / DPR2 full-scene mismatch HOLD / no release**

## Frozen input and scope
- GitHub branch `research/public-r4-independent-resvg-golden-matrix-20261010`, stacked on Draft R3 PR #356 -> R2 #354 -> R1 #353; v34 itself remains separate Draft PR #308 (not main/deployed).
- SHA-verified immutable `chatGPT及びCodex用/Minimalizer/SvgLocalRollbackV34_20261009` and v32 `ConnectedSourcePlanesV32_20261009`, Kyoko/Noel/Ririka, 340x340. Original SVGs contain a **frozen embedded PNG Facet plus source-RGB path layer**; do not call them fully vectorized or semantics-certified.
- The browser's opt-in installed `public-resvg-research.mjs` has a bounded 8-shape observer; this R4 experiment runs **all original scene content** with the genuine pinned `@resvg/resvg-wasm@2.6.2`, no CDN and no production integration.
- Research files: `scripts/public_r4_resvg_full_scene.mjs`, `scripts/verify_public_r4_cross_engine.py`, `scripts/verify_public_r4_component_split.py`, and `tests/test_public_r4_cross_engine_gate.py`.

## Cross-renderer comparison: whole hybrid scene

Test machine real Chrome **154.0.8037.98**; resvg-WASM **2.6.2**. Both render independently from the *same* archived immutable SVG source, with full RGBA byte comparisons. Native view: 340x340. High-DPR experiment: both render 680x680. Frozen v32/archived v34 are independent native Chrome references.

| Golden | frozen v32 vs native Chrome | Chrome vs resvg, 340² | Chrome vs resvg, 680² | Release |
|---|---:|---:|---:|---|
| Kyoko | 0 px | **0 px** | **35,588 px** | HOLD |
| Noel | 0 px | **0 px** | **30,690 px** | HOLD |
| Ririka | 0 px | **0 px** | **20,018 px** | HOLD |

**The original v34 340² visual and PNG alpha channels are identical across Chrome, resvg and frozen v32. But whole-scene 680² resampling is NOT identical.** Recording this as PASS would be a false release statement.

## Source-grounded component attribution

The derived diagnostic fragments preserve source-signed content; they only isolate either the **existing frozen PNG image tag** or **existing source-owner RGB path elements**. Neither fragment is proposed product output. Both native and DPR2 full-pixel comparisons run in two rendering engines.

| Golden | paths-only Chrome vs resvg 340 / 680 | Facet-only 340 | Facet-only 680 | Facet-only 680 max channel delta |
|---|---:|---:|---:|---:|
| Kyoko | **0 / 0** | 0 | **40,837 px** | 14 |
| Noel | **0 / 0** | 0 | **37,449 px** | 10 |
| Ririka | **0 / 0** | 0 | **25,862 px** | 10 |

All facet-only DPR2 alpha differences = 0; the pixel differences are RGB upsampling/interpolation behavior of the frozen raster layer, not differences in the original vector paths. This demonstrates **component-level evidence**, not semantic part correctness: neither tie/arm/staff nor neck/lower-body source-owned regions have signed per-part boundaries.

The R4 680² renderer disagreement **does not justify regenerating the embedded Facet or altering its colors**. No synthetic details, img2img, interpolation replacement, new facial features or path rewriting is allowed.

## Safety and reproducibility

- Full scene and component split source-level negative test: an intentionally added 340x340 opaque black rectangle is detected by both Chrome and independent resvg. The negative-only fixture is allowed explicitly by the diagnostic CLI; all arbitrary added nodes remain rejected.
- Source manifests verified **before** creating any output; only fresh research directories accepted; original source images stay unchanged.
- Per-Golden/native and DPR2 images saved: frozen v32, Chrome, resvg and enhanced **difference comparison gallery** for review. Those galleries are **diagnostics**, not signed Golden acceptance.
- All Python integration and Public/Local isolation tests through R4: **54 passed**; syntactic check PASS.
- Two independent real Chrome+resvg full-scene runs and component-isolation runs: **47/47 output files byte-exact** (22 full-scene and 25 component layer).
- Existing R1–R3 previous findings unchanged: no accepted vertex savings, no product quality improvement, no Local Minimalizer edits.
- Pinned vendor notice has MPL-2.0; packaging/legal review and redistributed license compatibility must still be signed before full production admission.

## Disposition and next work

**R4 diagnostic implementation COMPLETE, cross-engine DPR2 gate HOLD.** The vertex/path raster is exact even at DPR2. The embedded raster PNG interpolation differs. Do not loosen required whole-scene equivalence, and do not claim true 2x cross-renderer product release approval.

R5 may proceed **only as an off-by-default Public-only shadow instrumentation / browser route canary preparation**, never as a changed production image renderer. Required next checks: output byte parity across flag OFF/ON/error, offline/missing-WASM fallbacks, actual browser processing replay, rollback switch, Safari/iPhone separate device signoff, stage-8 original contours and user human Golden. Every R5 result must preserve HOLD until those additional gates are satisfied.

Authoritative evidence is saved in Google Drive `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R4_20261010` with two independent renderer outputs and images. GitHub PR remains Draft, not merged or deployed.
