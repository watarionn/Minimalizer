# SA10.60B / C01: GC001 first demonstrable arm-owner defect

Date: 2026-10-09. **C01 engineering diagnosis PASS, prototype promotion HOLD.** Stage8 original source ring policy HOLD, human Golden PENDING, Phase15 NOT RUN, production UNCHANGED. This does **not** establish a general solution or verify Phase03/05/06 internals.

## Frozen authority and source lineage

- Current release campaign `CMP-20261009-SA1060-TO-PRODUCTION`, base main `9c993cca6140036590a13e52c9faf1f5eca2379b` (PR #320).
- Original GC001 image SHA `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e` (source is RGBA; treating all pixels as opaque loses useful evidence).
- Signed GC001 Phase04 masks: right_arm `4900beccaf0ca4a9ca33600339df77976a4500f1db932fcb240a41907b935b91`, left_arm `49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f`, face `b4812364eaec7da9930a18ae85270d6612555d3fb3d80283efcf69b03aa6a72f`.
- SHA-signed Stage08 source research scene `7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08`, as stored with the approved SA10.34 research. Original Stage8 *source ring* budget is still `3604/1887`, FAIL.
- SHA-signed faceless SA10.57 SVG `bdea6fc36a953c01fe115032c10cb9313ecc900377f63954ff84bcb0392b2939`. It is verified read-only as input and was not repainted or published.
- Independent Raden source and three signed Phase04 mask SHA signatures are frozen in the attached script. All binary images and actual traced masks remain only in the private approved Drive.

## Observed first bad stage, not inferred root cause

1. A **four-connected exact RGB flood from a dominant original border color** (opaque-border anchor) identifies 35,514 source pixels. This is conservative original-image evidence, not a semantic segmentation ground truth. It operates in RGB, then checks the original alpha channel separately.
2. Among signed Phase04 GC001 pixels, background-connected exact source RGB overlaps **533 / 6,486** pixels of `right_arm`, **0 / 2,715** of `left_arm`, **0 / 4,937** of `face`. Within the 533 right-arm overlap, **520 are fully opaque** and **13 are not fully opaque**. The latter must not be casually deleted as if alpha were 255.
3. Independently rasterizing the immutable Stage08 *right_arm* rings confirms **533** of those exact connected-background RGB pixels persisted. The reconstructed Stage08 mask differs from signed Phase04 in **24 right-arm pixels**, **5 left-arm pixels**, **0 face pixels**. These are existing rasterization deltas, not SA10.60B changes.
4. Thus, the **earliest demonstrated defect in the checked Phase04→Stage08 chain is already in the signed Phase04 right-arm mask**. Phase05, Phase06, Phase03, subject segmentation, and the specific algorithmic reason for Phase04 misassignment were **not individually replayed**, so do not claim these causes have been ruled out. Stage08 did not introduce the measured 533-overlap. Existing Phase04 masks were never rewritten.
5. Raden was examined using an **independent source and distinct signed masks** with the same exact-RGB border-connected observation: right_arm **3**, left_arm **7**, face **0** pixels. This shows why an indiscriminate `remove all background colors from arm` policy would be unsafe. These overlap values alone do not authorize changing Raden.

## Isolated candidate / Diagnostic-2

A new **versioned private research candidate** removes only the 520 fully opaque, exact-border-RGB-connected source pixels from the signed GC001 right-arm mask. It adds 0 pixels, preserves the original signed left_arm and face masks, and preserves 1 connected component (6486→5966 pixels). The 13 lower-alpha RGB matches remain for independent judgement. Original SVG/Stage8 are unchanged. This is **only a potential mask correction**, not a proven anatomically accurate semantic mask or output render.

A private 4-panel diagnostic board shows signed original, source Phase04 right-arm mask overlay, Stage08 inherited ring overlay, and the isolated candidate overlay. Raw mask candidate, exact source-background pixel mask, private metrics, script/tests, ZIP/manifest and source-hash provenance are in the approved Google Drive campaign C01 folder. Public GitHub carries only this prose, generalized audit/test code, the cross-case **coordinate-free numeric** JSON, campaign progress, and the cross-chat handoff. Never commit image pixels, mask positions, Stage8 traced coordinates, or the actual private candidate.

## Verification

- **10/10 tests PASS** in repository-layout checkout analogue with real signed GC001 + Raden sources, and synthetic cases for exact color connectivity, interior disconnected duplicate colors, alpha preservation, SHA pins, role parity, fail-closed handling, isolation, and sanitized/public allowlist.
- Fresh independent re-execution: **5/5 output SHA matches** (candidate PNG, connected-background PNG, source comparison board, public metrics, private metrics).
- Both original input sets and Stage08 scene were SHA checked before creating output. No generated/AI-painted image, no source-raster embedding, no production switch and no human Golden certification.
- The earlier SA10.60A provisional arm-colour trial remains **unapproved**. C01 does not supersede it with a release candidate.

## Next C02 and parallel C03

- C02: independently validate candidate semantic arm-versus-long-hair/garment ownership; the image shows that signed `right_arm` owner also spans a source-side strand/garment-like area. Obtain Phase03→Phase04 actual stage manifests and, if available, Phase05/06 per-stage evidence to determine the **algorithmic** first cause, not just first measurable bad output. Do not infer correction solely from source background colors.
- Independently review topology of *both* arms and shoulder/sleeve/neckwear (and Raden garment/hair), signed face pixels, true SVG geometry budget, full-source Chromium before/after with deterministic SHA and extra unrelated signed holdouts before accepting a candidate into renderer logic.
- C03 Stage8 original 2370/1412 (Raden) and 3604/1887 (GC001) remain FAIL/HOLD. No waiver; actual release requires verified source-equivalent geometry or separately explicit approved versioned policy.
- C04 Golden authenticated human review and Approved-18/78 are still pending; keep Phase15, worker, production, iPhone release and browser routing unchanged until independent gates pass.
