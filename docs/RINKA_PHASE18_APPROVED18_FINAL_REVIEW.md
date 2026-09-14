# Phase 18 Approved 18 Final Review

Date: 2026-09-14
Branch: `feature/rinka-phase18-reference-rendering-20260913`
Reviewed head before closure: `6942c01`

## Purpose

This is the final Phase 18 production-promotion gate.
It compares the fixed Approved 18 corpus across four views:

1. original source image,
2. current Phase 16 production `approved_reference`,
3. Phase 18 structure candidate containing Checkpoints 1-4, and
4. the hand-approved geometric reference.

The generated comparison images remain local and are not committed.

## Corpus integrity

The 18 source images were reacquired from the official Hololive talent pages.
All 18 source SHA-256 values match `tests/assets/approved18_manifest.json`.

The 18 approved references were reacquired from the fixed Google Drive folder.
All 18 approved-reference SHA-256 values match the same manifest.

Therefore the final review uses exactly the locked Approved 18 corpus.

## Production-path sanity check

Phase 16 and the current `approved_reference` production path were rendered with:

- `level=4`
- `analysis_max_side=320`
- `preset=approved_reference`

Both pass the structural gate on 18/18 images with mean shape count 18.333333.
Their PNG outputs are byte-identical on 18/18 images, and the production metadata still reports `version=phase16`.

This confirms that the Phase 18 Checkpoint 1-4 renderer is not yet wired into production.
The correct Phase 18 candidate path is the structure renderer used by `tools/render_phase17_structure_candidate.py`; despite its historical filename, it calls the current Phase 18 `build_alpha_structure_shapes()` implementation.

## Phase 18 candidate closure

The Phase 18 candidate rendered successfully on 18/18 Approved images.
Its SVG output contains 9-17 subject polygons per image, mean 12.166667, excluding the background rectangle.

Compared with Phase 16, the candidate is visibly cleaner and more aggressively geometric.
Faceted blank faces, directional hair planes, characteristic torso accents, and selected hand/prop masses are present where their gates accept them.

## Visual review against the Approved 18

The candidate is not yet close enough to the hand-approved grammar for production promotion.
The dominant blocker is no longer polygon noise; it is loss of pose and identity-bearing structure.

Observed failure families:

- raised arms and hand-to-face/head gestures collapse or disappear on several references,
- long or lateral hair masses are compressed into head-adjacent blocks,
- torso and sleeve geometry is often reduced below the level needed to read the original pose,
- important outfit partitions are missing even when their colors survive,
- prop recovery remains intentionally conservative and therefore does not cover all approved identity cues,
- several candidates read as a bust/icon rather than the full approved silhouette.

Examples include Koganei-Niko, Todoroki-Hajime, Shishiro-Botan, Natsuiro-Matsuri, Momosuzu-Nene, Kobo-Kanaeru, Hakos-Baelz, and Gigi-Murin, where raised-arm gesture is a major part of the approved reference.
Kikirara-Vivi also demonstrates insufficient retention of the large twin-tail silhouette.
Otonose-Kanade demonstrates over-compression of the body/arm composition.

Phase 18 therefore improves geometric cleanliness but currently trades away too much structural identity.

## Production promotion verdict

**NO-GO for production promotion.**

Do not replace the Phase 16 `approved_reference` production renderer with the current Phase 18 candidate.
The Checkpoint 1-4 implementation should remain available as the experimental structure path.

The next implementation target should preserve Phase 18's coarse, straight-edged visual grammar while restoring large pose carriers before any further detail is added.
Priority order:

1. retain both major arm/forearm gesture masses when they materially define the silhouette,
2. retain large lateral hair/twin-tail/ponytail masses,
3. preserve torso-to-sleeve overlap and the dominant outfit partitions,
4. then re-run the locked Approved 18 comparison before production wiring.

No production code path was changed during this final review.
No GitHub Actions execution is required for this documentation-only closure.
