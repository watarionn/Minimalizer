# Handoff — SA10.25 Material Topology Consolidation

## SA10.25 checkpoint — 2026-10-07

Status: HOLD — provenance/ownership contract hardened; material consolidation remains open.

Phase 4 `unknown` is now emitted as source evidence with
`coverage_role=observed-unassigned`, pixel count, and explicit exclusion from
semantic topology. It is not a semantic owner and is not replayed by Phase
11/12. `__unbound__` follows the same fail-closed diagnostic classification.
Existing hard thresholds are unchanged.

Verification: focused structural tests `13 passed`; full `tests/zerobase`
`896 passed`; `compileall` passed. Real GC001 Phase 3–14 rerun and the
material-noise-vs-material consolidation proof remain required. This is not
SA10.25 PASS.

Start from SA10.24. Do not weaken fragmentation `0.20`, source boundary `0.90`, anatomy, provenance, or semantic relation gates.

Goal: preserve material source topology while rejecting segmentation-noise components/holes as optimization authority, then consolidate/re-vectorize existing source-owned primitives so the real GC001 candidate can satisfy both structural and fragmentation hard gates.

Required: generic material-topology definition; synthetic noise-vs-material topology regressions; no case-specific branch; no generated pixels; real GC001 rerun; existing PASS transaction rerun; visual review before production promotion.
