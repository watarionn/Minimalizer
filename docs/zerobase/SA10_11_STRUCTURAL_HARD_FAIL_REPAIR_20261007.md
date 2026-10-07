# SA10.11 Structural Hard-Fail Repair — 2026-10-07

Status: COMPLETE / STRUCTURAL HARD FAILS REPAIRED / NON-GC001 HARD EVIDENCE PASS

## Goal

Repair the Anatomy / Topology hard failures exposed by SA10.10 without weakening any hard gate, introducing case-specific coordinates, or breaking Phase10 geometry authority.

## Root-cause trace

### Juufuutei-Raden_stylecal_source

Phase4 contains a real `head` mask with 4,931 pixels, but no head-owned region survives into Phase6 and therefore Phase10 contains zero `head` primitives.

The head is a support-only structural surface substantially covered by face/hair. The exclusive semantic ownership path can therefore preserve the visible owners while losing the structural support part itself.

This was already upstream of Phase12. Phase12 was not the original deletion point.

### Hyakuto-Kyoko

The old Phase12 left-arm candidate retained more than 0.98 recall relative to Phase11, so Phase12 was faithfully preserving an already-drifted upstream geometry.

Against the Phase4 source-supported structural masks, SA10.10 exposed:
- left-arm structural geometry drift;
- `face:inside:head` relation loss;
- `left_arm:attached_to:torso` relation loss.

## Repair design

Phase10 remains unchanged as observed Phase7-mass geometry authority.

The repair is implemented in Phase12 because Phase12 already owns deterministic source-guided simplification and can consume read-only source evidence without reinterpreting Phase7/Phase10 semantic ownership.

Added:
- `minimalizer_zerobase/simplification/structural_source_repair.py`
- Phase12 integration in `simplification/style.py`
- Phase4 part-mask SHA binding in Phase12 artifact provenance
- Phase12 runner binding for Phase4 masks

The generic repair can activate only when source-supported structural evidence reports one or more of:
- a missing structural part;
- structural bbox-area ratio below 0.35 or above 2.8;
- a required source graph relation with confidence >= 0.5 missing from the current structural graph.

Repairable structural parts:
- head
- torso
- left_arm
- right_arm
- lower_body

Only the affected part is replaced by its Phase4 source-supported mask. Non-repaired parts remain evaluated against Phase11.

Repair records carry:
- `source_guided_kind=structural-source-repair-<part>`
- `source_evidence_refs=phase04:part_masks/<part>.png`

Generation, inpainting, hidden completion, Golden geometry, and case-specific coordinates remain forbidden.

## Actual repair results

### Hyakuto-Kyoko

Before repair, required structural relations missing:
- `face:inside:head`
- `hair:overlaps:head`
- `left_arm:attached_to:torso`

Repair parts:
- head
- left_arm
- torso

After repair:
- missing required relations: 0
- Anatomy: PASS
- Topology: PASS
- Source Authority: PASS

Phase12:
- selected profile: aggressive
- selected primitives: 26
- silhouette IoU: 0.990792

Phase14:
- machine: PASS
- human visual: PASS
- determinism: PASS
- silhouette preservation: 0.990792
- layout mean: 0.9608271237540492
- layout min: 0.9184889596025141
- identity retention: 0.963008
- primitive economy: 0.8354430379746836

Production candidate SHA-256:
`294a77a025656391a76b35cbb2fdb7f8f59c0e176e8433a1da0ca1fa5299065b`

Phase14 pure-evaluation determinism SHA-256:
`0f5e3d1a89650595fb4a38324c4e618d86f7d1102da4ffeea224d557c57c21d1`

Exact-output DINO semantic retention:
- SA10.10: 0.7709177748262631
- SA10.11: 0.7552631073534017
- delta: approximately -0.015655

The DINO decrease is diagnostic-only and cannot override the newly passing structural hard evidence.

### Juufuutei-Raden_stylecal_source

Before repair:
- `head` structural part missing
- `face:inside:head` missing
- `head:above:torso` missing

Repair parts:
- head

After repair:
- missing required relations: 0
- Anatomy: PASS
- Topology: PASS
- Source Authority: PASS

Phase12:
- selected profile: conservative
- selected primitives: 14
- silhouette IoU: 0.987733

Phase14:
- machine: PASS
- human visual: PASS
- determinism: PASS
- silhouette preservation: 0.987733
- layout mean: 0.9912281751704782
- layout min: 0.9551267735171939
- identity retention: 0.975258
- primitive economy: 0.46153846153846156

Production candidate SHA-256:
`a31acc69a055e4144484939a510f06dee61379e426dc0b39751f4a5cf90dd07f`

Phase14 pure-evaluation determinism SHA-256:
`7b73ada5108d7590a98dbbda041227a19498109b03ebbf2ca933bf9990cb5138`

Exact-output DINO semantic retention:
- SA10.10: 0.914517616858495
- SA10.11: 0.9313136511266809
- delta: approximately +0.016796

The existing actual-emission gap remains a separate diagnostic:
- allocated primitives: 2
- emitted primitives: 1
- emission realization ratio: 0.5
- actual component representation: 0.5
- actual primitive support: 1.0

It is not reinterpreted as SA10.5 Component Survival or Primitive Economy.

## Deterministic reproduction

Phase12 was regenerated into a second isolated output directory.

Byte-identical `12_final.png`:
- Kyoko: `294a77a025656391a76b35cbb2fdb7f8f59c0e176e8433a1da0ca1fa5299065b`
- Raden: `a31acc69a055e4144484939a510f06dee61379e426dc0b39751f4a5cf90dd07f`

Both reproduction comparisons matched exactly.

## Regression matrix

Canonical:
`benchmarks/regression/sa10/SA10_11_cross_case_matrix.json`

SHA-256:
`9503970702f7652e6536a2a5e7af81f55fc644c1cdab6f2f9751a1cdf8563586`

For both non-GC001 cases:
- Anatomy: AVAILABLE / PASS
- Topology: AVAILABLE / PASS
- Source Authority: AVAILABLE / PASS
- Phase14 machine: PASS
- Phase14 human visual: PASS
- determinism: PASS

Still explicitly UNAVAILABLE:
- Feature Survival hard evidence
- forbidden-face-detail hard evidence
- SA9 Teacher evidence

No candidate was used as its own adopted baseline.

## Verification

Focused regression chain:
- 38/38 PASS

Includes:
- existing Phase12 simplification regressions;
- structural source repair no-op and support-head recovery;
- SA10.10 hard-evidence contracts;
- SA10.11 real-case hard-evidence closure;
- SA10.8/10.9 matrix compatibility.

## Boundaries preserved

- no generative img2img;
- no inpainting / fill;
- no hidden completion;
- no Golden raster / coordinates / masks / colors / geometry as production input;
- no hard-fail override by DINO or aggregate metric;
- no aggregate quality score;
- no new production calibration threshold;
- no Feature Survival / face hard-gate fabrication without an adopted baseline.

## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_11_20261007_STRUCTURAL_REPAIR`

Drive folder ID:
`1zeYpnPL-ur-Zn6GWc2-ejuI64k7jUuM1`

Drive API read-back verified all 11 files.

Preservation set:
- two repaired Phase12 final PNGs;
- two Phase12 JSONs;
- two Phase14 evaluation JSONs;
- two exact-output DINO evidence JSONs;
- two fresh hard-evidence JSONs;
- SA10.11 cross-case matrix.

## Decision

SA10.11 is complete.

Structural hard failures are repaired generically and independently verified. The next unresolved hard-gate gap is legitimate adopted-baseline binding for Feature Survival and forbidden-face-detail evaluation.
