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


## Phase 4 bright-hair rescue guard 2026-10-04

The remaining Raden hair drift was isolated to one connected component: 996 newly added pixels at bbox x=81..135, y=159..240 (centroid about 111.6,197.6), with only 17 old hair pixels removed. Its median RGB was approximately (205,192,185). In Lab space its median differed from the preserved hair prototype primarily in luminance (L delta about 141), while the rescue path had been designed specifically to tolerate bright strands. This made proximity/brightness alone too permissive.

The bright face-side hair rescue now requires chroma agreement with the established hair mass before adoption. Luminance remains free to differ, preserving the intended bright-strand capability, while median a/b chroma distance must be <= 6.0. A pale face-adjacent regression test was added. Focused Phase 4 suite: **15 passed**.

Real Raden after the semantic-head and chroma guards now matches the preserved pre-d118 Phase 4 masks exactly for head, face, neck, torso, both arms, lower body, major clothing, and accessory. Hair differs by only 17 pixels (19,467 preserved vs 19,450 guarded), and those same 17 pixels remain unknown (445 preserved vs 462 guarded). The previous +996 false bright-hair component and the owner shifts (-604 torso, -272 right arm, -120 major clothing) disappear as downstream consequences. This reduces the Phase 4 drift to a single 17-pixel hair/unknown residual rather than broad semantic reassignment.


## Phase 4 guard closure and downstream validation 2026-10-04

The final preserved-vs-guarded Raden Phase 4 residual is 17 pixels: one 5x5-connected hair-adjacent component at bbox [117,43,5,5], median RGB about (197,189,188). All 17 pixels are within a 3px dilation of the guarded hair mask and the residual is about 0.015% of the 340x340 image. No Raden-specific recovery rule is added: the residual is intentionally accepted to avoid overfitting a general semantic decomposition rule to one character.

With the semantic-head and bright-hair chroma guards active, Raden was rerun through the strict ZeroBase2 Phase 3->12 shadow pipeline. Result: **PASS**, 22 primitives, selected profile `aggressive`, silhouette IoU **0.991045**, final SHA256 `7a0a3d5c948f23f5ab5f5d17ad5250eeea1692209ee6d304a9e107b9fa870b8e`, elapsed about 14.58 s. The previous Phase 12 `missing_visible_parts=["__unbound__"]` failure did not recur.

Per the restored preservation rule, the guarded Raden Phase 3-12 result images were copied to Google Drive under `Minimalizer / Differentiable Minimalization Research / Raden / Phase4_Guarded_Shadow`. The preserved set contains 37 PNG files including `Raden_phase12_guarded_final.png`. Local Temp remains scratch only.

**Phase 4 rescue repair status: CLOSED for this research gate.** The repair is minimal rather than a wholesale revert of `d118e60`: valid newer rescue behavior remains, destructive semantic-head shrinkage fails closed, pale face-adjacent bright-hair false rescue is chroma-guarded, and the independent Raden character reaches Phase 12 successfully.


## Guarded-current Raden differentiable revalidation 2026-10-04

After closing the Phase 4 rescue repair, the differentiable hair protocol was rerun against the current guarded Raden Phase 3-12 shadow output rather than the earlier preserved/pre-d118 Phase 4 control. The same three hair primitives (0003, 0005, 0006) were feasible; 0002 remained NO_FEASIBLE_CHECKPOINT and 0004 remained canvas-guard rejected.

The composed candidate has same-renderer silhouette IoU **0.998715** with 152 changed pixels. Frozen DINOv3 source-relative score improves from **0.487929** to **0.492020** (delta **+0.004091**); global, aligned-patch, and coarse-patch cosine all improve. This removes the temporary dependency on the preserved Phase 4 control and confirms that the repaired current semantic decomposition still supports the independent-character differentiable hair PASS.

A latent reproducibility bug in `compare_dinov3_pair.py` was also fixed: escaped newline literals in the progress/load block had made the committed runner syntactically invalid even though prior measurements used a temporary corrected copy. The committed runner is now directly executable.

Drive preservation: current guarded zero-change control, cumulative hair candidate, three accepted primitive images, and metrics JSON were copied to `Minimalizer / Differentiable Minimalization Research / Raden / Phase4_Guarded_DiffMin`.

**Gate result: PASS.** Current guarded Raden is now a valid independent-character control for the constrained Differentiable Minimalization protocol. Next expansion should evaluate additional semantic parts on this repaired current baseline before any Approved-18 escalation.

## Guarded-current Raden semantic expansion v1 2026-10-04

The repaired current Raden baseline was expanded beyond hair without changing the existing constrained protocol. Identity-core face/head/neck remained frozen for this step. Torso, right arm, major clothing, and lower body were searched with semantic-part ownership, polygon topology, and trust-region guards.

Feasible additions were torso 0000/0001, right-arm 0011, and major-clothing 0015/0016. Right-arm 0010 was canvas-guard rejected; major-clothing 0013/0014 and all three lower-body proposals had no feasible checkpoint and remained frozen. Together with the already accepted hair 0003/0005/0006, the cumulative candidate contains eight replacements.

Same-renderer silhouette IoU is **0.995840** with 403 changed pixels. Frozen DINOv3 source-relative score improves from **0.487929** baseline to **0.498803** candidate, delta **+0.010874**. Candidate global/aligned/coarse cosines are 0.532411 / 0.523671 / 0.447625, all above baseline.

Drive preservation: cumulative candidate, five newly accepted primitive images, and metrics JSON were copied to `Minimalizer / Differentiable Minimalization Research / Raden / Phase4_Guarded_DiffMin / Semantic_Expansion_v1`.

**Gate result: PASS.** The repaired current Raden baseline supports constrained semantic expansion beyond hair while preserving scene silhouette and improving independent DINO evidence. Lower-body and high-dimensional clothing proposals remain fail-closed rather than forcing motion. Next should test the remaining non-core left-arm/accessory groups, then decide whether the evidence justifies a tightly constrained head-only experiment; face remains frozen.

## Guarded-current Raden semantic boundary v2 2026-10-04

After Semantic Expansion v1 established an eight-replacement safe candidate, the remaining non-core groups were evaluated without relaxing the existing semantic trust policy. Left arm 0009 and accessory/held-object 0025 both returned NO_FEASIBLE_CHECKPOINT. The current eight-replacement candidate therefore remains the non-core safe frontier.

A head-only probe was then permitted under the existing identity-sensitive head trust radius (0.60, versus hair 1.50). Both head 0022 and 0023 returned NO_FEASIBLE_CHECKPOINT. The radius was not relaxed. Because no safe head evidence was obtained, face was not tested and remains frozen.

The retained frontier remains silhouette IoU **0.995840**, frozen DINOv3 score **0.498803**, delta **+0.010874** versus the guarded zero-change baseline. This step intentionally produces no additional visual mutation: its product is a measured semantic boundary and a fail-closed decision.

Drive preservation: retained frontier image plus left-arm, accessory, head batch evidence and boundary metrics were copied to `Minimalizer / Differentiable Minimalization Research / Raden / Phase4_Guarded_DiffMin / Semantic_Expansion_v2_Boundary`.

**Gate result: PASS_BOUNDARY_CONFIRMED.** Do not widen trust radii merely to force feasibility. Current Raden evidence supports hair + torso + one right-arm micro-plane + two clothing micro-planes; left arm, accessory, lower body, head, and face stay frozen at this stage. The next useful step is cross-character validation of this semantic-safe-frontier behavior rather than further fitting Raden.

## Cross-character validation: IMG_1205_4 2026-10-04

A new user-supplied 340x340 character image was admitted as a cross-character diagnostic without using the generated illustrative redraw as evidence. The canonical ZeroBase pipeline passed Phases 3-12. Phase 6 achieved subject-pixel coverage 1.0 with zero unbound pixels. Phase 12 selected the aggressive profile, reducing 150 Phase 11 primitives to 31 with silhouette IoU **0.969927**.

The unchanged Raden-derived semantic trust policy was then applied. Hair, torso, and right arm produced NO_FEASIBLE_CHECKPOINT. Major clothing produced four feasible micro-refinements (0021, 0023, 0024, 0026); two clothing proposals were self-intersection guard rejects and the rest failed closed. The four-replacement cumulative candidate has same-renderer silhouette IoU **0.998527** with 92 changed pixels.

Frozen DINOv3 source-relative score improves from **0.520927** to **0.522060** (delta **+0.001133**); global, aligned, and coarse components all improve. This is a second-character PASS with a different safe frontier from Raden, evidence that the protocol is not merely replaying Raden's accepted semantic parts.

Drive preservation: source, Phase 3-12 previews, Phase 12 final, zero-change control, differentiable candidate, and metrics were saved under `Minimalizer / Differentiable Minimalization Research / CrossCharacter_IMG_1205_4`.

**Gate result: PASS_CROSS_CHARACTER.** Keep the candidate diagnostic-only. The next escalation should add at least one more independent character before any Approved-18 corpus expansion or production routing change.

## Cross-character escalation gate: upstream robustness HOLD 2026-10-04

After the second-character PASS, two additional independent HoloMenImages cases were attempted with the same unmodified ZeroBase and Differentiable policies. This deliberately records pre-DiffMin failures instead of cherry-picking only compatible characters.

- **AZKi**: Phases 3-9 PASS; Phase 6 subject coverage 1.0 with zero unbound pixels. Phase 10 geometry FAIL on a single neck mass (`mass-0052`) because even the fidelity polygon did not satisfy the existing fidelity gate. Phase 11/12 correctly refused to run.
- **Gawr Gura**: Phase 3/4 PASS; Phase 5 structural graph FAIL because `neck-attached-to-torso` was missing. Phase 6 correctly refused to run.

No character-specific threshold was relaxed, no semantic ownership was overridden, and no generated/inpainted pixels were introduced. These failures occur upstream of Differentiable Minimalization and therefore do not invalidate the two successful differentiable diagnostics, but they block a meaningful three-character escalation.

**Decision: HOLD_CROSS_CHARACTER_ESCALATION.** The next engineering target is upstream ZeroBase cross-character robustness, specifically (1) conservative neck attachment inference for tiny-but-visible neck masks and (2) fidelity-safe geometry fallback for narrow neck masses. Re-run AZKi and Gawr Gura after a generic fix; only then resume the three-character Differentiable gate. Evidence and available previews/metrics are preserved in Drive under `CrossCharacter_AZKi` and `CrossCharacter_Gawr-Gura`.

## Neck robustness repair and third-character gate 2026-10-04

The upstream HOLD was addressed without character-specific thresholds. Phase 5 now permits only extremely small neck masks (<=0.1% of canvas) to use the existing 2x extended attachment gap, capped at confidence 0.55 and explicitly tagged as tiny-neck evidence. Phase 10 keeps all fidelity thresholds unchanged but gives neck fidelity fallback polygons a larger vertex budget (48x the normal neck budget, only after ordinary candidates fail) so fragmented narrow neck masses can be represented rather than accepted at lower fidelity.

Focused Phase 5/10 tests pass **21/21**, including a new tiny-neck conservative-gap regression test. Gawr Gura now passes Phase 5-11 but still fails Phase 12 on independent micro-part issues (41px left arm and 32px unbound mass); that case remains HOLD and was not forced through.

AZKi now passes Phase 10 (the former neck mass-0052 fallback reaches coverage/silhouette loss 0.159744) and Phase 12. Phase 12 selects aggressive with **27 primitives** and silhouette IoU **0.972287**. Under the unchanged Differentiable protocol, feasible proposals appeared in hair, torso, right arm, and major clothing. Groupwise DINO rejected hair (-0.000009), torso (-0.000077), and clothing (-0.002061). Right arm alone improved DINO from **0.638801** to **0.640704** (delta **+0.001903**) with same-renderer silhouette IoU **0.999668** and 20 changed pixels, so only right arm is retained.

**Gate result: PASS_THREE_CHARACTER.** Raden, IMG_1205_4, and AZKi now independently pass with different safe frontiers. Gawr Gura remains a recorded upstream Phase 12 robustness case, not a hidden exclusion. Evidence is preserved in Drive under `CrossCharacter_AZKi` and `CrossCharacter_Gawr-Gura`. This satisfies the previously required third independent character before a limited Approved-18 escalation; production routing remains unchanged.

## Approved-18 limited escalation wave 1 2026-10-04

After PASS_THREE_CHARACTER, the first six locked Approved-18 identities were run independently through the current guarded ZeroBase2 pipeline. The runner was corrected operationally so one fail-closed case does not suppress evaluation of later cases. No production routing or acceptance threshold was changed.

Wave result: **2/6 reached Phase 12 PASS**. Koganei Niko selected conservative at 28 primitives / silhouette IoU 0.985303. Shishiro Botan selected aggressive at 27 primitives / silhouette IoU 0.981583. The four HOLD cases remain explicit evidence: Kikirara Vivi stopped at Phase 10 fidelity (mass-0113, mass-0175), Isaki Riona at Phase 10 fidelity (mass-0247), Vestia Zeta at Phase 12, and Todoroki Hajime at Phase 5 structure.

The two Phase-12-pass cases then used the unchanged Differentiable protocol and groupwise DINO selection. Niko rejected hair (-0.001452), accepted torso (+0.003473) and major clothing (+0.000632); the cumulative accepted candidate uses five replacements, silhouette IoU 0.997769 / 207 changed pixels, and DINO 0.445039 -> 0.449609 (delta **+0.004571**). Botan accepted hair (+0.001265) and torso (+0.004580), rejected major clothing (-0.002338); the cumulative accepted candidate uses four replacements, silhouette IoU 0.994142 / 611 changed pixels, and DINO 0.571537 -> 0.577909 (delta **+0.006372**). Neither character produced a feasible right-arm proposal under the hard guards.

**Wave verdict: PASS_LIMITED_DIFFMIN / HOLD_FULL_APPROVED18.** Differentiable behavior generalizes positively to both upstream-pass cases, bringing independent successful identities beyond the original three. Full Approved-18 escalation is not authorized because upstream ZeroBase2 currently passes only 2/6 in this first locked wave. Next work should target the recurring upstream failure classes, especially Phase 10 fidelity, before expanding the remaining 12 identities. Evidence is preserved in Drive under `Approved18_Wave1_20261004`.

## Approved-18 wave 1 upstream fidelity repair 2026-10-04

Wave-1 Phase 10 failures were traced to raster semantics rather than permissive thresholds or insufficient vertex budgets. The fidelity fallback previously painted fill and hole rings in separate passes; on thin/nested masses this erased hole-boundary pixels. The generic repair now uses CHAIN_APPROX_SIMPLE, preserves an exact simple contour when the whole contour set fits the existing budget, and rasterizes all rings in one OpenCV FILLED draw so the even-odd rule is shared by Phase 10 and downstream composition. No fidelity threshold was relaxed.

Targeted tests: Phase-10 suite 12/12 PASS; Phase-10 plus stage-contract suite 31/31 PASS. Kikirara Vivi Phase 10 changed FAIL -> PASS (mean selected IoU 0.953976) and then reached Phase 12 PASS, aggressive 34 primitives, silhouette IoU 0.969395. Isaki Riona Phase 10 changed FAIL -> PASS (mean selected IoU 0.960649) and reached Phase 12 PASS, aggressive 31 primitives, silhouette IoU 0.980352. Existing Koganei Niko and Shishiro Botan remain Phase-12 PASS; Vestia Zeta remains a Phase-12 HOLD and Todoroki Hajime remains a Phase-5 HOLD. Wave-1 upstream Phase-12 success is therefore **4/6** after the generic repair.

A direct four-group Differentiable batch was started for Vivi/Riona but stopped after >5 minutes with eight concurrent pydiffvg containers still occupied on their first heavy candidates. This is recorded as a scalability boundary, not a semantic failure. The next DiffMin step must add character-independent candidate preflight/scheduling before Approved-18 expansion; brute-force parallel execution is not an acceptable production path.

## Approved-18 wave 1 closure and DiffMin scheduler 2026-10-04

Wave 1 now reaches Phase 12 PASS on all six sampled characters. Vestia Zeta was repaired without relaxing the critical-part gate: tiny critical semantic parts now fail closed to their observed Phase 11 primitives when Phase 12 polygon simplification would drop below 0.98 local IoU. Zeta conservative now PASSes with left-arm IoU 0.925439 and silhouette IoU 0.988774. Todoroki Hajime's Phase 5 failure was a tiny-arm attachment-gap case: the existing nearest-boundary evidence measured a ~34 px gap against the normal 20.4 px limit. Tiny arms (<=1.5% canvas) may now use the same conservative 2x gap allowance already used for tiny necks, with confidence capped at 0.55 and explicit evidence tag derived:tiny-arm-conservative-gap. Hajime then passed Phase 5 and continued through Phase 12; aggressive selected 19 primitives at silhouette IoU 0.987026. Focused Phase 5 + Phase 12 tests: 27/27 PASS.

The DiffMin batch path now has a character-independent preflight/scheduler. It rejects unsupported multi-component topology, skips polygons above a configurable vertex budget, skips negligible mismatch headroom, and ranks remaining work by mismatch-per-vertex before invoking pydiffvg. Vivi/Riona preflight demonstrated immediate rejection of unsupported/heavy candidates without optimizer cost. A Vivi major-clothing smoke with max_vertices=24 scheduled only three light candidates and completed in 46.11 s; two were feasible and one failed closed on polygon self-intersection. This replaces the previous eight-container brute-force pattern as the research execution path.

## Approved-18 full upstream closure 2026-10-04

The current character-independent ZeroBase2 rules now reach Phase 12 PASS on all 18 Approved-18 cases. Wave 1 was 6/6; the remaining 12 initially produced 4 PASS / 8 FAIL and exposed four reusable gaps rather than character-specific defects: strict arm fidelity fallback budget, accessory contour over-simplification, face/head spatial nesting when semantic head is hair-dominant, and rare SLIC masked pixels without a parent label. General fixes were applied without generative pixels or per-character thresholds. Highly fragmented semantic owners now fail closed toward Phase 11 geometry instead of forcing aggressive simplification; Koseki Bijou therefore selects conservative (291 -> 214 primitives, silhouette IoU 0.988196) rather than weakening identity gates. Final Approved-18 upstream status: 18/18 Phase 12 PASS. Full zerobase regression suite: 226/226 PASS.

## Approved-18 DiffMin scheduler escalation 2026-10-04

Approved-18 was first re-rendered from scratch under one current code snapshot; all 18/18 independently reached Phase 12 PASS. The character-independent DiffMin preflight found 461 schedulable polygons across 96 character/part groups. To avoid brute-force optimizer cost, execution was capped at three highest mismatch-per-vertex candidates per character and at most two per semantic part, with face/head frozen. This produced a locked 54-candidate execution plan.

The locked run produced 45 feasible guarded refinements across 17/18 characters and 9 fail-closed results. Failures included NO_FEASIBLE_CHECKPOINT, self-intersection, canvas escape, and four zero-boundary/degenerate pydiffvg inputs on highly fragmented Kobo/Bijou arm geometry. Those degenerate polygons are now rejected in scheduler preflight before optimizer invocation rather than crashing pydiffvg. No trust radius, ownership threshold, or character-specific threshold was relaxed. ZeroBase regression remains 226/226 PASS. Full repository pytest is not a valid observer-environment check because that environment intentionally lacks the unrelated FastAPI dependency; the targeted ZeroBase suite is green.

This closes the large-scale optimizer feasibility probe but does not yet authorize production adoption. Next gate is cumulative same-renderer composition plus frozen DINOv3 source-relative evaluation per character; only observer-positive cumulative candidates may advance.

## Approved-18 cumulative observer gate 2026-10-04

The 45 feasible local refinements were evaluated cumulatively with the established same-renderer normalization rule. A first comparison against canonical Phase12 PNGs reproduced the known compositor confound, so those numbers were discarded. Fresh zero-change controls were rendered with the same research compositor and all candidate comparisons were normalized against those controls. Under normalized evaluation, all 18 cases preserve silhouette IoU >= 0.997726; Kobo has no feasible replacement and is exact zero-change (IoU 1.0, 0 changed pixels).

Frozen DINOv3 was loaded once and evaluated source-relative across the full corpus. Nine characters improve and are retained as research candidates: Isaki Riona (+0.001399), Kikirara Vivi (+0.001707), Koganei Niko (+0.003473), Koseki Bijou (+0.002399), Momosuzu Nene (+0.000995), Mori Calliope (+0.002366), Shiori Novella (+0.001885), Todoroki Hajime (+0.000195), and Vestia Zeta (+0.005818). Eight cumulative candidates regress and are rolled back to zero-change: Aki Rosenthal, Gigi Murin, Hakos Baelz, Houshou Marine, Natsuiro Matsuri, Otonose Kanade, Raora Panthera, and Shishiro Botan. Kobo Kanaeru remains zero-change because no selected proposal survived the local optimizer/geometry guards.

Gate result: PASS_LIMITED_CORPUS_EVIDENCE. DiffMin demonstrates transferable observer-positive benefit on 9/18 Approved-18 characters without relaxing semantic trust, ownership, silhouette, or character-specific thresholds. The 8 observer-negative cases prove that local objective feasibility is not sufficient for adoption and validate the scene-level DINO rollback gate. This supports a future opt-in/guarded integration path, not unconditional production routing.

Evidence is preserved in Google Drive under Minimalizer / Differentiable Minimalization Research / Approved18_DiffMin_Escalation with per-character zero-change and accepted/rejected candidate images plus corpus scene/DINO/final-gate metrics.

## Guarded production integration foundation 2026-10-04

A production-facing decision boundary is now implemented without enabling DiffMin in the default route. MINIMALIZER_DIFFMIN defaults to off. The only opt-in mode is guarded, and it may apply a candidate only when local hard guards passed, same-renderer scene silhouette IoU remains at or above 0.985, frozen observer evidence is present, and candidate DINO score is strictly greater than baseline. Missing observer evidence, a tied/regressed DINO score, silhouette regression, or any hard-guard failure rolls back to the baseline.

This integration layer does not invoke pydiffvg, does not add a generated-content path, and does not alter the existing ProductionRouteSwitch. It is a pure fail-closed decision boundary intended to sit after research/worker-side candidate production. Default production behavior therefore remains unchanged until a separate explicit routing decision is authorized.

Regression result: 234/234 ZeroBase tests PASS, including new tests for default-off behavior, hard-guard rollback, silhouette rollback, missing observer rollback, DINO tie/regression rollback, positive guarded adoption, and unknown-mode rejection.

Gate result: PASS_GUARDED_INTEGRATION_FOUNDATION. Production routing remains unchanged; the next gate is wiring this decision boundary to a worker/candidate artifact contract without making local GPU execution the canonical source.
