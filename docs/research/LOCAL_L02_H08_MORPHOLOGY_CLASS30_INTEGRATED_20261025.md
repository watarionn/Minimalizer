# Lane A L02: signed H08 morphology-before-class30 integration (2026-10-25)

**Research-only, known-case-exposed; no semantic quality approval. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

The earlier Draft PR #439 used an older H08 composed owner. This run independently reconstructed the **latest** source-only sequence from authenticated private Drive inputs: composed `3e467694...`, strict `32bb5266...`, single-anchor `6472cfc4...`, class32 palette `f847f995...`, and class30 opt-in `94122b85...`. Four ZIP SHA pins and reviewed/Run30/AnimeSeg internal member manifests (19/7/5) were verified. Human labels were opened only **after** source-only owner candidates were frozen and hashed.

## Root cause and source-only correction

Applying morphology **after** the latest `94122b...` owner changes 0 pixels, because the 17 reviewed arm mistakes are already immutable. Morphology must run on the `6472...` **pre-palette** owner, before the class30/32 opt-in. Another hazard was exposed: the opt-in tries to resurrect **27** class32 pixels rejected by morphology. The new composition preserves that veto and prunes disconnected additions. Source-alpha confinement, immutable original owners, 4/8 component identity and cross-owner contacts are checked.

| Signed H08 known-only metric | Latest `94122b...` | New veto-preserving `c3a7e642...` |
| --- | ---: | ---: |
| Reviewed garment TP | 144,221 | 144,056 |
| Known false owner | 17 | **0** |
| Known arm false owner | 17 | **0** |
| Reviewed garment FN | 12,349 | 12,514 |

This **partial P0 tradeoff** removes 17 reviewed arm misassignments but sacrifices 165 reviewed garment pixels. The visual difference is small; the much larger missing sleeve/garment regions remain. **0 P0 cases fully resolved, 0 P1 cases accepted, 3 P0 cases unresolved.** The original signed RGB/alpha is unmodified. No generated pixels, annotation-based inference, unknown-as-negative scoring, or face drawing.

H06's pinned composed owner `ceaae119...` was unchanged (TP 294,020 / known FP 1,077 / FN 20,803). H04's signed Run30 owner was unchanged (known FP 4,423). Source-free targeted regressions: **38 PASS + 4 subtests**, not full repository CI. The candidate SHA `c3a7e642fe161207710bf59d7483bf77c9dd4e39549f0aff2483528696a3e0d2` was reproduced by the integrated source-only composition. Private source and comparison board remain outside GitHub.

## Integration gate

This PR remains **Draft**. Required: exact GitHub-head source-only replay and full CI; H08 sleeve/arm visual comparison and semantic owner review; genuinely unseen signed blind evaluation; Phase4 exclusivity/connection/critical-part preservation. Do not merge as production-quality or treat the tiny known-arm correction as completion. A-only source-free code/tests/docs; B L04/L07, Public/C08, production LocalWorker, Golden and release untouched.


## 2026-10-26 source-only opt-in bypass hardening (not yet signed-replayed)

A code review of the composition found a separate semantic escape: the earlier `veto` covered only class32 pixels present in the *first* palette proposal and removed by morphology. The subsequent `eligible_classes=(30, 32)` opt-in could propose **fresh class32 pixels absent from the morphology-approved candidate**, potentially connected through newly added class30 pixels. Those were not in the old veto set. This is a P0 owner-integrity risk, not evidence of an observed new H08 defect.

The A-only composition now rejects every newly added class32 pixel outside the morphology-approved `cleaned` mask, while still permitting source-supported class30 opt-in and previously approved class32. A new source-free negative fixture exercises a connected class30 bridge with 20 unapproved class32 pixels; an independent local NumPy/SciPy reproduction removed all 20 and preserved 160 class30 and 400 previously approved class32 pixels. GitHub code/test blobs were read back after writing.

**Important provenance boundary:** the previously recorded H08 candidate SHA `c3a7e642...` and 38-test result refer to the *pre-hardening* PR head. The new exact GitHub-head full pytest, signed H08 replay, and H04/H06 regression are **not yet verified**. Do not claim the new candidate has the old SHA, do not count a new P0/P1 visual improvement, and do not merge this Draft on the strength of the old evidence. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO remain binding.


## 2026-10-26 post-hardening signed-source replay (research-only)

A new independent local replay reconstructed the H08 source-only chain directly from the four existing private Drive archives, checked their pinned ZIP SHA-256 and the 19/7/5 reviewed/Run30/AnimeSeg member manifests, and reproduced the **pre-palette** SHA `6472cfc419dfc8b2c97ff19350f1b53f31f82033bde3103851072d646d1db14f` and **current-frontier** SHA `94122b855f70347ff6f318e02bbfa03cddd77e74e76c3772bfe59011df0b0086`. Human review masks were opened only after the new owner candidate was frozen and hashed.

With the PR's current opt-in class32 hardening, the frozen H08 owner candidate is **`a08e94531825fbc78dd740c6da484fce51838bcffdd2529d0bd1769810646161`**, **not** the older pre-hardening `c3a7e642...`. Source-only new pixels: 6,623 (class30: 839, class32: 5,784); 239 morphology vetoes, 27 attempted veto resurrections (0 surviving), and **29 fresh unapproved class32 opt-in pixels withheld**. The signed known-only postscore changed from current-frontier **TP 144,221 / known FP 17 (arm 17) / FN 12,349** to **TP 144,036 / known FP 0 (arm 0) / FN 12,534**. This is a **tradeoff**: 17 reviewed arm false owners removed, but **185 reviewed garment pixels lost** relative to the current frontier. It is not a P0 case resolution or a blind generalization PASS.

H06 signed composed owner `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c` stayed byte-identical, with TP 294,020 / known FP 1,077 / FN 20,803. H04 signed Run30 owner `5b56899313d57b1677cb6c30676fe2e60c9fa141331a379aff7ee7a0e6101b5e` stayed byte-identical, with known FP 4,423 / FN 3,186. Local targeted source-free regressions: **13 PASS**, including 4 current PR composition tests whose test/code Git blob SHA matched the fetched GitHub head. The contact-density palette and partition dependencies also matched main blob SHA; other dependency blobs and the whole-repository test tree were **not fully identical**, so this is **not exact full GitHub-head CI** and not a merge-ready certification. The private originals, arrays, visual boards and human coordinates remain exclusively in the established non-shared Drive; no private pixels are included here.

**Integration decision remains Draft/HOLD.** 0 accepted P0 cases resolved, 0 P1 accepted, 3 major known P0 cases unresolved. The substantive remaining work is H08 large sleeve coverage and H06/H04 semantic owner errors, plus exact-head/full CI, signed unseen blind, Phase4 quality and human Golden. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO. No Lane B/Public/C08/LocalWorker/Golden changes.
