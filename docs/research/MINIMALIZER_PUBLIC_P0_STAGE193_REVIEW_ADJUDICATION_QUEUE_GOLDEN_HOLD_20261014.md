# MinimalizerPublic P0 Stage193: independent-review attestation and private adjudication queue

Date: 2026-10-14 JST
Scope: research PR #393 Draft. This document intentionally contains **no private original images, reviewer-label arrays, screenshot crops, JSON payloads, or human account details**.

## Verified scope and safeguards

- The operator reported, in this conversation, that two separate reviewers did not see each other's work before submitting their separate annotations. The Stage193 source-free research function records that confirmation as **out-of-band operator attestation**. It does not represent software identity authentication or infer it from file names, device types, or hash differences.
- A reportedly used iPhone and B used PC. The client device difference is not a defect and is not itself evidence of independent identity.
- The immutable originals were rechecked privately for both cases. Each case contains 340 × 340 original pixels, of which 115,152 are fully opaque and 448 are nonopaque. All four inputs retain the exact source fingerprint and original semantic **proposal**, not certified ground truth.
- All fully opaque pixels are accounted into explicit classification agreement, taxonomy/background disagreement, abstention or uncertainty; **none are silently auto-painted**. The owner-only Stage193 ZIP holds original-image comparisons and a complete, source-pinned adjudication component queue.

| Case | Agreed opaque | Disputed opaque | At least one abstention | Uncertain | Manual inspection pixels | Four-connected directed-label components |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GC001 | 108,080 | 5,055 | 2,017 | 0 | 7,072 | 1,669 |
| Raden | 92,462 | 22,371 | 319 | 0 | 22,690 | 706 |

## Taxonomy before pixel-level adjudication

- **Sleeve**: Source-visible fabric belonging to the arm/shoulder sleeve, including attached puff/frill when this is part of the sleeve rather than the bodice.
- **Garment**: Bodice/skirt and garment fabric other than separable sleeve, neckwear and accessory.
- **Neckwear**: Visible neck/chest tie, ribbon, bow, scarf-like item where separable from garment.
- **Accessory**: Visible fitted badge, strap, buckle, goggles, epaulette, belt ornament or other separable object. Do not relabel an area by color alone.
- **Hair vs. background**: Classify only depicted strands, not hypothesized hidden hair; actual backdrop stays background.
- **Unreviewed / uncertain**: Distinguish missing proposals from explicit ambiguity, never fill from model inference. The original nonopaque source is not semantic-paint eligible.

These are working definitions requiring visual confirmation, **not auto-generated truth**. They address dominant Raden garment-versus-sleeve and GC001 garment-versus-accessory ambiguity. A connected class-pair region can contain genuine pixel-level boundary differences and may require subdividing.

## Implementation and validation

Source-free code: `web/static/public-review-adjudication-stage193-p0.mjs`.
Synthetic regression tests: `tests/js/test_public_stage193_p0.mjs`.

- Record operator-reported independence without identity assertion.
- Build a four-neighbor connected-component queue by ordered class pair, with exact zero-loss pixel accounting.
- Reject nonopaque labels, unknown roles, unexpected case/dimensions and mismatched array lengths.
- Log explicit manual A/B/DEFER decisions with reasons; **no automatic Golden even when both reviews agree or all queue items have been decided**.
- All tests pass in isolated local Node execution and in research GitHub Actions: https://github.com/watarionn/Minimalizer/actions/runs/38530910311.
- Private adjudication ZIP is stored only in owner-only Google Drive under `chatGPT及びCodex用 / MinimalizerPublic / StructuralRecovery_P0_20261010 / Stage193_Private_Adjudication_20261014`. Do not publish/download/rehost its bytes in public build systems.

## Next gate

Manual original-source adjudication of all disputed/abstained pixels, independent reviewer corrections as separate immutable versions where required, rereview of fine hair/skin/sleeve edges, whole-body silhouette/vertex threshold, actual iPhone Safari acceptance, and real rollback remain unresolved.

**Golden HOLD. PR #393 Draft/unmerged. Local Minimalizer untouched. Production deployment unauthorized.**
