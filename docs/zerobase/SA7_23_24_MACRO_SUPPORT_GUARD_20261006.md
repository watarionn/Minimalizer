# SA7.23-24 GC001 Macro Debug and Source-Support Guard — 2026-10-06

Status: SAFETY GUARD PASS / GC001 MACRO ADOPTION HOLD

SA7.23 applied SA7.22 macro re-authoring to existing GC001 Phase-04 semantic masks without renderer integration.

Initial evidence:
- hair source area 17,541 px; proposed supported area 22,484 px (about 28% expansion)
- major clothing split into coarse masses but retained support was uneven

This blocked renderer integration.

SA7.24 added rasterized per-mass hard guards:
- maximum expansion ratio 1.12
- minimum source coverage 0.65
- conservative external-contour fallback when a convex proposal violates the guard

An initial implementation incorrectly measured each mass against the whole part area and rejected everything. It was corrected to use each semantic mass as its own denominator.

After correction, unsafe hair proposals are still rejected on GC001; only one small clothing mass survives. Therefore the guard is doing its safety job, but the convex-hull macro algorithm is not ready for adoption.

Decision: merge the safety guard, keep renderer disconnected, and replace convex macro fitting with a non-convex coarse contour strategy in SA7.25.
