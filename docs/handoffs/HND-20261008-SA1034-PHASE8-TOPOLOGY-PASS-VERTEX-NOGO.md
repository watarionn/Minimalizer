# HND-20261008 SA10.34 Phase8 → Phase9

**State:** Phase8 research execution/verification complete. **NOT production complete.** Source-exact geometry and adaptive topology-safe simplification both reach *real-image whole-scene topology PASS*, but exceed the existing vector vertex budgets; browser SVG validity and human visual gate remain FAIL/UNVERIFIED. Research PR #223 MUST stay DRAFT / unmerged / undeployed.

Repo: `watarionn/Minimalizer`, working branch `research/sa1032-svg-contour-proposals`.
Full report `docs/zerobase/SA10_34_PHASE8_EXACT_AND_ADAPTIVE_NOGO_20261008.md`.

## Verified 2-image baseline

- GC001 source union (1 component,9 holes), selected original (2,21), IoU .9965670069. Raden source (1,3), selected original (1,8), IoU .9995680594.
- Exact source contours into the same existing 11 polygons: source/topology/official OpenCV vector→render parity 100%; **GC001 4265 vs prior ring budget 1887**, Raden **2815 vs 1412**. Lots of 1–2 point contours cannot be assumed to work in filled SVG.
- Adaptive `approxPolyDP` greedy edits preserving every low-area source island/hole and unchanged raw global hard gates: **GC001 3604 rings (50 edits), IoU .9982763313**, **Raden 2370 (27 edits), IoU .9995681651**. Both exceed original vector vertex limits.
- Major budget blockers: GC001 hair +556, unbound source `unknown` +535; Raden hair +260 and major_clothing +170. Do not relabel unknown to hair, or paint inferred geometry.
- Extended regression 56 tests PASS locally; source/palette/owner/Stage04 masks SHA, Phase11 composition and Phase12 scene are verified and unchanged.
- Research candidates + version comparisons preserved under **Drive `chatGPT及びCodex用/Minimalizer/SA1034_Phase8_ExactReplay_20261008`**.
- Evidence JSON under `docs/zerobase/evidence/sa1034_*.json`.

## Code introduced

`minimalizer_zerobase/reviewed_sa10/source_exact_vector_replay.py`: exact contour ring generator with Stage04 owner provenance, official raster parity, original vertex budgets, strict browser SVG gate.
`minimalizer_zerobase/reviewed_sa10/topology_constrained_vector_simplifier.py`: greedy per-ring polygon simplification, preserve tiny source islands/holes and raw owner/global topology, retain historical global IoU.
`tools/run_sa1034_phase8_exact_replay.py`: isolated research candidate + deterministic preview; checksum gates.
`tools/run_sa1034_phase8_adaptive.py`: baseline-anchored adaptive research candidate + preview.
`tests/zerobase/test_sa1034_*.py`: micro-island/hole, ownership immutability and non-promotion tests.

## Next engineering direction (Phase9 research)

1. **Do not retry simply increasing vertex limits or dropping micro components.** Need a representation that is visibly geometric, vector-valid and preserves constraints.
2. Research low-complexity piecewise Bézier/polygon geometry for large contours, while preserving tiny islands/holes using an explicitly browser-valid technique within the **same existing owner primitive**. Keep original total ring/component budgets hard, no hidden extra shapes, no img2img/generative fill/painting source pixels.
3. Implement browser raster parity as independent gate distinct from OpenCV `rasterize_primitive_candidate`. A 1-point OpenCV filled contour is NOT automatically a valid filled SVG polygon.
4. Test on GC001 and Raden with original Phase12 selection and source SHA before expanded corpus. Check raw full-scene union topology (no canonical threshold suppression), same color/owner/primitive count, silhouette, arms/face, SVG-browser render, visual review, original vertex cap. No merging until every gate passes.
5. User review and production deploy are conditional. Publish changed PR, CI+test proofs, then merge and verify only after user-approved candidate quality.

## Explicit developer caution

Early Phase6 numbers were noncanonical (custom `fillPoly`), corrected in Phase7. Never conflate source mask, `source_mask_replay` actual preview mask, serialized contour SVG/browser paths, and official OpenCV polygon raster. Any mismatch is its own blocker. Never claim 100% similarity proves *minimalization style*.

Avoid user's local working tree; use GitHub direct and isolated temporary worktree. RDC is only necessary for real case source images and source-mounted Drive binary preview sync.
