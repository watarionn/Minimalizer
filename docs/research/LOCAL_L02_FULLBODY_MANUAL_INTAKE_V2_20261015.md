# L02 full-body manual shape intake v2: source-only semantic review guards

**Status: Engineering validation PASS, semantic authority HOLD, Local release NO-GO.**

## Canonical unchanged input

- User reference: `H04_FULLBODY_MANUAL_REFERENCE_V1`, signed original source SHA256 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`.
- Original user JSON remains unchanged, SHA256 `be03cd35f7bcd0ca56350e748d3ff784f8b40683af440a8dd732c643d8d195fb`. It has 17 polygons but their original user names are generic and **not independent semantic sign-offs**.
- The 3 source-bound jacket polygons correspond to fullbody shape numbers 3, 9 and 10 by the previously independently checked geometric overlap with the earlier user-authored 3-jacket trace. Other names are proposals only.

## Expanded intake taxonomy and safety

The research validator `tools/research/verify_local_l02_manual_intake.py` now permits the full-body visible-owner labels `outerwear`, `arm_skin`, `hair`, `underlayer`, `accessory`, `unknown`, `face_skin`, `neck_skin` and `lower_body`. Head is a structural **parent** and must not be mistaken for an exclusive visible mask on top of child hair, face or neck. The ReferenceShapeEditor shape display order remains last visible shape on top. Returning masks are clipped to the exact signed original alpha, never adding source pixels.

For final/manual-ready label intake, `face_skin/face` or `face_skin/skin` is acceptable as an undetailed facial surface; labels for `eye`, `eyelash`, `eyebrow`, `iris`, `pupil`, `nose`, `mouth`, `lip` and other face microdetails are rejected to protect the default faceless style. The edit is **research intake only**: no production renderer or LocalWorker is changed.

An explicit `alignment_audit` read-only method lists user polygons crossing the signed source alpha by more than the existing strict `1.5%` per-shape threshold. This method never relaxes the formal validator's threshold and never edits original vertices.

## Private original-source H04 result

- Existing H04 trace has **17 geometrically well-formed polygons**; separate strict per-polygon source-boundary validation flags **4/17** polygons above 1.5% underlay transparency. This is not proof that the artistic contour is incorrect, only that the strict source-alpha intake policy requires manual reconciliation or an explicitly approved clip.
- Private reviewer board and `H04_FULLBODY_OVERSHOOT_SOURCE_AUDIT_PRIVATE.json` identify the exact 4 figure-layer positions and overshoot fractions; they are **not** included here because the detailed hand-authored trace and source-containing board are private.
- A new **nonapproved editable draft** copies the original reference's geometry, colors, order and embedded signed image without modifying any of them, but replaces each generic name with a **suggested semantic label**. Only the three jacket types had explicit user confirmation; all remaining names are unchecked guesses. This draft fails the strict H04 source-boundary gate on those 4 polygons and **must not** be called Golden, human-approved, or automatically promoted.

## Tests and authority

- Expanded semantic intake and alpha overshoot tests: **26/26 PASS** including the previous 18/18.
- Source-only flip-consistency tests separately: **13/13 PASS**.
- Private reviewer source images, JSON, shape labels and pixel masks remain stored under `Google Drive/chatGPT及びCodex用/Minimalizer`.
- All signed Phase4 original masks remain unchanged, no new visible pixels, no renderer or PWA change, no C08 scheduled campaign restart.
- **L02: HOLD; Golden: HOLD; Stage8: HOLD; production: NO-GO.** Human confirmation of figure labels and 4 overshooting boundaries is still absent. Separate H06/H08 human garment labels remain absent.
