# SA10.4 Component Survival / Primitive Economy Evidence — 2026-10-07

Status: COMPLETE / EVIDENCE CONTRACT PASS / GC001 COUNTS NOT YET CLAIMED

Added `evaluation/component_economy_evidence.py`.

The contract uses the same role-local frame as SA7.43 adaptive primitive budget:
- source components = major_component_count
- emitted primitives = allocated_primitives
- represented components must be supplied explicitly
- source-supported primitives must be supplied explicitly

It does not infer represented components from allocated primitive count.

This distinction matters for GC001:
- hair has 1 source major component and 1 allocated primitive
- major_clothing has 8 source major components and 3 allocated primitives
- those allocation counts alone do not prove which source components survived representation

Therefore SA10.4 does not yet replace GC001 UNAVAILABLE values with guessed 4/9 or 4/4 metrics.

Validation:
- negative / impossible counts fail closed
- represented > source fails
- source-supported primitives > emitted fails
- missing role evidence fails
- unknown role evidence fails
- evidence remains non-authoritative

Verification:
- SA10.4 through SA10.1 focused chain: 21/21 PASS

Next: SA10.5 must extract explicit role-local component-to-primitive support from the GC001 scene/provenance and only then populate Component Survival and Primitive Economy.
