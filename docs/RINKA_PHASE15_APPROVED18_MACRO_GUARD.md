# Phase 15: Approved 18 Macro Subject Guard

Phase 15 turns the 18 approved geometric-minimal portraits into an explicit regression target for `rinka_reference`.
The implementation remains AI-free and deterministic.

## Goals

1. Preserve the large subject silhouette before aggressive simplification.
2. Create one blank face plane even when explicit face metadata is absent.
3. Keep the Approved 18 inputs/references addressable through a checked manifest.
4. Expose a dedicated `approved_reference` preset.
5. Re-run all 18 source images and report structural regressions.

## Macro Subject Guard

`minimalize_engine/macro_subject_guard.py` builds coarse head, torso, and optional arm anchors from the existing deterministic subject mask.
It does not introduce a detector or learned model.

Phase 15 can recover additional portrait candidates from:

- the existing opaque-subject rescue mask (`phase15_opaque_rescue`), or
- a conservative border-connected background recovery (`phase15_relaxed_border`).

The latter is what allows the Koganei-Niko regression image to participate without a character-specific exception.

## Faceless fallback

`minimalize_engine/face_plane_fallback.py` estimates one source-colored face carrier from the upper subject region.
It intentionally creates no eyes, mouth, nose, or other facial features.

The final color selection prefers a bright warm YCrCb source cluster in the head window so hair colors do not become the face plane.
For the Approved 18 preset, this fallback is preferred even when the older Phase 12 face anchor is available.

## Approved 18 manifest

`tests/assets/approved18_manifest.json` records:

- the 18 source file names and SHA-256 values,
- the 18 approved reference file names and SHA-256 values,
- Google Drive folder ID `1oWUtdUAfLE4x8_T5VS5GQyHEHn7FQ35v`, and
- the fixed regression generation settings.

The approved images themselves are not committed to GitHub.
`tools/evaluate_approved18.py` accepts local source/reference directories and validates them against the manifest before evaluation.

## Dedicated preset

`approved_reference` is available through the engine and Web UI.
Unlike the general `geometric_poster` preset, it directly preserves the coarse subject color planes instead of running them through the full generic cleanup stack.
This avoids re-fragmenting already-good portrait masses.

## Approved 18 regression result

Latest local evaluation with `level=4`, `analysis_max_side=320`, and `preset=approved_reference`:

- evaluated images: 18/18
- Macro Subject Guard enabled: 18/18
- blank face carrier present: 18/18
- Phase 15 face fallback created: 18/18
- structural gate pass: 18/18
- mean output shape count: 17.50

Visual review shows a large improvement over the Phase 14 outputs: the blank face area, major hair mass, torso, arm gesture, and source palette now survive on the full set.
The result is intentionally coarse. It is a regression baseline, not a claim of pixel similarity to the hand-approved images.

## Validation

Local checks are required because metered GitHub Actions must not be used for this repository.

- targeted Phase 15 / target-style / Web tests pass
- `python -m compileall -q minimalize_engine web` passes
- `node --check web/static/app.js` passes
- `git diff --check` passes
- repository-wide pytest reaches 277 passing tests; the only two failures are the pre-existing tests that require the absent `tests/assets/false_face_phase85.png` fixture
- real Uvicorn `/api/info` smoke reports Web `0.11.0`, Rinka `phase15`, and the `approved_reference` preset

No generated Approved 18 images are intended for source control. Only code, tests, manifest, evaluator, and documentation belong in the Phase 15 pull request.
