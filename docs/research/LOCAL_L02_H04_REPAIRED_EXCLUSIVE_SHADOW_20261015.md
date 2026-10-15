# MinimalizerLocal L02: H04 exclusive owner research, pinned Phase5 PASS, Golden HOLD

2026-10-15. **Research-only candidate, NOT L02 closure.** Same-user manual H04 reference is evaluation evidence, not input to the candidate repair function. Preserve original signed Phase4 and all production routes.

## Source and derivation

- Signed H04 original 453 × 1400 RGBA SHA-256 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`.
- Signed Run122 original 11-mask Phase4 bundle SHA-256 `0798bfa21ea52dfe3d3d45435e1513dce0cdeb1712978debe4b272b22fee1b21`.
- Existing private dual-observer v2 shadow input NPZ SHA `94b3fc18865246ffeecb65aa487e0077391a140fd73a8504c4305dbaf7528c75`: original parent `head`, exclusive leaf owners, trained H04 out-of-fold garment evidence, cached independent AnimeSeg v3 class-10 general clothes consensus. **This is an inherited SHADOW, not the immutable Phase4 canonical stage.** None of the H04 manual polygons or vertex coordinates enter `resolve_owners`.
- Only the 2 large connected components of the dual-observer agreement are proposed as garment: 51,259 px before structural attachment support, 50,930 px after the repair. Remaining 497 px keep prior ownership rather than being promoted.
- The first owner reassignment failed ACTUAL pinned Phase5 due to missing `neck-attached-to-torso`: the source neck-to-torso gap grew from 16.12px to 56.75px. This is documented as an **explicit failing control**.
- Fixed with an original-TORSO-only 483px Dijkstra path-and-narrow-corridor reserve between the original neck support and the surviving main shirt. The path cannot traverse outside the original torso, nor paint source pixels. Afterward the neck-to-torso minimum gap remains 16.12px. 329 originally candidate garment pixels were retained as conservative torso instead.
- Reassign proposed jacket pixels from SHADOW `hair` / `torso` / `unknown` to `major_clothing` without changing signed protected anatomical parts. Preserve the largest surviving piece *for each previously connected component* of hair and torso. Small detached leftovers that lost their parent are `unknown`, not asserted jacket. This **abstention** moves 1,931 hair and 63 torso residual pixels to `unknown`, and increases its components 37→90. Speckled unknown is an **unreviewed quality concern**, not a rendering PASS.

## Actual structural and source checks

- Candidate NPZ SHA-256 `a380d45f6bd8104304779b175fe88e7a0ff326e04cc2d9135d1ea68b92bb03b3`, 2/2 replay bytes identical. Research-source metadata 2/2 bytes identical.
- Signed Run122 original mask union XOR=**0** against this proposal; protected `face`, `neck`, both arms, lower body, accessory all XOR=**0**; no source foreground generated.
- **Exclusive leaf masks overlap=0**. Non-exclusive parent `head` intentionally overlaps child `face`,`hair`,`neck`. `head=1`, `hair=4`, `torso=2` connected components maintained. `major_clothing=5` after the attachment bridge; `unknown=90` (was 37) requires assessment. The unchanged Run122 initial masks have different pixel occupancy; no claim of byte identity of the repaired garment, hair or torso masks.
- Actual Windows PC pinned `minimalizer_zerobase/structure/graph.py`, verified **Git blob `60848322332ac88297ef2688d06e32f17ed2b8bc`**, produced **21 anchors / 13 relations**, empty missing-arm / missing-core lists, no cycles, `graph_validation.pass=true` on the exact candidate NPZ.
- Strict source bytes SHA and decoded source RGBA equivalence enforced by the runner. All 25 public synthetic success/negative controls PASS. The offline runner refuses overwriting an existing output directory. Original signed input and runtime worker are untouched.

## Human jacket agreement is diagnostic, not generalized truth

- H04 user's jacket parts 3, 9 and 10 are the authenticated handwritten region basis; the rest of the 17 shapes lack fully approved semantic labels, with 4 trace polygons exceeding the strict 1.5% original-alpha outside tolerance.
- 2-observer agreement BEFORE torso bridge: H04 visible jacket IoU **0.863355**, precision 0.935073, recall 0.918411 (tuned on same H04 source). Core AFTER neck bridge IoU **0.858302**. Whole `major_clothing` IoU vs **jacket-only** human mask **0.785034** because general-clothing includes non-jacket shirt / underlayer; this metric is not a classifier validation for jacket category and must not be swapped with the core score.
- H06/H08 independent AnimeSeg Mask2Former 384px CPU inference completed offline with immutable source and checkpoint hashes; early stdout gives among **opaque** pixels H06 class `clothes` 0.701789, H08 0.287509. This is **not jacket-specific and NOT accuracy**, and the 422,713-byte resulting private ZIP currently resides on owner's synced G Drive mount. The connector-side cloud readback was not confirmed when recording this report.
- No cross-character human jacket/arm labels; existing H04 learner fails horizontal flip consistency on unseen H06/H08 (IoU 0.226774 / 0.237584). Scale normalization and mirror augmentation attempts were rejected for H04 regression.

## Next gated prerequisites to claim L02 COMPLETE

1. Review and approve revised H04 full-body 17-shape taxonomy and confirm four trace polygons which overshoot the signed silhouette (do not silently edit the user reference). Or submit revised signed-source JSON; use already deployed Reference Shape Editor at `/reference-shape-editor/`.
2. Complete **independently labelled jacket and sleeve/arm masks** for H06 and H08 from their exact SHA-signed originals; source/metadata starters are in the private Drive packages. User review or signed pixel-coordinate annotations required; do not pretend a model class equals ground truth.
3. Evaluate current EXACT owner proposal against those unseen labels, source boundary and occlusion ordering, plus visual quality signoff and protected-part regression; generate a new model/shadow and pinned Phase4→Phase5 reproduction if cross-character failures persist. Human Golden remains required.

**Formal status**: L02 `HOLD`, human Golden `HOLD`, Stage8 original rings `HOLD`, production `NO_GO`. Never reuse pinned graph PASS as semantic or release approval. Public/C08, local worker, front-end, scheduled automation unchanged. Private ZIP contains user-supplied source imagery and polygons; never commit it to GitHub.
