# MinimalizerPublic StructuralRecovery P0: Stages136–155 adaptive *observed-source* RGB vs geometry (GOLDEN HOLD)

2026-10-13 JST. Repo `watarionn/Minimalizer`, branch `research/minimalizerpublic-p0-stage136-155-20261013` based on main AFTER PR #390 (source-only StructuralRecovery), #391 (independent Stage135 preview) and #392 (live production documentation). **Do not change main, normal Public runtime, existing Stage135 live preview, Stage51, Local or production in this research PR**. Owner may test previous published Stage135 preview separately. No generative fill, no inferred body parts.

## Stages136–145: original-RGB adaptive palette and exact source membership
Source-free `web/static/public-adaptive-source-rgb-p0.mjs`:
1. **136:** original SHA/PNG and untrusted fullframe proposal binding via the existing robust Stage77 / Stage31 source validator; original bytes never modified.
2. **137:** allow only source alpha 255 pixels with explicit untrusted label codes (not face, background, zero/unreviewed), require pixel source membership.
3. **138:** deterministic source-only palette: every sampled RGB must literally appear among the same *original input tile and proposal role*.
4. **139:** group by source role within fixed 8/16/32/64px tiles; retain untrusted source role separate from color.
5. **140:** cap source-observed colors per tile at 1/2/4/8/16 with population-weighted farthest-first and deterministic ties; no external model, guessed RGB or generated data.
6. **141:** hard per-original-pixel RGB L1 upper bound; reject, do not misreport, if budget exceeded.
7. **142:** horizontal color+role runs with exact vertical rectangle reuse; group paths, count all 4-vertex rectangles and UTF-8 SVG bytes.
8. **143:** independently replay rectangles over *every source coordinate* to confirm no overlap, false paint, unknown source color or lost selected opaque pixel.
9. **144:** record actual wrong-vs-original RGB pixel count, total RGB L1, mean RGB L1 over selected pixels, worst per-pixel L1 and channel-wise squared sum; zero alpha of excluded pixels.
10. **145:** SHA256 bind original, proposal labels, selected pixel mask and rendered RGBA; full SVG and status checked by independent rebuild-and-verify. Every renderer and release gate remains **Golden HOLD**, even if a JSON claims approval.

## Stages146–150: finite, honest multi-objective comparator
`web/static/public-adaptive-source-rgb-frontier-p0.mjs`:
11. **146:** compare tile 8/16/32px and 1/2/4/8 source color settings on the same original-source SHA and same selected pixel membership; 12 finite candidates per case.
12. **147:** report every input option's real vertices, SVG bytes, wrong RGB pixels, mean/max/L1 errors and selected pixel count, not just a cherry-picked sample.
13. **148:** pareto filtering over **finite tested grid** (not global optimum) and no-feasible-candidate when numeric error/vertex limits are not jointly achieved.
14. **149:** reject mismatched source and mask SHA or duplicate/invalid parameter grids; finite frontier cannot claim complete scene or quality.
15. **150:** keep 0 independent human semantic pixels and **unconditional production veto** irrespective of apparent better RGB or fewer vertices.

## Stages151–153: GC001/Raden SHA-pinned ORIGINAL Chrome replay
Both full 340×340 original-source RGBA and previous Stage114 historical left/right-arm signed-owner masks are loaded from an isolated **PRIVATE** folder. Every selected original-alpha255 pixel was marked `uncertain_subject`, NOT arm skin/sleeve/person ground truth, after excluding historical face/background observations. This is an **untrusted partial-region source RGB study**, not body segmentation or full image conversion.

Stage151 **GC001:** 9,160 source-selected pixels. Stage152 **Raden:** 20,177 source-selected pixels. Each has 12 tested tile/color options and source SHA/mask identity checks. Stage153 compares 3 representative palettes at both 340 and 680 in **actual Google Chrome** for each original, totaling **12 real browser renderings**. In all 12, SVG RGBA equals independently replayed rectangle pixels exactly; any **RGB difference from the source original** is honestly counted (not silently called exact).

| Original / 1x Chrome | Tile / colors per tile | Wrong original RGB pixels (selected only) | Mean RGB L1 / selected pixel | SVG bytes | Explicit SVG rect vertices |
|---|---|---:|---:|---:|---:|
| GC001 | 32 / 2 | 6,991 / 9,160 | 68.718 | 16,844 | 4,000 |
| GC001 | 16 / 4 | 6,588 / 9,160 | 31.247 | 36,912 | 7,940 |
| GC001 | 8 / 8 | 5,258 / 9,160 | 12.077 | 93,720 | 15,188 |
| Raden | 32 / 2 | 18,052 / 20,177 | 34.489 | 36,209 | 8,568 |
| Raden | 16 / 4 | 16,805 / 20,177 | 12.346 | 99,330 | 22,976 |
| Raden | 8 / 8 | 12,730 / 20,177 | 4.044 | 215,161 | 43,268 |

Comparisons using **identical original+mask**: Stage135 exact source RGB partial rectangles GC001 27,496 vertices / 257,837 bytes / 0 source RGB wrong, Raden 67,572 / 398,021 / 0 wrong. Stage114 one source RGB for entire class GC001 880 vertices / 3,814 bytes / 9,159 wrong, Raden 924 / 4,082 / 20,176 wrong. The new sampled-tile candidates occupy a useful intermediate range, but **none of the six visual-tested partial candidates meets historical whole-character vertex budgets**, and source RGB differences are real. Do not claim a globally optimal design.

**Historic Stage8 full-body SVG remains GC001 3604>1887 and Raden 2370>1412 FAIL.** No reviewer has independently verified actual person/background/hair/hand/sleeve boundaries. Neither selected-color consistency nor alpha-only membership establishes a human Golden. The original colored image may include complex backgrounds. Human semantic labels certified: **0**.

## Stages154–155: CI and isolated preservation
16. **154:** `tests/js/test_public_stage136_155_p0.mjs` adds **31 new tests** against original SHA tampering, observed-only palette, color budget veto, exact pixel-membership/rectangles/alpha, source RGB accounting, parameter grids, finite Pareto limits, replay SHA, UI-independent release veto. Register suite in `.github/workflows/minimalizerpublic-p0-research.yml` stages1–155. Baseline Stage135 533; actual GitHub Actions run 38324096774 / job 115058668448 on executable/test SHA a7cd048b315ad95c9d9c5c82eef329bcbcce8ce9 confirmed **564 PASS, 0 failed, 0 skipped** in decoded runner log.
17–20. **155 release documentation / no release:** keep private original-derived SVGs, real Chrome results, reviewer-mask provenance and SHA manifest in PRIVATE Drive ZIP; GitHub only source-free modules/tests and reproducible human-HOLD documents. Do not publish any source RGBA, GC001/Raden SVG or private screenshots on the live website, and do not merge this unfinished research into main or enable ordinary Public.

Next Stage156+: actual independently verified fullframe human semantic labeling (requires human input, cannot simulate); after that optimize full-scene source-confirmed silhouette+palette+arm/sleeve/hair/collar using explicit fidelity and genuine shape budgets; evaluate device Safari and rollback. Existing Stage135 live opt-in preview is unchanged. The good adaptive middle ground is **research, not complete image quality**.
