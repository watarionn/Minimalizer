# Pose-line guidance commit boundary (2026-09-20)

Branch: `feature/pose-line-guidance-contract`
Status: calibration + integration audit closed; no main merge/deploy authorization.

## Proposed boundary
Treat the current V2 pose/line integration as one atomic feature boundary because the changes are coupled through the same data path:
RTMLib structural guide -> region annotations -> RAG structural relation;
DeepLSD line guide -> edge line support -> merge cost;
pose-aware line gate v2 -> gated line support before Region Merge.

Core implementation:
- `minimalize_engine/v2/analysis_guidance.py`
- `minimalize_engine/v2/rtmlib_guidance.py`
- `minimalize_engine/v2/deeplsd_guidance.py`
- `minimalize_engine/v2/pipeline.py`
- `minimalize_engine/v2/characteristic.py`
- `minimalize_engine/v2/types.py`
- `minimalize_engine/v2/region_merge/{types,graph,cost,hierarchy}.py`
- `minimalize_engine/v2/__init__.py`

Validation boundary:
- V2 guidance / RTMLib / DeepLSD / structural-line tests
- Region Merge cost + hierarchy tests
- exact-binding 18 and Approved-78 audit docs
- default floor=0.20 regression lock

Do not include temporary audit outputs, generated guide caches, Approved-78 hierarchy-cut worktree changes, or missing `false_face_phase85.png` fixture repair.
Full-suite state at boundary: 563 passed; 2 fixture-missing failures; integration subset 51/51 passed.
