# HND-20261006 Minimalizer PB5 / SA5 Face Neutralization Compatibility Audit

Date: 2026-10-06
Status: PB5 COMPLETE / SUPERSEDED BY PB6 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now historical. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-pb6-sa6-anatomy-occlusion-evidence-backport-next.md`.

PB4 implementation:
- PR #185
- merge SHA: `b82387d7b30e9b0459cfd2abe87d6a97fe2b5aca`

Canonical PB4 record:
`docs/zerobase/PB4_SA4_SEMANTIC_DEBUG_BOARD_BACKPORT_20261006.md`

PB4 Drive evidence:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB4_SA4_20261006`

Folder ID:
`1ChMsJKXfY6kX0Pe2VV3v05JJ_QuDITn3`

## PB4 closure

Classification:
**IMPLEMENTED + DIAGNOSTIC-ONLY**

GC001:
- component rows: 83
- observed Evidence: 111
- advisor Evidence: 0
- promoted production authority: 0
- removal observer unavailable: 83
- merge observer unavailable: 83
- insufficient-evidence: 83
- semantic context: AVAILABLE / 0.7298672763136121
- production policy changed: false
- production output changed: false
- candidate SHA unchanged: true

Verification on exact merged implementation main `b82387d7b30e9b0459cfd2abe87d6a97fe2b5aca`:
- focused PB2/PB3/PB4: 35/35 PASS
- ZeroBase: 713/713 PASS
- compileall: PASS
- git diff --check: PASS

## PB5 / SA5 Face Neutralization Compatibility Audit — COMPLETE

Primary objective:
prove that the precedent-derived PB2/PB3/PB4 observer/debug stack coexists with canonical face neutralization without weakening the image-level face safety contract.

PB5 is a compatibility/safety audit first.
It must not replace SA7.38.

### Canonical face contract to preserve

Source:
`docs/zerobase/SA7_38_FACE_NEUTRALIZATION_RECONCILIATION_20261006.md`

Implementation:
`minimalizer_zerobase/semantic_abstraction/face_raster_guard.py`

Canonical contract:
- deterministic post-render face raster safety guard;
- inputs are current rendered RGB, original source RGB, authorized semantic face mask;
- choose a face fill from actually observed source-face pixels;
- modify exactly face-mask pixels;
- zero changed pixels outside the authorized face mask;
- no Golden/adopted-baseline raster repair authority;
- no facial-feature proposals;
- no generative reconstruction/inpainting;
- no case-specific coordinates or colors.

Required hard result:
- Forbidden Face Detail = 0.00%
- face-guard writes outside face mask = 0

### PB5 questions

1. Can PB2 face/head component Evidence coexist without becoming face render authority?
2. Can PB3 semantic-retention/recommendation evidence mention face/head components without suggesting a production action?
3. Can PB4 debug-board visualization show face evidence without changing face raster bytes?
4. Can a high semantic/advisor score ever weaken or hide the image-level Forbidden Face Detail hard gate?
5. Is any new face-layer implementation actually justified?

Expected answer to question 5 may be **no**.

### Preferred classification logic

PB5 should end as one of:

- **NO-OP-BY-DESIGN + COMPATIBILITY PASS**
  if existing SA7.38 is already the safest correct authority and PB2/PB3/PB4 require no face implementation change;

or

- **OBSERVER-ONLY DIAGNOSTIC ADDITION**
  only if a narrowly scoped diagnostic adds audit value without touching face rendering.

Do not modify the face raster guard merely to create a change.

### Required synthetic tests

1. PB2 face/head Evidence remains production_authority=false.
2. PB3 unavailable semantic perturbation cannot imply face omission.
3. PB3 perfect semantic score cannot override face hard failure.
4. PB4 board must display face hard failure explicitly when supplied.
5. PB4 generation leaves guarded face raster byte-identical.
6. face raster guard still changes zero pixels outside face mask.
7. guarded raster still yields Forbidden Face Detail = 0.00%.
8. observer/advisor unavailable paths do not change face output.
9. arbitrary primitive advice cannot become face geometry authority.
10. existing SA7.38 tests remain unchanged and passing.

### GC001 audit

Use the current SA7.44 candidate + canonical source face mask.

Required checks:
- run canonical face raster guard;
- verify outside-face changed pixels = 0;
- verify Forbidden Face Detail = 0.00%;
- generate PB2/PB3/PB4 diagnostic context around face/head;
- verify diagnostics do not alter guarded raster SHA;
- preserve a compatibility report, not a new adopted visual candidate.

### Production boundary

PB5 must not:
- change face pixels for diagnostic reasons;
- promote semantic retention to face authority;
- promote primitive advisor output to face geometry;
- reinterpret head/hair overlap as face depth authority;
- use Golden/v12 raster as face repair input;
- introduce eye/mouth/eyebrow/nose detail;
- weaken the 0.00% image-level face-detail gate.

### Preferred implementation order

1. Re-read SA7.38 guard/tests and current PB2/PB3/PB4 contracts.
2. Add compatibility tests before changing production code.
3. Run the focused face + backport suite.
4. If all compatibility tests pass without production changes, classify NO-OP-BY-DESIGN.
5. Only add observer-only diagnostics if a concrete audit gap remains.
6. Run full ZeroBase.
7. Run GC001 compatibility audit.
8. Preserve report/artifacts to Drive.
9. Classify PB5 explicitly before PB6.

## Expected classification

**NO-OP-BY-DESIGN + COMPATIBILITY PASS** is currently preferred unless the audit discovers a real diagnostic gap.

## After PB5

PB6 / SA6 Anatomy / Occlusion Evidence Backport.

PB6 will reuse PB2/PB4 layer relation evidence around anatomy/topology while preserving existing anatomy authority.

## Current state declaration

The canonical continuation point is:

**PB6 / SA6 Anatomy / Occlusion Evidence Backport**
