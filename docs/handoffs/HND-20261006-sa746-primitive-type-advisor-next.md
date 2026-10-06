# HND-20261006 Minimalizer SA7.46 Primitive-Type Advisor Research Handoff

Date: 2026-10-06
Status: SA7.46 COMPLETE / SUPERSEDED BY SA7.47 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now historical. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-sa747-layer-occlusion-evidence-next.md`.

SA7.45 implementation:
- PR #180
- merge SHA: `015551fbdcca9114a10bbdd001f970e6d3f2e0f9`

Canonical SA7.45 record:
`docs/zerobase/SA7_45_SEMANTIC_RETENTION_OBSERVER_20261006.md`

Latest adopted visual baseline remains:
`a60aaa12ff22c2f6384a598442964710ce939d87`

## SA7.46 Primitive-Type Advisor Research — COMPLETE

Goal:
absorb StarVector's semantic primitive-selection idea without granting a VLM/LLM direct production geometry authority.

Primitive families to study:
- polygon
- rectangle
- ellipse
- line
- ribbon

Required architecture:
external/deterministic advisor suggestion
-> validate vocabulary/provenance
-> compare against source-derived geometry evidence
-> record agreement/disagreement
-> optionally identify explicit deterministic promotion rules
-> no production rendering change in SA7.46

Hard boundaries:
- advisor output is non-authoritative;
- arbitrary generated SVG/code is never executed;
- no coordinates/colors from advisor become production authority;
- no unsupported primitive family is accepted;
- high confidence cannot override source geometry or existing hard gates;
- production output must remain unchanged if advisor is unavailable.

Acceptance:
- schema/validation tests
- deterministic geometry-evidence baseline
- advisor/source agreement audit
- malformed or unsupported suggestions fail closed
- production no-op proven
- GC001 research report preserved

Next after SA7.46:
- SA7.47 Layer / Occlusion Evidence Research
- SA7 closeout
- Post-SA7 Backport PB2 -> PB7
