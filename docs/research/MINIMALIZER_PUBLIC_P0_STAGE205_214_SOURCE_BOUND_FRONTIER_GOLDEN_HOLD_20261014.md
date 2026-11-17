# MinimalizerPublic P0 Stages 205–214: source-only review, geometry and color frontier

2026-10-14 JST. PR #393 **Draft**, Golden **HOLD**, no production or Local Minimalizer modification.

## Stage-by-stage implementation

These stages deliver tested **engineering research**, not completion of human semantic approvals:

| Stage | Implementation / measured scope | Verification / authority |
|---|---|---|
| 205 | Complete opaque pixel ledger for agreement, boundary disputes, part taxonomy, abstention and uncertain. Ordered A→B confusion counts; no inferred ground truth. | 340×340 private source SHA-checked; no automatic approval |
| 206 | Deterministic 32×32 manual-review tile worklist, weight background-ownership risk without suppressing small conflicts. | 121 original tiles, exact unresolved-pixel coverage |
| 207 | Individual original-RGB witnessed pixel adjudication packet; reject missing reason, wrong RGB, already-agreed index, duplicate or nonopaque pixel. | Candidate only; **0 human-adjudicated pixels** produced |
| 208 | SHA-pinned immutable reviewer correction audit A-v2/B-v2 with class transition statistics. | Previous A/B originals remain unchanged; no v2 reviewer file fabricated |
| 209 | Per-role exact SVG contour from **agreement proposals only** (hair/face/skin/sleeve/garment/neckwear/accessory). Evenodd, no overlap. | Source pixel replay exact, no external image generation |
| 210 | Comparable numeric baseline: rectangle vs union contour vs per-role contour of same observed pixels. | Full-body numeric vertex cap still **FAIL** |
| 211 | Role-scoped palette of sampled original RGB values, finite palette experiment with true per-pixel RGB L1 loss and mismatch counts. | Zero invented color; lossy 4-color choice is **NOT** original-color preservation |
| 212 | Explicit non-generated eyes/nose/mouth policy and face-region-only diagnostic. | No synthetic facial detail |
| 213 | Fail-closed readiness report requires original preservation, human adjudication, full-body Golden, vertex budget, real iPhone, rollback and owner release. | Automatic release **always false** |
| 214 | Machine-readable source-free checkpoint and human-readable handoff with PR, CI, unresolved gates and next actions. | No original pixels, private label arrays or original-derived SVG in GitHub |

Code: `web/static/public-stage205-214-evidence-frontier-p0.mjs`
Tests: `tests/js/test_public_stage205_214_p0.mjs` (20 new PASS).
Updated workflow: `.github/workflows/minimalizerpublic-p0-research.yml`.
GitHub Actions run: https://github.com/watarionn/Minimalizer/actions/runs/38536860562, head `d0b5ce686d68845438679687e129d0489f8cc085`: **698/698 PASS, fail 0**.

## Actual PRIVATE original-source measurements

Original SHA and both reviewer-file digests were independently revalidated in an owner-local private audit. A/B independence was verbally confirmed by the operator, not verified through software authentication. Each original is 340×340: 115,152 fully opaque, 448 nonopaque; the 448 source-nonopaque pixels have zero semantic proposals. No original or A/B file was modified.

| Metric | GC001 | Raden |
| --- | ---: | ---: |
| Agreed-person proposal pixels | 47,448 | 47,888 |
| Agreed-background pixels | 60,632 | 44,574 |
| Background-ownership conflicts | 1,589 | 1,297 |
| Part-classification conflicts | 3,466 | 21,074 |
| Unreviewed/abstained opaque pixels | 2,017 | 319 |
| **All unresolved opaque pixels** | **7,072** | **22,690** |
| Exact rectangle vertices (Stage203) | 6,292 | 3,532 |
| Exact union-contour vertices (Stage204) | 4,588 | 2,436 |
| **Exact seven-part contour vertices (Stage209)** | **4,832** | **2,546** |
| Historic whole-body vertex cap | 1,887 | 1,412 |
| Unverified stage-211 4-color/role preview: RGB mismatch of agreed-person pixels | 40,562 | 45,759 |

The limited 4-color/role palette loses many original RGB pixels. It is a measurement of loss, **not** permission to overwrite original colors. All exact contours in this comparison reflect *incomplete and untrusted agreed-person masks*, so these numbers are **not** a completed full-body benchmark. Raden's largest taxonomy disagreement is garment vs sleeve: 17,772 pixels; GC001 garment vs accessory: 2,390 pixels. Human adjudication of those and smaller discrepancies remains pending. A and B agreeing still does **not** establish semantic truth.

## Privacy & storage

The owner-only source-derived evidence ZIP is in Google Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/Stage205_214_Private_20261014`:
https://drive.google.com/drive/folders/1ZLfnIQy6W4A0q0tu6q7uq45G5wuhx6lj

Private archive SHA256: `fba3c929f85a0808fe5e655a5077d7bede3e4264ce711f8d2acdc42e650a51a4`.
Archive contains only private aggregate audit, explanatory scripts, color-coded disagreement images, not A/B originals; scripts require original private archives. Never publish these diagnostic images, labels or original source-derived data to GitHub, production, or CI.

## Status / next blocking work

1. Private human source-image adjudication of every unresolved opaque pixel, including separate versioned A/B v2 if corrections required. Do not silently adopt A/B on region size, color or majority.
2. Obtain a complete validated semantic wholebody, then rerun exact silhouette and the **true** final contour budget. Existing Stage8 caps fail, as do current incomplete candidate representations.
3. Improve source-derived interior colors, clothing layering and neckwear *without hallucinating absent source features*, quantify source RGB distortion.
4. Physical iPhone Safari test; full regression; actual deploy/rollback rehearsal; independent Golden visual signoff and explicit operator release decision.
5. Keep PR #393 Draft, Golden HOLD, Local Minimalizer and main/live public untouched until all gates pass.

**Ten engineering stages implemented and tested. Human Golden and production remain unapproved.**
