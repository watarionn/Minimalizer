# Rinka Reference Phase 11: Geometric Poster Abstraction

Status: **Checkpoint 2 implemented on Draft branch**

Branch: `feature/rinka-phase11-priority1-faceless-hands-20260910`

## Goal

Move the Rinka Reference output toward the reviewed geometric examples: very large color masses, faceless heads, fingerless hands, and deliberate poster-like polygons. The aim is not to trace more accurately. The aim is to preserve identity using fewer, stronger shapes.

## Priority order

1. Faceless output, fingerless hands, stronger small-detail deletion.
2. Hair as larger planes and clothing as large color blocks.
3. Geometric backgrounds, presets, and Web UI controls.

## Checkpoint 1 implementation

- `RINKA_REFERENCE_VERSION` advances to `phase11`.
- Facial eyes/mouth/brows/nose and other explicit facial micro-features are removable regardless of upstream importance. The largest safe face carrier remains as the skin/head plane.
- Recognized hands are collapsed to one `target_hand_symbol` per known side. The symbol is a six-vertex beveled polygon derived from the original hand orientation and filled area, so an open hand cannot produce a partial three-finger silhouette.
- Same-side hand fragments are designed to merge into one symbol before gesture-arm simplification.
- Arm simplification continues to use the resulting hand symbol as a gesture anchor.
- A conservative post-pass removes tiny lace/ruffle/stitch/seam/nail/finger fragments and low-value target fragments while keeping hair and props protected.
- Evaluation telemetry now records hand-symbol counts, hand vertices removed, and micro-detail removals.

## Local validation

Fixed 16-image corpus, level 4, `analysis_max_side=220`:

- baseline Phase 10 mean shape reduction: **34.64%**;
- Checkpoint 1 mean shape reduction: **35.56%**;
- baseline mean vertex reduction: **25.06%**;
- Checkpoint 1 mean vertex reduction: **25.76%**;
- recognized hand inputs: **15**; generated hand symbols: **15**;
- hand-symbol vertex removals: **3**;
- additional target micro-details removed: **4**;
- face fragments removed by the complete target pass: **9**;
- Night River general-scene output remains unchanged;
- target PNG change footprint versus the Phase 10 baseline averages about **0.103%** of pixels, with a maximum of about **0.465%**, showing that the new behavior is localized rather than a global composition rewrite.

Tests: **245 passed / 2 pre-existing missing-fixture tests deselected**. The deselected tests require `tests/assets/false_face_phase85.png`, which is absent from the repository baseline. Targeted Phase 11/target-style/Phase 10 regression tests: **43 passed**.

## Checkpoint 2 implementation

Priority 2 is now implemented. Hair is treated as a small set of filled poster planes: local bang/strand lines shorter than 22% of the short canvas side are removed when a nearby filled hair mass already carries the identity, while long flow cues are retained. Filled hair polygons may be simplified only when local raster IoU stays at least 0.93, area drift stays within 8%, and centroid movement stays within 1.5% of the short side.

Outfit processing now groups nearby same-family garment pieces into shared dominant color blocks. Upper garments, lower garments, footwear, and generic segmented clothing remain separate families. Only near colors (distance <=32) and nearby pieces are flattened; signature accent colors remain distinct. A second geometric merge is allowed only for a small same-color piece whose union-to-hull IoU is at least 0.80, while the Phase 5 one-detail-per-base invariant remains protected.

Fixed 16-image corpus, level 4, `analysis_max_side=220`:

- Checkpoint 1 mean shape reduction: **35.56%**; Checkpoint 2: **40.32%**;
- Checkpoint 1 mean vertex reduction: **25.76%**; Checkpoint 2: **26.99%**;
- hair inputs: **52**; local line cues removed: **24**; long flow cues preserved: **1**;
- simplified filled hair planes: **6**, removing **9** vertices;
- outfit block candidates: **45**; color blocks: **44 -> 36**; recolored shapes: **8**;
- no additional outfit hull merge activates on the fixed corpus, although the guarded merge path is covered by a focused test;
- target-PNG change footprint versus Checkpoint 1 averages about **0.490%**, maximum about **2.242%** on Mizumiya;
- Night River remains unchanged.

Validation: **73 targeted tests passed**; full local suite **249 passed / 2 pre-existing missing-fixture tests deselected**; `compileall` and `git diff --check` pass. No GitHub Actions run is required for this checkpoint.

## Next checkpoint

Priority 3 is geometric background compression plus preset/Web UI exposure. Keep the current subject abstraction intact and avoid broad background deletion that can erase scene-defining cues.
