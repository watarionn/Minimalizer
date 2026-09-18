# Minimalizer 2.0 Mainline Integration

Updated: 2026-09-18
Status: locally validated, ready for remote review/merge
Base main commit: `9c61773f10547f6dc5ab8bb2e0d61e1be1a31430`
Integration branch: `integration/minimalizer-2-analysis-guidance-mainline`

## Why this branch exists

The historical Minimalizer 2.0 V2 development branch and current `main` no longer share a useful merge base.
Directly merging the historical branch would therefore risk replaying obsolete history over the Phase 18 mainline.

This branch starts from current `main` and reintroduces the validated V2 namespace and browser migration contract as additive mainline changes.

## Integrated scope

- full `minimalize_engine/v2/` namespace
- Calibration 05 V2 contracts and regression coverage required by the current implementation
- Calibration 06 provider-independent `AnalysisGuidance`
- rembg foreground guidance with `isnet-anime` and confidence power `2.0`
- MediaPipe optional semantic guidance
- Grounded-SAM optional semantic gap guidance
- V2 opt-in Web endpoint
- browser Standard PNG default routing to V2 with compatibility fallback
- V2 CLI shadow PNG
- browser/CLI/V2 regression tests
- local CI definition brought forward to the already established Phase 16 target-style contract and V2 smoke

## AI / ML contract

Generated image content is not introduced.

- rembg is foreground authority
- MediaPipe is optional lightweight semantic evidence
- Grounded-SAM is optional higher-cost evidence for hair, face-skin, limb, and accessory
- all provider masks are guidance only
- final geometry and rendering remain Minimalizer-owned
- semantic hard pairs remain disabled
- YOLO remains deferred

## Validation on current mainline

V2-focused regression:

`195 passed, 334 deselected, 1 warning`

Full repository regression:

`527 passed, 2 failed, 1 warning`

The two failures are the pre-existing missing fixture only:

- `tests/test_character_face_geometry.py::test_rejected_face_skips_face_geometry_quality`
- `tests/test_character_quality_retry.py::test_rejected_face_is_not_penalized_as_missing_face`

Both fail because `tests/assets/false_face_phase85.png` is absent.

Phase 16 retained safety evaluation completed on the integrated tree and the workflow assertions passed locally.

Local real-server smoke also passed:

- `/api/info`
- `/api/v2/info`
- legacy Standard SVG route
- browser-default Standard PNG -> V2
- Rinka Reference -> legacy
- Color Strip -> legacy

The browser-default V2 request reports:

- `X-Minimalizer-Route: v2`
- `X-Minimalizer-Configured-Analysis-Max-Side: 400`
- `X-Minimalizer-V2-Preset: minimal`

## Merge safety

This integration deliberately does not copy the historical branch''s `MINIMALIZER_2_CURRENT.md` or `MINIMALIZER_2_HANDOFF.md` because those files describe the obsolete detached development history rather than current mainline state.

Remote publication should use this integration branch, not the divergent historical V2 branch.
