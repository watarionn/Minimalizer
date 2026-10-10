# MinimalizerPublic R50–R51 | Signed source-owner human review handoff

2026-10-10 | Research annotation workflow implemented. **No human source-photo review has actually been supplied, no colors/owners changed and production is NO-GO.**

## R50: private original-photo owner review worksheet

Stacked on R42–R49 Draft PR #383. Read the private R44 comparison board audit and the R42 independently pending 22-owner packet. Require original GC001/Raden source-photo SHA and signed Stage8 geometry SHA from authentic SA10.34. Reopen each private R44 source/mask comparison board and verify its SHA-256 **before** generating a human-editable UTF-8 BOM CSV.

Initial worksheet has **10 priority owner rows**, 5 each: right arm, left arm, major clothing, accessory/held object, unknown. It records case, original-photo SHA, Stage8 source-scene SHA, private comparison-board file, owner and visible-mask pixel counts, independent signed Phase04 XOR where available. All manually editable fields initially **PENDING** and reviewer/date/evidence note blank.

This is a starting point for actual first-party manual review, not an annotation performed by the AI. All real PNG photo overlays and the editable CSV belong **only in private Drive**. Do not publicly commit source-derived images, original-photo coordinates or inferred label corrections.

## R51: fail-closed import verification

`scripts/verify_public_r50_r51_human_review_worksheet.py` verifies 10 original reviewer row identities, source/file SHA binding, unchanged CSV schema, no duplicate parts and allowed statuses. `PENDING` remains unapproved. If a future CSV says `ACCEPT_MASK`, `REJECT_MASK`, or `UNCERTAIN`, require a reviewer identifier, date and note. **But this is not a cryptographic signature nor verified human identity**, therefore the resulting record always states human source-owner semantics and Golden approval **FALSE**.

Seven dedicated tests PASS: initialized pending, missing role rejection, forged source SHA rejection, faux human signoff never promoting, unsigned claimed acceptance blocked, tampered R44 source/photo preview rejection and Local/Public code isolation. Combined full R1–R51 regression final test pending final independent rerun before claiming a total pass count.

## Blocked upstream requirements

- R37's browser-exact original masks do not establish anatomy, signed clothing/tie/staff labels, source-photo pixel quality or correct colors.
- R49's source-observed RGB candidates fail to consistently improve held-out spatial partitions: GC001/Raden left arm 0/4, Raden right arm 0/4.
- Face details remain formally hidden, no generated pixels, palette changes or image-to-image techniques.
- R6 eight original blocked release gates remain, including Stage8 original source-ring caps **GC001 3,604 > 1,887**, **Raden 2,370 > 1,412**, protected owner source photo semantics, full-scene resvg DPR2, human Golden, physical Safari, vendor legal and actual rollback.
- No live Public host, Local Worker, GitHub main, source image, signed original mask or signed palette is changed.

## Source and preservation

Source script: `scripts/verify_public_r50_r51_human_review_worksheet.py`
Tests: `tests/test_public_r50_r51_human_review_worksheet.py`
Private canonical Drive: `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R50_R51_20261010`, containing `PRIVATE_R50_human_source_owner_review_PENDING.csv`, numeric audit and SHA manifest.

Keep GitHub PR Draft and unmerged; actual owner edits require independently assessed human evidence, source-photo authority and separate Stage8/renderer/Golden gates.
