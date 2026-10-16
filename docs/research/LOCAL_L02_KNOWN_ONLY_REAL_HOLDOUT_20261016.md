# Local L02: explicit-human-negative three-character replay (2026-10-16)

**Status: research experiment completed / independent outerwear recognition FAIL / L02 HOLD / Golden HOLD / production NO_GO.**

## Source authority and exactly what ran

- Source: private Google Drive archive `MinimalizerLocal_L02_ReviewedEvidence_PRIVATE_20261016.zip`, SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`. The existing signed H04/H06/H08 source-hash and human JSON/SVG parity checks are applied unchanged by `benchmark_leave_character_out.prepare()` / `verify_reviewed_annotations.inspect()`.
- `tools/research/benchmark_leave_character_out.py` Git blob `51fa98168284229f40cfada6431ab8959fde07fb`, `verify_reviewed_annotations.py` blob `c5a218b40d169afa03665386c76a2737c9cf87e4`, `local_l02_manual_supervised_shadow.py` blob `41cd3047ef556f4aaa9c32bc01b2f71f5aeb3ae9`. All three exact byte-identical to GitHub `main` at `63a5dbd9befc22b6ecf51a9ebb531580a61825ea`.
- Executed the PR #408 known-negative diagnostic via those canonical `prepare`, `sample_train(..., negative_method="known")`, `HistGradientBoostingClassifier(**MODEL_PARAMETERS)`, `predict`, and `score` functions at the pinned 900px diagnostic size. Each held-out character excluded from training, 15,000 maximum positives/explicit-negative samples per training character, pinned seed and threshold 0.5.
- Source-only image features (18 channels) plus signed alpha at inference; human pixels are labels only for the **training cases** and final held-out **scoring**, never inference inputs or renderer geometry. Nonannotated source pixels are **UNKNOWN** and never training negatives.
- Private input H04 four reviewed overshoots are scope-specific, H06/H08 strict overshoots remain **not approved**. Source-alpha clipping remains strict for research evaluation, and H06/H08 annotations are partial.
- Private full output archive: `chatGPT及びCodex用/Minimalizer/MinimalizerLocal_L02_ExplicitKnownNegativeLOCO_PRIVATE_20261016.zip`, SHA-256 `c2133af02b78b029ff5eb7467dab05b96a847f847f6800a825d9e7927308cbd3`. Google Drive file ID `1nU_ikd0o-PLBmrqzDlqpp9lyfZQpFAL_`, verified by read-after-write with matching size 16,628 bytes and ZIP SHA.
- The three NPZ and JSON outputs are **byte-identical across two independent replays**. The private JSON SHA-256 is `780eb3a12041159e16347b6d124d552eb7e08ab829a5a5e462582d62337506dc`. These raw predictions, source underlays, original images and user polygon vertices MUST NOT be committed publicly.
- The reviewed public archive's original synthetic checks passed 30 manual-intake and 6 transfer-negative-control tests in the local isolated environment. This was not a complete repository CI rerun.

## Signed-source-aligned results (labelled-only diagnostic IoU)

| Held-out character | Original presumed-negative LOCO (#407) | Only human-explicit negative LOCO (#408) | Positive recall | Known-negative false-positive rate | Unknown predicted source pixels |
|---|---:|---:|---:|---:|---:|
| H04 | 0.005419 | **0.218283** | 0.942314 | **0.951932** | 1,813 |
| H06 | 0.032561 | **0.164998** | 0.165145 | 0.015261 | 9,086 |
| H08 | 0.017511 | **0.029907** | 0.031384 | **0.515640** | 18,600 |

The prior result remains valid as an experiment with **assumed** negative pixels, but its score combines negative-label contamination and generalization failure. Removing unknowns from negative training improves all three labelled-only IoUs, yet still has catastrophic H04/H08 known-negative false positives and H06/H08 positive misses. **This is not a generalizable outerwear observer.** The labelled-only IoU is *not* whole-image precision on partial H06/H08 annotations. The model is fitted to just three characters and its parameters were originally examined on H04, not prospectively tuned on independent data. No threshold adjustment or label injection is an acceptable shortcut.

### Label support at 900px diagnostic resolution

| Case | Human outerwear-positive pixels | Explicit other-category-negative pixels | Unknown opaque pixels | Known alpha share |
|---|---:|---:|---:|---:|
| H04 | 21,721 | 75,685 | 2,217 | 97.7746% |
| H06 | 63,750 | 3,735 | 54,609 | 55.2730% |
| H08 | 31,704 | 3,037 | 73,996 | 31.9496% |

The limited explicitly-negative support for H06/H08 materially constrains learning; **unknown is not automatically negative**. No release gate has been changed and no output/owner mask is promoted.

## Decision and next engineering gate

**REJECT as production observer; L02 HOLD, Golden HOLD, Local/Public production NO_GO.** Retain this benchmark as a permanent *negative-control* measuring how much label-assumption changes the outcome. Next work must evaluate an **independent, garment-role/outerwear-specific observer**, alongside explicit underlayer vs jacket separation, source-alpha bounds, abstention when authority is weak, and truly held-out character evaluation with precommitted gates. Generic AnimeSeg `clothes` remains an independent but non-exclusive garment cue, not an outerwear owner. After a candidate passes all three independent-character evaluations, only then replay the actual Phase4→5 exclusive source-owner graph and human faceless Golden. Do not change LocalWorker, Public/C08, signed images, polygon annotations, or production gates as a consequence of these improved-but-failing IoUs.
