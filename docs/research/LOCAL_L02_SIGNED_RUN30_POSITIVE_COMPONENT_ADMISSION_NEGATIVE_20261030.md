# L02 historical Run30 independent-positive component gate: negative result (2026-10-30)

**Decision: REJECT for P0/Phase4 promotion.** This is a new fixed source-only component-admission hypothesis tested on the already-exposed, signed historical Run30 H06/H08 owner maps. It is **not** a strict/composed-owner improvement, current-PR-head replay, unknown-character blind result, or a visual Golden PASS.

## Canonical inputs and provenance
- GitHub main `4a4348990084848c981811b414e6221411271f84`; Draft PR #445 head before this note `d42b492c882b8bea3390bfc84a559522a7570754`.
- Existing non-shared Drive `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`. Archive SHA-256: Run30 owner `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; signed reviewed evidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; DeepFashion2 outerwear observation `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`; offline AnimeSeg class map `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Available ZIP member manifests verified 7/7, 19/19, 5/5. These checks do **not** reauthenticate the independent model weights.
- H06/H08 native 2000x2000 owner arrays, DeepFashion2 positive arrays, and AnimeSeg class-ID maps were the **only inference inputs**. Human masks were opened **only after both proposed outputs and their SHA-256 were frozen**, for postscore and source-alpha escape checks. No manual coordinate, label, generated pixel, model call, or case-dependent threshold entered inference.

## Frozen source-only hypothesis and outcome
Propose additions only at `owner==0 & DeepFashion2_positive & AnimeSeg_class10_generic_clothes`. Partition candidates into 8-connected components. Admit a **whole** component to an existing owner only when it touches exactly one owner type; otherwise abstain. Before accepting each component, reject it if any 4/8-connected owner component count changes or any new 8-neighbour cross-owner contact appears. Existing owner pixels are never deleted or reassigned. No class30/32 cherry-picking or postscore-driven retuning.

| Historical signed case | Positive-intersection candidate px | Admitted px | Rejected by topology | Ambiguous two-owner px | Newly recovered reviewed garment | New known non-garment | New unknown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H06 | 3,514 | 153 | 3,361 | 0 | 41 | 0 | 112 |
| H08 | 14,711 | 532 | 0 | 14,159 | 237 | 0 | 295 |

H08 additionally has 20 unattached candidate pixels. H06/H08 4/8 owner component counts remained unchanged for admitted pixels; no new cross-owner contacts and no pixels outside the separately checked signed opaque source were observed. H04 **not replayed**: the matching archived AnimeSeg class-ID map was not available in this input set, so this experiment abstains instead of inventing an observer.

Candidate SHA-256 (private arrays not committed): H06 `1f3934d12230d99410fe7821d7b5438d2bcb0184f541e04b129d4a52f9f54009`; H08 `96bd939f38872d88f6207aec97130a6ff19f68262a60d78426c2193c15a2c107`.

**Interpretation:** independent-positive intersection plus whole-component owner/contact safety is not a viable major-defect repair. H06 only recovers 41 reviewed garment pixels while the existing underlayer false-owner problem remains untouched; H08 recovers 237, and 14,159 candidate pixels are ambiguous across two owners. Neither is a P0 or P1 visual fix. Do not tune this same known-case gate for a small IoU gain or widen ownership permissions using human postscore.

## Integration decision
- **Accepted P0 0 / P1 0; unresolved major H04/H06/H08 3.** This result is a source-free negative control only; no executable code, inference wiring, private image, model weight, masks, Golden, or production assets promoted.
- PR #445 remains Draft / unmerged. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.
- **Next substantive engineering:** obtain and authenticate a distinct, licensed, positive pixel/subpart-level outerwear-versus-underlayer/arm observer (not another generic-clothes overlap); integrate a source-only owner-exclusive candidate with critical-part retention and H04 regression, then exact PR-head Phase4 QA. Only after Phase4 PASS, perform signed Phase5 replay, independent unseen signed blind, and owner QA. iPhone physical acceptance occurs after production deployment, not as a pre-deployment GO gate.
