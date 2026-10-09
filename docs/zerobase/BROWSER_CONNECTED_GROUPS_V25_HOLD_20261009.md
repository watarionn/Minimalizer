# BrowserFallback v25: source-backed connected color groups (RESEARCH HOLD)

Date: 2026-10-09
Status: **RESEARCH COMPLETE / PRODUCTION HOLD: NO PERCEPTIBLE GARMENT/ARM GAIN**
Pull request: [#290](https://github.com/watarionn/Minimalizer/pull/290), draft.
Branch: research/browser-color-groups-v25-20261009; stacked on held v24 PR #284.
Code-bearing CI verification commit: 97043e759b911030c823864807e08f2ad2d69414.
Public production: **Facet v15 unchanged**. MinimalizerLocal / Local Worker unchanged.

## Purpose and method

v24 single-pixel source correction preserved topology but changed only 0–8 visible pixels. V25 tests connected source-observed groups between *existing* Facet color regions, without image synthesis or any new image colors.

- Isolated web/static/browser-color-groups-v25.js: seed from independently measured original-RGB gain, grow source-supported bounded groups (4–256 pixels, depth <=6), prevent donor region splitting by full 4-connected flood verification, preserve original region IDs and accepted palette.
- Existing canonical shared-boundary contour and actual rendered OpenCV-compatible 2x raster must still pass geometry, silhouette, color-mass and automatic thin-feature safety guards. Independent *rendered* source RGB error must decrease. Any invalid contour, negative source gain, or changed protected color rolls back to unchanged Facet.
- Isolated test route: ?browserFallback=force&browserFallbackQuality=group. All legacy facet, sharp, near, color, etc. quality paths and original default are unaffected.
- Source RGB is **material evidence, not semantic arm/garment ownership**. No eyes, mouth, nose, or invented anatomical detail is added.

## Actual Chrome 154 comparison, 340 × 340 original sources

The real app.js browser request produces a PNG byte-identical to the direct Group engine for all three sources. All frozen v24 Facet/Near/Color PNG results compare byte-identically to their saved ZIP counterparts (9/9).

| Case | Gate | Source candidates | Moved source pixels | Render changed pixels | Facet to Group vertices | RGB input MAE Facet to Group | Facet / Group time |
|---|---|---:|---:|---:|---|---|---|
| Kyoko | pass | 826 | 23 | 46 | 1377 → 1381 | 20.17230 → 20.15777 | 4.65 / 6.81 s |
| Noel | pass | 1001 | 18 | 11 | 1232 → 1232 | 24.23747 → 24.22751 | 4.76 / 6.93 s |
| Ririka | pass | 725 | 13 | 17 | 880 → 878 | 20.94304 → 20.94017 | 4.32 / 5.97 s |

All cases retain 40 regions, zero changed white/nonwhite silhouette pixels, pass independent post-render RGB fidelity and improve source squared-RGB error. Kyoko's characteristic green tie mass (1994 pixels) and left sleeve pixel/ROI are unchanged; Noel's staff color mass and staff ROI unchanged.

**CI**: all 12 GitHub Actions jobs pass on 97043e7. The Group research job passes 45 total tests including 4 new deterministic and topology-source contract tests; JS syntax and Python compilation pass.

## Visual review and Ship gate

**HOLD_NO_PERCEPTIBLE_GARMENT_ARM_GAIN.** Original / Facet / v24 Color / v25 Group collage was visually reviewed. Only 46/11/17 of the 115600 raster pixels changed; large garment/arm color-plane fragmentation and missing arm structure are still present. Kyoko adds 4 vertices. Runtime is approximately 1.4–1.5x Facet. The improvements to source-color MAE are real but negligible for visual recognition.

DO NOT merge PR #290 to main, deploy to Public/Local, touch Local Worker, or promote v25 on metric PASS alone.

## Evidence and reproduction

Canonical, private Google Drive folder under chatGPT及びCodex用/Minimalizer:
[ColorGroupsV25_20261009](https://drive.google.com/drive/folders/1VycRsfCByJKxzdp5NoVcJO1JFgt_seLK)

- v25_source_facet_color_group_comparison.png: 3×4 source/Facet/Color/Group visual comparison.
- v25_raw_images_metrics.zip: all 3 original sources plus Facet/Near/Color/Group PNGs, Chrome metadata and summaries.
- v25_metrics.json, v25_metrics.csv, v25_report.md: independent quantitative audits.
- v25_evidence_manifest.json: SHA-256 read-after-copy verification of eight evidence files and the frozen v24 reference.
- tools/run_browser_groups_v25_chrome.py, tools/analyze_browser_groups_v25.py and tests/test_browser_color_groups_v25.py: executable replay and guards.

For each source extracted from frozen v24 ZIP, from isolated v25 checkout:
python tools/run_browser_groups_v25_chrome.py --root CHECKOUT --source ORIGINAL.png --out OUT_DIR --reference-zip FROZEN_V24.zip --case-name Kyoko

Substitute Noel/Ririka as needed; then run:
python tools/analyze_browser_groups_v25.py --kyoko KYOKO_OUT --noel NOEL_OUT --ririka RIRIKA_OUT --out AUDIT_OUT --reference-zip FROZEN_V24.zip

The accepted v24 baseline is frozen, not derived from an approximation. A **second full Chrome 154 replay** was independently executed for Kyoko, Noel and Ririka. All 12 PNG byte streams (Facet/Near/Color/Group × 3) and selected shape/region metadata are identical to the first run. First and repeat SHA-256 hashes and read-after-write verification are recorded in v25_replay_sha_verify.json and the updated v25_evidence_manifest.json in the canonical Drive folder.

## Next: v26 source-linked structural/semantic planes

Do not continue low-value RGB-only micro-corrections. Identify the upstream color-plane/arm/garment decomposition failure and inspect real interfaces for semantic part evidence; do not assume local ZeroBase labels directly transfer to Browser. Propose sizeable but source-supported connected garment/arm patches constrained by part evidence and explicitly preserve uncertainty. Maintain zero image synthesis, existing colors, protected tie/sleeve/staff and exact silhouette. Require visibly clear multi-subject gain and reasonable runtime before any production promotion.

This v25 branch remains a HOLD reference, not a release candidate.
