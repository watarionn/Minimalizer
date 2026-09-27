# ZeroBase Phase 5 - Importance Engine

Status: CLOSED

## Scope
Phase 5 assigns inspectable preservation importance to reconstructed canonical regions.
It does not analyze pixels, classify material/color, fit primitives, prune regions, or render output.

## Contracts
- ImportancePolicy owns dimension weights, semantic priors, identity roles, and tier thresholds.
- ImportanceDecision exposes semantic, subject, spatial_mass, confidence, identity_accent, score, tier, and rationale.
- ImportanceEngine consumes canonical Scene/Region/Subject data only.
- apply() returns a new Scene and preserves the source Scene unchanged.

## Determinism
Decisions are sorted by descending score then region_id.
All score dimensions are clamped to 0..1 and score calculation uses explicit persisted weights.
Unknown semantic roles receive a neutral prior instead of implicit rejection.
## Preservation policy
Default dimensions intentionally separate large visual mass from semantic and identity value.
Identity-bearing accents can remain important even when spatially small.
Subject membership is explicit rather than inferred from analyzer-specific output.
Tiers are advisory preservation decisions: disposable, preserve, protect.
Later phases may consume these decisions but must not erase their inspectable breakdown.

## Verification
- ZeroBase suite: 26 passed
- real SLIC -> EvidenceFusion -> RegionReconstructor -> ImportanceEngine: PASS
- input-order/replay stability: PASS
- source Scene immutability: PASS
- production import boundary remains isolated
- git diff --check: PASS

## Phase 5 closure
No user-blocking decision remains.
Phase 6 may consume importance values and decision provenance for Palette & Material reduction.
Material/color evidence must remain independent from preservation importance and must not rewrite Phase 5 rationale.
