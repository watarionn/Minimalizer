# MinimalizerPublic R67–R73: Source-photo RGB/Lab robustness

**2026-10-10. Research complete. 258 selected pytest PASS. Two independent actual Chrome runs produced nine bit-identical evidence artifacts. Release NO-GO.**

This branch is stacked on held Draft PR #385. Authenticated original GC001/Raden source photos, signed original SA10.34 Stage8 11-owner scenes, protected face-hidden policy and original R6 eight-blocker report are read-only. Prior R66 source-derived masks and SVGs are verified against canonical private Drive SHA manifest **before** use. No img2img, generated features, synthetic garment/skin paint, modified Stage8 masks/palettes, public product routing or Local Worker changes.

**R67:** Previous R66 11-owner source photo RGB matched better in 18 changed pixels GC001 and 8 Raden, by selection. Independently tested each pixel with OpenCV 8-bit LAB Euclidean-distance proxy against original source photo at Gaussian sigma 0, 0.6 and 1.2. This is a photo observation robustness challenge, not CIEDE2000 or an independent anatomical label. At sigma 1.2, GC001 5/18 and Raden 1/8 worsen.

**R68:** Strict individual-pixel photo RGB+all-three-Lab nonregression and alpha=255 reduces R66's changed canvas pixels: **GC001 18→12**, **Raden 8→7**. There is no automatic smoothing of output; blur applies only to numeric photo color assessment.

**R69:** Limit each owner to its original one-pixel source mask band and previously proposed delta. Preserve original owner connected components, hole contours, <=1% changed pixels, luminance/chroma, independent Scharr/Canny scores and true source RGB nonregression. Fail-closed restore of any failing owner. GC001 right arm **8**, left arm **3**, major clothing **1** retained; Raden right arm **3**, left arm **0**, major clothing **4** retained. All human semantic owner approvals remain unsigned.

**R70:** Actual authorized Windows Chrome 154 verifies complete original-versus-candidate 11-owner RGB palette/z-order exact SVG masks at both 340px and 680px against independently computed NumPy composite. Each case, both stages, both DPRs: **zero pixels different from signed source-mask composite**. The official whole-character resvg/Facet gate is separate and still HOLD.

**R71:** Original Stage8 budget **GC001 3604 > 1887**, **Raden 2370 > 1412**; signed human Golden, independent source arm/garment/tie/staff ground truth, legal distribution, physical iPhone Safari, actual host cache rollback and cross renderer whole-scene checks all HOLD. R6 eight original blockers unchanged. No main merge, no production deployment, no new face microfeatures.

**R72:** Private photos/board reviews for GC001/Raden, source-derived candidate PNGs and audit remain on Google Drive only. No source coordinates or derived art in public GitHub. The 19 pixel color improvement is heavily selection-biased on the same photo and **not** an independent quality gain.

**R73:** Implementation `scripts/verify_public_r67_r73_photometric_source_stability.py`; tests `tests/test_public_r67_r73_photometric_source_stability.py`. **258/258** selected Public R1–R73 and Local/Public regression tests PASS. Two independent actual Chrome full research runs produce **9/9 byte-identical evidence files**. Preserve at `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R67_R73_20261010`, with SHA readback. Keep Draft/unmerged and product NO-GO.

Next meaningful step: independently signed source-photo semantic owner masks or human Golden comparison. More RGB fitting to already-seen source pixels alone cannot validate anatomy.
