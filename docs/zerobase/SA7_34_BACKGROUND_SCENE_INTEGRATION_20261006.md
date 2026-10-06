> **SA7.35 correction (2026-10-06):** Historical hard-gate values copied from the SA7.2 report are superseded. Fresh evaluation with the canonical SA7.35 path gives source-supported Feature Survival **FAIL (missing=3)** and Forbidden Facial Detail **14.4622% FAIL** for this candidate family. The previous missing=0 / 0.00% values must not be used for visual-adoption claims. See `SA7_35_HARD_GATE_RECONCILIATION_20261006.md`.

# SA7.34 Background Multi-field Scene Integration / Hole-safe Composition — 2026-10-06

Status: CANONICAL SCENE INTEGRATION PASS / VISUAL ADOPTION HOLD

SA7.34 connects the SA7.33 source-only background field geometry to the canonical `VectorScene`.

## Production contract

- source RGB + source-derived subject mask only
- existing canonical subject primitives are never mutated
- existing generic `background` primitives are replaced only when safe source-supported background geometry exists
- generated background primitives are always assigned z-order below every subject primitive
- SA7.33 field polygons are preferred
- if a background fully wraps a subject and cannot be represented safely as one filled polygon, use a hole-safe bounding-box frame decomposition (top / bottom / left / right rectangles)
- if neither representation is safe, preserve the existing scene unchanged
- Golden and Browser fallback v12 are never inference inputs
- provenance records mode, generated count, replaced-background count, and `golden_raster_used=false`

## GC001 canonical scene result

Mode: `field_polygons`

- generated background primitives: 2
- background z-orders: -2, -1
- minimum subject z-order: 1
- canonical subject primitive count before: 14
- canonical subject primitive count after: 14
- subject primitive dataclasses identical before/after: YES

This proves that SA7.34 changes only the background layer at the canonical scene level.

## Visual evaluation

- Visual Delta vs adopted baseline: 69.6834% — PASS
- SA7.29 -> Golden LAB MAE: 54.9392
- SA7.33 research-only background candidate -> Golden: 32.6683
- SA7.34 canonical scene candidate -> Golden: 33.1502
- Browser fallback v12 -> Golden: 16.2422
- v12 regression floor: FAIL

The small difference between SA7.33 and SA7.34 is expected: SA7.33 added source fields behind the previous evaluation SVG while SA7.34 properly removes the old generic background primitive and replaces it in the canonical scene.

Role-local background weighted gap remains about 0.09089, compared with 0.16390 before the background work. The major background/composition improvement therefore survives canonical integration.

## Hard-gate evaluator consistency finding

Running the current production feature-survival and forbidden-face evaluators directly on the same GC001 subject mask reports:

- SA7.29: missing=1, forbidden-face ratio=0.144622
- SA7.33: missing=1, forbidden-face ratio=0.144622
- SA7.34: missing=1, forbidden-face ratio=0.144622

This is not an SA7.34 regression. The results are identical across all three candidates and conflict with the historical GC001 hard-gate report path that recorded missing=0 / forbidden-face=0.00%.

Therefore the project currently has a hard-gate definition/path mismatch. Visual adoption must remain blocked until that mismatch is reconciled. SA7.34 architecture can still merge because canonical subject geometry is byte-for-byte/dataclass-identical and the focused/full regression suites cover background integration independently.

## Decision

Merge the canonical background scene integration.

Do not update the adopted visual baseline.
Do not append SA7.34 to accepted Minimalizer Version History.

Next recommended stage: SA7.35 Hard-Gate Path Reconciliation. Establish one canonical GC001 feature-survival / forbidden-face evaluation path, reproduce the historical 0/0 result or explain why it was invalid, and freeze a single gate before further visual adoption work.
