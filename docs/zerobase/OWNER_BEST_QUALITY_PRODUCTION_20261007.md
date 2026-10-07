# Owner Best Quality Production

Date: 2026-10-07

## Goal

The owner's production use must execute the highest-quality currently authorized Minimalizer route, not merely the newest static frontend.

## Route order

1. ZeroBase2 Phase 3-12 production pipeline authorized by the Phase 14 closure.
2. Local high-quality Minimalizer 2.0 when ZeroBase2 fails closed for the input or route.
3. Browser Fallback v12 only as a last-resort availability path.

Browser fallback is never labeled as best quality.

## Durable authorization

Local Worker falls back to the tracked production authorization manifest at config/production/zerobase2_phase14_authorization.json.

That manifest is bound to Phase 14 closure SHA-256 3f2ee1c2e17caaa832ca266a8816f5457707b3e4cc25ced2cc6ccee5ad442d5a.

An explicit MINIMALIZER_PHASE14_CLOSURE path still overrides the tracked manifest, and a local closure artifact is preferred when present.

## Runtime evidence

ZeroBase2 owner responses expose `quality-tier=best`, `engine=zerobase2-reviewed-sa10-phase12`, `semantic-profile=reviewed-sa10`, `provenance=reviewed-sa10-phase3-12+phase14-gate`, and `route=zerobase2`.
Local V2 fallback exposes `quality-tier=high`. Browser fallback is visibly marked `FALLBACK`.

## Production requirement

A release is not complete until the deployed owner Local Worker is on the same GitHub production baseline, `/health` reports `active_production_route=zerobase2` and `best_quality_profile=reviewed-sa10`, a real source returns `X-Minimalizer-Route: zerobase2` and `X-Minimalizer-Semantic-Profile: reviewed-sa10`, and the Shin UI identifies the actual route used.

## 2026-10-07 verification

The reviewed profile is a generic frozen semantic profile, not a case-name branch. The current profile remains available for research and future promotion.

- Hyakuto-Kyoko reproduced the reviewed SA10.13 final exactly from the original source: `84022e48e13ed7a80f8e3425d085d311e3ab7c86fcb28278ba079e182a33646a`.
- Kyoko Phase 4, Phase 10, and Phase 11 reviewed artifacts also reproduced their canonical SHA-256 values exactly.
- Juufuutei-Raden was evaluated as a cross-case check. Its reviewed profile candidate passed every Phase 14 machine gate: fragmentation `0.0`, silhouette `0.990181`, identity retention `0.975258`, major-color-mass consistency `0.8032293438911438`.
- The Phase 14 fragmentation maximum remains unchanged at `0.2`.
- Focused production/profile/browser/semantic regressions: `118 passed`.
- `git diff --check`: PASS.

Evidence is preserved under the canonical Drive hierarchy:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/OWNER_BEST_QUALITY_20261007`

Drive folder ID: `1mgaVzRaMxS4NDx5LQ2Zhej_SQTp0pvp4`.
