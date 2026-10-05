# SA7.1 Semantic Survival Reservation Evaluation — 2026-10-05

Status: REJECTED / VISUAL FAIL / DO NOT MERGE

## Goal

Replace late generic accent restoration with deterministic source-supported survival reservations before optional geometry spending.

## Implementation candidate

Branch: `feature/semantic-abstraction-sa71-survival-reservation`

Added:

- `semantic_abstraction/survival_reservation.py`
- source-pixel + authorized-semantic-mask reservations
- deterministic bounded reservation budget
- source-supported baseline survival gate so old Minimalizer-only artifacts are not canonized
- synthetic tests proving source support, deterministic ordering, bounded budget, and fail-closed mask validation

No Golden raster, Golden coordinates, GC001-specific colors, or GC001-specific feature names are used by production logic.

## Verification

- focused tests: 19 PASS
- full ZeroBase: 521 PASS
- git diff --check: PASS
- GC001 Visual Delta vs adopted silhouette baseline: 39.878% PASS
- GC001 source-supported survival: 16 required signatures, missing=0 PASS
- GC001 forbidden face detail ratio: 0.00% PASS

A diagnostic found that the one signature which failed the older baseline-only gate,
quantized RGB (80,144,208), is absent from the original source as well.
Therefore it is an older Minimalizer artifact and must not become a permanent required feature.

## Four-way visual review

Actual four-way reviewed:

Source | Browser fallback v12 | SA7.1 | Rinka Golden

Visual decision: FAIL.

Although metric gates pass, SA7.1 removes too much semantic identity structure.
The output does not preserve the goggles/front-hair identity structure adequately and remains much farther
from the intended Golden abstraction than the metrics imply. Metric PASS does not override visual FAIL.

## Decision

REJECT SA7.1. Do not merge the candidate visual behavior into main.

The experiment establishes two useful facts:

1. source-supported survival filtering is necessary to avoid preserving artifacts created by an older Minimalizer;
2. color/position signatures are insufficient semantic authority for required identity features such as goggles.

## SA7.2 next direction

Connect required identity semantics directly to primitive reservation.

1. represent required identity features as semantic parts or semantic feature bindings,
2. bind observer evidence to authorized parent parts without inventing identity from color alone,
3. allocate required minimum primitives before macro geometry,
4. define category grammar for identity structures such as eyewear/accessory, collar/tie, and major hair-front masses,
5. keep facial internals suppressed,
6. require source support plus semantic-role survival,
7. evaluate on synthetic non-GC001 fixtures before GC001,
8. rerun unchanged hard gates and actual four-way visual review.

Do not solve SA7.2 by increasing generic accent count.

## Artifacts

Canonical visual artifact destination:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_1_20261005`

Artifacts:

- `GC001_semantic_reauthor_sa71.png`
- `GC001_comparison_4way_sa71_20261005.png`
- `GC001_version_history_sa71_20261005.png`
- `GC001_sa71_source_supported_gate_report.json`

The comparison was regenerated with the actual Rinka Golden before final review.
