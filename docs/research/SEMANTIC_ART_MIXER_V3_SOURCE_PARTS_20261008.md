# Semantic Art Mixer v3: source-owned subject, face parts and regional palettes (2026-10-08)

**Stage:** independent real-image research COMPLETED, **89/89 affected regression tests PASS** with one existing Starlette/httpx deprecation warning, **not a production promotion**. This is the continuation of the owner's feedback that v2's face looked like an artificial circle, the figure silhouette was unstable across art styles, and unwanted eye-like details were appearing.

## Important: use earlier work, do not duplicate model training

Repo already contains source-observed diagnostic masks from the Minimalizer ZeroBase Phase03/04 corpus: `docs/zerobase/diagnostics/phase03/Hyakuto-Kyoko/03_subject_mask.png` and Phase04 `part_masks` for face, hair, left/right arms, torso, neck, clothing, lower body and accessory. These original-referenced masks are used in the new research implementation, **not** as a claim of general automatic segmentation. Every mask is loaded at its native 340×340 size, documented by SHA-256, and required to agree spatially with the subject mask. The script remains GC001-specific and rejects a different source SHA.

An existing non-authoritative AnimeSeg Mask2Former PoC in `docs/zerobase/SA10_27_ANIMESEG_OBSERVER_POC_20261008.md` had already observed separate eye, brow, nose, mouth, hair and clothing classes on GC001. Its saved inference **mask file was not located in the current private research paths**, so this v3 does **not** quietly load or pretend to reuse that model. It performs a smaller deterministic source-only audit for facial details, without running GPU/torch or copying inferred pixels into art.

## Source provenance

Canonical original: `chatGPT及びCodex用/Minimalizer/SA1041_FullCharacterSVG_20261008/original_inputs/GC001_source.png`, 340×340, SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`.

Actual aligned reference diagnostic masks:
- Figure foreground, Phase03: **54,450 pixels**.
- Face, Phase04: **4,808 pixels**. Unlike v2's 4,624-pixel hand-drawn/convex face plane, this follows a source-observed facial contour (forehead, hair overlap, jaw/chin).
- Hair **14,654**, left arm **2,717**, right arm **5,923** pixels.
- Torso **5,827**, neck **1,996**, lower body **12,563**, major clothing **3,737**, accessory/held object **217** pixels (overlap and source-ownership arbitration still experimental).

## Four iterations, each executed with four existing styles

Four recipes reused from v1: `voronoi_ink_dots`, `mosaic_sparse`, `pixel_hatch_dots`, `geometric_ink`. The art modes themselves and their hashed inputs were not regenerated or modified. **16 independent 340×340 PNG comparison results** were saved.

1. **A_subject_clip**, deliberate negative control: source foreground/body mask clips source-derived Shape + Stroke + Texture, background comes from median-filtered original. Subject/background ownership is enforced, **but false-looking eyes remain** and it is **not** approved for a UI option.
2. **B_face_parts_observed**: exact saved Phase04 facial plane; native source skin RGB medoids in three vertical tone bands, sampled after excluding actually observed eye-color islands. No drawn eyes, eyebrows, nose or mouth. **Face dark mark count: zero**.
3. **C_part_palette**: face as above, plus source-masked hair, both arms and major clothing, with small discrete palettes snapped back to **actual original source RGB pixels**, never synthetic cluster-center colors. Better outfit/hair silhouette, but some chest/neck motifs still noisy.
4. **D_extended_parts**: same source-owned region logic, plus torso, neck, lower body and actual accessory masks. **Visual best for anatomy and character recognizability**, with significantly less interference from the selected style. It is also **closest to the original source** and not yet proof of a good *minimal* shape budget or a generally useful style-combination mechanism.

### Facial-part recognition versus rendering

- The source-only HSV micro-observer recognized two separated colored eye components (initial measured sizes approximately 37 and 34 px, centers x≈147 and x≈192, y≈127). Their bboxes are drawn **only in a separate diagnostic audit image**.
- A restricted manual nose-color ROI found **one** source-colored candidate. The mouth-stroke ROI found **two** disjoint line fragments. They are deliberately labeled **non-authoritative candidates** because simple hue/brightness thresholds can be confused by eyebrows, blush, cheek shadows or hair. They are **not** a robust learned face parser.
- The project's GC001 semantic Golden manifest explicitly marks `facial_details` as **forbidden for rendering**. Distinguishing eye/nose/mouth evidence from any permission to paint them is intentional. Candidate boxes are never pasted into any Art Mode.
- The B/C/D face fills still look plain and stylized. Removing pseudo-eye artifacts is a negative safety condition; **no restoration of facial identity is claimed**.

### Measured real-image gates

- **16/16 outputs**: zero Shape/Stroke/Texture leakage outside the observed foreground mask; zero original necktie RGB mismatches after the existing Color Lock.
- **12/12 B/C/D outputs**: zero dark face-feature pixels within the saved face mask.
- Deliberate A negative controls retained visible/internal dark facial marks: **1,586 / 1,023 / 1,084 / 674**, respectively. They must never be silently presented as accepted results.
- Per-region palettes use source medoid colors only and protect source-owned material regions.
- Two successive real GC001 runs with `python -W error` generated byte-identical SHA-256 for **all 16 art PNGs** and **both gallery images**:
  - `gallery_4recipes_4trials.png`: `596d6437311f37633682996623687c9f4186007309009dea9aba0e2574d591a2`.
  - `gallery_D_four_styles_mobile.png`: `fe78401d5e8a600317fd740d2f25b24e2530aa6f7a72e057841ae366f9a3ac6a`.
- `tests/test_semantic_art_mixer_v3_source_masks.py`: eight offline tests (including fail-closed missing eye pair, nose/mouth candidate audit-only, face plan no eyes, source-only palettes, mask consistency).
- Full affected local regression, including v1/v2, LocalWorker, RRM, Browser and split-page tests: **89 passed, 1 existing deprecation warning**.

## Exact artifacts and permanent code

Source/reproduction:
- `tools/research/semantic_art_mixer_v3_source_masks.py`
- `tests/test_semantic_art_mixer_v3_source_masks.py`

Private Drive canonical location: `chatGPT及びCodex用/Minimalizer/SemanticArtMixer_v3_SourceMasks_20261008/`, folder ID `1opReVFm-08a4xeWFkDWFaiIzkDL1G5f_`.

Artifacts include full 4×4 result matrix, compact mobile comparison of original+four D candidates, `manifest.json` with source/role mask/asset hashes, source-mask overlay preview, and *separate* facial observation audit images. The original source, 19 pre-existing Art Modes, v1 and v2 outputs are retained.

**Remote Google Drive synchronization must be confirmed by live connector**; filesystem writes on the authorized PC are insufficient proof of cloud sync.

## Next improvement gates

1. **Generalize from GC001** using clean, original-signed subject/face/body masks on a second source such as Raden; no fake reuse of Kyoko coordinates/colors or acceptance of incorrect mask provenance. Missing observer input must fail closed.
2. Compare D's strong geometric/part protection with an **explicit style and primitive budget**: retain exact subject silhouette, arm/torso negative spaces and source face boundary while simplifying the many source-colored material pixels into a small number of verified vector planes. Do not call near-source raster pixels a successful minimal SVG reduction.
3. Reuse the isolated AnimeSeg **observer** if and only if a real verified mask artifact is available under acceptable resource use, then validate independent eye/nose/mouth classes. Its metadata must retain authority=false; it cannot invent visual content.
4. Do not promote A, v2 face-oval result or any partial trial to MinimalizerLocal or MinimalizerPublic. Release only after independent two-character visual review and Golden silhouette/topology/color tests.

Repro: `python -W error tools/research/semantic_art_mixer_v3_source_masks.py --root PRIVATE_MINIMALIZER_DRIVE --out PRIVATE_V3_OUTPUT`.

**No neural image-generation pipeline, GPU job, new model download, LocalWorker restart, Public deploy or change to RRM was made.**
