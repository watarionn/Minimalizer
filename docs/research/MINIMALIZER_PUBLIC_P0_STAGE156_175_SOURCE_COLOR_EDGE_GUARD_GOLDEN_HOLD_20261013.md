# MinimalizerPublic StructuralRecovery P0 Stages156–175: Original Source Color Edge Protection (GOLDEN HOLD)

2026-10-13 JST. Repository `watarionn/Minimalizer`, Draft PR #393 on `research/minimalizerpublic-p0-stage136-155-20261013`; main is source of baseline, no merging. No edits to existing Public converter, Local Minimalizer, Stage51, Stage135 opt-in public page, main or production. No generative or missing-pixel fill. **Original source color edges are not independently human-reviewed subject outlines.** Color-only metrics cannot prove body, hair, hands, face blank or background identity.

## 20 completed engineering steps

- **156** Full original-source SHA and proposal RLE validation for RGB edge evidence (`public-source-edge-fidelity-p0.mjs`).
- **157** Whole-image source alpha membership conservation, painted pixels only where source=255 and untrusted labels permit; excludes false background and face proposal labels.
- **158** True original RGB directly compared to rendered candidate RGB, no ignoring color errors.
- **159** Independent per-selected-pixel RGB L1 / SSE / max / percentile and changed-pixel totals, cross-checked with Stage136 candidate.
- **160** Original-vs-rendered 4-neighbor high-contrast source RGB edge retention: retained, lost and artificial counts with conservation checks, no semantic edge certification.
- **161** p95 and mean per-original-selected-pixel error.
- **162** Full-original tile priority review agenda, all tiles counted (may return a prioritized viewport subset), **0 verified human reviewers**, zero inferred body labels.
- **163** `public-source-edge-guard-p0.mjs`: original-source RGB endpoint locks across actual high-contrast adjacent pixels of the same untrusted role, retaining only source-observed colors.
- **164** Source-selected alpha mask and original source RGB binding preserved exactly, no new pixels.
- **165** Source-high-contrast edge endpoints restored to exact original color, verified 0 high-contrast original edges lost at chosen threshold.
- **166** Restoration only changes selected output pixels to original RGB and must not increase total original-source RGB mismatch/L1 over Stage136 palette baseline.
- **167** Binary transparent/opaque alpha and no off-mask fill.
- **168** Role-safe exact rectangle SVG construction and byte/vertex metrics, deterministic replay.
- **169** Complete SHA/structure/bitmap rejection of tampered source/color/approval metadata.
- **170** No promotion to human semantic truth or product via JSON flags.
- **171** Explicit edge threshold and rectangle budget gate. Invalid options fail closed.
- **172** `public-source-edge-frontier-p0.mjs`: finite 3-option edge-color/vertex comparison, fixed original source identity.
- **173** Exact numeric budget selector can reject entire grid and cannot claim global optimum or release.
- **174** SHA-pinned original GC001/Raden private Chrome replay at **340 and 680** with three palette variants for each original, **12/12 SVG pixel/alpha replay PASS** including honest original RGB differences and no original color edge loss.
- **175** New tests, standalone research CI, GitHub and Google Drive artifact preservation, human Golden HOLD.

## Real GC001/Raden source evidence: same untrusted partial arm-owner proposals, not whole characters

Originals GC001: **9,160** selected candidate source pixels; Raden: **20,177**. Owner masks are historical source evidence, NOT independent human-reviewed person ownership. Selected source-only pixels must have original alpha255 and skip original historical face/background masks. Source RGB differences below are **real mismatches with original RGB**, not renderer defects.

| Case | Tile / observed colors | Baseline changed original RGB | Edge-guard changed original RGB | Baseline vertices | Guard vertices | Guard SVG bytes | Lost high-contrast original color edges |
|---|---|---:|---:|---:|---:|---:|---:|
| GC001 | 32 / 2 | 6,991 | **3,437** | 4,000 | **17,192** | 158,581 | **0** |
| GC001 | 16 / 4 | 6,588 | **3,202** | 7,940 | **18,032** | 163,390 | **0** |
| GC001 | 8 / 8 | 5,258 | **2,649** | 15,188 | **20,444** | 181,016 | **0** |
| Raden | 32 / 2 | 18,052 | **15,242** | 8,568 | **18,980** | 136,831 | **0** |
| Raden | 16 / 4 | 16,805 | **14,122** | 22,976 | **29,612** | 181,251 | **0** |
| Raden | 8 / 8 | 12,730 | **10,628** | 43,268 | **46,348** | 266,012 | **0** |

The edge guard decreases wrong-original-RGB counts and protects threshold-defined original color transitions, but can **increase rectangle vertices dramatically**. None of these represents or satisfies the historical **complete-character** vertex budget. True historical Stage8 fullbody baseline still GC001 **3,604>1,887** and Raden **2,370>1,412** (FAIL). Avoid calling palette/RGB edges actual anatomical silhouette or hair outline. The finite grid is not globally optimal. Original RGBA may contain opaque backdrop and nonperson pixels. **Independently human-certified semantic pixels: 0.**

Browser 12/12 means Chrome SVG exactly recreated the *computed, not fully original RGB* output on selected pixels, including at DPR2. It does NOT mean RGB equality everywhere, full body shape or physical iPhone Safari verified. Positive approval flags are systematically vetoed. `tests/js/test_public_stage156_175_p0.mjs` adds 32 Node tests to Stage155 564, expected total **596**; confirm *actual GitHub Actions logs* before declaring remote PASS.

Original source masks and derived SVGs retained ONLY in private Drive ZIP under `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage156_175_20261013`. Public GitHub contains only generic source-free JS/tests/docs. PR #393 **Draft/Golden HOLD**, no merge or production. Next Stage176+ requires real independently enrolled people and source original-frame wholebody annotations, then genuine scene outline budget and human visual Golden and real device/rollback verification.
