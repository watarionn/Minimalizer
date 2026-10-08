# HND-20261008 SA10.36 → Next: clean interior geometry with verified SVG

## Starting point

**Repo:** `watarionn/Minimalizer`.
**Branch:** `research/sa1032-svg-contour-proposals`; **draft PR #223**, NOT MERGED / NOT DEPLOYED.
**Canonical results:** `docs/zerobase/SA10_36_APPAREL_MATERIAL_GRAY_BLOCK_20261008.md`.
**User goal:** preserve the already-accepted outer silhouette while replacing a giant flat gray trapezoid on GC001's outfit with an intelligible low-complexity material hierarchy. Never draw facial eyes/nose/mouth, alter arms or loosen source topology gates.

## SA10.36 work completed

- Diagnosed exact live visible owner as **`lower_body`**: 12,640 pixels, former warm-gray RGB (104,91,86).
- Source has **two bright white shirt sections**, **two navy/dark uniform panels**, and a **thin bright green center tie** in that same owner region.
- Implemented `minimalizer_zerobase/reviewed_sa10/semantic_apparel_material_planes.py`: source RGB class masks, conservative morphology and polygon approximation, 5 closed material subpaths drawn in dark→white→green painter order and clipped to original owner and protected face/arms.
- Real source color medoids, not generated colors, raster textures or Photoshop/AI fill.
- GC001 visually corrected gray area: **largest original-gray component 12,632→476 pixels**, source LAB MSE on lower_body **55.7641% lower**, green necktie **1,615 drawn px vs 1,550 source-class px (+4.2%)** with max +10% gate. Five additional polygon subpaths / 36 vertices / existing 11 outer primitives completely intact.
- Negative control Juufuutei-Raden: no comparable outfit source evidence, **zero edits**, preview SHA256 identical to preexisting Phase9 candidate.
- Distinct real source SHA verified, immutable Phase8/9 lineage; all changed pixels reside inside `lower_body`, zero face/arm change, outer silhouette/topology unchanged; crosscase research gate PASS.
- **81 extended local regression tests PASS**, latest research CI must PASS. Two independent reruns produced identical 4 output file SHA256s per case.
- Full measured evidence under `docs/zerobase/evidence/sa1036_*.json`. Visual and material polygon files under Drive `chatGPT及びCodex用/Minimalizer/SA1036_Apparel_Material_20261008`:
  https://drive.google.com/drive/folders/1_57W-ftJqdPFAse8ZSVwBXVuEJaPfaw3

## Engineering files

- `tools/run_sa1036_color_owner_diagnosis.py`
- `minimalizer_zerobase/reviewed_sa10/semantic_apparel_material_planes.py`
- `tools/run_sa1036_material_grammar.py`
- `tools/run_sa1036_apparel_crosscase.py`
- `tests/zerobase/test_sa1036_semantic_apparel_material_planes.py`
- `tests/zerobase/test_sa1036_apparel_crosscase.py`
- `.github/workflows/sa1032-svg-research.yml`

## Still hard HOLD

1. Original Phase8 outer-vector ring budget: GC001 3,604 >1,887; Raden 2,370 >1,412. New apparel geometry is **five additional filled polygons**, never hide them in the "11 primitives" count. With Phase9 overlays, GC001 total filled elements estimate is 19, Raden 12.
2. The source-owner mask used for clipping is a verified research raster, but its **browser SVG clip-path representation and exact pixel parity are not verified**. Tiny islands/1–2 point rings are also unresolved.
3. Independent human artwork approval is pending. Correct colors may still produce undesired angles, apparel semantics, or fragmentation.
4. Only the distinctive dark / white / green apparel pattern is implemented, other outfits should remain unchanged unless a separate evidence-backed grammar exists.
5. This is not a deployment candidate. PR #223 must stay DRAFT / unmerged. No changes to the production BrowserFallback.

## Next prioritized work

- Have user inspect the three-way GC001 PNG; keep large pale shirt panels and green tie constrained to their *observed* source portions.
- Make a browser-valid SVG clip-path exporter for internal polygons and polygon parent mask holes. Compare browser raster to the research preview at 340x340; never bypass via PNG embedding.
- Work on genuinely minimal, low-vertex outer/inner combined geometry. Use source-mask topology as a hard constraint, but avoid tracing every one-pixel noisy source island with new visible polygons.
- Require combined budget, original source-to-render topology, face/arm immutability, source color, across-character negative control, broader independent cases and human signoff before any merge, deploy or quality PASS.

**Operational:** GitHub and Google Drive are the canonical stores. Use RDC only where necessary to run local original images and verify mounted Drive binaries. Never modify user's local main worktree; use isolated checkout.
