# HND-20261006 Minimalizer SA7.47 Layer / Occlusion Evidence Research Handoff

Date: 2026-10-06
Status: SA7.47 COMPLETE / SUPERSEDED BY PB2 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now historical. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-pb2-sa2-evidence-adapter-backport-next.md`.

SA7.46 implementation:
- PR #181
- merge SHA: `cc38323274546970a16c9ab0d233f85b0417bcc7`

Canonical SA7.46 record:
`docs/zerobase/SA7_46_PRIMITIVE_TYPE_ADVISOR_RESEARCH_20261006.md`

## SA7.47 Layer / Occlusion Evidence Research — COMPLETE

Goal:
absorb LayerPeeler / SuperSVG layer reasoning as observer evidence without replacing canonical anatomy/topology or render z-order authority.

Evidence should describe:
- role-mask overlap
- overlap ratio per role
- boundary contact / adjacency
- disjoint relationships
- optional front/behind direction when an existing canonical z-order observation is supplied
- provenance of direction evidence

Hard boundaries:
- observer cannot reorder the scene;
- source overlap evidence cannot invent occlusion direction;
- canonical z-order may be observed but not changed;
- ambiguous/disjoint relations remain explicit;
- no Golden/v12 production input;
- no generative layer decomposition;
- no anatomy/topology authority replacement.

Acceptance:
- deterministic pairwise relation graph
- mapping-order invariance
- overlap/contact/disjoint synthetic tests
- optional z-order direction audit
- explicit non-authority
- GC001 source-mask evidence report
- production output unchanged

After SA7.47:
- SA7 Closeout / Integration Gate
- Post-SA7 Precedent Backport PB2 -> PB7
- SA8 -> SA9 -> SA10
