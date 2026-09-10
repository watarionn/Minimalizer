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
