# Rinka Reference Phase 9: Semantic Primitive Optimization

Phase 9 improves the Phase 8 semantic macro rescue without broadening its activation gate. The goal is to make rescued character images read as intentionally designed geometric posters rather than contour fragments.

## Scope

Phase 9 is limited to the existing evidence-gated Rinka Reference rescue path. Standard mode, Color Strip, and ordinary non-rescue Rinka outputs keep their established behavior.

The fixed Omaru Polka regression image is used as evidence for this failure class, but no filename or image-specific special case exists in the engine. Rescue remains controlled by the Phase 8 geometric failure gate.

## Semantic Shape Tree

`minimalize_engine/character/semantic_shape_tree.py` converts Character Structure into a semantic hierarchy such as `subject -> head -> face / hair / accessory` and `subject -> torso -> outfit`, with arms, legs, and props as separate branches.

Each node has a primitive budget, merge group, and protection state. Face, prop, and distinctive accessory nodes are protected, and semantic boundaries prevent unrelated parts from being treated as one mergeable mass.
## Localized Primitive Optimizer

`minimalize_engine/character/primitive_fit.py` generates several simple-shape candidates inside each semantic part and scores them using mask IoU, coverage, precision, centroid alignment, and complexity.

The current candidate families are polygon, trapezoid, rotated rectangle, triangle, and ellipse. Part-aware priors slightly favor an ellipse for the face and a trapezoid for the outfit while retaining a fidelity fallback when the preferred primitive is substantially worse.

The outfit trapezoid is also subject to a visual-area safety rule. If the selected trapezoid would exceed the allowed macro area, it is scaled around its center and re-scored rather than replaced by a jagged fallback polygon. This preserves readable geometry while preventing a return of the giant-slab failure.

## Distinctive head feature

`minimalize_engine/character/head_feature.py` may preserve a very small number of high-saturation, high-contrast head-region features. It rejects background-like red, skin/hair-like colors, overly large components, dark noise, and near-duplicate colors.

On the fixed rescue sample the final gate retains one blue head feature near the hat/ribbon area. The synthetic `accessory` tree node is protected from cross-semantic merging.
## Rejected experiments

The iteration deliberately rejected two approaches after rendering the real regression input. Cropping outfit reconstruction to the upper 60% of the torso produced a large white horizontal slab. Broad head-feature extraction produced a new red/brown plate. Neither approach is included in the final Phase 9 candidate.

A hard primitive-area rejection was also rejected because it caused the outfit to fall back to a triangular polygon. The accepted approach instead scales the preferred trapezoid and re-evaluates it.

## Fixed-corpus evidence

At level 4 and analysis max side 220, the 16-image corpus currently records about 38.72% mean shape reduction and 32.76% mean vertex reduction. The new semantic macro path activates on 1/16 images only. Non-rescue worst identity delta is about -0.0449 and non-rescue worst silhouette delta about -0.0010.

For the rescue case, the largest and second-largest final filled shapes are about 6.39% and 5.37% of the canvas, compared with the pre-rescue failure gate at about 25.4% and 24.7%.

Phase 9 telemetry records one Semantic Shape Tree activation, nine primitive fits, one head-feature activation, one face ellipse selection, and one outfit trapezoid selection.

Future VTracer-style region proposal work is deliberately outside this Phase 9 change. Do not loosen the rescue activation gate without new corpus-backed evidence.
