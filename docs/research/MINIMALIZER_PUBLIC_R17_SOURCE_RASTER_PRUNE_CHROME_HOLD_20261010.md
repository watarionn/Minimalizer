# MinimalizerPublic R17 | Source-mask-exact consecutive-vertex pruning research

Date: 2026-10-10. **R17 engineering PASS / candidate browser parity FAIL / Stage8 original budget HOLD / production NO-GO.**

## Branch/source and safety

Research branch `research/public-r17-greedy-exact-mask-geometry-20261010` stacked on held R12–R16 Draft PR #373, R11 #372 etc. No production deploy or main merge, and no changes to Local Minimalizer, Local Worker, browser fallback, source photos, immutable Stage8, frozen Golden or user-approved policy. Default eyes/nose/mouth/eyebrows remain invisible. No Generative Fill/img2img/visible pixels or semantic owner reassignment.

Private source geometry is **never added to public GitHub**. Implemented in:
- `scripts/research_public_r17_consecutive_vertex_prune.py`
- `scripts/verify_public_r17_chrome_owner.py`
- `tests/test_public_r17_consecutive_vertex_prune.py`

## Why R12 yielded zero but R17 works

R12 tried applying OpenCV Douglas–Peucker `approxPolyDP` to entire rings, and rejected any ring with a changed owner raster. That changed too many contour edges simultaneously. R17 instead removes **individual or consecutive 1–12 source vertices in isolation** and compares **the complete existing source-owner polygon raster (OpenCV `cv2.drawContours` with all original holes)** against the frozen adaptive source-owner baseline after each trial. It accepts the edit iff the owner mask bytes stay exactly unchanged. No vertex coordinate interpolation, new point, new color, dropped ring or unknown-owner relabeling is permitted. Both forward and reverse deterministic strategies run with repeated passes, winner selected by true ring-occurrence count.

The input is locked to BOTH its canonical SHA-256 signed original-source photo identity and the **entire privately archived SA10.34 adaptive Stage8 source JSON SHA**, so a similarly numbered substituted geometry is refused. The 11 original owner identities, z-order, palette, ring counts and hole role/depth are checked. Results saved only in privately mounted Google Drive.

## Actual input and owner-raster-perfect research reduction

| Case | Existing original adaptive Stage8 vertices | Best preserved-owner OpenCV candidate | Removed | Savings | Historical Stage8 cap | Remaining over |
|---|---:|---:|---:|---:|---:|---:|
| GC001 | 3604 | **2359** | 1245 | 34.5% | 1887 | **472** |
| Raden | 2370 | **1455** | 915 | 38.6% | 1412 | **43** |

Both best candidates selected deterministic **reverse** order (versus 2364/1456 forward). The owner's raster image is **byte-identical** for each of 11 owners in each image. New source points: **0**; changed existing paint colors: **0**; modified original source files: **0**.

This is significant **research candidate vertex removal**, but **not** a pass of the original signed Stage8 cap for either case, and absolutely not proof that rendering in Chrome matches the previous scene. The historical original 3604/2370 records continue to be FAIL, not silently replaced by new numbers.

## Independent real-Chrome owner SVG rendering (important negative result)

The same source/candidate pairs were rendered in real headless Chrome **154.0.8037.98** through the existing `full_character_svg._contour_mask_svg` generator, using the **same 11 original owner palettes, 1/2-point contours and mask semantics**, at native 340px and 2x 680px. Independent of official OpenCV masks, Chrome visibly changes some colored pixels even when OpenCV does not.

| Case | Aggregate per-owner Chrome 340px changed pixels | Aggregate per-owner Chrome 680px changed pixels |
|---|---:|---:|
| GC001 | **927** | **2008** |
| Raden | **802** | **1610** |

All 11 owners were tested; each owner shows some Chrome differences. These are **summed independent per-owner test images**, not full-character composited pixel totals. The renderer's SVG vector-path fill semantics differ from OpenCV's inclusive contour raster and thin shape behavior. **The R17 best candidates therefore FAIL strict browser parity and must NOT be shipped.** No optimization can be promoted based on the OpenCV PASS alone. The earlier SA10.41 baseline browser-versus-official-mask errors and source semantic part issues also remain unresolved.

## Test/verification and release decision

- The complete Public R1–R17 plus Local/Public isolation tests: **117 pytest PASS**.
- New synthetic positive proves a straight-line point can actually be removed without changing any owner raster; negative tests reject tampered source/owner SHA, corrupt references and output overwrite.
- Chromium 340px+680px independently tested in GC001 and Raden; Chrome parity FAIL (measured, never waived). Real source-owner masks SHA are audited in the private report.
- Production status **NO-GO**. Original Stage8 cap remains exceeded, genuine human Golden, Approved-18/78, protected arms/tie/accessory semantic correctness, physical iPhone Safari, MPL-2.0 legal review, real production rollback and separate R4 whole-scene resvg DPR2 disparity remain HOLD.
- Report and private candidate files should be read back from the Drive folder **`chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R17_20261010`** before claiming preservation.
- No R17 Draft PR merge or deploy.

## Next concrete engineering target

R18 should take original and R17 candidate rings and perform **incremental Chrome native+DPR2 checks before accepting each owner-local subsequence** rather than relying on OpenCV equality. Accept only changes that are exact in BOTH official OpenCV owner masks AND the real browser owner SVG (340/680), while preserving original source identities and 1/2pt micro-contours. A 43-vertex Raden budget gap cannot be declared closed until actual signed owner semantics and full-scene browser acceptance are proven. Start with the owners showing the highest vertex opportunity, and halt only the unapproved promotion, not safe diagnostics.
