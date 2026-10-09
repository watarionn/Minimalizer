# CMP-20261009-SA1060-TO-PRODUCTION | Minimalizer 本番リリースキャンペーン

**Status: ACTIVE / RELEASE HOLD** (2026-10-09). **Current: C02 IN PROGRESS, C02a complete / C02b ready.** This is a campaign definition and starting snapshot, not an authorization or deployment. Progress tracker data: [JSON](CMP-20261009-SA1060-TO-PRODUCTION.json).

## Goal and frozen baseline

Take current SA10.60A GC001 arm-quality research through signed-source correction, high-quality Rinka Reference style, immutable Stage8 resolution, real human multi-image Golden, Phase15, and SA10.61 live Chrome/iPhone verification. The target is **recognizable hair, clothing masses, both arms and pose with intentionally absent facial microfeatures**, not merely lower color MAE or a polygon count.

Base GitHub main: `d0144af58e6858f7e63a5412b34d7785ebbad195`, merged [PR #317](https://github.com/watarionn/Minimalizer/pull/317) / [PR #319](https://github.com/watarionn/Minimalizer/pull/319). Canonical handoff: [SA10.60A → SA10.60B](../handoffs/HND-20261009-SA1060A-GC001-ARM-DIAGNOSTIC-SA1060B-NEXT.md). Research preflight: [SA10.60 gates](../research/SA1060_RELEASE_PREFLIGHT_AND_POLICY_DECISION_20261009.md).

SA10.60A's actual GC001 right-arm signed mask overlaps **533 exact-background-connected source pixels** (not an automatic semantic truth statement); its improved RGB research candidate is **not approved**. Historical signed source Stage8 **Raden 2370/1412 FAIL, GC001 3604/1887 FAIL**, notwithstanding under-cap final SVGs. Only **2 independent signed Golden originals**, human judgments **PENDING**. Phase15 for this release **NOT RUN**. Existing live route is **not verified** by this campaign's creation.

## Campaign milestone board

| ID | Track | Start | Exit evidence / next action |
| --- | --- | --- | --- |
| C00 | Baseline / source authority lock | **COMPLETE** | main HEAD and PR #317/#319 verified |
| C01 | SA10.60B first-bad-stage source-owner diagnosis | **COMPLETE** | GC001 arm/background 533px overlap traced to earliest demonstrably wrong Phase04/05/06/owner stage, with provenance; if Phase04 not at fault, correct attribution |
| C02 | Source-grounded arms / clothing / hair quality recovery | **IN_PROGRESS** | GC001 arms/shoulders/sleeves/neckwear then Raden costume/hair evaluated against signed originals |
| C03 | Resolve historical source Stage8 ring budget | **HOLD** | Option A: source-equivalent geometry fits immutable original source ring caps AND separately deployed SVG expanded budgets, validates face/arm owners and topology in real Chromium; OR Option B: explicitly approved, versioned policy change with historical failure retained and compatibility/rollback documented |
| C04 | Expanded multi-image artistic Golden + Phase14 gate | **HOLD** | Authentic owner/human signoff per signed original and all six SA10.59 criteria; rejects identity/arm/garment visual failures even when metrics PASS |
| C05 | Release candidate & reversible runtime preflight | **BLOCKED** | Freeze exact candidate/source/config/renderer SHA and version; live production route is independently measured, not inferred from conflicting historical docs |
| C06 | Phase15 guarded integration + final Go/No-Go | **BLOCKED** | Actual approved production integration route tested in real browser and API with X-Minimalizer-Route and /health evidence; fallback not mistaken for success |
| C07 | SA10.61 production deployment and device smoke | **BLOCKED** | After authorized Go deploy intended build and independently confirm remote deployed SHA/route |
| C08 | Verify / Review / Ship / Preserve / Closeout | **BLOCKED** | Final commit/PR merge/remote HEAD/live build verifiably match accepted candidate |

C03 runs as a parallel research track alongside C01/C02; C04 can prepare parallel human/corpus protocols but cannot PASS before C02 quality evidence. C05 and later are blocked until **both** C03 and C04 pass. No fabricated timetable: scope depends on geometry feasibility and genuine visual review, not a preset number of chat turns.

## Release invariants

- Default Rinka Reference face microfeatures OFF: eyes,nose,mouth,eyebrows; face/hair/skin evidence preserved for structure
- Visible output deterministic source-bound geometry only; no generated visible pixels, img2img/inpainting, raster embedding, automatic missing-content completion
- SHA-locked source originals and Stage04 masks cannot be overwritten; author new candidates and maintain provenance
- Actual original Stage8 ring cap and expanded deployed SVG cap are separate and cannot be swapped
- Visual FAIL overrides numerical PASS; human Golden signoff cannot be synthesized by automation
- Production is neither authorized nor deployed until independent Stage8 policy, human Golden and runtime/rollback/device evidence pass
- Avoid RDC unless other official GitHub/Drive/remote routes cannot complete the task; record actual route/verification

## Stage8 decision contract

- **A (preferred):** source-preserving geometry/representation satisfies **original** immutable source ring caps and separately measured true expanded SVG caps, plus original owner/face/arm topology and real Chromium visual comparison.
- **B (only by explicitly approved change request):** new versioned policy distinguishes unchanged historical FAILED source complexity from a new deployed-output constraint, defines exceptions, compatibility, source guards, rollback and owner approval. No retroactive Stage8 PASS or silent budget loosening.
- Previous epsilon-family inability is **not** a proof of universal impossibility. Do not infer a geometry algorithm cannot work without testing it.

## Golden + Phase14 acceptance

Authentic source-image provenance, six review criteria per case (faceless style, hair/head, attire/accessories, arms/pose, silhouette/identity, no unsanctioned detail), signed human review and independent holdout corpus. Expand beyond two signed originals to Approved-18 and the canonical Approved-78 Phase14 gate, preserving SHA binding and deterministic replay. Real-world subjective FAIL overrides metric optimism. Review notes must identify failed image/part and first bad stage. Do not treat a filled-in form or our observations as an authenticated human approval.

## Operational loop / safety

Each milestone: **Goal → Produce → Verify → Review → Ship → Preserve → Next**. Stage completion means versioned artifacts, two-case/regression evidence (as relevant), independent visual QA, reproducibility, merged commit and correct Drive preservation where needed. PR merge alone is not completed artwork, and successful deployment command alone is not confirmed live correctness.

- Engineering may progress without repeated low-value approval requests while the step is reversible and respects frozen contracts. A new rendering policy, unapproved Golden promotion, destructive cleanup or a production-route cutover requires documented approval and actual eligibility.
- Stop only the blocked promotion track for HOLD; continue independent diagnostics or policy alternatives. Record cause, affected cases, failed metric/visual judgment, mitigation, and next executable step.
- Use GitHub for code, sanitized gate metrics, stage status and handoffs; existing **`chatGPT及びCodex用/Minimalizer` Google Drive** for private originals, actual SVG/PNG, detailed comparisons and signed provenance. Never publish actual private source image or source-traced coordinates to public repo. Prefer official direct tools, no needless RDC.
- Production verification must inspect actual server health/route, selected request's response route, rendered output and iPhone behavior; a silent Browser Fallback is not a ZeroBase PASS. Older documentation differs on preferred route, so **measure the current route** before the cutover.
- Rollback is mandatory and tested both before and (if needed) after deployment; verify the old state is actually active.

## Completion gates

**Release GO** requires independent source/face/arm authority; formally resolved Stage8 decision; true expanded geometry cap; signed real human Golden and Approved-18/78; deterministic real Chromium; Phase15 live browser route; tested rollback. **Campaign CLOSED** additionally requires SA10.61 real Chrome and iPhone proof, remote release identity/read-after-write, and durable GitHub + private Drive handoff. Neither a status field nor this Markdown is a deployment mechanism.

## Useful sources

- [Target style](../TARGET_STYLE.md), [AGENTS](../../AGENTS.md), [ZeroBase 2nd cycle design](../zerobase/ZEROBASE_2ND_CYCLE_DESIGN.md)
- [Previous SA10.59 visual review metrics](../research/evidence/sa1059_golden_review_metrics_20261009.json)
- [SA10.60 preflight frozen blockers](../research/evidence/sa1060_release_preflight_20261009.json)
- [SA10.60A GC001 arm source-owner diagnostic](../research/SA1060A_GC001_SIGNED_ARM_MASK_AUDIT_20261009.md)
- Approved private Drive for SA10.60A: https://drive.google.com/drive/folders/126DtYlC_OxJJLKbszaXL9VqKkQ-5K3WR
- Approved private Drive for SA10.59: https://drive.google.com/drive/folders/1McAwnpwHeAUSMy-adwULfU2B0y2gqyep

## Campaign checkpoint C01 verified (2026-10-09)

- **C01 COMPLETE:** GC001 SHA-signed original Phase04 `right_arm` already overlaps source-connected exact border-background RGB in 533 pixels. The immutable Stage08 right-arm rings inherit the same 533 pixels (existing Phase04–Stage08 mask raster XOR = 24). **Earliest demonstrable bad stage is Phase04**, not a proven diagnosis of the upstream Phase03 algorithm or individual Phase05/06 internals.
- Of the 533 exact RGB intersections, **520 fully opaque pixels** form an isolated non-promoted mask candidate subtraction; 13 partial-alpha pixels stay unchanged. Candidate right-arm connected components remain 1. Human validation of complete semantic anatomy is still required; the candidate is not artwork approval.
- Independent Raden signed image/masks: 3 right-arm, 7 left-arm exact RGB overlaps. Fixed tests including real signed sources **10/10 PASS**, independent rerun **5/5 artifacts hash matched**. Source binaries, Stage08, SA10.57 SVG, production unchanged.
- [C01 evidence](../research/SA1060B_C01_FIRST_BAD_STAGE_GC001_20261009.md), [public metrics](../research/evidence/sa1060b_c01_coordinate_free_20261009.json), [C02 handoff](../handoffs/HND-20261009-C01-PHASE04-FIRST-BAD-C02-NEXT.md), [private Drive comparison/mask](https://drive.google.com/drive/folders/1QA2AqOfqRomdHsNbqb4dvoKvV-_mYPwA).
- **Current next: C02 READY.** Stage8 original budget C03 HOLD, authenticated human Golden C04 HOLD, C05+ deployment blocked. No release authorization.

## C02a recovered original source revision checkpoint (2026-10-09)

**C02a verified, C02 final artistic gate still OPEN/HOLD.** First checked original Phase03 subject mask includes **648** dominant source-border-connected exact RGB pixels; of those **533** persisted in the recovered Phase04 right-arm part mask and **31** in hair. Original Phase03 used rembg/isnet-anime; the diagnostic does not prove color-matched pixels are non-subject or pinpoint causal model behavior. Historical C01 first-checked Phase04 observation was valid for its narrower evidence chain, but earliest **newly examined** source stage is now Phase03.

Important **version provenance conflict**: recovered current Phase04 left_arm = **2,330** pixels; previously signed SA10.41 Phase04-derived left_arm = **2,715**; raster XOR **385** and historical variant contains all new pixels. Face and right-arm raster XOR=0 between those source versions. The byte-hash mismatch of re-encoded mask PNGs is independent of this true source-history divergence. Historical signed artifacts remain frozen. Source data were recovered **read-only** with minimum remote access then versioned to approved Drive; local is not canonical.

- [C02a source audit and independent tests](../research/SA1060C_C02A_PHASE03_PHASE04_PROVENANCE_20261009.md) (12/12 PASS)
- [Sanitized numeric measurements](../research/evidence/sa1060c_c02a_coordinate_free_20261009.json)
- [C02b handoff](../handoffs/HND-20261009-C02A-PHASE03-PROVENANCE-C02B-NEXT.md)
- [Private SHA-pinned 19-file Phase03/04 source archive, visual board and manifest](https://drive.google.com/drive/folders/1g3jckoCVzxLDKVW_cJ6ukhBMiVtlkMeY)

**Next C02b:** real source-bound hair/arm/sleeve/garment quality correction with actual Chromium and holdouts; **not accepted by these numeric audits**. C03 Stage8 original rings, C04 human Golden and C05–C08 release remain unchanged HOLD/BLOCKED.

## On each next-step request

Read the latest `main` and this campaign's JSON + latest C-stage handoff, reconcile any newly merged work, choose the earliest READY step with unmet objective evidence, implement/verify/review/merge and persist, update **both** this board and JSON with actual evidence. Never mark HOLD as PASS through the tracker, and never claim production promotion until live tests pass.
