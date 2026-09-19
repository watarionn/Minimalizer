# Minimalizer 2.0 Approved-78 Hierarchy Cut Calibration

Updated: 2026-09-19
Base main: `1440201aeffb77e7b9ab11c2ef1ad834bece747a`
Status: production-default Approved-78 gate complete; 40-shape Minimal policy validated locally

## Purpose

Approved references expanded from 18 to 78 images. This calibration isolates hierarchy-cut
selection before changing Region Merge cost, segmentation, semantic guidance, or rendering.

The original ten-case expansion pilot (69-78) suggested that 24 visible shapes could work.
The full Approved-78 rerun showed that conclusion did not generalize: 24 shapes was too
aggressive on several of the older and newly added silhouette classes.

## Full corpus comparison

All policies below were evaluated on the same 78 input/reference pairs with V2 Minimal,
analysis guidance disabled, and identical Region Merge inputs.

| Policy | mean shapes | color similarity | edge IoU | silhouette IoU |
| --- | ---: | ---: | ---: | ---: |
| old Minimal policy | 74.218 | 0.932866 | 0.096545 | 0.543229 |
| 40-shape candidate | 40.000 | 0.932102 | 0.090415 | 0.519639 |
| 32-shape candidate | 32.000 | 0.932020 | 0.086899 | 0.511585 |
| 24-shape candidate | 24.000 | 0.931248 | 0.081886 | 0.496173 |

The 40-shape candidate reduces visible complexity by about 46% relative to the old policy while
losing only about 0.0008 mean color similarity, 0.0061 edge IoU, and 0.0236 silhouette IoU.
By contrast, the 24-shape candidate cuts about 68% of shapes but loses 0.0147 edge IoU and
0.0471 silhouette IoU on the corpus. The strongest regressions appeared in cases such as
Omaru Polka, Achichi Mela, Mizumiya Su, IRyS, Sakura Miko, Hyakuto Kyoko, and Sorashina Sopia.

The first 18 approved references remain stable across compact candidates, but cases 19-78
expose the over-compression. For 19-78, mean silhouette IoU is 0.415087 with the old policy,
0.384461 at 40 shapes, 0.373932 at 32 shapes, and 0.353896 at 24 shapes.

## Adopted default policy

`minimal` changes from the old `CutPolicy(40, 70, 0.70, 0.75)` family to:

`CutPolicy(24, 40, 1.00, 1.10, target_weight=1.10)`

To preserve preset ordering below Minimal, `ultra_minimal` becomes:

`CutPolicy(12, 20, 1.30, 1.25, target_weight=1.35)`

Detailed and Balanced remain unchanged. This avoids widening the scope of the calibration and
keeps the change focused on the two coarsest presets.

## Safety boundary

This calibration changes hierarchy-cut defaults only. It does not change Region Merge cost,
foreground guidance, semantic providers, characteristic color extraction, primitive conversion,
or the production routing contract.

The full 78-case compact-v6 run completed 78/78 with zero errors and exactly 40 visible shapes
per Minimal case. A second gate then ran the actual production-default implementation with no
cut-policy monkeypatch. To avoid the native long-process termination observed after case 19,
the runner isolated the corpus into fresh 10-case processes (final chunk 71-78), then aggregated
the reports. All 78 cases completed successfully with zero evaluation errors. The aggregate
metrics exactly match compact-v6: color similarity 0.932102, edge IoU 0.090415, silhouette IoU
0.519639, and 40.0 visible shapes.

## Decision

The 24-shape pilot result is superseded by the full-corpus result. Forty shapes is the current
Minimal default candidate because it gives a large simplification step without the sharper
silhouette collapse seen at 32 and 24 shapes.

The exact default implementation passed the hierarchy-cut unit suite (6/6) and the full
Approved-78 production-default gate (78/78, zero evaluation errors) without the evaluation
monkeypatch. The repository-wide suite then completed with 528 passed and 2 failures. Both
failures are the pre-existing missing-fixture cases that reference
`tests/assets/false_face_phase85.png`; neither reaches the hierarchy-cut code changed here.
No new regression attributable to this calibration was observed.
