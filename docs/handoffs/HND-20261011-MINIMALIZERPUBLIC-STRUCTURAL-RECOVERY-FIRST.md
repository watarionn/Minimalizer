# MinimalizerPublic: structural recovery P0 → next chat handoff (2026-10-11)

**Owner's latest explicit priority (overrides the R67–R73 micro-pixel trajectory):**

> 「やっぱり、細かい何画素を気にする前に他に全然できてないところを直したい。」

**Do not keep iterating R67's 12+7 individual pixel changes as the main task.** Focus first on the *visible, obviously incomplete* silhouette/arms/garment/held-object structure of the real Public Minimalizer. Actual source-photo fidelity, not tiny RGB/edge metric gains, determines progress. The user is moving to a separate chat and wants continuity. No new research candidates should be represented as released product integration without full approval.

## Authoritative current state

- GitHub repository `watarionn/Minimalizer`, `main` is production engineering base; never overwrite existing user edits on the Windows original working tree. GitHub + Google Drive are canonical; authorized local PC/RDC is an optional execution tool, not an automatic prerequisite.
- R52–R66 experiments: [Draft PR #385](https://github.com/watarionn/Minimalizer/pull/385), 250 selected tests PASS, still **held/unmerged**. Geometry-scores alone caused RGB regression and required source-photo nonregression gates.
- R67–R73 experiments: [Draft PR #386](https://github.com/watarionn/Minimalizer/pull/386), 258 selected tests PASS, still **held/unmerged**, only 12 GC001 and 7 Raden source-photo-fitted pixels retained; *not* independently approved semantic anatomy/quality. Private data: [LibraryConvergence_R67_R73_20261010](https://drive.google.com/drive/folders/1uy5d6NG-PpPQAiyN9XPKj21BVIHjgg6w).
- User-requested actual production **standalone inspection preview** was published as seven *new* files, **not** a change to the ordinary image upload/conversion engine: [live R67 preview](https://cf278796.cloudfree.jp/minimalizer/static/public-r67-review-20261010.html); [Draft PR #387](https://github.com/watarionn/Minimalizer/pull/387), intentionally unmerged. Published assets: 1 HTML + 6 derived Stage8 11-owner RGB comparison PNGs (not original photos). HTTPS readback new 7/7 exact, existing runtime 7/7 unchanged, live Chrome desktop/mobile simulation passed. This is **not** a live example of new arbitrary-user-image processing. Private live rollback/provenance: [PublicR67_ProductionPreview_20261010](https://drive.google.com/drive/folders/1XyFZKbuqOJOFsDM1s-9nsdSGeMWyiL73).
- **More recent structural P0 diagnostic already exists**, do not lose it or redo its source characterization: [StructuralRecovery_P0_20261010](https://drive.google.com/drive/folders/1tZ3e3DBK7d_eryWl19dBaB90okr6Uapz), including `STRUCTURE_P0_VISUAL_DIAGNOSIS.json`, private original-vs-public mode comparisons, replay scripts and SHA manifest. This was built against signed original GC001/Raden and actual live Public screenshots. It is read-only research; P0 says **no production deploy** and **human Golden not signed**.

## Structural P0 actual findings (from signed diagnosis JSON)

The live browser was tested on `lite40`, `facet40`, `facet80`, `facet120` for genuine GC001 and Raden inputs. The true browser shape counts for Facet were 40/80/120, respectively. Crucially: adjusting only a nominal maxShapes/palette target did **not** reliably change effective complexity; changing the effective hierarchy target does produce distinct shape counts. Nevertheless, increasing the count is **not enough**:

- **GC001:** More regions partially recover navy fabric, sleeve boundaries and badge color, while goggles, coherent collar, overall silhouette and costume overlap remain inadequate.
- **Raden:** Even at 120 regions, bow, corset lacing and sleeve ruffles still collapse into broad dark clothing regions.
- **Face:** Source-eye-like patches can appear in browser output and violate the approved specification that eyes/nose/mouth should **not** be drawn. Block these at the owner/part boundary rather than assuming global color optimizers prevent them.
- **Likely architectural problem identified by P0:** Global whole-image region hierarchy merges distinct clothing parts, and the globally shared palette is too coarse; shape-count tweaks alone cannot preserve semantic source parts. This is the current leading *hypothesis*, not proof that any one library/model fixes it.

## Next-chat primary goal and proposed engineering sequence

**Goal:** Repair large, conspicuously missing visual structures in actual *public browser output* while preserving the source identity and the non-generative Minimalizer policy.

1. **Use the P0 originals and comparison artifacts first.** Read `StructuralRecovery_P0_20261010/STRUCTURE_P0_VISUAL_DIAGNOSIS.json` and replay scripts before modifying algorithms. Build a concise before/after diagnosis with visible issues on both original examples, and retain the currently deployed Lite/Facet results as the baseline. R67 sample-pixel preview is reference-only, not the new quality target.
2. **Restore owner/part distinctions before global simplification.** Investigate source-observed segmentation/part partitions for silhouette, left/right arm, torso, collars/sleeves, layered garments, bow/tie/corset and accessory/held object. Use observers only to locate existing source pixels; no img2img, generated fill, invented details or arbitrary recoloring. Where source semantics are uncertain, abstain and ask for independent review, rather than flattening ownership to a single clothing mass.
3. **Per-part contour and palette allocation.** Prevent distinct sleeve/collar/bow/corset/held-object source parts from being swallowed by the global image region hierarchy. Allocate shape and color budgets to recognizable source parts under an explicit cost model. Do not treat merely raising 40→80→120 as a solved defect.
4. **Fix major geometry/artifact quality first.** Confirm silhouette, arms visibly present and separated, garment layering/z-order, tie/bow/collar/ribbon boundaries, accessory visibility and source palette placement. Examples: GC001 navy sleeve/collar/goggles/costume overlap; Raden bow/corset lacing/ruffles. P0 screenshots provide concrete failure evidence; avoid unsourced reconstruction.
5. **Face redaction is mandatory.** Suppress *eye-like* and mouth/nose source microfeatures across Lite/Facet and any new geometry pipeline; no exceptions for improved RGB/edge scores.
6. **Evaluate actual Public browser behavior** at real source examples 340px and DPR2 680px, with version-order comparisons and independent source-photo/semantic visual review. Record large perceptual changes, ownership leakage, occlusion and shape area, **not** a tiny pixel count as the primary win. Preserve Chrome whole canvas RGB/mask parity where appropriate, but do not conflate it with source/photo anatomy or Golden human signoff.
7. **Release process:** Keep an isolated Draft research PR and private Google Drive source-derived artifacts. Test isolation and rollback. Expose the best substantive implementation for user inspection only when it actually improves the major defects and passes safe local/browser checks. Do not silently overwrite default production with a HOLD candidate; any opt-in preview must clearly distinguish research from standard production.
8. **Cleanup/preservation:** SHA readback Google Drive under `chatGPT及びCodex用`, document source lineage, negative control and changed product files; minimize RDC use. Never clean/overwrite the owner's original dirty working tree.

## Success criteria for the resumed task

A substantive stage should demonstrate **visible recovery of a missing part or source-anchored layering**, not merely 7–19 optimized pixels, more metadata, or a higher global shape budget. Prefer the P0 side-by-side public screenshots and frozen original inputs. Record which P0 defects improve, remain unchanged or regress. Users should be able to recognize sleeves, bow/collar and held objects where source evidence supports them, while eyes/nose/mouth remain hidden.

## Release restrictions, scope and next action

R6 original eight blocked release gates remain: historic Stage8 source-ring budget (GC001 3604 > 1887; Raden 2370 > 1412), Golden signoff, semantic arm/garment/source ownership, whole-scene Chrome/resvg DPR2/Facet, real iPhone Safari, licensing and real production rollback. No production incorporation of R67 source-pixel study is authorized. **Current P0 structure recovery is diagnosis-only and not yet in the live default converter**.

**Immediate next-chat action:** Start by reading this handoff and the **P0 Drive evidence**. Then perform the first meaningful source-part-preserving segmentation/rendering implementation and genuine GC001/Raden comparative test, protecting signed source and the live default engine. Do not resume R74 as another near-invisible color/edge optimization.

**Explicit user priority:** "まずは全然できていないところを直す。数画素の調整は後回し。"
