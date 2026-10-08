# SA10.34 Phase 8: source-exact geometry & budget-aware contour research gate

Date: 2026-10-08 JST · Repository: `watarionn/Minimalizer` · PR #223 (DRAFT, NOT MERGED)

## Disposition

**Phase 8 research/prototype/evidence complete. Production integration/promotion is NO-GO.**
This phase explicitly refuses to trade the core "few geometric primitives with clean boundaries" goal for a mere source-pixel-exact tracing result.

Two independent signed real-image cases were evaluated from unchanged Stage04/11/12 artifacts in an isolated temp worktree. Both previous Stage12 previews are preserved and neither were redeployed.

## Critical technical breakthrough

The image mismatch was caused by (a) the `group_min_area=2` dropping legitimate 1-pixel/low-area source owner islands, and (b) Phase12 serializing simplified `parameters.rings` while actual `source_mask_replay` displayed the group source-derived mask, so vector export and preview were not guaranteed to match.

**All 11 existing primitives can preserve their current owner, material/color, primitive identity and draw order while using actual Stage04 owner contours (including `unknown` without relabeling it).** Source contours extracted with `cv2.RETR_TREE + CHAIN_APPROX_SIMPLE` and rasterized with the official `rasterize_primitive_candidate` are **pixel exact** for the source masks, even for single-pixel islands and nested holes. Unlike the Phase6 diagnostic, this is the canonical renderer.

The research prototype uses deterministic *geometry only*. It does not paste source image pixels, paint masked overlays, invent image content, add face details, or alter the production renderer.

### Exact-source candidate

| Real case | Old Stage12 vector ring vertices | Exact source ring vertices | Primitive count | Full-scene silhouette IoU | Raw global topology | Official vector/raster parity | Budget |
|---|---:|---:|---:|---:|---|---|---|
| GC001 | 1,887 | 4,265 | 11 → 11 | 1.000000 | (1,9) → (1,9), PASS | PASS | **FAIL** |
| Juufuutei-Raden | 1,412 | 2,815 | 11 → 11 | 1.000000 | (1,3) → (1,3), PASS | PASS | **FAIL** |

Source raw topologies and full-scene anatomy gates PASS without any post-normalization relaxation. The existing old vector budgets remain the hard limits. Total component vertices independently exceed original limits: GC001 1,697 → 3,803, Raden 1,306 → 2,599. Source-perfect polygons add unacceptable jagged/raster-like complexity and do **not** satisfy Minimalizer's geometrically simplified output objective.

There are 90 degenerate (one/two-point) filled contours in GC001 and 7 in Raden, valid under OpenCV filled contour semantics but not automatically valid as browser SVG filled paths. **Do not mistake OpenCV polygon parity for SVG/browser parity.**

### Adaptive topology-preserving simplifier

A separate greedy simplifier tests `approxPolyDP` candidates on one existing ring at a time and accepts a modification **only** when:
- The same owner/material/primitive count and structural support role survive.
- Raw owner topology is unchanged.
- Every <=8 px source-owner island and enclosed hole footprint is protected.
- Owner IoU stays >=0.995.
- The **unchanged** whole-scene SA10.18 hard gate passes, and full silhouette IoU never falls below the historical real-image baseline.
- The actual official renderer exactly matches the stored modified polygon coordinates.

| Real case | Exact ring vertices → adaptive | Saved vertices | Adaptive silhouette IoU | Historical Stage12 IoU | Adaptive raw topology | Original budget |
|---|---:|---:|---:|---:|---|---|
| GC001 | 4,265 → 3,604 | 661 (50 accepted ring edits) | 0.9982763313 | 0.9965670069 | PASS (1,9) | **FAIL** (1,887) |
| Raden | 2,815 → 2,370 | 445 (27 edits) | 0.9995681651 | 0.9995680594 | PASS (1,3) | **FAIL** (1,412) |

**Primary vertex hot spots:** GC001 hair (+556 vs prior ring budget) and unbound/unknown (+535), with the latter deliberately remaining unbound. Raden hair (+260) and major clothing (+170) lead the overage. This directs future work toward primitive-level geometric abstraction, not simply chasing raster IoU.

## Verified provenance and regression

- Input image SHA256 matches Stage04/11/12 manifests.
- Each Stage04 part-mask file checksum matches its Stage04 stage manifest.
- Phase11 composition SHA256 matches Stage11 stage manifest.
- Saved Phase12 candidate checksum matches the Stage12 stage manifest.
- Primitive identities, order, owner, material and support-only roles remain unchanged.
- Output research render uses the existing `_render` plus original deterministic face-color guard; zero changes outside authorized face pixels.
- No production source, Phase04/11, Stage12 or deployed BrowserFallback paths changed.
- Local extended focused regression **56 tests passed**; GitHub research CI is required to pass before this phase is closed. Research evidence is stored with all failing limits intact.

## Evidence / visual review

- [GC001 exact geometry](evidence/sa1034_gc001_exact_replay_20261008.json)
- [Raden exact geometry](evidence/sa1034_raden_exact_replay_20261008.json)
- [GC001 adaptive](evidence/sa1034_gc001_adaptive_replay_20261008.json)
- [Raden adaptive](evidence/sa1034_raden_adaptive_replay_20261008.json)
- [GC001 per-owner budget gap](evidence/sa1034_gc001_vertex_budget_gap_20261008.json)
- [Raden per-owner budget gap](evidence/sa1034_raden_vertex_budget_gap_20261008.json)

Preview images, candidate full polygon JSON, metrics and before/after comparisons saved under **Google Drive `chatGPT及びCodex用/Minimalizer/SA1034_Phase8_ExactReplay_20261008/`** (GC001 and Raden subfolders). Neither version is user-approved for production. Visual gate is **PENDING**.

## Next phase / release blocking

1. Replace high-cardinality pixel-following polygon segments with a genuine topology-aware **low-primitive, low-vertex geometric/Bézier representation**. Preserve each source island/hole, face and both arms without inventing geometry or reassigning `unknown`. Use source evidence as constraint, not as an excuse to clone source pixel noise.
2. Solve one/two-point contours with **browser-valid SVG filled geometry** and test at real browser pixel resolution. Do not silently hide dots in SVG or add separate face primitives. Keep primitive count.
3. Repeat real GC001 and Raden tests with **both vertex counts <= the previous Stage12 limits**, *the original* full-scene hard gates, official renderer/export parity and independent human visual signoff.
4. Only after those pass run broader corpus/full CI and consider merge/deploy. **This PR remains draft and unmerged; no production promotion.**

**The result is a genuine structural breakthrough but not yet a Minimalizer-quality image.**
