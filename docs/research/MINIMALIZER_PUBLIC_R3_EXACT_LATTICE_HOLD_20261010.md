# MinimalizerPublic R3: exact-lattice collinear geometry feasibility and Golden gate

Date: 2026-10-10. Status: **RESEARCH R3 VERIFIED COMPLETE / ZERO QUALITY IMPROVEMENT / PRODUCT HOLD**.

## Source and product boundary

- GitHub repository `watarionn/Minimalizer`, branch `research/public-r3-exact-visible-edge-geometry-20261010` based on R2 Draft PR #354, which is based on R1 Draft PR #353. v34 held Draft PR #308 remains stacked on v33 and is not promoted.
- Inputs are **immutable SHA-verified** three v34 hybrid SVGs and frozen v32 PNG Golden originals in `chatGPT及びCodex用/Minimalizer/SvgLocalRollbackV34_20261009` and `ConnectedSourcePlanesV32_20261009`. All source-content policy, no-face-parts, no-new-RGB, arm/tie/staff visibility protection, and source-owner semantic HOLD remain unchanged.
- No modifications or integration in MinimalizerLocal, Local Worker, live Public UI/route, Python engine, or production deploy. This experiment changes only separate CLI research and tests.

## Research decision and algorithm

R2 Simplify.js yielded **16 masks-safe candidate color groups / 42 nominal vertices**, all of which failed real Chrome exact RGBA and were rolled back. R3 tests the strongest analytic simplification: eliminate a middle vertex **only if A, B, C are exactly collinear AND B lies strictly between A and C in the same forward direction**. Backtracking, spikes, micro-notches, holes, disconnected rings, color-group RGB and painting order must remain intact.

A new source-only module `scripts/public_r3_exact_collinear.cjs` uses R2's already-validated SVGPathCommander parser and pinned browser rasterizer; no new packages. For candidate contours it:
1. Proves exact integer lattice position and safe collinearity with cross-product zero and positive forward dot-product.
2. Compares the **multiset of every directed unit lattice edge** before and after, retaining direction and multiplicity. This is a stronger geometric invariant than equality of the finite image raster alone.
3. Independently compares the **whole source color group with all loops/holes** using existing OpenCV-compatible 2x raster mask.
4. Preserves all other SVG groups byte-identically; absolutely no new owner/color/point generation.

The independent `scripts/verify_public_r3_chrome.py` validates the archived SHA manifests first, renders original and candidate in real Chrome at 340×340 and 680×680, independently compares frozen v32 original and archived v34 Chrome PNG RGBA channels, and checks a deliberately injected unsupported black rectangle as a negative control. All new outputs go to no-overwrite research-only paths.

## Real Golden result, Chrome 154.0.8037.98

| Golden | Color groups checked | Original contour vertices | Strict collinear groups | Analytically removable vertices | Chrome native diff | Chrome 2x diff |
|---|---:|---:|---:|---:|---:|---:|
| Kyoko | 238 | 6,088 | 0 | 0 | 0 | 0 |
| Noel | 371 | 8,976 | 0 | 0 | 0 | 0 |
| Ririka | 301 | 12,434 | 0 | 0 | 0 | 0 |
| **Total** | **910** | **27,498** | **0** | **0** | **0** | **0** |

All three RGBA Golden parity tests PASS at native and 2x, but **the result is negative for shape simplification**. There were **zero strict middle-of-straight-line vertices** among the frozen source contours. Therefore no real improvement in geometry/silhouette/arm/tie/staff or vertex count occurred, and original v34 SVG bytes and SHA-256 remain unchanged. This is not a general impossibility proof for other algorithms, only the proven lack of strict collinear middle vertices for these three frozen v34 cases.

- Synthetic **positive**: exact collinear original lattice vertices can be deleted, and both directed edge multiset and full owner raster remain equal.
- Synthetic **negative**: micro-notch and reverse-direction spike/backtracking are rejected. Multi-ring disconnected components and RGB order are unchanged.
- Normal production image conversion was not modified, and strict stage-8 original ring budget and semantic ownership remain HOLD.

## Verification and reproducibility

- `node tests/js/test_public_r3_exact_collinear.cjs`: **5 safety scenarios PASS** using real R2/SVGPathCommander/browser raster modules.
- Targeted combined Python Public and Local isolation suite including prior R1/R2: **50 PASS**.
- Node `--check`, Python `py_compile`, git diff check PASS.
- Actual Chrome three-Golden run **twice PASS**, both runs with 3/3 exact frozen original/native/2x comparisons and unsourced paint negative-control rejection.
- The seven output files (3 SVG candidates, 3 detailed audit JSON files, 1 overall `public_r3_gate.json`) compare **7/7 byte-exact** between independent runs.
- The three SVG candidate SHA-256 files match corresponding archived v34 originals exactly (Kyoko `583b21c49b5cfca0b6a4ec1ee7399c4c26fcf1effcb32ba316919bbc0c7400be`; Noel `342a476aa0965f9fc5d0e8f7652fa5e8241b829a1967fe4583ba29d9ff1ff`; Ririka `c253f524cdb2d570a6e45809f008f3fa2ccf5a4b19af7aa6a08227500d563b20`).

## Engineering conclusion

R3 algorithmic feasibility work and strict safety verification are **complete**. **No R3 geometry candidate qualifies for release**. Retain the exact v34 SVG contours and all semantic/Golden/Stage8 HOLDs. Do not claim improvement or remove protected details.

**Next R4:** independent Chrome vs resvg-WASM, full source/Golden comparison matrix, version-sequenced images, protected parts (tie, arms, staff), normal and high-DPR tests, reproducible evidence, and human visual sign-off boundary. R4 comparison itself will not authorize production without Stage8 and semantic source ownership passing.

Artifacts to preserve under canonical `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R3_20261010/` with this report and signed-outcome JSON. Source Golden remains in existing reference folders, no duplicate original data.
