# SA7.17 High-Resolution Geometry Re-evaluation — 2026-10-06

Status: FAIL / SA7.14 GEOMETRY WITNESS RETIRED

SA7.16 repaired the corpus before this run. GC001 was not used.

Positive high-resolution source results using the frozen SA7.14 witness:
- Friend-A eyeglasses: paired=false, bridge=true, best score 0.480760
- Hyakuto Kyoko forehead goggles: paired=false, bridge=false, no valid pair
- Kaela Kovalskia forehead goggles: paired=false, bridge=false, best score 0.488105

Required frozen pair score remains 0.62. No threshold was lowered.

Conclusion: thumbnail resolution was not the sole cause of SA7.14 failure. The closed-pair geometry assumptions are too narrow across ordinary glasses and forehead goggles. Retire SA7.14 as semantic evidence. SA7.15 remains safety-only filtering.

Next: SA7.18 re-evaluates the already cached Grounding-DINO+SAM stack on the corrected high-resolution corpus with the previously frozen generic eyewear vocabulary. No new model download and no GC001 tuning.
