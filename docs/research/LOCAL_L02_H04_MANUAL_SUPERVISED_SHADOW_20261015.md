# MinimalizerLocal L02: H04 hand-labelled jacket to source-only guarded shadow

Date: 2026-10-15 JST  
Status: `H04_MANUAL_SUPERVISED_ENGINEERING_PASS / PHASE5_PINNED_GRAPH_PASS / L02_SEMANTIC_GENERALIZATION_HOLD / PRODUCTION_NO_GO`

## Why

An earlier H04 pre-manual v2 colour witness missed a large portion of the viewer-right jacket and sleeve, and over-included central shirt / lower clothing. A later user-authored full-body 17-polygon trace, authenticated against the **exact signed H04 source PNG**, supplies ground-truth annotations for jacket polygons 3/9/10 by geometric overlap against the user's earlier independent three-jacket trace. Names of the other 14 polygons remain unassigned; no inferred semantic labels are imported.

**Training uses the user's jacket label mask privately, but inference never loads that manual mask, polygons, SVG, or stored vertex coordinates.** This is single-case supervised research, not a deployed multi-character segmenter.

## Pinned inputs and versions

- Signed H04 source 453×1400 RGBA SHA-256 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`, read from signed Run105 18-source archive; all 18 source images independently hash-matched their own bundle manifest.
- Immutable original Phase4 stage SHA-256 `def1eac131b60ae12fa14675441f21a342cfdfde7d1b96c168ba351c74a9eec0`, 11 part-mask hashes verified without modification.
- Hand-created full-body JSON SHA-256 `be03cd35f7bcd0ca56350e748d3ff784f8b40683af440a8dd732c643d8d195fb` and SVG SHA-256 `8e8f21957559dd75afa1e3c4e6c5a93e92cb2ab9c2afe66917178cb1b4a927fe`. Embedded image decoded to the exact signed H04 SHA.
- Pre-manual v2 source mask NPZ SHA-256 `5d6c8839b9651db9e14132c891c80d41ef5d2233b9c668dc75d5ee6f2f67d310`.
- Actual Phase5 structural graph Git blob **`60848322332ac88297ef2688d06e32f17ed2b8bc`** checked on live Windows-side repository, and executed in the pinned Python environment against the new shadow NPZ. The worker service and repository were **not changed**.
- Local research environment: Python sklearn 1.8.0, OpenCV 4.13.0.92, NumPy 2.3.5. Output artifacts include byte hashes; those hashes matter more than later dependency-version drift.

## Method

1. Authenticate old and new manual geometries, source images and pre-existing component owner masks via SHA checks (private harness only).
2. Construct an H04 binary **jacket-only** training label from the three user-authored jacket polygon visible regions, excluding protected anatomical source masks and transparent pixels.
3. Extract from the **source image only**: LAB pixels, small/large Gaussian-blurred LAB, LAB residuals, local Sobel edge magnitude, and image foreground-relative x/y. A fixed-seed HistGradientBoosting classifier learns from human labelled pixels. No ReferenceShapeEditor coordinates are supplied to `inference()`.
4. Infer with source-alpha and the **existing anatomical face/neck/arms/lower-body protected region**; extrapolation above the original signed neck boundary is guarded. Pixels unsupported by signed mask union are never promoted. Hyperparameters and this neck guard were explored on this same H04 example, so these tests must not be reported as unbiased new-character generalization.
5. Evaluate spatial holdouts: train viewer-left/test viewer-right, reverse, train upper/test lower, reverse, and alternating large tile holdout. The side-split predictions assemble an **out-of-fold H04-only** audit candidate. A full-H04 model is included for overfitting diagnostics but its in-sample score is **not** used to judge generalization.
6. Apply median spatial regularization and remove tiny prediction islands. **Do not delete** pre-existing signed or shadow hair/head/arm masks; add inferred jacket-like evidence as **overlapping major_clothing evidence only**, preserving source ownership and foreground union. Occlusion semantics remain unresolved.
7. Replay **this exact new output** through the pinned Phase5 graph. This is a graph integrity gate, not a body-part/garment-truth guarantee.

## Results: signed H04 within-image evaluation only

| Diagnostic | Pre-manual candidate | New side-held-out shadow | Interpretation |
|---|---:|---:|---|
| Jacket ROI IoU (before spatial regularization) | 0.607232 | **0.799184** | Independent regions within same image; not new character |
| Jacket ROI precision | 0.691453 | **0.845551** | Too-broad central/shirt detection reduced |
| Jacket ROI recall | 0.832926 | **0.935791** | Missing jacket/sleeve reduced |
| Regularized, source-union-constrained IoU | 0.607232 baseline | **0.801025** | Conservative evidence-only output |
| Viewer-left jacket source-visible recall | 0.929353 | **0.967592** | Shape 3 |
| Viewer-right jacket source-visible recall | 0.645151 | **0.836706** | Shape 9 |
| Viewer-right sleeve source-visible recall | 0.411672 | **0.936304** | Shape 10 |
| Source-pixel generation/inpainting | 0 | **0** | RGB source unchanged |

The 5 within-H04 spatial splits all improved IoU, including lower-trained/upper-tested after an anatomical guard. Their split placement, feature choice and hyperparameters were explored with knowledge of H04; this **does not prove an unbiased benchmark**. Full-image fit achieved a much higher *in-sample* score and is not an acceptance metric.

**Topology of the conservative, overlapping Phase5 shadow:** head 1, hair 4, torso 2, major_clothing 2 components; all source mask classes except additive major_clothing evidence retained exactly; protected masks 0 XOR; foreground union 0 XOR. Running the **exact** resulting NPZ SHA `fa66810c36dfaac3d9a9de1fb5984fc3e923d8ee240e697af4dd2d6a093d9cc0` with pinned Git blob returned `pass=true`, 21 anchors, 13 relations, 0 missing arm attachments, 0 isolated major parts, 0 missing core relations, 0 occlusion cycles.

Verification: **16/16** synthetic security/invariant tests PASS plus actual H04 signed-file integrity and source-only evaluation; **2 separate executions** of the new NPZ and private metrics produced byte-identical SHA. All 18 Run105 original source entries matched the bundle inventory; **17 have no authenticated jacket reference**, so no independent cross-character semantic quality can be claimed.

## Mandatory HOLDs and next step

- **L02 not yet formally complete.** This method is trained/calibrated on just one person and no truly independent annotated other-character test exists. Unknown-owner/overlap handling and layer precedence require a stronger semantic authority beyond graph topology.
- Need at least one **additional signed original + human-labelled jacket/hair/arm** or independent calibrated semantic labels, used as a **never-trained-on** test case. Compare jacket precision, recall, overlap and source-only integrity, then finalize candidate policy and full Phase4→5 replay for a real input without user labels at inference.
- Do not deploy this H04 research model, change the running LocalWorker/Public, override source Stage8 complexity, mark C04 Golden PASS or resume the paused C08 campaign. The user's full-body reference remains an immutable separate artefact.
- No source imagery, manual vertices/label rasters, training examples or identification secrets go into public GitHub. Private coordinates, original image, H04 comparison raster, NPZ mask candidates and harness live only under `Google Drive/chatGPT及びCodex用/Minimalizer/`.
