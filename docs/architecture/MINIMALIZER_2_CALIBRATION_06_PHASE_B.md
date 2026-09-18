# Minimalizer 2.0 Calibration 06 Phase B

Updated: 2026-09-17
Status: PASS with foreground-integration follow-up required
Scope: rembg adapter and Approved-18 foreground model comparison

## Goal

Evaluate rembg strictly as non-generative input analysis.
The rembg mask is analysis evidence only. It is never rendered as output geometry.
Minimalizer still owns the complete output path:
`pixel -> micro structure -> superpixel/region -> merged region -> primitive`.

## Isolated evaluation environment

Provider dependencies stayed outside the base Minimalizer requirements:
- Python `3.11.9`
- rembg `2.0.84`
- onnxruntime `1.30.0`
- Approved-18 corpus: `18 / 18` cases

No MediaPipe, Grounded-SAM, or YOLO dependency was added in this phase.

## Model comparison

Three rembg models were evaluated on the same Approved-18 character corpus.
`isnet-anime` is the clear initial model for character illustrations.
| model | mean sec | subject area | ambiguous fraction | components | largest component share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `isnet-anime` | 0.646 | 0.672 | 0.0208 | 1.83 | 0.99984 |
| `isnet-general-use` | 0.577 | 0.483 | 0.1018 | 8.33 | 0.99469 |
| `u2net_human_seg` | 0.203 | 0.396 | 0.0659 | 11.22 | 0.94341 |

The numeric means are not used as a stand-alone quality score. Visual contact sheets were reviewed case by case.

`isnet-anime` retained complete character silhouettes, including hair, sleeves, arms, and accessory extents, with little uncertain interior mass.
`isnet-general-use` frequently treated legitimate character interior regions as low-confidence foreground.
`u2net_human_seg` is fast but unsuitable for this corpus: Koganei-Niko, Koseki-Bijou, Mori-Calliope, and Vestia-Zeta contained near-empty or severe subject loss. Hakos-Baelz and Kobo-Kanaeru were also visibly unstable.

Because the first three models produced a clear winner, `birefnet-general-lite` was not added. This follows the dependency-minimization rule rather than expanding the model stack without a demonstrated need.

## Adapter implementation

Added a lazy-loaded rembg adapter in `minimalize_engine/v2/rembg_guidance.py`.
The default evaluation model is `isnet-anime`.
The adapter requests `only_mask=True`, converts the result to a normalized subject-probability map, and derives conservative confidence from distance to the uncertain `0.5` boundary.

Importing Minimalizer V2 does not import rembg itself. Provider loading occurs only when a rembg session or guidance mask is explicitly requested.
## V2 integration result

`isnet-anime` guidance was then fed through the existing V2 subject/background Region Merge contract at the hosted `analysis_max_side=400` envelope.

Approved-18 result:
- algorithm digest changed: `18 / 18`
- hard invariant failures: `0 / 18`
- mean final Region Merge root delta: `+5.667`
- mean `subject_background` barrier delta: `+1048.722`

This proves that rembg evidence reaches the intended Region Merge stage and strongly prevents cross-boundary merges.
It also shows that the current dynamic hard-barrier use is too strong to enable as the production default without another integration pass.

An eight-case visual subset was rendered as source / baseline / guided triplets. Selected regions remained `70 -> 70` in all eight cases, but mean final visual groups changed `32.5 -> 36.5`.
The largest increases were Koseki-Bijou `33 -> 40`, Isaki-Riona `30 -> 40`, and Momosuzu-Nene `30 -> 39`.
Raora-Panthera improved in the opposite direction at `37 -> 35`, while Kobo-Kanaeru remained `41 -> 41`.

Therefore the problem is not the foreground model. The remaining issue is how its evidence is scoped into the merge hierarchy.

## Phase B decision

Adopt `isnet-anime` as the initial rembg model for character/illustration foreground analysis.
Keep rembg optional and isolated for now. Do not add it to the base runtime requirements yet.
Do not enable the current direct dynamic subject/background hard-barrier behavior as the browser default.
The next foreground integration should preserve the successful boundary evidence while avoiding unnecessary character fragmentation. Preferred candidates are:
1. boundary-scoped subject/background protection instead of repeatedly propagating every mask distinction as a hard merge barrier
2. analysis-only background flattening or equivalent foreground-layer separation before SLICO, while preserving the original source image for color/identity evidence

No visual thresholds, SLIC targets, Region Merge weights, facet thresholds, or preset semantics were tuned to make the provider look better.

## Validation

Focused adapter + guidance tests: `10 passed`.
Approved-18 guided comparison: hard invariant failures `0 / 18`.
Machine-readable results: `MINIMALIZER_2_CALIBRATION_06_PHASE_B_EVALUATION.json`.
Evaluation tools remain reproducible under `tools/evaluate_rembg_guidance.py` and `tools/compare_rembg_guided_v2.py`.

## Next boundary

Calibration 06 Phase C should refine foreground/background integration using the accepted `isnet-anime` evidence before adding MediaPipe semantics.
MediaPipe remains the next semantic provider after the foreground contract is stable.
Grounded-SAM and YOLO remain deferred.

Do not create/update a PR, touch `main`, merge, deploy, or run GitHub Actions without the corresponding explicit approval.
