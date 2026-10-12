# MinimalizerPublic P0 Stage67–71: source-edge spatial palette and actually rendered multi-color SVG (HOLD)

Date 2026-10-12. Research branch `research/public-structural-recovery-p0-part-preservation-20261011` / Draft PR #390, base Stage66. **No change to `main`, normal Public conversion, Local Minimalizer, or Stage51 publicly visible read-only research preview.** All input pixels are from SHA-pinned, original-source GC001/Raden 340×340 PNG and RGBA; no generative fill, inferred anatomy, faces or extra image content. Historical owner names `left_arm` and `right_arm` describe unverified masks, not independent skin/sleeve/hair evidence. The observed background mask is NOT independently approved.

## Stage67: strong-source-boundary-aware spatial palette

Implemented `public-source-spatial-palette-p0.mjs`: RGB medoid labels from Stage63 are allowed to move only if at least **3 four-connected neighbors** under source RGB L1 contrast ≤65 agree, and the new medoid's original-pixel RGB L1 is ≤ existing +18. Candidate accepted ONLY if connected-color components decrease, strong original high-contrast edge recall does not decrease, original-source RGB L1 ≤101% of before, and weak-source-color edges wrongly introduced by the candidate do not increase. Otherwise strict fallback to exact Stage66 assignments. Only original medoid colors and original footprint retained, never a painted product change. One deterministic simultaneous relaxation round.

Original 2-image 4-zone result:

| Original / historical region | Changed in candidate | Decision | Source RGB L1 before → selected | Disconnected same-color components before → selected | Strong edges retained before → selected | Weak-source false palette edges before → selected |
|---|---:|---|---:|---:|---:|---:|
| GC001 left_arm | 46 | **REJECT** (896 → 894 retained) | 125,478 → 125,478 | 445 → 445 | 896 → 896 | 747 → 747 |
| GC001 right_arm | 82 | **ACCEPT as PRIVATE preview only** | 329,024 → 321,304 | 864 → 774 | 1,954 → 1,955 | 1,945 → 1,706 |
| Raden left_arm | 230 | **ACCEPT as PRIVATE preview only** | 208,067 → 205,860 | 2,028 → 1,766 | 1,688 → 1,688 | 2,630 → 2,396 |
| Raden right_arm | 259 | **REJECT** (440 → 439 retained) | 193,701 → 193,701 | 1,094 → 1,094 | 440 → 440 | 1,976 → 1,976 |

These are color graph diagnostics within historical unconfirmed owner masks; weak-edge and component counts do NOT certify whether a region is sleeve, hair or skin. Only 312 original-pixel medoid labels are changed within accepted private previews; no geometry or colors are extrapolated outside the input.

## Stage68: genuinely rendered source-color SVG

`public-source-palette-svg-p0.mjs` converts each medoid label's exact original pixel subset into source-locked SVG butt-capped lines (no embedded raster, no script, no gradients). Source owner and original RGBA independently SHA-256 pinned. Every palette color is verified as an RGB triplet that actually occurs in eligible original pixels. Foreground owner pixels all covered, background kept transparent, no overlap by construction. Outputs are **PRIVATE diagnostics only**, not automatic renderer output.

| Case / historical owner | Observed pixels | SVG stroke segments | SVG document bytes |
|---|---:|---:|---:|
| GC001 left_arm | 2,715 | 749 | 18,740 |
| GC001 right_arm | 6,445 | 1,533 | 29,946 |
| Raden left_arm | 10,307 | 3,242 | 56,548 |
| Raden right_arm | 9,870 | 2,418 | 40,042 |

SVG source-only stroke representation is **not** a resolved complete-character polygon vertex budget. Colored paths are numerous; Stage8 historical whole-character cap GC001 3,604 > 1,887; Raden 2,370 > 1,412 remains FAIL. Do not conflate original polygon vertex count with stroke endpoints or segment counts.

## Stage69: independent source re-derivation

`public-source-palette-verdict-p0.mjs` checks independent SHA-256 of original source RGBA and owner mask; replays the spatial trial and raster-path generator, byte-compares rendered SVG source and checks selected labels. Modified input pixels, forged palette colors, SVG markup injections, forged acceptance decisions and invalid assignments are rejected. Always `SOURCE_COLOR_SVG_PREVIEW_ONLY_HOLD`, no product coloring approval, no semantic labels, no full-scene Golden.

## Stage70: actual Chromium 340 / 680 chromatic proof

Chromium `/usr/bin/chromium` Playwright canvas render of the actual source-derived 4 owner SVGs, each at 340px and 680px. PNG encoded and independently checked in NumPy/PIL against source owner membership and exactly selected RGB palette values:

- **8/8 cases: 0 missing / newly painted source pixels; 0 wrong palette RGB pixels; 0 partial-alpha pixels.**
- Both original PNG SHA-256 identifiers match the stored original manifests.
- Four-panel PRIVATE comparison: signed original source photo, frozen Facet40, Stage66 source 8-medoid, Stage67 accepted/rejected spatial choice. The full body outside the narrow research masks still looks coarse; **not Golden**.
- This is isolated actual Chromium, NOT live Public HTTPS render or iPhone Safari proof.

## Stage71: verification, evidence and release HOLD

Stage67–69 have 27 new Node regression tests, including deliberate SHA mismatch, original-absent palette, forged assignments/SVG and strong-edge preservation. Separate GitHub Actions run will establish the total CI verdict. All public JS and tests committed to PR #390 only. Source original PNG/RGBA, mask bytes, SVG outputs, screenshot comparisons and PNGs stay in PRIVATE Drive archives under `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage67_71_20261012`. Do not store raw images in public GitHub.

**Hard blockers remain:** 0 independent signed sleeve/skin/hair semantic pixels; face/sleeve/arm full-body correctness, silhouette, medoid-based color quality and design Golden not approved; SVG full-scene budget fails; real iPhone Safari and production rollback still required. Research status: **DRAFT / HOLD, not deployable.**
