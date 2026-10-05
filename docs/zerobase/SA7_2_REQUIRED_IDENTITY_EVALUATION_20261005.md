# SA7.2 Required Identity Geometry Evaluation — 2026-10-05

Status: REJECTED / VISUAL FAIL / DO NOT MERGE

## Goal

Move identity preservation from generic color accents to semantic authorization:

observer evidence -> authorized SemanticPart parent -> required primitive reservation -> geometry.

## Candidate

Branch: `feature/semantic-abstraction-sa72-required-identity`

Implemented experimentally:

- `identity_binding.py`: required semantic identity roles and minimum primitive reservations.
- `identity_structure_observer.py`: deterministic coherent-structure observer.
- observer proposals cannot create visible identity geometry unless an authorized SemanticPart parent permits promotion.
- required roles for major hair, major clothing identity, and major accessory.
- head-internal observer evidence excludes suppressed semantic authority and remains subordinate to the head SemanticPart.
- no Golden raster, Golden coordinates, or GC001-specific feature/color constants in production logic.

## Verification

- focused SA7.2 tests: 15 PASS.
- full ZeroBase: 528 PASS.
- git diff --check: PASS.
- GC001 Visual Delta vs adopted silhouette baseline: 41.398% PASS.
- GC001 source-supported feature survival: 16 required, missing=0 PASS.
- forbidden face detail ratio: 0.00% PASS.
- candidate primitive count: 28.

## Actual four-way review

Source | Browser fallback v12 | SA7.2 | Rinka Golden

Visual decision: FAIL.

SA7.2 can observe a coherent region overlapping the source eyewear and can preserve multiple
authorized head-internal components, but the rendered result still does not reconstruct the semantic
identity structure as eyewear/front-hair/headwear. It produces disconnected patches inside a coarse
head/hair mass.

The failure is upstream of primitive count. Increasing generic accent count is not an acceptable fix.

## Root cause

Current Phase4 semantic masks are too coarse for the required abstraction decision.

For GC001, eyewear is not an independent semantic part. It is absorbed into head/hair evidence.
Likewise, major front-hair structure is not represented as a distinct semantic identity part.

Renderer-side observers can locate evidence but cannot legitimately decide that several pixels together
mean `eyewear` without a richer semantic decomposition contract.

## Decision

REJECT SA7.2 visual behavior. Do not merge the experimental branch into main.

Preserve the architectural finding:

> Required identity geometry must be reserved from explicit semantic parts, not reconstructed from
> generic color accents or renderer-local guesses.

## SA7.3 next direction: Fine Semantic Part Decomposition

Extend semantic evidence/parts before geometry with explicit identity-bearing categories:

- eyewear
- headwear
- hair_front
- hair_side
- collar
- tie_or_neckwear
- major_accessory

Requirements:

1. observer models/evidence may propose masks and labels but remain non-authoritative;
2. deterministic semantic adapter promotes evidence only under explicit confidence/structural rules;
3. unknown remains fail-safe and is never silently deleted;
4. face internals remain forbidden;
5. each required identity part receives a minimum geometry budget before macro masses;
6. renderer consumes the resulting parts and does not infer their semantic identity;
7. synthetic non-GC001 fixtures first, then holdout, then GC001;
8. unchanged hard gates and actual four-way review remain mandatory.

## Artifacts

Canonical Drive destination:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_2_20261005`

- `GC001_semantic_reauthor_sa72.png`
- `GC001_comparison_4way_sa72_20261005.png`
- `GC001_version_history_sa72_20261005.png`
- `GC001_sa72_source_supported_gate_report.json`
