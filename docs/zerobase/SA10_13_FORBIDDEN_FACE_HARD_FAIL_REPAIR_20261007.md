# SA10.13 Forbidden-Face Hard-Fail Repair — 2026-10-07

Status: COMPLETE / FORBIDDEN-FACE HARD FAIL REPAIRED / ALL CURRENT NON-GC001 HARD EVIDENCE PASS

## Goal

Repair the forbidden-face-detail hard failures exposed by SA10.12 without weakening the canonical face threshold, sacrificing Feature Survival, or changing the immutable adopted baselines.

## Root cause

SA10.12 established legitimate adopted baselines and exposed fresh forbidden-face failures:

- Hyakuto-Kyoko: 0.058444259567387684
- Juufuutei-Raden_stylecal_source: 0.012738853503184714
- required maximum: 0.0

Phase12 already had a source-guided face-plane simplifier, but that only simplified the face-owned primitive geometry/color. It did not guarantee that the final rendered pixels inside the authorized Phase4 face mask were a single neutral plane.

At the final raster, multiple production primitives / colors can still overlap the face mask. The canonical forbidden-face gate correctly detects those internal color details.

## Repair

Reused the existing SA7.38 deterministic FaceRasterGuard:

`minimalizer_zerobase/semantic_abstraction/face_raster_guard.py`

Integrated it into:

`minimalizer_zerobase/simplification/artifacts.py`

The guard now applies to Phase12 production candidate rasters after semantic geometry has been selected and rasterized.

Inputs are strictly:
- the production render;
- original source RGB;
- the bound Phase4 `face.png` semantic mask.

The guard:
- chooses one representative RGB actually observed inside the source face mask;
- replaces only pixels inside that semantic face mask;
- changes zero pixels outside the face mask;
- does not modify semantic primitives, ownership, topology, masks, or geometry;
- uses no Golden / adopted-baseline pixels for inference;
- performs no generation, inpainting, hidden completion, or missing-content reconstruction.

Candidate preview rasters are guarded as well, so Phase13 human review sees the same neutral-face visual policy as the final production raster.

## Unicode-safe artifact I/O

Phase12 PNG read/write helpers were also moved to:
- `numpy.fromfile + cv2.imdecode`
- `cv2.imencode + ndarray.tofile`

This preserves deterministic behavior while avoiding Windows Unicode-path failures.

## Fresh SA10.13 candidates

### Hyakuto-Kyoko

Production candidate SHA-256:
`84022e48e13ed7a80f8e3425d085d311e3ab7c86fcb28278ba079e182a33646a`

FaceRasterGuard:
- face pixels: 4,808
- changed face pixels: 4,808
- changed outside face pixels: 0
- fill RGB: [251, 226, 220]
- version: sa7.38-v1

Canonical visual hard gate:
- Feature Survival: PASS
- required signatures: 17
- missing signatures: 0
- Forbidden Face Detail: PASS
- forbidden-face ratio: 0.0
- overall canonical hard gate: PASS

Other hard evidence:
- Source Authority: PASS
- Anatomy: PASS
- Topology: PASS
- Phase14 machine: PASS
- Phase14 human visual: PASS
- determinism: PASS

Exact-output DINO semantic retention:
- SA10.11/12 production image diagnostic: 0.7552631073534017
- SA10.13 neutral-face candidate: 0.7637557534622893
- DINO remains diagnostic-only.

Fresh Phase14 deterministic-evaluation SHA:
`44eabdd61953d51966d363ba0014907f757d3d43f3de485da5272fd7eb9c76b6`

### Juufuutei-Raden_stylecal_source

Production candidate SHA-256:
`576a7baa1cf2dcf1a3254fb7daecefb1f5520dc8833294924077ba8ef98ab4b5`

FaceRasterGuard:
- face pixels: 1,413
- changed face pixels: 1,413
- changed outside face pixels: 0
- fill RGB: [194, 178, 175]
- version: sa7.38-v1

Canonical visual hard gate:
- Feature Survival: PASS
- required signatures: 9
- missing signatures: 0
- Forbidden Face Detail: PASS
- forbidden-face ratio: 0.0
- overall canonical hard gate: PASS

Other hard evidence:
- Source Authority: PASS
- Anatomy: PASS
- Topology: PASS
- Phase14 machine: PASS
- Phase14 human visual: PASS
- determinism: PASS

Exact-output DINO semantic retention:
- SA10.11/12 production image diagnostic: 0.9313136511266809
- SA10.13 neutral-face candidate: 0.9295234636673059
- DINO remains diagnostic-only.

Fresh Phase14 deterministic-evaluation SHA:
`f5e6ed30048508d6e36734d37685ec5557798c2ff827fa3792bbf8068db64961`

The existing Raden actual-emission gap remains diagnostic-only and unchanged.

## Immutable baseline boundary

SA10.12 baseline adoption records were not changed.

SA10.13 candidate hashes differ from adopted baseline hashes.

Both hard-gate bindings confirm:
- adoption transaction != SA10.13 evaluation transaction;
- same_transaction = false;
- candidate_bytes_equal_baseline = false;
- production_inference_allowed = false.

The adopted baseline is evaluation-only.

## Deterministic reproduction

Phase12 was regenerated again into separate output directories.

Byte-identical final PNGs:
- Kyoko: `84022e48e13ed7a80f8e3425d085d311e3ab7c86fcb28278ba079e182a33646a`
- Raden: `576a7baa1cf2dcf1a3254fb7daecefb1f5520dc8833294924077ba8ef98ab4b5`

Both reproduction checks matched exactly.

## Regression matrix

Canonical:
`benchmarks/regression/sa10/SA10_13_cross_case_matrix.json`

SHA-256:
`c51e576c30e13aac0091b8ad8f3cb3fa44163a45d97a3dd0a7260f15c4f52899`

For both current non-GC001 cases, all available hard evidence now passes:
- Feature Survival
- Forbidden Face Detail
- Anatomy
- Topology
- Source Authority
- Phase14 machine
- Phase14 human visual
- determinism

SA9 Teacher evidence remains explicitly UNAVAILABLE.

## Verification

Focused regression chain:
- 43/43 PASS

Covered:
- Phase12 simplification regressions;
- SA7.38 FaceRasterGuard;
- SA7.35 canonical hard gate;
- SA10.11 structural repair;
- SA10.12 adopted-baseline binding / visual hard-gate backfill;
- SA10.13 real-case face repair;
- cross-case matrix visibility.

## Boundaries preserved

- max_forbidden_face_ratio remains 0.0;
- Feature Survival remains independent and still passes;
- no Golden inference input;
- no browser-v12 inference input;
- no adopted-baseline inference input;
- no generation / inpainting / hidden completion;
- no semantic geometry authority change;
- no aggregate quality score;
- no calibration threshold;
- DINO cannot override hard evidence.

## Decision

SA10.13 is complete.

The current Kyoko/Raden non-GC001 hard-evidence set is fully available and passing except for intentionally separate SA9 Teacher diagnostics. The next step is to integrate these independently-visible hard reports into a reproducible production regression transaction and expand coverage without introducing aggregate authority.


## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_13_20261007_FORBIDDEN_FACE_REPAIR`

Drive folder ID:
`1C04kwWeBglGf6JlC0MqjdEQ_6GvTPK55`

The folder was created through the Drive API under the existing canonical Semantic_Abstraction parent. No Japanese parent folder was created from the local mount.

Drive API read-back verified all 19 preserved artifacts:
- 2 repaired Phase12 final PNGs;
- 2 Phase12 metrics JSONs;
- 2 Phase12 stage JSONs;
- 2 Phase14 evaluation JSONs;
- 2 baseline-bound visual hard-gate reports;
- 2 FaceRasterGuard evidence reports;
- 2 combined hard-evidence reports;
- 2 exact-output DINO evidence reports;
- 2 SA10.13 regression fixtures;
- 1 cross-case matrix.
