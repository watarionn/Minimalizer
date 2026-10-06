# SA10.6 Role Mask Preservation & GC001 Remeasurement — 2026-10-07

Status: COMPLETE / GC001 REMEASURED / ALL SA10 DIAGNOSTICS AVAILABLE

Added `evaluation/role_mask_artifact.py`.

Lossless evaluation artifact:
- hair.png
- major_clothing.png
- manifest.json with SHA-256, pixel counts, image shape
- source_derived=true
- evaluation_only=true
- production_output_changed=false

GC001 canonical masks were recovered from the documented Phase4 workspace:
`C:\Work\Temp\macro-gc001\artifacts\GC001\phase_04\part_masks`.

Recovered mask evidence:
- shape: 340 x 340
- hair pixels: 17,541
- major_clothing pixels: 3,217

These exactly reproduce the historical SA7.43 budget provenance:
- hair: 1 major component, 1 primitive
- major_clothing: 8 major components, 3 primitives
- global allocated: 4 / 5

SA10.5 direct overlap remeasurement:
- source components: 9
- represented components: 4
- Component Survival: 4/9 = 0.4444444444444444
- emitted primitives: 4
- source-supported primitives: 4
- Primitive Economy: 4/4 = 1.0

Role detail:
- hair: 1/1 components represented, 1/1 primitives source-supported
- major_clothing: 3/8 components represented, 3/3 primitives source-supported

The 50% component-coverage and 65% primitive-support thresholds remain measurement-contract parameters, not quality gates.

Verification:
- role-mask preservation + SA10.5 + SA10.4 focused chain: 9/9 PASS
- GC001 budget reproduction matches historical provenance exactly

Decision:
The two previously UNAVAILABLE SA10 diagnostics can now be populated from direct source-derived evidence.

Next:
SA10.7 should update the reproducible GC001 regression artifact to consume the SA10.6 evidence, preserve the complete artifact set to canonical Drive, and perform the first all-metrics SA10 review without adding thresholds.
