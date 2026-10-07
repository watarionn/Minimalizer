# SA10.17 Fragmentation Repair

Status: CLOSED for the La-Darknesss / Kaela-Kovalskia fragmentation cluster.

## Root cause
Phase 12 treated high-cardinality identity-critical owners as a reason to replay exact Phase 11 source primitives whenever simplification IoU fell below the local guard. That preserved many micro-fragments. The generic repair keeps exact replay only for genuinely small critical parts; larger critical owners remain protected by the existing part-level recall/IoU hard gates.

No case name, fixed coordinate, fixed color, fixed mask, or Phase 14 threshold change was introduced.

## Evidence
SA10.16 initial evidence: La-Darknesss fragmentation_penalty=0.4339622642 with 47 Phase 12 primitives; Kaela-Kovalskia fragmentation_penalty=0.2954545455 with 42 primitives.

After the generic repair: La-Darknesss uses 24 primitives and fragmentation_penalty=0.0; Kaela-Kovalskia uses 26 primitives and fragmentation_penalty=0.0; both have tiny_component_count=0 in the regenerated Phase 14 artifacts.

A reusable ownership diagnostic was added in minimalizer_zerobase/evaluation/fragmentation_ownership.py with tools/run_sa1017_fragmentation_diagnostic.py. It is diagnostic-only and has no authority to override hard failures.

## Verification
- tests/zerobase/test_phase12_style_simplification.py + test_sa1016_multi_fresh_case.py: 23 passed.
- SA10.14/15/16 transaction/admission regression tests: 16 passed.
- git diff --check: PASS.
- Phase 14 fragmentation threshold remains 0.2.
- Existing Feature Survival, face/anatomy/topology, source-authority and provenance hard gates were not relaxed.

## Boundary
Fuwawa-Abyssgard remains a separate Phase 7 visual-break family and is not claimed repaired here. A new untouched external holdout was not promoted in this patch; the next handoff starts from source-silhouette/anatomy preservation because the production GC001 review exposed a higher-priority structural failure (face geometry drift and arm disappearance) that existing hard gates do not yet reject.
