# SA10.20 Topology preservation — 2026-10-07

Status: IMPLEMENTED / READY FOR REVIEW

SA10.20 strengthens the existing SA10.18 hard gate while retaining SA10.19
source-derived contour evidence as diagnostic-only. The structural report now
records deterministic 8-connected component counts, hole counts, and Euler
characteristics for every semantic part and for the union of all parts.

The source Phase 5 semantic graph remains authoritative. Every source-derived
adjacency/attachment relation with confidence at least `0.5` must remain in the
candidate graph. A detached arm, component split/merge, candidate-only hole,
removed source hole, or changed Euler characteristic is a topology hard fail.
No threshold was weakened, no case-specific branch was added, and no repair or
generated visible content is performed.

Verification:

- Synthetic SA10.20 regressions cover an arm component split and source-hole
  removal/Euler change as hard failures.
- Existing SA10.18/SA10 regression, ZeroBase, compileall, and deterministic
  artifact checks remain required before closure.

Next handoff: integrate saliency/perceptual metrics as observer evidence only;
source anatomy, silhouette, topology, and graph authority remain hard gates.
