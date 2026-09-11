# Rinka Reference Phase 16: Approved 18 Identity / Structure

Phase 16 starts from merged Phase 15 main `155db1ffc4e0c2ab1911db747a1930cacf613bb7`.
It uses the 18 user-approved geometric references in Google Drive as the formal visual regression set.

Reference folder ID:
`1oWUtdUAfLE4x8_T5VS5GQyHEHn7FQ35v`

The fixed evaluator run remains:
- level: 4
- analysis max side: 320
- preset: `approved_reference`

## Goal

The main Phase 15 failure was not simply too many small polygons.
Several portraits lost pose / body layout because a rejected subject mask could outrank a safer rescue, and the direct approved-reference path did not render its macro subject anchors.

Phase 16 therefore prioritizes:
1. correct portrait-mask selection;
2. head / torso / arm macro structure;
3. blank face + limited fringe layering;
4. major identity colors;
5. coarse shape count near the approved examples.

## Accepted implementation

### Candidate-mask precedence

`phase15_subject_candidate()` no longer treats RGBA/mask presence as acceptance.
The order is now:
1. accepted Phase 10 segmentation;
2. safe accepted opaque rescue;
3. relaxed-border recovery;
4. rejected segmentation only as a final fallback.

This fixes cases where `reason=confidence_gate` still became the final portrait mask even when a safer rescue existed.

### Approved-reference macro skeleton

The approved-reference direct renderer now injects the Phase 15 macro head, torso, left-arm, and right-arm anchors instead of recording them only as telemetry.
These anchors provide a coarse pose skeleton below the subject color planes.

The approved-reference subject scaffold is intentionally coarse:
- 6 color clusters;
- maximum 10 subject planes;
- contour epsilon ratio 0.052;
- macro anchors are separate protected structure.

Standard/default subject-plane settings keep their existing defaults.

### Face / fringe hierarchy

The metadata-free face fallback uses a narrower central face window and renders at z=31000.
Approved-reference rendering may promote at most two coarse fringe planes above the blank face.
Oversized upper-hair masses are not promoted directly; only a clipped face-overlapping slice may be used.

A bright-head guard rejects dark low-chroma fringe candidates when the macro head is very bright.
This removes gray shadow/line aggregation from pale-haired faces such as Otonose Kanade while preserving chromatic or genuinely dark hair cases.

### Role-aware macro colors

Macro color selection now uses source position as well as frequency:
- torso samples the central lower subject and rejects skin/background candidates;
- side arms sample outer-side pixels;
- an arm color matching the head is replaced only when that head color is not strongly dominant and a substantial chromatic alternative exists.

This restores large identity blocks such as Hakos Baelz's cyan/yellow sides and Houshou Marine's red torso while retaining genuinely dark sleeves.

### Identity-color and gesture representatives

Approved-reference mode can preserve local light tones for large non-skin white/gray components so a bright clothing plane does not inherit the face cluster color.
Central lower-body bright components receive a small identity bonus.

Color-representative protection is limited to chromatic clusters with enough area.
Neutral gray/black clusters are not kept merely to satisfy color diversity.
This retains useful gold/brown accents without displacing larger neutral structure on Raora, Vestia, or Kobo.

A separate upper-gesture representative gate may keep one bright, large, outer-side upper-body plane per side.
It is restricted to 1-5% canvas area, upper 42% of the image, outer 30% side zones, sufficient extent, and high luminance.
These planes receive a dedicated `phase16_upper_gesture_plane` role.

This recovers pose-supporting upper-arm masses without protecting fingers or micro-detail.

## Rejected experiments

The following trials were explicitly rejected during the Approved 18 iteration:

- 7 color clusters with the same 10-plane cap: did not reliably recover Marine's white/gold cues and reduced subject coverage on key cases.
- preserving one representative for every color cluster: forced low-value neutral gray/black planes into Raora, Vestia, and Kobo.
- promoting large hair/hat masses as ordinary fringe: could hide the blank face; the regular fringe area limit is therefore 1.35x face area and oversized hair uses clipping only.
- an upper-arm bridge that unioned bright gesture planes with macro arms: candidate20 produced an oversized bright slab across Nene's head/face and was reverted.
- deleting all small planes by area: rejected because canonical hand/prop structures and meaningful accents can legitimately be small.

Do not reintroduce these experiments without new corpus evidence.

## Current fixed-set evidence

Candidate21 after reverting the failed upper-arm bridge:
- Approved 18 count: 18;
- macro guard enabled: 18/18;
- blank face carrier: 18/18;
- Phase 15 face fallback: 18/18;
- structural gate: 18/18;
- mean final shape count: about 18.33.

The Rinka Reference metadata version is `phase16`.

## Closure validation

Local closure validation on 2026-09-11:
- targeted Phase 16 / related Web suite: **78 passed**;
- repository-wide pytest: **284 passed / 2 failed**;
- both repository-wide failures are the pre-existing missing `tests/assets/false_face_phase85.png` fixture cases;
- `python -m compileall -q minimalize_engine web`: passed;
- `node --check web/static/app.js`: passed;
- `git diff --check`: passed;
- real Uvicorn `/api/info` smoke: passed and reports Web `0.11.0`, Rinka `phase16`;
- Approved 18 evaluator: structural gate **18/18**, macro guard **18/18**, face carrier **18/18**, mean final shapes **18.33**.

GitHub Actions are intentionally not used for this closure because metered Actions usage may be chargeable. Local validation is the release evidence for the Draft PR.
