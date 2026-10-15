# MinimalizerLocal L02: independent-image flip robustness and negative control (2026-10-15)

**Formal milestone: HOLD / production: NO-GO.** This document contains no private original pixels or manually traced source geometry.

## Real signed-source diagnostics

The H04 human-label-trained single-model classifier was evaluated on the exact signed H04, H06 and H08 images. H06 and H08 were temporarily transformed into analysis frames (foreground height ~900), and their signed originals were **not overwritten**. A temporary horizontal flip is only a test-time transform, **not** a second independent trained model or a semantic ground truth.

| Original case | Flip agreement IoU | Verdict | Signed original SHA-256 |
|---|---:|---|---|
| H04 (training subject) | 0.593929 | ABSTAIN | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` |
| H06 (unseen coat) | 0.226774 | ABSTAIN | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` |
| H08 (unseen pink jacket) | 0.237584 | ABSTAIN | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` |

The flip test is a non-semantic consistency diagnostic, **not** a jacket-quality IoU.

## Rejected mitigations

| Experiment | H04 same-image spatial-held-out jacket IoU | Full-model flip agreement on H04 | Decision |
|---|---:|---:|---|
| Previous source-only H04 learner | 0.799184 | 0.593929 | RESEARCH-ONLY; not generalizable |
| Mirror-augmented half-frame training | 0.611905 | not measured | REJECT: jacket regression |
| Mirror-invariant x-position feature | 0.585136 | 0.997321 | REJECT: high self-consistency but worse jacket quality |

The H04 OOF values remain one-character spatial tests; repeated selection/tuning on H04 invalidates independent semantic accuracy claims.

## Implementation and safety verification

- Added reusable `local_l02_flip_consistency_gate.py`, **13/13 synthetic negative/positive tests PASS**.
- Source authority now validates both the exact SHA-256 of compressed PNG/WebP bytes and their **fully decoded RGBA byte-for-byte equality** with the array passed into the experiment. Passing a genuine hash paired with modified pixels fails closed.
- Disabled outside-alpha predictions and invalid model probabilities; uncertainty stays explicit. The method never rewrites any source image, mask owner, model config, or LocalWorker production binary.
- Signed H04/H06/H08 study repeated using existing H04-only HistGradientBoosting model. All three fail flip-consistency quality safeguards and none can be promoted. H06/H08 have **zero independent human jacket labels**. Source image/model overlays and per-pixel experimental evidence stay PRIVATE in Drive.
- A separate candidate that directly ORed model clothing evidence into Phase4 major_clothing previously increased component count from 5 to 29 and remains vetoed; the existing pinned Phase5 graph pass applies only to unchanged owners, **not** repaired-exclusive owners.

## Exact remaining acceptance gates

1. Receive independent H06 or H08 source-bound reference garment silhouettes and occluding arm skin via ReferenceShapeEditor JSON. Blank original-source identical starters were previously created in private Drive `MinimalizerLocal_L02_DualObserver_PRIVATE_20261015.zip`.
2. Independently evaluate garment precision/recall and hair/arm/neck occlusion without using the same test image to tune. Labels missing means numerical semantic performance `null`.
3. Build a **mutually exclusive visible-owner** H04 Phase4 candidate that preserves original head-parent hierarchy, signed foreground, protected arms, and auditable topology, then execute **that exact candidate** through pinned Phase5 graph and full Phase4→5 staging.
4. Obtain actual user/human quality sign-off and independent control success before declaring L02 complete. Do **not** infer this from 13/13 engineering tests or flip consistency. Separate C03 Stage8/C04 Golden/production gates remain HOLD.

**Decision: engineering flip diagnostic PASS; investigated augmentation variants REJECTED; L02 semantic repair HOLD.**
