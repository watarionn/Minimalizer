# Experimental Guarded DiffMin Observation

Status: experimental, default production routing remains OFF.

This phase records outcomes from explicitly guarded DiffMin runs without promoting DiffMin to the default route. Observation records are derived from retained release audits, so the monitoring layer does not need CUDA, pydiffvg, Docker, or DINO inference.

Each record captures run identity, candidate identity, effective mode, adoption/rollback outcome, rollback reason, same-renderer silhouette IoU, DINO delta when available, and kill-switch state.

## Seed baseline

Approved-18 release audit, 2026-10-04:

- candidates: 18
- adopted: 9
- rolled back: 9
- adoption rate: 0.5
- rollback reason: observer-not-improved = 9
- minimum same-renderer silhouette IoU: 0.9977261592191052
- mean DINO delta across all 18 records: 0.00013529822925117642
- kill-switch records: 0

This is a seed baseline, not a production success target. Future real-use observations should be appended as independent run IDs and compared against this baseline. Default-on promotion remains a separate Human Review Gate.

## Promotion evidence to collect

The observation phase should accumulate enough independent real-use runs to answer: whether guarded adoption remains beneficial outside Approved-18, which rollback reasons dominate, whether any hard/silhouette integrity failures appear, and whether operator kill-switch use is ever required. No single adoption-rate threshold automatically authorizes default-on routing.
