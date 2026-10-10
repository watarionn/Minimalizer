# MinimalizerPublic R30–R37 | Source-mask-exact Chrome vectors, non-generative composition, semantic HOLD

**2026-10-10 | Eight consecutive engineering/research stages executed. Signed binary owner-mask browser fidelity PASS; product-quality and production NO-GO.**

## Safety and original-source lineage

Stacked upon R26–R29 held Draft PR #379; inherits R25 independent original-source 340px diagnostics, immutable R26 candidate masks, original SA10.34 Stage8 owner JSON, R6 original release NO-GO. All GC001/Raden signed photos, signed Stage04 face/left/right binary masks, 11 original Stage8 owner polygons, RGB source palettes, original masks SHA-256 and original source-scene SHA-256 are **read-only**. No img2img, no Generative Fill, no new facial microfeatures, no painted or corrected original photos, no source owner relabeling, no changes to web/static or Local Minimalizer/Worker, no GitHub main merge, no production deployment.

Public GitHub contains **only** generalized Python scripts, tests and coordinate-free numeric report. Private derived SVGs, masks, any review render PNG stay inside `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R30_R37_20261010/`.

### R30: source-only semantics and provenance

Authenticated original SA10.34 source scenes and the R26 evidence chain. Formally detected that original/independent **source-photo-only semantic right-arm/garment/tie/staff grounding remains UNSIGNED**. Merely matching fully opaque border RGB does not prove whether a pixel is anatomical arm or background, even with perfectly faithful binary raster reproduction. Explicit `ABSTAIN`; no changed source owner mask accepted for product. Hidden eyes/nose/mouth remain hidden.

### R31: source-pixel-aligned row-run SVG

Implemented `scripts/verify_public_r30_r35_exact_mask_vectors.py`: for each binary signed mask row, locate maximal contiguous foreground runs and render each interval as an exact integer-coordinate closed rectangular SVG path. Every covered pixel is from the **existing signed binary mask**, no interpolation or bitmap/image embedding. Rebuild the binary mask from rectangles in Python to prove equality **before** launching Chrome. Source masks remain untouched. Synthetic holes, thin runs, source corners and boundary edge cases tested.

### R32: reversible vertical rectangle merging

Only identical (x,width) runs on immediately consecutive rows may merge into a taller rectangle, never a bounding-box approximation. Guaranteed no overlap and exact reconstruction. Full original 11-owner mask totals:

| Original source | Pixel-row rectangles | Vertically merged rectangles | Source-owned full-scene SVG bytes (row→merged) | Gzip9 bytes (row→merged) |
|---|---:|---:|---:|---:|
| GC001 | 2,659 | **2,038** | 44,830 → **34,479** | 11,879 → **10,548** |
| Raden | 2,045 | **1,418** | 35,580 → **24,787** | 9,093 → **7,895** |

The rectangle count and its nominal corner occurrences are **not** the original Stage8 primitive ring vertex budget. The new representation actually uses many more shape corners than the original fixed budget and is not a Stage8 budget pass.

### R33: **real Chrome** native and DPR2 zero-pixel mask parity

Chrome **154.0.8037.98** tested both row-run and vertical-merged geometry for:
- each original Stage8 source-owned **11 individual masks × 2 source photos**, and
- each original Stage04 **face, left arm, right arm signed mask × 2 source photos**,
- at independent **340px and 680px** Chrome renders.

This is **2 subjects × 14 masks × 2 geometry encodings × 2 DPRs = 112 authentic signed mask pixel comparisons**, ALL **0 changed pixels** against each binary source mask expanded by nearest block-preserving dimensions. Binary exact Chrome owner-mask representation is a genuine improvement over R27's contour-serialized browser disparity.

For signed Stage04 (source masks are observational only; no face details painted):

| Signed Phase04 mask | Source pixels | Row-run rectangles → vertical rectangles | Raw SVG bytes row→vertical | Gzip9 bytes row→vertical |
|---|---:|---:|---:|---:|
| GC001 face | 4,937 | 73→52 | 1,508→1,130 | 595→555 |
| GC001 left arm | 2,715 | 155→111 | 2,840→2,076 | 869→793 |
| GC001 right arm | 6,486 | 143→108 | 2,580→1,992 | 967→913 |
| Raden face | 4,052 | 71→53 | 1,458→1,134 | 609→568 |
| Raden left arm | 10,419 | 178→132 | 3,368→2,546 | 1,152→1,065 |
| Raden right arm | 9,870 | 153→95 | 2,683→1,738 | 854→750 |

### R34: R26 private candidate right-arm deletion rendered without browser spill

R26's unapproved source-background connected RGB subtraction candidate remains UNSIGNED SEMANTICALLY. New exact bitmap-vector representation merely demonstrates that its changed source pixels can now be isolated **without any extra changed pixels elsewhere in Chrome**:

| Unapproved arm trial | Deleted signed source pixels | Chrome 340 changed | Chrome 340 changed OUTSIDE source deletion | Chrome 680 changed | Chrome 680 changed OUTSIDE source deletion |
|---|---:|---:|---:|---:|---:|
| GC001 | 520 | **520** | **0** | **2,080** | **0** |
| Raden | 3 | **3** | **0** | **12** | **0** |

Contrast with R27 contour-mask SVG: GC001 549/2232 changed and spill 35/164 outside deleted pixels; Raden 5/23 changed and spill 3/13. R34 isolated the **renderer spill**, not arm anatomy truth. Candidate masks **NOT product-adopted**.

### R35: fail-closed source/release check

Requires both original source SHA signatures, all 11 source owner + 3 Stage04 protected signed masks for each case, explicit no independent semantic owner anchor, true browser 340/DPR2 exactness and R26 candidate deletion rendered with no spill. Enforces R6 **8 original BLOCKED release gates**, historic Stage8 GC001 **3,604 > 1,887** and Raden **2,370 > 1,412**. No claims of source-photo aesthetic quality, tie/staff/arm anatomy, human Golden, resvg Facet whole-scene DPR2, physical iPhone Safari, MPL licensing or active host rollback.

R35 formal status `BROWSER_BINARY_SIGNED_MASK_REPRESENTATION_PASS_PRODUCT_NO_GO`; `productionReleaseAuthorized=false`.

### R36: genuine 11-owner colored source-mask scene Chrome exact

Implemented `scripts/verify_public_r36_r37_full_owner_composition.py`. Independent numpy reference starts from a white canvas and **paints the 11 original Stage8 signed source-owner masks in their exact historical z-order with their existing palette RGB**. This is a frozen **Stage8 owner-mask palette composite**, not the signed Stage04 full character, photo or all additional garments/Facet scenes.

True Windows Chrome renders both row and merged geometry at 340 and 680; every one of the **eight** full-scene comparisons (2 cases × 2 modes × 2 DPR) is **0 changed pixels** against that independent numpy mask/RGB/z-order reference. This is a non-generative, source-owned, exact-raster SVG candidate with fully preserved owner masks.

### R37: quantify the old SVG contour renderer limitation and tradeoff

The original source-ring contour SVG from R19 was independently Chrome-rendered at both resolutions and compared against the **same original Stage8 mask/palette composite**:

| Signed source | Original contour SVG wrong 340px | Wrong 680px | New merged-rectangle SVG wrong |
|---|---:|---:|---:|
| GC001 | 2,603 | 11,012 | **0 at both** |
| Raden | 2,289 | 9,414 | **0 at both** |

**R37 tradeoff:** New merged exact-source owner composite raw SVG = **34,479 B / 24,787 B**, gzip9 = **10,548 B / 7,895 B**. Previously validated R19 relative coordinate Stage8 SVGs were **smaller** (R23 source composite 27,539 B / 14,685 B, gzip9 4,798 / 2,810 B) but retained the original mask/Chrome discrepancy. Thus raster-exactness costs storage/geometry, and **no claim of better overall quality or speed** is warranted.

### Engineering validation and restricted follow-up

- Entire selected Public R1–R37 and Local/Public isolation suite **205 Python tests PASS**, including true Chrome positive mask/composite and negative geometry controls.
- Two-source authentic Chrome diagnostics report SHA and private SVG SHA are verified; independent replay should be byte-compared before asserting reproducibility in Drive.
- Original source artifacts unmodified, generated source-derived SVGs private only, and GitHub PR must remain **Draft, not merged**.
- Important: this is **exact preservation of existing source-owner pixels**, not proof that those source masks correctly describe human arms, tie, staff, costume, silhouette or original photo. It does not solve original Stage8 budget. Do not swap this into the product yet.

**Next meaningful research:** independently ground semantic arm/garment/tie/staff source masks to authoritative original-photo part annotations and approved samples; then explore compact exact-vector representation with a real original Stage8 cost model. Separate human Golden, physical Safari, vendor licensing, full-scene DPR2 and real hosting rollback remain before any production admission.
