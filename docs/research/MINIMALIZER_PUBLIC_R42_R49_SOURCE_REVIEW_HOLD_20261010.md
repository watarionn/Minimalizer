# MinimalizerPublic R42–R49 | Original-photo semantic inspection and spatial held-out color test

**2026-10-10. R42–R49 research implementation/diagnostics completed. Product release NO-GO.**

## Source authority and isolation

Stacked on R38–R41 Draft PR #382, with the historic R25/R30/R36 signed evidence and original frozen Stage8 scenes still immutable. GC001 and Raden source photos were SHA-pinned and read-only. **Only** private source-photo comparison boards, private per-owner palette/holdout measurements and coordinate-free audit were generated. No generated pixels, source corrections, new face details, signed owner changes, public web runtime, Local Worker or main merge.

### R42–R43: recovered previously unexecuted owner-review work

Actually executed the existing `scripts/verify_public_r42_r43_semantic_review_packet.py` against canonical private R38–R41 signed numeric audit. **22 review items** for two original cases, every independent human/model owner signoff remains false and every palette approval false. Previously stalled execution is now complete. A test file covers no auto approval, hidden face and falsified signoff.

### R44: source-photo vs old owner-mask private visual packet

Added `scripts/verify_public_r44_source_owner_review_boards.py`: each original signed source photo next to (i) a source-colored Stage8 owner-only mask and (ii) a thin original mask-outline overlay over the original photo. Five priority owners per case: right arm, left arm, major clothing, accessory/held object and unknown. These contact sheets preserve the original image pixel data and original owner masks, and go **private Drive only**, not public GitHub.

Evidence: **GC001** `unknown` raw owner 1,991px, but only **19px** visible after later owners; **Raden** `unknown` raw 447px, **0px** visible. GC001 Stage8 vs independently signed Stage04 right arm 24px XOR; left arm 5px. Raden 2px / 0px. Thus not all original mask pixels have visible or source-color significance; blindly adjusting hidden unknown colors has little/no final canvas value. This is occlusion accounting, **not** semantic owner truth.

### R45: observed source-pixel color candidates without source editing

`scripts/verify_public_r45_visible_source_palette.py` only considers visible, two-pixel-eroded owner pixels with original alpha=255 and excluding source-border-connected exact RGB. It chooses a representative source RGB that actually appears in the original sampled region. It **does not paint the new RGB into the product or its original signed source scenes**.

Measured candidate improvement in *training-region* original-photo MAE:

| Part | GC001 MAE gain | Raden MAE gain |
|---|---:|---:|
| right arm | +0.324082 | +0.022291 |
| left arm | +1.787132 | -0.005196 |
| major clothing | +3.708245 | +0.080939 |
| accessory/held object | +0.348485 (44 samples) | -0.090090 (74 samples) |
| unknown | no visible samples | no visible samples |

Some other owners have large source-RGB conflicts, notably GC001 hair: old RGB `[239,129,48]`, observed source medoid `[231,231,242]`, RGB L1 difference **304**, with 955 original opaque interior samples. This could arise from owner/occlusion mismatch, intended minimal colors or source sampling, and **must not be interpreted as automatic hair recolor approval**. GC001 major clothing RGB L1 shift 105. Signed face feature hiding remains mandatory.

### R46–R48: fail-closed part/color risk triage

`scripts/verify_public_r46_r48_color_risk_gate.py` cross-checks source visual occlusion (R44), source color samples (R45), 22-item unsigned semantic packet (R42) and R6 eight original release blockers. Marks insufficient source samples, completely invisible owner, protected hidden face, and unusually large observed color shifts, all **unsigned**.

Formal state: masks/owners/palette unchanged; human semantic review not signed; R6 eight blockers HOLD. Original Stage8 GC001 3604>1887 and Raden 2370>1412 still fail, despite R37 perfect source-mask reproduction.

### R49: source-photo spatial held-out validation (no overfit to the same pixels)

`scripts/verify_public_r49_spatial_color_holdout.py` uses 4 non-overlapping 16px spatial-block classes. Train source-observed RGB representative on three classes and evaluate **held-out original photo pixels** in the fourth. No source image edit or candidate product repaint.

Held-out MAE improvement among 4 spatial folds:

| Owner | GC001 improved folds | Raden improved folds |
|---|---:|---:|
| hair | 2/4 | 2/4 |
| right arm | 2/4 | 0/4 |
| left arm | **0/4** | **0/4** |
| major clothing | 2/4 | 2/4 |
| unknown | 0 trials, no visible source ROI | 0 trials |

The source-medoid color candidate does **not** demonstrate robust held-out improvement for important parts. Even a robust RGB gain would not prove anatomy or minimalization aesthetics; geometry and independent semantic source labels remain the main path to real quality.

## Tests and handoff

Prior R1–R41 selected regressions = **211 PASS**. The new R42–R48 test cases = **13 PASS** and R49 tests = **3 PASS**. The final selected Public R1–R49 and Local/Public isolation regression was rerun in the genuine Windows test environment: **227/227 pytest PASS**. All new code and source-free reports in Draft GitHub; private source-derived PNGs, RGB proposals and spatial-validation JSON remain in `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R42_R49_20261010` with independent SHA readback.

**Next meaningful step:** independently sourced/pinned photo annotation of arms, clothing, accessory and overlap *before* any model-based source-only owner correction. Do not try to reduce training MAE by repainting protected parts, new details, fabricated palettes or Stage8 cap reclassification. Release stays **NO-GO**.
