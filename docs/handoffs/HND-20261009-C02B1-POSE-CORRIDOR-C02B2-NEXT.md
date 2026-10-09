# C02b1 to C02b2 handoff: source pose confidence HOLD (2026-10-09)

## Verified state

- Campaign issue #321, prior C01 merged PR #323, C02a merged PR #325. C02 still **IN_PROGRESS**. Stage8 and human Golden HOLD; C05–C08 production BLOCKED. Do not mutate production or signed original assets.
- The actual original GC001 Phase03/04 snapshot is privately archived SHA-pinned in Drive `chatGPT及びCodex用/Minimalizer/Campaign_SA1060_to_Production_20261009/C02_Phase03_Phase04_Provenance_20261009`, https://drive.google.com/drive/folders/1g3jckoCVzxLDKVW_cJ6ukhBMiVtlkMeY . Source full image exists in prior signed Drive archive and is bound by SHA. Reuse this Drive instead of repeated RDC calls.
- C02a corrected the *earliest examined* exact background-RGB overlap from Phase04 to Phase03. Stage04 historical-left-masks version drift 385px; never alias.
- C02b1 recovered original `rtmlib` COCO17 right shoulder/elbow/wrist pose. Three versions prune-only within frozen right-arm mask, 3,096/3,823/4,551 pixels retained; all remove 533 exact-background-connected RGB matches without fragmenting arm support. However wrist confidence **0.462252 <0.60**, so **pose corridor FAIL/HOLD** even though 9/9 engineering tests PASS, no Golden/true SVG budget/Chrome/independent Raden yet.

## Next C02b2

1. Obtain a stronger independent arm / garment / flowing-hair owner cue, preferably segmented source-observation masks/edges with confidence tied to original source and model provenance; no img2img, generative fill, or facial microfeatures. Use C02a source snapshot and pinned original, not mutable workspace.
2. Cross-case Raden and additional independent source controls, check optical/semantic class confusion. Reject a low-confidence wrist-only solution or per-character manual polygon patch.
3. Build a reversible source-signed mask+SVG research candidate in isolated private Drive, real Chromium baseline and delta, original Stage8 ring and expanded SVG vertices accounted independently, face/hair/arms/silhouette and material boards for human review. No production promotion without source integrity and Golden.
4. In parallel C03 can study alternative original source-ring encoding or prepare **explicit** versioned policy decision; archived signed original Stage8 failure remains unchanged. C04 human review cannot self-certify.

Code: `tools/research/sa1060d_pose_arm_source_corridor.py`, `tests/zerobase/test_sa1060d_pose_arm_source_corridor.py`, `docs/research/SA1060D_C02B1_POSE_CORRIDOR_RISK_20261009.md`, `docs/research/evidence/sa1060d_c02b1_coordinate_free_20261009.json`. Report is *non-promoting research*, not C02 completion.
