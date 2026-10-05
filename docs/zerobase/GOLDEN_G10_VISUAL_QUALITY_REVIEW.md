# G10 Visual Quality Review

Status: **HARD-GATE GENERALIZATION PASS / VISUAL QUALITY HOLD**

G10 remains frozen as evaluation-only evidence. No G10-specific tuning is authorized.

## Independent review

The five fresh cases successfully preserve a coarse character footprint and deterministic palette, but the rendered candidates remain materially below the human Golden abstraction target.

Common failure classes across the suite:

1. **Primitive pile-up instead of silhouette design.** Repeated authorized primitives occupy nested/overlapping rectangles and ellipses. Budget is now geometrically effective, but it does not yet form a coherent outer contour.
2. **BBox authority is too coarse.** A feature-wide bbox gives legal placement but not enough shape topology. The 4x4 centroid descriptor moves primitives, yet cannot express left/right lobes, taper, holes, or contour turns.
3. **Palette contamination remains possible.** Dominant-bin color is deterministic, but broad feature bboxes can contain neighboring regions/background. This is especially visible when hair/accessory colors collapse toward pale skin/background-like values.
4. **Semantic granularity ceiling.** Four broad roles are enough to test wiring, not enough to retain identity-bearing clothing and head-accessory structure demonstrated by the Golden.
5. **Composition is renderer-valid but abstraction-poor.** Primitive economy exists numerically, while negative-space and feature hierarchy are not explicitly optimized.

## Decision

Do not tune thresholds, colors, or case rules on G10.

The next generic implementation target is **mask-topology-aware authorized fitting**: derive deterministic low-resolution occupancy components/contour anchors from the already-authorized semantic mask and fit primitives to those anchors while remaining inside semantic authority. This is a geometry mechanism, not a new semantic classifier.

A subsequent fresh G11 corpus must decide adoption. G10 is retained only as regression/evaluation evidence.
