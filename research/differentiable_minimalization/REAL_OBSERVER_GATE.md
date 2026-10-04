# Real observer runtime gate

This directory is research-only. It must not modify Minimalizer production requirements.

## Reuse before install

Minimalizer already validated an isolated RTX 5060 semantic observer environment in Calibration 06 Phase E:
Python 3.11.9, Torch 2.11 CUDA 12.8, Transformers 5.17, Grounding-DINO tiny + SAM ViT-B. Reuse cached model assets/environment when present rather than duplicating the ~4.47 GB environment.

## Required real evidence

P5 adoption remains HOLD until Diagnostic-2 (Hyakuto Kyoko / Raden) has:
1. real frozen semantic features from a pretrained observer;
2. real semantic-region masks from an analysis-only segmentation observer;
3. baseline and refined renders bound to the same source;
4. deterministic repeat;
5. machine A/B result plus mandatory human visual QA.

Synthetic/injected test observations never count as corpus evidence.


## Recovery probe 2026-10-03

A narrow local search found a pre-existing non-Minimalizer environment at `C:\\Work\\Benchmarks\\memory-compare-20260928\\.venv` whose installed package tree includes Torch, Transformers, and Transformers SAM/SAM2/SAM3 modules. This is a **reuse candidate only**, not a canonical dependency. Direct read-only execution of that environment was blocked by the remote-operation safety gate, so no mutation, package install, or model download was attempted.

The expected Hugging Face cache directories for `IDEA-Research/grounding-dino-tiny` and `facebook/sam-vit-base` were not confirmed by the narrow probe. Therefore the old Phase E model weights must not be assumed present.

Recovery policy: do not bind Minimalizer to the benchmark environment. If execution access is later available, inspect its exact Torch/Transformers/CUDA versions and cached model availability read-only. Reuse only shared model/cache assets or reproduce a dedicated observer environment from a pinned manifest. Production requirements remain unchanged.


## Reuse decision 2026-10-03

Read-only inspection shows the benchmark venv is Python 3.11.9 but Torch 2.14.0+cpu with no CUDA build, and Transformers 5.15.1. It is rejected as the Phase E GPU observer runtime. The standard Hugging Face hub cache also does not contain the Phase E Grounding-DINO tiny or SAM ViT-B model directories.

A research-only observer-runtime.lock now records the previously validated Phase E target versions and model IDs. DINOv3 stays unresolved until an official compatible model identifier is verified rather than guessed.

Gate result: environment/cache recovery is complete. Existing assets cannot close the runtime gate. Next is one shared observer environment from the pinned target, followed by Diagnostic-2 real measurements.


## Runtime smoke 2026-10-04

- Shared environment: `C:\\Work\\SharedAI\\minimalizer-observers` (research-only; production requirements unchanged).
- PyTorch 2.11.0+cu128 on NVIDIA GeForce RTX 5060: PASS; real CUDA tensor computation completed.
- Transformers 5.17.0: PASS.
- Grounding-DINO `IDEA-Research/grounding-dino-tiny`: PASS; real model loaded on CUDA, about 660 MiB allocated at smoke point.
- SAM `facebook/sam-vit-base`: PASS; real model loaded on CUDA, about 358 MiB allocated at smoke point.
- DINOv3 `facebook/dinov3-convnext-tiny-pretrain-lvd1689m`: HOLD. The official Hugging Face repository is gated and returned HTTP 401 without user authentication. Meta's official DINOv3 README likewise requires obtaining model-weight access before pretrained-weight use. No credential was requested, stored, or bypassed.

Gate decision: observer runtime infrastructure PASS for CUDA + Grounding-DINO + SAM; DINOv3 pretrained semantic observer remains HOLD on an external access prerequisite. Diagnostic-2 may exercise the regional observer path now, but a DINOv3-backed adoption decision remains fail-closed until official pretrained weights are legitimately available.


## Diagnostic-2 source binding 2026-10-04

Canonical source identity was resolved without using the dirty local repository as authority.

- Hyakuto-Kyoko: `Hyakuto-Kyoko_list_thumb.png`, 340x340 RGBA, SHA-256 `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`.
- Juufuutei-Raden: `Juufuutei-Raden_list_thumb.png`, 340x340 RGBA, SHA-256 `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`.
- GitHub stage manifests supplied the canonical names and hashes.
- Google Drive supplied the binary PNGs.
- Both downloaded binaries were independently SHA-256 verified and exactly match the GitHub stage-manifest hashes.

This closes the Diagnostic-2 source-provenance gate. Observer measurements must bind evidence to these hashes; filename-only selection is prohibited.


## Diagnostic-2 real Grounded-SAM observation 2026-10-04

The shared observer runtime was verified on the RTX 5060 with Python 3.11, torch 2.11.0+cu128, CUDA available, and Transformers 5.17.0. Cached observer weights were reused with local-files-only for the final two-case run.

The exact SHA-bound Diagnostic-2 inputs were evaluated with `IDEA-Research/grounding-dino-tiny` + `facebook/sam-vit-base` using the existing Phase E prompt and rembg subject authority.

Results:

- Hyakuto-Kyoko active-area ratios: hair 0.0501903, face-skin 0.0291003, limb 0.0151298, accessory 0.0768339; 20 accepted detections, 0 oversize rejects; 1.100 s.
- Juufuutei-Raden active-area ratios: hair 0.1448270, face-skin 0.0241436, limb 0.1239792, accessory 0.0215225; 19 accepted detections, 2 oversize rejects; 0.263 s.
- Two-case mean inference time: 0.681693 s/image.
- Peak CUDA memory: 1378.613 MB.
- No zero-area semantic channel for hair, face-skin, limb, or accessory.
- Spatial confidence maps were emitted as per-case NPZ files plus a contact sheet and report JSON in the isolated local evidence directory.

Interpretation: real regional observation is now operational on Diagnostic-2 and is no longer represented only by injected test fixtures. This is observation evidence, not yet an adoption PASS. The current `RegionObservation` coverage contract still cannot prove spatial IoU/shape retention, so the next evaluation step must bind these spatial maps to an immutable overlap descriptor before any strong regional-retention claim.


## Spatial regional guard contract 2026-10-04

Regional evaluation now distinguishes coverage retention from spatial retention. `RegionObservation` can carry an immutable rectangular boolean spatial mask; `spatial_iou` and `regional_spatial_iou` measure overlap, while the legacy coverage ratio remains available for compatibility. Equal coverage with relocated geometry can therefore fail the regional gate.

The A/B evaluator now requires spatial regional evidence before ADOPT. Missing spatial evidence yields HOLD; a critical-region IoU below the current research floor of 0.85 yields REJECT. Missing masks in an invoked spatial guard fail closed.

Focused P0-P5 + spatial-guard suite: 31/31 PASS in the isolated research worktree. This contract removes the earlier coverage-only limitation, but the existing Grounded-SAM confidence NPZ evidence still needs an adapter that thresholds/binds those maps into these immutable masks for baseline-vs-candidate Diagnostic-2 comparison.


## Grounded-SAM confidence-to-mask adapter 2026-10-04

A canonical research adapter now converts the existing Phase E NPZ evidence (`labels` + `confidence[label,y,x]`) into immutable `RegionObservation.spatial_mask` values using the unchanged Phase E active threshold `confidence >= 0.20`. It rejects malformed and non-finite evidence and does not mutate source pixels or vector geometry.

Adapter-focused regional/evaluation suite: 21/21 PASS. Real Diagnostic-2 source evidence was also passed through the adapter. The recovered coverages exactly reproduce the prior Grounded-SAM report, and self-overlap is 1.0 for hair, face-skin, limb, and accessory on both Kyoko and Raden.

This closes the confidence-map-to-spatial-contract bridge. It does not by itself measure Minimalizer retention: the next gate requires rendering the SHA-bound baseline/candidate outputs, observing them with the same frozen Grounded-SAM configuration, and comparing their masks against these source observations.


## Source-to-baseline spatial observation 2026-10-04

A strict current-code shadow regeneration was attempted for both Diagnostic-2 cases in the isolated Python 3.11 analysis environment. Kyoko completed Phase 3-12 with selected profile `aggressive`, 34 primitives, silhouette IoU 0.96808, final SHA-256 `045f72b867d53215091255f56d3a399fb548c474d2330107c9a8d8b4043c845c`. Raden failed closed in current Phase 12 because a 51-pixel `__unbound__` baseline part was removed by both candidates and therefore appeared in `missing_visible_parts`. The input SHA `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00` matches the canonical Raden Diagnostic-2 source, so this is a current-code behavior drift rather than an input mismatch.

For observation only, Raden therefore uses the preserved canonical Drive Phase-12 artifact from 2026-09-29; Kyoko uses the newly regenerated current baseline. These are explicitly not treated as a symmetric adoption A/B pair.

Frozen Grounded-SAM observation of those baseline images completed successfully. Source-to-baseline spatial IoU at the unchanged confidence >= 0.20 threshold was:

- Kyoko: hair 0.018097, face-skin 0.568797, limb 0.0, accessory 0.122446.
- Raden: hair 0.0, face-skin 0.678067, limb 0.0, accessory 0.0.

The baseline observer also produced zero active limb area for both cases and zero active hair area for Raden. Therefore these raw semantic-mask IoUs cannot currently serve as hard Minimalizer retention gates: the observer distribution changes substantially after geometric abstraction. This is valuable negative evidence. The next refinement step must compare source and rendered candidates with an abstraction-aware spatial descriptor or a calibrated observer threshold rather than promoting these raw values into adoption thresholds.


## Abstraction-aware spatial descriptor PoC 2026-10-04

Raw mask IoU was demoted from hard-gate candidacy after the source-to-baseline experiment. A research-only abstraction-aware descriptor now combines normalized region coverage, centroid retention, bounding-box overlap, and an 8x8 area-resampled occupancy map. The score weights are coverage 0.15, centroid 0.25, bbox 0.20, occupancy 0.40. These are PoC weights, not canonical thresholds.

Unit behavior is fixed by tests: identical masks score 1.0; a small boundary perturbation is intentionally scored more leniently than raw pixel IoU; large relocation remains penalized; a missing region cannot be mistaken for retention. Focused spatial/regional suite: 13/13 PASS.

Diagnostic-2 source-to-baseline observations:

- Kyoko: hair 0.901345, face-skin 0.845991, limb 0.393948, accessory 0.694276.
- Raden: hair 0.342069, face-skin 0.867721, limb 0.350408, accessory 0.691240.

Interpretation: the descriptor successfully recovers useful spatial agreement for Kyoko hair and both face-skin channels despite very low raw mask IoU. It does not rescue channels for which the frozen semantic observer emits no candidate region, notably both limb channels and Raden hair. Therefore the descriptor is promising as an abstraction-tolerant measurement, but it is still HOLD as a hard adoption gate. Missing semantic detections must remain explicit evidence rather than being hidden by high background occupancy similarity.

Next: add DINOv3 patch-level spatial evidence as an observer-independent companion, then evaluate a combined descriptor without weakening the existing fail-closed identity/silhouette contract.


## DINOv3 patch-spatial contract 2026-10-04

The pinned model ID `facebook/dinov3-convnext-tiny-pretrain-lvd1689m` was reverified against the official Meta/Hugging Face release. It is a 27.8M-parameter DINOv3 ConvNeXt Tiny image-feature-extraction model. The repository is gated. The shared local observer runtime currently has no cached processor/model for this ID and no HF token, so real model download/inference was not bypassed or fabricated.

A model-independent immutable DINO spatial contract was completed instead. It accepts a finite dense feature map and records aligned patch features plus a global feature. Comparison reports global cosine, aligned patch cosine, coarse 4x4 spatial cosine, and a research score. The contract specifically detects spatial relocation even when global feature means are unchanged.

Focused DINO-spatial + abstraction-spatial tests: 8/8 PASS. Real Diagnostic-2 DINO measurements remain HOLD until the gated weights are legitimately available to the isolated observer runtime. No adoption threshold was invented from fixture data.


## Real DINOv3 Diagnostic-2 observation 2026-10-04

The gated official model `facebook/dinov3-convnext-tiny-pretrain-lvd1689m` was obtained through the authenticated Hugging Face device flow and cached locally. No token was written to the repository. The model loads offline from cache after acquisition.

Runtime verification on the isolated observer environment:

- model: DINOv3 ConvNeXt Tiny, 27.8M parameters
- input tensor: 1x3x224x224
- final dense feature map: 7x7x768
- CUDA execution: PASS on RTX 5060
- measured peak CUDA allocation during Diagnostic-2 extraction: about 129.29 MB after model load

Source-to-baseline Diagnostic-2 results using the same frozen model and preprocessing:

- Hyakuto-Kyoko: global cosine 0.633302, aligned patch cosine 0.612491, coarse spatial cosine 0.576816, research score 0.604167.
- Juufuutei-Raden: global cosine 0.521796, aligned patch cosine 0.507560, coarse spatial cosine 0.421382, research score 0.480245.

The first measured source extraction included CUDA warm-up (1.224 s); subsequent image inference was roughly 0.0046-0.0089 s, so the warm-up value must not be treated as steady-state throughput.

Interpretation: unlike cross-style Grounded-SAM semantic masks, DINOv3 returns non-degenerate dense evidence for both cases without requiring named-part detection. This supports using frozen DINO patch features as an independent companion observer. The current scores are evidence, not calibrated pass/fail thresholds. DINOv3 is therefore ADOPTED as research observer evidence but remains HOLD as a standalone hard adoption gate.

Focused DINO/SAM/spatial/evaluation suite after real inference: 29/29 PASS.


## Combined candidate gate 2026-10-04

A research-only combined candidate gate now composes the existing objective/identity/silhouette/determinism contract with independent observer trends. Identity and silhouette remain hard authority and cannot be overridden by DINOv3 or Grounded-SAM evidence. Observer evidence is comparative: DINO and abstraction-aware regional scores are classified as IMPROVED, STABLE, REGRESSED, or UNAVAILABLE relative to the baseline. No absolute DINO/SAM pass threshold is inferred from Diagnostic-2.

Decision precedence is fail closed: hard-guard failure => REJECT; required hard evidence missing => HOLD; DINO or named-region regression => REJECT; DINO unavailable => HOLD; otherwise an objective improvement with hard guards passing and non-regressing observers may ADOPT. Raw cross-style SAM pixel IoU is deliberately excluded from this composed authority.

Focused combined-gate suite: 25/25 PASS. Tests lock the critical invariant that better observer scores cannot rescue an identity hard-guard failure.

The gate is ready for a real rendered differentiable candidate A/B. That next measurement must compare baseline and candidate observer evidence generated from the same frozen DINO/SAM runtimes; fixture scores are not adoption evidence.


## First real candidate preflight: polygon-only baseline 2026-10-04

The first planned real Kyoko differentiable candidate was intentionally stopped at preflight rather than fabricated. The current Phase12 selected profile is `aggressive` with 34 primitives, and all 34 are polygons; there are zero rectangle or ellipse primitives. The existing differentiable geometry optimizer only has safe tensorization/raster contracts for rectangle and ellipse, so applying it to this baseline would not constitute a real candidate.

This exposed the next required implementation boundary: fixed-topology polygon refinement. A fail-closed polygon guard was added before any real polygon optimization. It requires unchanged vertex count, finite/in-canvas vertices, preserved winding, minimum 90% signed-area magnitude by default, no segment self-intersection, and a default 4px per-vertex trust region. Focused polygon + combined-gate tests: 14/14 PASS.

No Kyoko candidate score was fabricated and no Phase12 artifact was mutated. Next step is to connect diffvg polygon vertices to this guard, optimize only within the trust region, render the guarded candidate, and then run the already-completed combined observer gate.


## First real guarded polygon candidate 2026-10-04

The first real differentiable Minimalizer candidate was generated from the current Kyoko Phase12 selected output. Preflight showed the selected profile contains 34/34 polygons, so the experiment used one existing face polygon (`phase12-aggressive-0018`) with fixed vertex count and no topology/material/primitive-count changes.

The diffvg optimization targeted the canonical Phase4 face mask for 30 Adam steps. Vertex displacement was parameterized inside a 4px Euclidean trust radius (2.75px per-axis tanh bound), then validated by the polygon guard. Result: local differentiable mask loss 0.00584775 -> 0.00201125 (about 65.6% reduction), guard PASS. A first overlay-only render was correctly rejected as evaluation methodology because it could leave old pixels behind; the probe was changed to fully rerender all 34 Phase12 primitives in raster order before observer evaluation.

Full-rerender candidate versus baseline changed 252 pixels with RGB MAE 0.068924. Baseline-relative foreground silhouette IoU was 0.996765 and a diagnostic normalized pixel-MSE identity proxy was 0.999899. The latter is explicitly a proxy, not the canonical Phase14 identity metric.

Frozen DINOv3 source-relative evidence remained within the research stability tolerance: baseline score 0.604167, candidate 0.595553, delta -0.008614. Global/aligned/coarse components were 0.633302/0.612491/0.576816 baseline and 0.622417/0.605000/0.568058 candidate.

Grounded-SAM abstraction evidence exposed observer instability. Source-relative hair slightly improved 0.901345 -> 0.906210 and accessory was essentially stable 0.694276 -> 0.693231, while limb stayed at 0.393948. However face-skin collapsed from 0.845991 to 0.388360 because the candidate Grounded-SAM run returned zero face-skin active area after only this small geometric edit. Under the current fail-closed combined observer semantics, this is a named-region regression and the candidate is REJECTED.

This rejection is not evidence that the rendered face is visually destroyed. Combined with the earlier source-to-Minimalizer SAM failures, it is evidence that Grounded-SAM rediscovery of named parts is too brittle to act as an unconditional hard veto across strongly abstracted renders. DINO remained non-degenerate and stable. The next evaluator revision should use renderer-owned semantic part masks for hard geometric retention, keep DINO as independent perceptual evidence, and demote Grounded-SAM named-part rediscovery to supporting diagnostic evidence unless calibrated on a larger corpus.


## Renderer-owned semantic authority 2026-10-04

The combined candidate gate was revised after the first real candidate exposed Grounded-SAM cross-style brittleness. Hard semantic retention now comes from renderer-owned semantic masks rather than named-part rediscovery. DINOv3 remains an independent perceptual/spatial veto/hold observer. Grounded-SAM abstraction scores remain recorded diagnostic evidence but no longer veto a candidate by themselves.

The ownership gate is fail closed and compares rasterized masks for canonical semantic ownership. Its current research default is per-critical-part IoU >= 0.985. Missing ownership evidence => HOLD; ownership regression => REJECT. Tests explicitly verify that a Grounded-SAM named-part regression cannot veto a candidate when hard ownership, identity/silhouette, objective and DINO evidence are safe, while an ownership regression cannot be rescued by improved DINO. Focused authority suite: 20/20 PASS.

The same first Kyoko face candidate was then measured with renderer-owned geometry rather than SAM rediscovery. The selected face polygon changed from its canonical Phase12 geometry to the guarded diffvg proposal with ownership IoU **0.911208**, below the research hard-retention floor 0.985. Therefore the candidate remains **REJECT**, now for a renderer-grounded reason rather than because Grounded-SAM failed to rediscover face-skin. This is a materially stronger rejection rationale.

The result also shows that the 4px polygon trust region is too permissive for a large identity-critical face primitive even though whole-image silhouette and DINO stayed stable. The next optimization revision should make the trust region semantic-part-aware (face much tighter than clothing/hair) and/or include ownership-mask retention directly in the differentiable objective instead of relying only on a post-hoc guard.


## Semantic-part-aware trust experiment 2026-10-04

Polygon refinement now has an explicit semantic trust policy and a differentiable ownership-retention term. Face uses a much tighter trust radius than hair/clothing, and the optimization objective is target-mask loss plus a weighted MSE to the original renderer-owned polygon mask. Focused semantic-trust/ownership/polygon/candidate tests: 19/19 PASS before the real probe.

Kyoko face sweep results, all using the same canonical Phase12 polygon and Phase4 face target:

- Original permissive probe: ownership IoU 0.911208, target loss 0.005848 -> about 0.00201.
- radius 0.45, ownership weight 4: IoU 0.974141, target loss 0.005848 -> 0.005545.
- radius 0.20, weight 4: IoU 0.973074, target loss -> 0.005529.
- radius 0.45, weight 12: IoU 0.976571, target loss -> 0.005734.
- radius 0.45, weight 40: IoU 0.977169, target loss -> 0.005815.
- radius 0.08, weight 12: IoU 0.974891, target loss -> 0.005768.

The experiment therefore improved ownership retention substantially but did **not** reach the 0.985 hard floor while preserving a useful target improvement. Merely shrinking the continuous subpixel radius did not monotonically improve rasterized ownership IoU because the post-hoc ownership measurement uses hard rasterization and is sensitive to boundary pixel quantization. The 0.985 threshold was not weakened to force a pass.

Decision: keep the semantic-aware objective, but HOLD face-polygon adoption. The next refinement should optimize a soft differentiable overlap surrogate (soft IoU/Dice) and select/checkpoint the best iterate satisfying a hard-raster ownership constraint, rather than returning the final Adam iterate. This turns ownership from a weighted preference into a constrained optimization problem.


## Constrained optimization and semantic-part union breakthrough 2026-10-04

A constrained checkpoint optimizer was added. It records every Adam iterate, measures hard-raster renderer ownership, and selects the lowest target-loss checkpoint that both improves on the initial target loss and satisfies the hard ownership floor. If none exists, it fails closed with `NO_FEASIBLE_CHECKPOINT`. Soft Dice to renderer ownership is also used inside the differentiable objective. Focused constrained/ownership/trust/polygon/candidate tests: 23/23 PASS, then 24/24 PASS after semantic-union coverage was added.

For the Kyoko face polygon, 60 steps produced no checkpoint satisfying ownership IoU >= 0.985 plus target improvement. This confirms that the large identity-critical face primitive should currently remain frozen rather than weakening the gate.

The same primitive-level 0.985 constraint also rejected three tested hair fragments. This revealed a granularity error: semantic identity belongs to the complete composition part, not each individual hair fragment. The hard ownership constraint was therefore changed to the union mask of all renderer-owned polygons with the same `composition_part`.

With semantic-part union ownership, Kyoko hair primitive `phase12-aggressive-0001` produced the first feasible constrained candidate. The selector chose step 4 automatically: target loss 0.151622519 -> 0.151593864, hair-union ownership IoU **0.998245**, polygon guard PASS, trust radius 1.5. The full 34-primitive scene was then rerendered rather than overpainted.

Independent evidence on the full rerender: DINOv3 source-relative score 0.604167 baseline -> 0.599238 candidate, delta **-0.004929**, inside the current research stability tolerance. Baseline-relative whole-foreground silhouette IoU was **0.985505**, with 920 changed pixels. Thus the candidate clears the current 0.985 silhouette floor by a narrow margin and strongly clears semantic hair ownership. This is the first real candidate to satisfy the core renderer-grounded retention constraints while improving its local source-target objective.

Status remains research ADOPT-for-next-evaluation, not production adoption. The improvement magnitude is small and the silhouette margin is narrow. Next work should batch the remaining hair primitives, retain only individually feasible proposals, and compose them incrementally with a scene-level silhouette/DINO rollback gate so local improvements cannot accumulate into a global regression.


### Hair batch feasibility

A reusable semantic-part batch runner was added and executed across all four Kyoko Phase12 hair polygons. Results: primitive 0000 had no feasible checkpoint and remained frozen; primitives 0001, 0002 and 0003 were feasible. Their selected ownership IoUs were 0.999198, 0.998647 and 0.999248 respectively, each with a real but small target-loss improvement and polygon guard PASS. This validates fail-closed per-proposal search rather than forcing every primitive to move.

A scene-level rollback policy was then introduced for incremental composition. Every accepted local proposal must keep whole-scene silhouette IoU >= 0.985 and DINO score within 0.01 of the baseline reference; otherwise that proposal is rolled back. This is the next guard against individually safe local changes accumulating into a global identity regression.


## Renderer-normalized scene gate and Kyoko cumulative candidate 2026-10-04

A zero-change rerender control exposed an evaluation confound: reconstructing the unchanged Phase12 scene with the research PIL compositor already differs from the preserved Phase12 PNG by 917 pixels and gives silhouette IoU 0.985580. Therefore the earlier near-0.985 scene scores were dominated by renderer mismatch rather than optimizer geometry. Scene rollback evidence is now interpreted against a zero-change image produced by the same research compositor. Production adoption must eventually use the canonical renderer directly; thresholds must not compare images from different rasterizers.

Under renderer-normalized evaluation, the three-hair candidate has silhouette IoU 0.999297 relative to the zero-change control. An exhaustive seven-subset hair search was added as reproducible tooling. The full three-hair set was retained because it preserves ample normalized scene margin while keeping all three local objective improvements.

Major-clothing search found 3/8 feasible local proposals (0025, 0026, 0027). Accessory/held-object found 0/2 and remained frozen. Lower-body found 1/4 feasible (0011). Left arm found 1/3 feasible (0037); right arm found 0/1. Torso found 1/2 feasible (0020). Neck found 0/1. Unknown `__unbound__` primitives were never optimized.

Head was given a tighter 0.60 px trust radius because it lies close to the identity core. It produced 2/5 feasible proposals (0051, 0053); face itself remains completely frozen because no face checkpoint met the hard constraint.

The cumulative Kyoko v7 research candidate contains 11 constrained replacements: hair 0001/0002/0003, major clothing 0025/0026/0027, lower body 0011, left arm 0037, torso 0020, head 0051/0053. Against the same-renderer zero-change control it has whole-scene silhouette IoU **0.997456**. Source-relative DINOv3 score is 0.598479 control versus 0.597705 candidate, delta **-0.000774**, comfortably inside the current research stability tolerance. The candidate therefore passes the current renderer-normalized scene rollback checks while every included primitive also passed semantic-part ownership and polygon guards.

This is still a research candidate, not a production migration decision. The local objective improvements are individually small, Diagnostic-2 currently has only Kyoko as a fully runnable current Phase12 case, and the research compositor must be replaced by or proven equivalent to the canonical renderer before production gating. Next expansion should repeat the exact constrained/normalized protocol on an independent character after resolving the Raden Phase11/12 drift, rather than tuning thresholds further on Kyoko.


## Raden drift isolation and independent-character control 2026-10-04

The first reproducible Raden drift was isolated to Phase 4, not Phase 12. Current Phase 3 subject extraction is byte-identical to the preserved repository diagnostic (Raden subject-mask SHA256 matches), while the current Phase 4 part map differs. Running the exact pre-`d118e60` Phase 4 implementation (`8d95659`) against the same current Phase 3 input reproduces the preserved Raden `04_part_map.png` byte-for-byte. This rules out the current Python/MediaPipe/RTMLib environment as the primary cause of this drift.

Commit `d118e60` introduced a large Phase 4 semantic-rescue expansion, including guarded hair hints, face-side/bright hair rescue, unknown-component rescue, owner rescue, and semantic-head refinement. On Raden, current versus preserved masks differ materially in hair (+979 px) and head (-3333 px), with smaller changes in right arm, torso, major clothing and unknown; face, left arm, lower body, neck and accessory remain identical. Those Phase 4 changes propagate into Phase 6 region count (334 preserved versus 364 current) and eventually the failing current Phase 12 path.

A controlled run using the preserved/pre-`d118e60` Phase 4 semantics followed by the **current** Phase 5-12 implementation passes end-to-end: Phase 11 has 30 primitives; Phase 12 aggressive selects 22, silhouette IoU 0.991528, and no missing visible parts. This does not reproduce the historical 74→55 counts because downstream stages have legitimately evolved, but it proves the Phase 4 drift is sufficient to explain the current Raden stop. Production Phase 4 is not reverted by this research result; the old Phase 4 output is used only as a frozen independent-character control until a guarded production fix is designed.

The Raden zero-change research compositor itself differs from the canonical Phase 12 PNG (silhouette IoU 0.994397, 456 changed pixels), reinforcing the same-renderer normalization requirement found on Kyoko. Under that normalized control, three feasible Raden hair proposals (0003, 0005, 0006) compose to silhouette IoU **0.998715** with 152 changed pixels. Primitive 0002 had no feasible checkpoint and 0004 was rejected by the canvas topology guard. This is the first independent-character evidence that the constrained polygon protocol transfers beyond Kyoko. DINO confirmation for this cumulative Raden candidate remains pending because the local DINO comparison process stalled during this run; no semantic score is inferred or fabricated.


## Raden DINOv3 semantic gate 2026-10-04

The previously reported local DINO stall was diagnosed as an observability problem rather than a model/runtime failure. Hugging Face authentication is valid, CUDA is available on the RTX 5060, and the cached official `facebook/dinov3-convnext-tiny-pretrain-lvd1689m` processor/model load successfully. The Transformers cold import can remain silent for more than the RDC quick-return window, so the research pair runner now emits explicit progress before processor load, model load, source inference, baseline inference, and candidate inference.

Real source-to-render DINOv3 evidence for the independent Raden control:

- normalized baseline: global 0.510325, aligned patch 0.516570, coarse patch 0.438307, research score 0.487929
- constrained hair candidate (0003 + 0005 + 0006): global 0.520027, aligned patch 0.518557, coarse patch 0.441897, research score 0.492020
- research score delta: **+0.004091**
- same-renderer silhouette IoU candidate/control: **0.998715**
- changed pixels: 152

All three DINO dimensions improve while the silhouette remains within the already conservative local guard. This is a **Raden hair semantic PASS for the current PoC protocol**, not a production adoption threshold. It is independent-character transfer evidence beyond Kyoko. Primitive 0002 remains no-feasible-checkpoint and 0004 remains topology/canvas rejected; fail-closed behavior is preserved.


## Raden torso + clothing cumulative transfer 2026-10-04

The independent-character run was extended without relaxing any existing trust/ownership thresholds. Adding torso primitive `phase12-aggressive-0000` to the three accepted hair replacements yields same-renderer silhouette IoU **0.997166** (257 changed pixels). Its local checkpoint passed at ownership IoU 0.989834. Source-relative DINOv3 improves from the normalized baseline score 0.487929 to 0.492394, delta **+0.004465**; global, aligned-patch, and coarse-patch cosine all remain above baseline.

The two lower-complexity major-clothing polygons were then evaluated before touching the 75/85-vertex clothing shapes. Primitive `0015` (28 vertices) passed at ownership IoU 0.986376 and primitive `0016` (11 vertices) passed at 0.990751. The cumulative six-replacement Raden v3 candidate (hair 0003/0005/0006 + torso 0000 + clothing 0015/0016) has same-renderer silhouette IoU **0.996473** with 335 changed pixels.

Its real DINOv3 source-relative metrics are: global **0.532881**, aligned patch **0.524440**, coarse patch **0.449059**, research score **0.499745**. Against the unchanged normalized baseline score 0.487929, the cumulative delta is **+0.011816**. All three perceptual dimensions improve, and the DINO gain grows substantially after the clothing additions rather than merely staying inside a tolerance band.

This is stronger cross-character transfer evidence for the constrained refinement protocol. The two large 75/85-vertex clothing polygons remain intentionally unoptimized pending need: the smaller safe changes already produce a positive semantic gain, so extra high-dimensional movement is not justified by the current evidence. No production threshold is inferred from two characters.


## Google Drive preservation gate restored 2026-10-04

A preservation-process miss was identified during the Differentiable Minimalization PoC: research images had been allowed to remain under local Temp while optimization continued, despite the project rule that phase result images are preserved to Google Drive. Cause: the PoC execution loop did not encode Drive preservation as a phase-completion gate. Impact: intermediate Kyoko/Raden evidence temporarily existed only in local working storage. Correction: optimization was paused and existing outputs were retrospectively copied to the canonical Minimalizer Drive hierarchy. Prevention: a phase is not considered preserved/complete until its result images are copied to Drive and the preservation location is recorded; local Temp remains scratch only.

Drive preservation root: `Minimalizer / Differentiable Minimalization Research`, separated from the existing `Minimalizer ZeroBase 2nd Cycle` archive. Subfolders: `Kyoko`, `Raden`, and `Comparison Evidence`. Under Kyoko and Raden, Phase_03 through Phase_12 image outputs are preserved by phase. Research cumulative images are preserved at the character-folder level.

Current preservation inventory after retrospective copy:
- Kyoko: 48 PNG files total. Phase image counts P03..P12 = 3,3,2,4,5,4,3,3,3,6 plus research cumulative/control images.
- Raden: 41 PNG files total. Phase image counts P03..P12 = 3,3,2,4,5,4,3,3,3,6 plus research cumulative/control images.
- Kyoko cumulative/control set includes current baseline, zero-change rerender control, early diffvg/semantic candidates, hair candidate, v1-v7, with v7 as the current research candidate.
- Raden cumulative/control set includes Phase14 historical baseline, zero-change rerender control, hair v1, hair+torso v2, and cumulative v3.

The local Google Drive mount reported all files copied successfully. Connector-side search indexing had not yet surfaced the newly copied v7 file at the immediate verification point, so index visibility is explicitly **pending** rather than falsely reported as verified. Filesystem-level Drive-mount counts above are verified. Future phases must perform both copy verification and, when available after sync propagation, connector-side visibility verification.


## Preservation verification and first Phase 4 guard 2026-10-04

Google Drive connector indexing now exposes both `Kyoko_v7_head_try.png` under the research Kyoko folder and `Raden_v3.png` under the research Raden folder. The retrospective preservation gate is therefore **PASS** at both mount-copy and connector-visibility levels.

The first guarded Phase 4 repair was implemented on the research branch. Raden's largest single Phase 4 drift was the semantic-head refinement: preserved/pre-`d118e60` head coverage was 14,526 px while the unguarded current refinement reduced it to 11,193 px (3,333 px removed). `_semantic_head_mask` now treats face-local semantic support as evidence rather than authority and fails closed when a proposed refinement retains less than 80% of the structural head envelope. The existing synthetic remote-spill cleanup test remains valid, and a new destructive-shrink regression test locks the fail-closed behavior. Phase 4 focused tests: **14 passed**.

Real Raden rerun with the guard restores the head mask **exactly** to the preserved 14,526 px mask (XOR difference 0) while leaving the newer hair/owner-rescue behavior available for separate evaluation. Remaining preserved-vs-current differences after the head repair are hair +979 px (1,013 XOR), torso -604 px, right arm -272 px, major clothing -120 px, and unknown +17 px. This isolates the next repair target without reverting the whole `d118e60` feature set.
