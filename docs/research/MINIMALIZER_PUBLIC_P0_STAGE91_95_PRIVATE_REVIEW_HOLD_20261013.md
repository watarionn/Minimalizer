# MinimalizerPublic StructuralRecovery P0, Stages91–95 (2026-10-13)
Research only. PR #390 remains Draft, Golden HOLD. No main, Local, ordinary Public, Stage51 or production changes.

## Stage91: private offline original-image manual review surface
`web/static/public-offline-human-review-p0.mjs` creates **PRIVATE local HTML files** from independently SHA-pinned original GC001/Raden 340x340 RGBA. Source-free UI code is committed; HTML embedding original bytes stays only in PRIVATE Drive ZIP. The workspace has source-only zoom (1–8x), pan, hand-drawn 10-class untrusted labels, erase, undo/redo, 121-tile navigation, JSON RLE export/import, and two-draft comparison. It verifies original source SHA256 in Chrome and rejects cross-case/source changes, forged approval and nonopaque pixel labels. The image itself is never edited. UI drafting does not count as human semantic truth.

## Stage92: cryptographic receipt transport
`public-human-review-provenance-p0.mjs` uses externally supplied public P-256 key SPKI and SHA256 pin to verify a signature covering case, original RGBA and PNG SHA, Stage82 packet SHA, complete label SHA and key SHA. Tests verify a genuine generated key/signature and reject forged, swapped or altered receipts. **Public-key possession and two distinct signing keys do not prove two independent human identities.** No real human reviewer was enrolled.

## Stage93: fullframe ambiguity ledger
`public-human-review-dispute-map-p0.mjs` independently validates two source-bound untrusted drafts, checks every pixel in 32px source tiles, and counts all matches/disputes/abstentions. A synthetic test confirms 1,024 disputed original-grid pixels, not only the first-512 preview. Original RGB high-contrast edges are review priorities, never anatomy prediction. Duplicate drafts are rejected.

## Stage94: real Chrome private reviewer
Both SHA-pinned original GC001/Raden HTML review files opened through offline file URLs in actual Google Chrome. Functional proof covers creating a label, exporting a draft, reimporting RLE, rejecting mismatched source SHA and transparent labeling, and distinguishing unmatched reviewer authority. **2/2 browser cases PASS**. Screenshot PNG, original-embedded HTML and replay JSON/script are PRIVATE Drive only. No physical iPhone Safari or HTTPS test.

## Stage95: research test/CI and archive
`tests/js/test_public_human_review_stage91_95_p0.mjs` adds **14 local Node tests** and workflow registration. Actual GitHub Actions run 38268814585 / job 114877682712 on code SHA c6190031b0d12e6ae6246b9f4763a0b069bd5120: 475 PASS, 0 failures, 0 skipped (Stage90 had 461 tests). Public repo only has source-free code/tests/docs. Remaining BLOCKERS: 0 independently human-reviewed semantic pixels, 0 externally authenticated reviewer identities, unknown person/background/arms/sleeves/hair/necktie human Golden, Stage8 whole-character vertex budgets GC001 3604>1887 and Raden 2370>1412 FAIL, physical iPhone Safari and rollback untested.

Next Stage96+: real authenticated independent humans label GC001 and Raden entire original, independently adjudicate conflicts, then opt-in whole-body source-exact SVG budget and Safari/rollback tests. **No merge or product release.**
