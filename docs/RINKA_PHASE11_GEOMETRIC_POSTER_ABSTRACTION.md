# Rinka Reference Phase 11: Geometric Poster Abstraction

Status: **Checkpoint 1 implemented on Draft branch**

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

## Next checkpoint

Priority 2 should consolidate hair into fewer major flow/color planes and outfit structure into fewer large color blocks. It must preserve pose, major silhouette, and signature color placement, and should be evaluated against the same fixed corpus before any background/UI work begins.
