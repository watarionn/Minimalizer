# MinimalizerPublic Paper.js / Delaunator: real two-source signed SVG and Chromium audit

Date: 2026-10-09
Status: **REAL TWO-SOURCE RESEARCH RUN COMPLETE / LIBRARY PROMOTION NO-GO / GOLDEN HOLD / PRODUCTION UNCHANGED**
Scope: research-only scripts; **no production imports** in `web/static`, local worker or release configuration.

## Frozen input and authority

Use the existing canonical SA10.41 private Drive archive `chatGPT及びCodex用/Minimalizer/SA1041_FullCharacterSVG_20261008/` (folder ID `1-S22L7dMzs7tH32aLMel5bTSSsTQY7Oi`), with two source PNGs and the six saved Stage04 signed face/left_arm/right_arm masks. `real_prepare.py` checks SHA-256 of all eight input files before making raw 340x340 masks and RGB for research. Original signed full-image OpenCV references remain unchanged. The second subject is not an independently verified match for GC001 apparel semantics.

- GC001 original SHA: `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`
- Raden original SHA: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- Original role mask SHA keys: see `tools/research/public_geometry_js/real_prepare.py` and private archive `verified_real_inputs.json`.
- GC001: face 4937 px (one connected component, zero holes); left arm 2715 (10 components, one hole); right arm 6486 (one component, one hole).
- Raden: face 4052 (one component, zero holes); left arm 10419 (one component, zero holes); right arm 9870 (two components, zero holes).

These are original-observed masks only. An extracted largest boundary **does not represent the complete signed part** where holes/other components exist.

## Implementation and Node execution

- `real_guards.mjs` rejects whole-role Paper acceptance when signed topology is incomplete (components, holes, complete pixels) or when candidate expanded/lost source pixels/landmarks.
- `real_guards.test.mjs` adds six synthetic regressions for these hard gates. Together with six existing tests: **12 PASS, 0 FAIL** on Windows Node 26.3.0.
- `real_trial.mjs` really invoked Paper.js 0.12.18 and Delaunator 5.1.0 on both original signed-source cases, using input files created by the verified `real_prepare.py`.
- Delaunator renders only signed arm candidates; no filled face, iris, eye, nose, mouth or generated body content. Sampled RGB values are checked across **all three channels** against original source RGB.
- Two separate actual Node real-image runs produced SHA-identical **13/13** generated research files. Rerun after three-channel RGB check was 12/12 tests PASS and SHA-identical **13/13** outputs.
- All six Paper role proposals were rejected. Largest-component contour sampling alone was never interpreted as whole-role success.

### Paper.js raw largest-component contour diagnostics (not complete source-role geometry)

| Case / signed role | External pixels | Missing component pixels | Whole role accepted |
|---|---:|---:|---|
| GC001 left arm | 23 | 178 | no |
| GC001 right arm | 126 | 249 | no |
| GC001 face | 7 | 108 | no |
| Raden left arm | 42 | 234 | no |
| Raden right arm | 123 | 203 | no |
| Raden face | 16 | 98 | no |

### Delaunator arm source-resolution pixel-centre diagnostics

| Case / role | Accepted triangles | Rejected leaving signed mask | Covered / source pixels | Extra pixel centres |
|---|---:|---:|---:|---:|
| GC001 left arm | 50 | 19 | 1656 / 2715 (61.0%) | 0 |
| GC001 right arm | 177 | 20 | 5718 / 6486 (88.2%) | 0 |
| Raden left arm | 293 | 22 | 9452 / 10419 (90.7%) | 0 |
| Raden right arm | 253 | 22 | 8262 / 9870 (83.7%) | 0 |

These pixel-centre measurements cannot guarantee SVG alpha/continuous coverage.

## Actual Chromium browser raster QA

`chromium_audit.py` loaded the four isolated signed-arm candidate SVGs as data-URI images and took transparent screenshots at DPR 1 and 4 with **Chromium 144.0.7559.96**. It compared alpha against each **independently SHA-verified signed Stage04 mask**. A previous `file://` test was blocked by the execution environment; it was corrected to an HTML data-URI renderer without changing SVG bytes. The source original PNG and role mask SHA-256 are checked again by this script.

| Case / role | 4x rendered opaque source coverage | 4x outside-mask alpha>0 subpixels | 4x outside-mask alpha>=128 subpixels |
|---|---:|---:|---:|
| GC001 left arm | 57.8269% | 0 | 0 |
| GC001 right arm | 85.9409% | 10 | 2 |
| Raden left arm | 89.2120% | 22 | 12 |
| Raden right arm | 82.1150% | 7 | 3 |

**Browser strict zero-extra FAIL** on 3 of 4 arms, despite source-resolution candidate pixel-centre extra count=0 for all 4. Transparent antialias fringes and geometry footprints must be measured before claiming protection. Browser candidate also leaves major source-covered holes/gaps. Visual inspection of `real_two_case_chromium_comparison.png` confirms disconnected small triangles and missing arm surfaces; it is **not a full-character Minimalizer render**, and must not be assessed as a finished product.

Neither the constrained full topology, global figure silhouette, clothing/palette identity, original vertex budget, complete Golden visual review nor production gate passed. **No geometry gets promoted.**

## Preservation and reproducibility

Public source:
- `tools/research/public_geometry_js/{geometry.mjs,real_prepare.py,real_guards.mjs,real_guards.test.mjs,real_trial.mjs,chromium_audit.py}`
- Prior synthetic PoC and exact `package-lock.json` remain unchanged.
- Live `web/static` and LocalWorker remain unchanged.

Private results: `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_RealTwoSource_20261009/` ([Drive folder](https://drive.google.com/drive/folders/1VifAjtJ4SmkqccNfjELuI-4Za3cjZKs7)).
- 13 deterministic JS diagnostics: per-role Paper path SVG, per-arm Delaunator SVG, combined arm candidates, `real_metrics.json` (individual Drive files).
- `MinimalizerPublic_Paper_Delaunator_Real_Chromium_20261009.zip` (Drive file ID `1725H0L44XNONDKSbGToGiLIkhuWUucTk`) contains `chromium_audit.py`, signed input metadata, real JS metrics, Chromium metrics, eight alpha-render PNGs and actual side-by-side PNG. The original source photos are **not** included as independent raw files, but side-by-side private comparison contains source pixels. Keep archive in private Drive, **never commit it to public GitHub**.
- Local archive ZIP checksum SHA-256 `bb75566bf9b8e77f4cf7d084095a2b6cfb85d3a6bc99e4e90e837baa5b321b04` refers to the initial archive; if archive contents are refreshed to the latest script, record the *new* SHA and verify Drive read-after-write.

Repro on authorized scratch environment (place original signed inputs in SA10.41 layout):

```sh
cd tools/research/public_geometry_js
npm ci --ignore-scripts --no-audit --no-fund
npm test
python real_prepare.py --root /path/to/private/SA1041_FullCharacterSVG_20261008 --out /tmp/prepared
node real_trial.mjs /tmp/prepared/prepared.json /tmp/js-candidates
python chromium_audit.py --input-root /path/to/private/real-case-image-mask-folders \
  --candidate-root /tmp/js-candidates \
  --signed-manifest /tmp/prepared/verified_inputs.json \
  --out /tmp/browser-audit
```

For the Chromium command, `--input-root` must contain `GC001/` and `Raden/` folders, each with `<case>_source.png` and `signed_left_arm_stage04_mask.png`, `signed_right_arm_stage04_mask.png` (all unchanged from SA10.41). Real browser requires Python Playwright, NumPy, Pillow, and an installed Chromium binary. `chromium_audit.py` currently selects `/usr/bin/chromium` and is Linux-focused; change executable path explicitly if reproducing on Windows, without altering original image assets.

## Decision / next

Research execution and negative Chrome gate: **CLOSED**. Production release: **HOLD/NO-GO**. The next independent research goal is source-boundary-aware *constrained/clipped* polygon fills that preserve all signed components/holes, with color pixels from original source, no face features, explicit primitive budgets, and actual Chrome 1x/4x zero-expansion gates. Never restore quality by enlarging the silhouette, inventing a skin plate, or reintroducing an unsafe fallback.
