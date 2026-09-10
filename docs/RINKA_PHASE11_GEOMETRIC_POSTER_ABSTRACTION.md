# Rinka Reference Phase 11: Geometric Poster Abstraction

Status: **Checkpoint 3 local closure complete; Draft PR preparation**

Branch: `feature/rinka-phase11-priority3-background-presets-ui-20260910`

Checkpoint 2 was merged to `main` in PR #22 at `c5691318df69e1030ca89dd6a404e58294ba24a1`.

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

## Checkpoint 3 implementation

Priority 3 turns the accepted subject abstraction into a poster composition without rewriting the subject. Two explicit presets are now defined:

- `geometric_poster` (default): Phase 11 faceless/fingerless subject abstraction plus a flat poster background and three large five-vertex angular panels.
- `faceless_subject`: the same Phase 11 subject abstraction without synthetic background panels.

Geometric background activation requires subject evidence. General scenes without subject evidence remain on their source background path. Transparent or near-neutral character inputs derive a deterministic contrasting base color from a dominant hair/garment anchor; already useful source background colors remain available as the base. Panel orientation mirrors with subject placement so the layout is not tied to one image. Up to two large, high-importance skyline/water/horizon/structure cues may survive as scene context.

A first broad implementation was rejected during local evaluation because `_target_mass_kind()` intentionally classifies generic `midground` shapes as background-like for older cleanup logic; using that classification as a deletion rule caused identity-supporting midground structure to disappear. Checkpoint 3 therefore has a stricter background replacement gate: only explicit background layers/tags or accepted `opaque_background` evidence may be replaced. Generic midground structure is retained.

Fixed 16-image corpus, level 4, `analysis_max_side=220`:

- geometric background enabled: **15/16** images; Night River remains unchanged;
- generated poster panels: **45**; surviving poster panels after the final shape cap: **45**;
- definite background shapes additionally replaced by the new stage: **0** on this corpus;
- strong scene cues preserved by the stage: **11**;
- non-poster subject shape signatures are identical between `geometric_poster` and `faceless_subject` on **16/16** images;
- geometric-poster mean shape reduction: about **31.10%**;
- geometric-poster mean vertex reduction: about **21.59%**.

The lower reduction percentages are intentional accounting, not a regression in subject abstraction: each character output now spends three extra shapes / fifteen vertices on the poster background.

Web candidate v0.9.0 exposes the two presets only when Rinka Reference is selected. Standard remains the default mode and keeps its existing controls. The API accepts `rinka_preset=geometric_poster|faceless_subject`, reports the default/available presets from `/api/info`, and returns `X-Minimalizer-Rinka-Preset`. Rinka still uses the frozen level-4 subject profile and rejects Standard detail overrides.

## Checkpoint 3 closure validation

Local closure is complete. Repository-wide pytest passes **259 tests / 2 pre-existing missing-fixture tests deselected**, with the same missing `tests/assets/false_face_phase85.png` fixture as earlier phases. `compileall`, JavaScript syntax validation, and `git diff --check` pass. The final 16-image evaluator reproduces **31.10%** mean shape reduction and **21.59%** mean vertex reduction for `geometric_poster`, with Phase 10 activation still **4/16**, background generation **15/16**, and **45/45** generated panels surviving. A direct preset comparison confirms identical non-poster subject-shape signatures on **16/16** images.

A real local Uvicorn smoke confirms HTTP 200 for Standard, Rinka `geometric_poster`, Rinka `faceless_subject`, and Color Strip. `/api/info` reports Web **0.9.0**, Rinka Phase **11**, default preset `geometric_poster`, and both available presets. The geometric-poster contact sheet was visually reviewed across all 16 corpus images; no new background-induced subject regression was found, and Night River stays on its ordinary scene background path.

## Next checkpoint

Open a Draft PR with `[skip ci]` validation provenance. Do not change the subject abstraction or broaden background deletion merely to improve reduction percentages. Production remains Web v0.8.0 until a later explicitly approved deployment verifies v0.9.0 on Railway.
