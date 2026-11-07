# L02 independent semantic-observer shortlist: coat / upper-clothes / arm (2026-10-30)

**Decision: research candidate only; no owner promotion.** This is a source-free Lane A investigation that selects an independently pretrained semantic observer to test against the actual H06 underlayer and H08 arm/sleeve failures. It does not claim model inference, signed-image improvement, licence clearance for production, unseen generalization, or Phase4 PASS.

## Canonical quality boundary

- GitHub main at selection: `4a4348990084848c981811b414e6221411271f84`. Draft PR #445 at start: `0f11fe7188dc730ef35fb6867381324109fa843e`. The adopted completion plan and L02 research README were read, as were canonical Drive Run30/Run31 handoffs.
- Existing **strict historical** H06: 1,077 reviewed underlayer false-owner pixels already in frozen owner2, and 20,803 reviewed missing outerwear pixels. H08: 19,309 reviewed missing outerwear pixels; prior owner-colour prototype imported 117 known arm pixels. H04 remains a mandatory regression case.
- Earlier component, hue, AnimeSeg and DeepFashion2-only experiments cannot distinguish H06's true class32 garment from underlayer and H08 sleeve from arm reliably. A new observer must produce affirmative, independently derived **subpart-specific** predictions, not just absence of garment evidence.

## Candidate comparison from primary upstream sources

| Observer | Independently exposed classes relevant to P0 | Published licence signal | Decision |
| --- | --- | --- | --- |
| [SCHP LIP 20-class checkpoint](https://huggingface.co/pirocheto/schp-lip-20) | `7=Coat`, `5=Upper-clothes`, `14=Left-arm`, `15=Right-arm`, plus hair, face, glove | Hugging Face model metadata says MIT; original [SCHP code](https://github.com/PeikeLi/Self-Correction-Human-Parsing) is MIT. **Training dataset LIP usage terms and derivative checkpoint rights still require independent verification for any commercial/production adoption.** | **Priority offline research candidate**, no production clearance |
| [See-through SAM body-part model](https://huggingface.co/24yearsold/l2d_sam_iter2) / [source taxonomy](https://github.com/shitagaki-lab/see-through/blob/main/common/live2d/scrap_model.py) | V2/V3 separate `topwear` and `handwear`, but **do not expose a distinct underlayer or arm-skin class**. V1 has `skin`, but is not the V2/V3 class contract. | Apache-2.0 declared for weights/code | Not a standalone H06 underlayer or H08 skin-vs-sleeve arbiter |
| [mattmdjaga SegFormer B2 clothes](https://huggingface.co/mattmdjaga/segformer_b2_clothes) | `4=Upper-clothes`, `14/15=Arms`, but no dedicated `Coat` class | Model metadata `license: other` | Hold pending exact licence provenance |

The SCHP LIP checkpoint was published with a 20-class output and an ONNX INT8 research option; its LIP validation mIoU is reported as 59.36%, **not an anime-character accuracy estimate**. The model's label set has the required *possibility* of positive coat-vs-upper-clothes-vs-arm discrimination. It does **not** guarantee that a stylized sleeve, skin, or underlayer will be recognized correctly. The LIP dataset itself is reported by independent dataset catalogues as non-commercial; do not infer production rights from the model card's MIT tag alone.

## Exact next engineering contract (not yet executed)

1. Authenticate checkpoint bytes, model-card revision, actual upstream model/weight licence, dataset use restrictions, preprocessing and ONNX output labels. Do not fetch or run private originals through third-party hosted inference. No additional dependency or PC configuration changes without need.
2. Run **offline** on the existing signed H04/H06/H08 RGB/alpha only, using a single pinned, character-independent preprocessing and immutable checkpoint. Freeze predicted label-map SHA and confidence handling **before** reading human-reviewed masks. Keep checkpoint and raw masks in approved private storage; GitHub receives source-free code and aggregate evidence only.
3. First run **observer-only diagnostics**, no owner modifications: measure H06 class32 frozen owner2 overlap with `Coat` vs `Upper-clothes` and explicit arm predictions, plus reviewed true coat retention; measure H08 missing sleeves vs predicted coat/upper-clothes and known arm overlap; run H04 negative regression. Preserve unknown as unknown. A predicted absence of coat is **not** positive underlayer evidence.
4. Only if affirmative distinctions are demonstrated, implement a separate **pre-existing owner abstention** contract for H06 and bounded source-alpha **additive** candidate for H08, each with explicit ABSTAIN, no owner reassignment, 4/8 component identity, cross-owner contacts and critical-part preservation. No blanket OR/AND, no per-character threshold fit, no human-label coordinates at inference.
5. Exact current PR-head source-only QA, signed strict replay and independent unseen signed blind are separate gates. If any P0/P1 or topology regression is observed, preserve FAIL and reject. No Phase5/Golden/production promotion until Phase4 quality PASS.

**Current verified outcome:** accepted P0 fixes **0**, P1 fixes **0**, unresolved H04/H06/H08 **3**. New inference code **0**; model inference **not executed**; no merge. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** Lane B L04/L07, Public/C08, production LocalWorker and Golden are out of scope. Physical iPhone acceptance remains post-deployment.
