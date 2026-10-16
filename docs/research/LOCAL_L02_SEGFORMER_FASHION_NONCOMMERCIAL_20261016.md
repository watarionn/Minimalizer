# L02: SegFormer-B2 Fashion independent research-only shadow (2026-10-16)

**Work package: completed as noncommercial research. Independent character quality: not approved. L02 HOLD / Golden HOLD / production NO_GO.**

## Provenance and usage boundary

The pinned [sayeed99/segformer-b2-fashion](https://huggingface.co/sayeed99/segformer-b2-fashion) was audited and actually run, locally on CPU, against the H04/H06/H08 signed originals. Repository revision `e82089f3b76fdc5522727f6e793ff3d470c15e74`; `model.safetensors` SHA-256 `47313d9daf8f759b803b0bf449a4719bcd5b5a46eacad343e99e9660f8cedec1`; processor SHA `6073ac6a37530ed2a19443d6a748f5579887b3ae48f6730073954b0b38cf3fd6`. Exact class IDs: `5=jacket`, `10=coat`, separate from `upper-clothes` or `sleeve`. The model card declares licence `other` and links to the [NVIDIA SegFormer licence](https://github.com/NVlabs/SegFormer/blob/master/LICENSE), which restricts use to noncommercial research/evaluation. **No production or commercial authorization** may be inferred from these results. This candidate must not be installed into LocalWorker or Public.

One research trial used a temporary, isolated Python dependency directory, not the Windows system Python package set. Public model files were downloaded by the local PC; **no private input images were uploaded to Hugging Face or any external inference service**. The original RGBA was SHA-verified, composited to white only for transient inference input, processed with the model's official 512×512 normalization, predicted classes 5/10, resized logits to native source coordinates and clipped to the original alpha. Human polygons/masks were inaccessible to the model and used only for later positive/explicit-negative/unknown evaluation. All original source bytes, annotations, signed Phase4 masks and owner maps are unchanged.

## Real results (only labelled source pixels scored)

| Case | Prior independent DeepFashion2 IoU (#411) | This model IoU | Known-negative FPR | Unknown predicted pixels |
|---|---:|---:|---:|---:|
| H04 | 0.000000 | **0.614489** | 0.020200 | 176 |
| H06 | 0.627044 | **0.825905** | 0.000000 | 76,778 |
| H08 | 0.606773 | **0.616561** | 0.000000 | 3,814 |

The 2nd independent observer detects some of the H04 jacket that DeepFashion2 missed and improves H06. However, H06/H08 human markings cover only 55.27% and 31.96% of opaque source. Unknown regions are *not* negatives; H06's substantial unknown-positive area cannot be asserted correct. H04 still misses about one third of explicitly labelled jacket pixels; H08 similarly. **The three-source semantic quality/outerwear-owner gate is not passed, and visual Golden was not performed.**

Run twice with exact equality of the first experiment's JSON bytes and native predicted masks across all three cases. An additional public, path-independent runner at `tools/research/local_l02_segformer_fashion_shadow.py` was executed against the same pinned model and private archive, reproducing **all 3 IoUs and prediction SHA-256**. New synthetic tests `tests/test_local_l02_segformer_fashion_shadow.py`: **12/12 PASS** in the isolated local Python environment, including explicit noncommercial approval refusal, source alpha, known-negative/unknown separation and pin mismatch. Full repository CI was not run.

Source-free metrics: [JSON](LOCAL_L02_SEGFORMER_FASHION_AGGREGATES_20261016.json). Private outputs are in the pre-existing mounted Google Drive folder `chatGPT及びCodex用/Minimalizer` as `MinimalizerLocal_L02_SegFormerFashion_VerifiedRunner_PRIVATE_20261016.zip`; **cloud-provider sync readback remains unverified** (file not yet returned from connected Drive search). Do not claim remote archival completion without an actual Drive read-after-write. No private imagery/labels/NPZ/weights committed.

## Exact next engineering gate

1. Resolve model usage licence separately from quality; prohibit production use of this pinned noncommercial candidate.
2. Review independent H04/H06/H08 native candidate-mask overlays privately; inspect *where* missing outerwear, hair/arm occlusion and underlayer are mistaken rather than tuning the score to the labelled reference.
3. Compare a permissively licensed independent fine-grained model or conservative cross-observer agreement on new signed holdouts, with no held-out manual polygons in inference and fail-closed ABSTAIN for ambiguous outerwear. The next candidate must meet semantic topology and source owner protections, not only a labelled IoU.
4. Only after independent owner semantics pass should exclusive Phase4→5 actual pinned replay, Stage8 budgets, Chrome DPR1/DPR2, H04 Golden review and iPhone signoff be reconsidered. L02→L03 is **blocked**, not silently skipped. L07 non-destructive PWA checks may run independently.

**No facials (eyes/nose/mouth/brows), no img2img/inpainting, no source pixel synthesis, no production Worker/Public/C08 changes, no campaign restart.**

## Final checksum closure (2026-10-16)

The reproducible local research runner was strengthened to reject any change in the model **architecture config** SHA-256 `44b342a5e9301a1716dac8a56537e82acfdae8f0597069b0414b7704e39b8705` and preprocessing config SHA-256 `6073ac6a37530ed2a19443d6a748f5579887b3ae48f6730073954b0b38cf3fd6`, in addition to the already-pinned weight SHA. Synthetic safety regression now **13/13 PASS**, including deliberate mutations of both configs. Private runner ZIP verified on the mounted PC Drive: **21,268 bytes**, SHA-256 `d5c4ea8ba8843a72707d87ace6ffcf3839e9d62912c3cb08e797383a0243b2fe`, with three native prediction arrays identical to the initial independently run shadow. A mounted Drive file is not evidence of cloud-provider synchronization; connected Google Drive search still returned no matching new ZIP. Do not mark that archival gate complete unless cloud readback succeeds.
