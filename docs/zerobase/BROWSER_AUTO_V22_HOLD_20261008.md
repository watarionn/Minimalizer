# BrowserFallback v22: automatic guarded palette-region candidates

Date: 2026-10-08
Status: **RESEARCH ENGINEERING PASS / PRODUCTION HOLD**
Branch: `research/browser-auto-gated-v22-20261008`, based on **held** v21 research PR #232 (v20/v19/v18/v17 stacked).
The publicly deployed Facet v15 in `main` remains unchanged.

## Why v22

The project wants stronger intentional straight-sided color planes without adding back deliberately omitted facial details. Mass v16's broad 40→30 cut severely corrupted colors, while v21 proved that single **manually identified** same-palette neighboring regions can occasionally be merged without substantial raster changes, as long as thin distinctive details such as Noel's staff are protected.

v22 eliminates per-image hardcoded region IDs from candidate discovery and safeguards, but does **not** claim that decreasing polygon records alone equals a major visible-art-quality improvement.

## Design

- Research-only opt-in URL `?browserFallback=force&browserFallbackQuality=auto`. No new default and no merge into the public production branch.
- The engine segments each image using the exact same accepted Facet v15 Lite structural preprocessing, canonical shared contours, OpenCV-compatible flat raster, color medoids and 40-region hierarchy.
- Capture all actual touching region pairs without accepting any merge during the probing step. From those, rank **same accepted palette ID** pairs that pass *all* previous v21 contact/shape/source-color gates except the original small-area threshold, enforcing the targeted upper donor cap of 6% of the work raster. Sort deterministically by ascending source RGB distance, descending contact ratio, ascending donor area and finally IDs as a stable tie-break. Try at most four selected pairs.
- Evaluate candidates independently, one at a time, always against the unmerged Facet baseline, with **no accumulation** of separate merging proposals. For each candidate enforce existing one-pair orientation, contact, 6% maximum donor fraction, source color and topology constraints.
- The proposed polygon graph must use strictly fewer vertices and the rendered result must satisfy v19's changes ≤0.15% of pixels, RGB-channel MAE ≤0.30, maximal single-color mass delta ≤0.15% and zero white/nonwhite silhouette changes. On any violation return the original accepted Facet output.
- v22 additionally detects four-connected, long, low-occupancy exact-color components in the baseline (including diagonal thin accessories), preserving pixels belonging to these thin components. No character name, face reconstruction, or image-specific ROI is required for *automatic* operation. This is a conservative shape-aware safeguard, **not** a universal semantic understanding of thin objects.
- Output includes `autoMergeStatus`, `autoMergeCandidates`, `autoMergeAttempts` and `autoMergeSelected`; the actual UI route advertises `auto` and produces the same PNG bytes as direct engine execution.
- Previous Lite, Sharp, Shape, Facet, Selective, Near and Exact modes are left unchanged. The auto route exists only in this draft research branch.

## Real Chrome 154, original 340×340 golden images

Same original Kyoko GC001, Shirogane Noel and Ichijou Ririka references, browser subject guidance and settings used for v15–v21. Independent SHA256 comparison confirms original Facet and Near PNGs remain unchanged.

| Source | Ranked pairs | Tested pairs | Result | Regions | Vertices | Changed pixels | Chrome Facet / Auto time |
| --- | ---: | ---: | --- | --- | --- | ---: | --- |
| Kyoko | 3 | 1 | **PASS** | 40→39 | 1377→1366 | 3 | 6.20s / 13.59s |
| Noel | 2 | 2 | **FALLBACK** | 40→40 | 1232→1232 | 0 final | 7.16s / 21.55s |
| Ririka | 0 | 0 | **FALLBACK** | 40→40 | 880→880 | 0 final | 5.85s / 7.26s |

The actual automatically selected Kyoko pair is donor 14→recipient 17, which is **discovered from the image**, not hardcoded into the v22 algorithm. It reduces 11 vertices and alters exactly 3 output pixels. Kyoko's full-image representative green RGB(149,211,27) count remains 1,994; sample gray left sleeve (95,275) RGB(65,66,74) and its protected ROI remain unchanged.

Noel automatically discovers 16→24 as the highest-ranked pair but **rejects the 161-pixel change to its thin dark-brown staff with `raster_rejected:protected_feature`**, without any staff coordinates or Noel-specific color lists in the v22 engine. Its next candidate 34→27 is rejected for 552 pixels of tentative raster change. The final PNG is byte-identical to original Facet. Ririka has no eligible candidate and also returns exact Facet.

**No real-image merge polluted a protected region in the final output.** Independent external image audit additionally checks Kyoko tie and sleeve, Noel's staff rectangle and brown pixel mass, and unchanged white-background silhouette.

## Tests and evidence

- New `tests/test_browser_auto_gated_v22.py`: opt-in profile, deterministic ranking, no cross-palette/small-side/aspect/oversize suggestions, synthetic long diagonal line with automatic shape protection, and invalid configurations fail closed.
- Full isolated Windows v12–v22 suite: **60 PASS**, JavaScript/Python syntax checks pass. All **9/9 GitHub Actions PASS** for Auto v22, v21, v20, v19, v18, v17, Facet v15, Shape v14 and Sharp Lite v13 on reviewed runtime revision.
- `.github/workflows/browser-auto-v22.yml` and inherited v13–v21 workflows: **9/9 confirmed PASS**. Document-only commits are rechecked independently.
- `tools/run_browser_auto_v22_chrome.py`: real Chrome UI/engine parity.
- `tools/analyze_browser_auto_v22.py`: baseline SHA256, ROI/color/silhouette fidelity, trace audit, montage, report, raw archives.
- `tools/package_browser_auto_v22.py`: source+evidence preservation with SHA256 check.
- [Google Drive evidence folder](https://drive.google.com/drive/folders/10uAjIiEoObdHr82bBmlzGv4h5L5gqn0h) in the short canonical path `chatGPT及びCodex用/Minimalizer/AutoSelectiveV22_20261008`. **Ten of ten files confirmed through Google Drive API** in the shallow canonical folder, and also SHA256-matched byte-for-byte against the mounted local copy. The initially created overly deep duplicate folder was deleted after authoritative shallow-folder verification. No other project files were touched.

## Gate and next iteration

**HOLD PRODUCTION.** This is a genuine automatic candidate selection proof of concept with successful rollback on a distinctive accessory. But the only accepted image changes **three pixels**, and the repeated baseline/segmentation trials are **~1.2–3.0× slower** than Facet on these samples. Neither the visual design improvement nor the responsiveness is sufficient to replace the public best-quality mode.

v23 should avoid endlessly tuning same-palette merger thresholds. Recommended next step: directly inspect intentional **large color-plane geometry** (hair, clothing, shoulder silhouettes), assess contour straightness and junction quality against a perceptual reference, and use a shared preprocessed hierarchy to reduce redundant Chrome computation. A new mode should only be considered for production when it exhibits a clearly visible improvement with protected color regions, stable topology, reasonable latency and three-golden regression.
