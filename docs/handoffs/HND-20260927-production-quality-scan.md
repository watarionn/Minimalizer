# Production Quality Scan / Polygon Decimator Handoff — 2026-09-27

## Checkpoint

This checkpoint is audit-complete and ready for integration review on:

- branch: `feature/production-quality-scan`
- worktree: `C:\Users\watar\Documents\Minimalizer-quality-scan`
- base: current `origin/main`
- production main is not modified by this checkpoint.

The previous Geometry Mass production rollout is already closed on main. This branch starts the next quality phase: finding and reducing pathological polygon contour density without changing semantic structure.

## Production Quality Scan finding

The current post-Shading / post-Geometry pipeline still contains cases where a single semantic part holds hundreds of polygon vertices.

Stage A / B identified the main pathology as contour density, not palette count or visible-shape count.

Representative examples from the baseline scan:

- Aki Rosenthal: head carried an ~800-vertex dense contour.
- Mori Calliope: head had 502 vertices across 9 loops.
- Nerissa Ravencroft:
  - left_arm 264 vertices / 7 loops
  - right_arm 593 vertices / 8 loops
  - left_leg 258 vertices / 3 loops
- IRyS: left_leg had 440 vertices.
- Hyakuto Kyoko: right_leg 277 vertices / 2 loops.

## Implementation in this branch

### 1. Post-Shading pathological polygon decimation

A post-Shading polygon-decimation stage was added. It runs after the Shading Flatten guard selects its final candidate, so ordinary decimation does not participate in the Shading decision itself.

It only targets unusually dense polygon loops.

Safety is based on rasterized geometry fidelity:

- minimum IoU: 0.965
- max undercoverage: 0.025
- max overcoverage: 0.035
- minimum meaningful vertex savings
- normal low-vertex polygons are ignored

### 2. Adaptive single-loop decimation

`max_vertices` is treated as an ideal target, not a hard requirement.

If a contour cannot safely reach the ideal target, the code keeps the simplest intermediate candidate that still satisfies the fidelity guard.

Observed result:

- Aki: 843 -> 127 part polygon vertices in latest top-12 regression
- IRyS: 892 -> 503 in latest top-12 regression

Earlier isolated probes showed the same direction, including IRyS left_leg reducing from 440 to a low-hundreds safe candidate.

### 3. Multi-loop decimation

Multi-loop polygons are XOR-composed in the renderer, so holes must be preserved.

Implementation therefore:

- never deletes or merges loops
- simplifies large loops independently
- keeps small loops untouched
- compares connected-component + hole topology before/after
- rejects candidates that change topology
- applies whole-geometry IoU/under/over guards

### 4. Topology-aware backoff

A strong loop candidate may preserve pixel fidelity but change hole count.

Instead of relaxing the topology guard, the implementation walks back through progressively more conservative candidates until it finds the simplest candidate that preserves topology.

Key diagnosis:

- Mori head:
  - strong candidate 502 -> 80
  - IoU ~0.9686
  - holes 9 -> 11, so correctly rejected
  - topology-aware backoff found a safe weaker candidate
- Nerissa right_arm:
  - strong candidate 593 -> 417
  - IoU ~0.9804
  - holes 10 -> 11, so correctly rejected

Latest representative output:
- Mori: 581 -> 185 part vertices
- Nerissa: 1142 -> 746
- Kyoko: 339 -> 138

## Tests

Focused person-part tests currently pass:

- `tests/test_v2_person_parts.py`: 60 passed

Added tests cover:

- dense single-loop reduction
- normal polygon no-op
- adaptive intermediate target
- multi-loop hole preservation
- topology-changing candidate rejection
- topology-aware backoff to a safer candidate

A full project regression has NOT yet been run for this WIP checkpoint.

## Top-12 representative regression

Latest scan:
`artifacts\production_quality_scan\decimator_top12_regression.json`

Comparison:
`artifacts\production_quality_scan\decimator_top12_comparison.json`

Compared with the pre-decimator Stage B baseline:

- cases: 12
- cases with vertex reduction: 7
- vertex-regression cases: 0
- total part-polygon vertex savings: 2,429
- alpha failures: 0
- max color similarity loss: about 4.28e-05
- max edge IoU loss: about 0.00417

Selected examples:

- Vivi: 288 -> 77
- Aki: 843 -> 127
- Mori: 581 -> 185
- Nerissa: 1142 -> 746
- IRyS: 892 -> 503
- Mela: 217 -> 97
- Kyoko: 339 -> 138

Bijou / Marine / Baelz / Miko / Tsuzuri remained unchanged in vertex count in this scan.

## Closure evidence

Vivi's same-guidance ON/OFF diagnostic is now closed. With identical guidance and config, Decimator enabled and disabled produced the same Shading Flatten decision: accepted=false, reason=part_polygon_vertices, baseline part vertices=288, candidate part vertices=351, baseline global vertices=1546, candidate global vertices=1523. The post-Shading decimator therefore does not feed back into the Shading decision.

Regression:
- targeted Shading Guard + person-part: 68 passed
- broader V2 suite: 322 passed, 1 unrelated Starlette deprecation warning
- full repository: 664 passed / 2 known pre-existing failures
- both full-suite failures require the repository-absent `tests/assets/false_face_phase85.png`; this same baseline failure is documented across earlier closures and does not reach this V2 change.

Approved-68 controlled ON/OFF audit:
- 68 cases, 0 scan errors in both runs
- total part polygon vertices: 9,631 -> 6,073
- savings: 3,558 vertices (~36.9%)
- improved: 14; unchanged: 54; regressed: 0
- visible shape-count changes: 0
- Shading decision changes: 0
- Geometry Guard accepted-event changes: 0
- alpha preservation failures: 0
- max absolute color-similarity delta: 0.0002683848
- max absolute edge-IoU delta: 0.0041742169
- PNG changes: 14, exactly the 14 cases where decimation reduced vertices

Largest reductions include Aki 843->127, Mori 581->185, Nerissa 1142->746, IRyS 892->503, Tokino Sora 385->71, Raden 392->80, Kyoko 339->138, Vivi 288->120, and Mela 217->97.

Local evidence:
- `artifacts\production_quality_scan\decimator_approved68_audit.json`
- `artifacts\production_quality_scan\decimator_off_approved68_baseline.json`
- `artifacts\production_quality_scan\decimator_approved68_comparison.json`

## Recommended next steps

1. Review the final branch diff and commit the audit-complete implementation/tests/tool/handoff.
2. Open/prepare the integration PR.
3. Merge to production main only after the normal explicit integration approval.

## Important boundaries

- Audit is closed; do not merge to main until the normal explicit integration approval.
- Keep the existing Geometry Mass Final Guard intact.
- Keep Shading Flatten Guard intact.
- Do not relax topology preservation merely to achieve lower vertex counts.
- Artifacts under `artifacts\production_quality_scan` are local evidence and are not intended to be committed unless explicitly selected.
