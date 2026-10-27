# L02 PR #445 source-free dependency closure and main drift (2026-10-27)

**A-only integration review, not a visual quality improvement.** L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / Local production NO_GO. No original images, masks, annotations, coordinates, NPZ, secrets, or model weights are included.

## Authenticated repositories and source-free archive

- GitHub main read directly: `4a4348990084848c981811b414e6221411271f84`. PR #445 remains Draft/unmerged at review head `4e89ebee028220327b4f89178375b87b77221ce2`. PRs #429/#441/#443 also remain Draft/unmerged.
- Canonical non-shared Drive: `chatGPT及びCodex用/Minimalizer`. Historical **source-free** 2026-10-23 22:53 integrated staging archive SHA-256: `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`.
- Its `MANIFEST_SHA256.json` SHA-256 is `3bbd99ebdec94247f4d4cb1a6bc0be3919f3686522ed09314dadbf66d25ff944`; **98/98** file hashes matched independently before extraction. Isolated `PYTHONPATH=source:source/tools/research python -m pytest -q source/tests` returned **235 passed, 31 subtests passed**. These are archive tests, not current-main CI or semantic quality proof.
- The archive has **98 source-free files** and a stale `local_l02_canonical_strict_signed_replay.py` with H08 composed pin `82313762...`, while its bundled guarded contact implementation SHA-256 `b49d3c0744c838715e44b7405ec0b621c8b356c1de710eff7b803ed71bc196a7` belongs to the newer `3e467694...` composed stage. PR #429 carries a separate guarded-pin repair patch; **do not silently substitute a historical pin**.

## Exact main dependency gap

Ten direct or near-direct stage/replay modules were checked against the live main via GitHub file reads. **Nine are absent** from main:

`local_l02_canonical_strict_signed_replay.py`, `local_l02_no_merge_signed_replay.py`, `local_l02_composed_dual_contact_shadow.py`, `local_l02_composed_p0_shadow.py`, `local_l02_enclosed_class32_shadow.py`, `local_l02_class30_dual_seed_extension_shadow.py`, `local_l02_class32_independent_contact_shadow.py`, `local_l02_cross_owner_selective_veto_shadow.py`, and `local_l02_source_palette_sleeve_shadow.py`.

The tenth, `local_l02_cross_owner_contact_gate.py`, **exists but has a different Git blob**: archived staging `8c17798afbd92814f2e592adbdaf53ecfab30d7a` versus main `d5c1c99b50acbe94db094675170d6f3689f50b13`. Main now imports `local_l02_frozen_owner_transition_audit` (present on main, blob `b284d5699424284d7b9d72cf62be8e7ff2306a5c`); the archive version does not. This is a **real version/contract conflict**, not merely missing files. A bulk copy of the archive onto main would bypass review of this drift and is prohibited.

## Signed replay completed in this audit

The existing non-shared Drive provided the authentic ReviewedEvidence, Run30 owner, SleeveSemantic and AnimeSeg archives. Their external SHA-256 pins and internal manifests **19/7/5** verified. Using the isolated archived source-only stage (not main), H06 was replayed: composed/strict SHA `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c`, reviewed outerwear TP **294,020**, known FP **1,077** (all underlayer), FN **20,803**, known arm FP **0**. This reproduces an inherited unresolved defect; it does not fix one. H08 replay began but did **not** complete within the execution budget; no new H08 result is claimed.

## Ship decision and next concrete work

**Accepted P0 improvements 0, P1 improvements 0; H04/H06/H08 unresolved 3.** No code is merged or promoted. Stage only a version-pinned A-only dependency closure after reconciling the main cross-owner gate with the historical staging implementation, then run full regression against signed H04/H06/H08 and independently review critical arm/underlayer/sleeve preservation. Source-only Phase4 owner exclusivity, connection and critical-part retention must PASS before Phase5. Unseen signed blind, full CI, Golden and user iPhone acceptance remain pending. Do not touch Lane B, Public/C08, LocalWorker production, or Golden.