# Rinka Reference Phase 10: AI-free Subject Segmentation

Phase 10 starts by separating an opaque character thumbnail into background and subject before geometric simplification. It uses only deterministic OpenCV / NumPy image processing. No model, neural network, API, or learned weights are involved.

## Checkpoint 1

`minimalize_engine/subject_segmentation.py` samples border colors, clusters dominant backdrop colors, compares pixels in Lab space, and treats only backdrop-colored components connected to the image edge as background. This edge-connectivity rule is important: an outfit region may legitimately reuse the same red as a red backdrop, and an enclosed matching-color region must remain part of the subject.

The segmentation path is confidence-gated by aspect ratio, border dominance, subject area, center occupancy, border leakage, and a combined confidence score. Existing useful alpha subjects are not re-segmented.

Rinka Reference still uses the Phase 8 failure gate before the new segmentation may affect rendering. On the fixed 16-image corpus the new path therefore changes only the known Omaru Polka opaque-thumbnail failure class. Other inputs retain their established rendering path.

For the fixed Omaru sample, the accepted segmentation reports background RGB approximately `(207, 40, 48)`, foreground area about `0.630`, center fill about `0.935`, border leak about `0.295`, and confidence about `0.610`.

## Trial-and-error findings

Several variants were rendered against the real Omaru regression image. A broad border-prototype set incorrectly accepted a white edge cluster as backdrop, so Phase 10 now rejects prototype colors that are too far from the dominant border color. A robust trimmed subject bounding-box experiment was also rejected because it damaged the recognizable pose and part layout.

Feeding the new mask directly into the Phase 9 semantic-macro rescue also produced a less coherent result and was rejected. The accepted checkpoint instead routes the failure-gated image through the ordinary alpha-subject character analysis, then applies Rinka target cleanup. The generic `subject_base` underlay is removed only for an activated Phase 10 segmentation because it otherwise becomes a giant poster slab after the backdrop has already been separated.

This reduces the largest final filled shape on Omaru from the failed Phase 10 prototype's roughly `50.8%` of canvas to about `15.7%`, while retaining the baton, main body masses, blue lower accent, and source-facing character silhouette more coherently than that prototype.

## Compatibility and safety

Historical Phase 8/9 behavior remains callable for regression tests through `enable_ai_free_subject_segmentation=False`. Phase 10 is opt-in only inside the existing `minimalize_rinka_reference()` mode; stable Minimalizer mode and Color Strip are unchanged.

Targeted Phase 8/9/10, target-style, and Web API tests pass `62/62`. Repository-wide testing reaches `234` passing tests; the only two product-code-independent failures are the pre-existing tests that require the absent `tests/assets/false_face_phase85.png` fixture. The remaining version-expectation tests were updated from Phase 9 to Phase 10.

Checkpoint 1 is a segmentation foundation, not the end of Phase 10. The next quality step should simplify the already-separated subject while preserving the raised-arm gesture and major character color blocks, rather than returning to global backdrop/subject competition.

## Checkpoint 2: deterministic subject color planes

Checkpoint 2 replaces the segmented case's noisy internal Character Structure fills with a deterministic color-plane scaffold. The scaffold uses only NumPy/OpenCV: subject pixels are reduced to a small deterministic palette, nearby same-color islands are bridged inside the accepted subject mask, and each retained component is simplified to a straight-edged polygon. No random seed, learned model, or external inference is used.

The bridge is deliberately small and clipped to the Phase 10 subject mask. At the level-4 / 220px corpus checkpoint it uses a 3x3 kernel. This raised Omaru plane coverage from the first unbridged prototype's roughly 51% to about **77.0%**, while polygon overdraw outside the segmented subject remains about **1.35%**. The final rendered foreground reaches about **75.6% IoU** with the accepted subject mask, versus about **65.1%** for Checkpoint 1, while final vertex count drops from **187 to 137**.

The scaffold keeps six representative subject colors. Colors that collapse too close to the already-separated backdrop are shifted away from the backdrop before rendering; Omaru currently requires one such adjustment. A conservative side-gesture detector protects one dark raised-right-arm plane. Existing Character Structure is not discarded entirely: hand and prop/weapon carriers are copied over the scaffold, retaining the left holding hand plus sword/baton blade and guard cues.

Real-image trials rejected several alternatives before this checkpoint: a full silhouette underlay restored coverage but became an overly dominant dark slab; local-color gap carriers created broad cream blocks; 5x5 and 7x7 per-color closing over-smoothed the figure into tall merged masses; and 0.05 contour epsilon removed too much pose structure. The accepted checkpoint uses small 3x3 bridging at 220px and a polygon epsilon ratio of 0.036. A 0.036 sweep retained the same gesture and slightly improved final silhouette IoU while reducing scaffold vertices from 148 at 0.030 to 126.

On the fixed 16-image corpus the existing Phase 8 giant-slab gate still isolates the new scaffold to Omaru only. Phase 10 segmentation/scaffold activation is **1/16**. The unaffected 15 images retain worst pre-target identity/silhouette deltas of about **-0.0449 / -0.0010**. Corpus mean shape reduction is about **36.71%** and mean vertex reduction about **31.38%**. The checkpoint favors the documented visual target over maximizing reduction percentage: Omaru gains stronger silhouette/pose continuity while keeping the raised arm, diagonal prop, large light head/hair planes, torso contrast, and blue lower accents readable.

Checkpoint 2 is the current Phase 10 working candidate. Further changes should improve macro-plane hierarchy or reduce obviously redundant internal fragments without weakening the measured subject coverage, right-arm gesture, prop retention, or the unaffected-corpus safety line.
Local validation after Checkpoint 2: the dedicated Phase 10 tests pass **4/4**; the combined Phase 8/9/10 + target-style + Web API suite passes **63/63**; and the repository-wide suite passes **239 tests with 2 explicitly deselected**. A run without deselection reports only the same two pre-existing `tests/assets/false_face_phase85.png` missing-fixture failures. `git diff --check` and Python compilation are part of the local closure check.
A late palette-budget sweep also tested four and five subject colors. Four colors looked numerically attractive at the 220px checkpoint (17 final shapes / 91 vertices and about 0.794 foreground-mask IoU), but at the original 340px scale it collapsed too much of the head/torso into one large light slab and weakened internal pose separation. Five colors was intermediate but did not improve the six-color composition. Six colors therefore remains the accepted budget; do not optimize only the 220px scalar metrics at the expense of the original-scale visual review.

## Checkpoint 3: fragment consolidation and broader opaque-thumbnail activation

Checkpoint 3 generalizes the AI-free opaque-thumbnail path to the four corpus thumbnails supplied for visual review: Oozora Subaru, Omaru Polka, Shirogane Noel, and Juufuutei Raden. Activation is still gated. Polka uses the original giant-slab failure gate; Subaru and Noel use a high-confidence structural gate; Raden uses a dense-subject gate. The other 12 fixed-corpus images remain outside Phase 10 activation.

`minimalize_engine/subject_plane_cleanup.py` adds deterministic fragment absorption before polygon extraction. Tiny neutral islands are reassigned to a nearby dominant color when safe, while high-saturation accents and long gesture-like fragments are protected. Polygon simplification is now adaptive: simplified contours must pass a local raster-IoU guard, and unsafe approximations fall back toward the original contour rather than becoming oversized triangles. A macro-anchor ranking then limits the scaffold to the most compositionally important subject planes.

At level 4 / analysis max side 220, the four activated thumbnails use 17 subject planes each. Subject-plane coverage is approximately Subaru 0.761, Polka 0.691, Noel 0.659, Raden 0.925. Outside-subject overdraw is approximately 0.011, 0.003, 0.025, and 0.024 respectively. The fixed 16-image evaluator reports activation 4/16, 68 total subject planes, 738 scaffold vertices, five gesture planes, mean subject-plane coverage about 0.759, and maximum outside-subject overdraw about 0.0246. The unaffected 12 images keep worst identity/silhouette deltas around -0.0185 / -0.0010.

Visual iteration rejected a blanket confidence-only activation because it produced unsafe Noel geometry, and rejected aggressive simplification that created giant triangular slabs. The accepted activation routes combine segmentation evidence with baseline geometry and keep the raster-fidelity guard. Current local validation passes the dedicated Phase 10 suite 6/6, the combined Phase 8/9/10 + target-style + Web API suite 65/65, and the repository-wide suite 241 passed / 2 deselected for the two unchanged missing-fixture tests.
