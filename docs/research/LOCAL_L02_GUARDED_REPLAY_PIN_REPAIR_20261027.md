# L02 guarded signed replay: H08 stale provenance pin repair (2026-10-27)

**Lane A, dormant source-free staging only. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Actual signed replay and root cause

The canonical Drive ReviewedEvidence (SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`), Run30 owner (`6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`) and AnimeSeg384 (`9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`) private archives were independently materialized. Their internal manifests passed 19/19, 7/7 and 5/5. The signed source loader verified the embedded originals before source-only inference. Human masks were used only after the owner candidates and hashes were frozen.

The archived `local_l02_canonical_strict_signed_replay.py` in `LaneA_L02_20261023_2253_SelectiveSignedOptIn_Integrated_SOURCEFREE.zip` still expects the **older unguarded** H08 composed SHA `82313762...`, and aborts with `COMPOSED_BASELINE_SHA_MISMATCH`. The actually assembled **conservative cross-owner-guarded** wrapper (source-file SHA-256 `b49d3c0744c838715e44b7405ec0b621c8b356c1de710eff7b803ed71bc196a7`) produces `3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a`. The same guarded owner is documented in `LOCAL_L02_20261023_2020_BOUNDED_COMPONENT_REPLAY.md`. The earlier and guarded owners must not be conflated: the guard rejects 43 new four-neighbour and 84 diagonal cross-owner contacts, pruning 100 unsafe additions. Do not remove the guard to match the old SHA.

## Repaired staging-only replay

The adjacent `LOCAL_L02_GUARDED_REPLAY_PIN_REPAIR_20261027.patch` updates **only** the H08 expected owner hashes, pins the exact guarded wrapper source SHA, and marks the replay as staged-overlay-only. It does not change owner inference thresholds, model weights, source pixels, masks, or any production module. The patched script completed authenticated signed H06 and H08 replays:

| Case | Guarded composed SHA-256 | Strict SHA-256 | Reviewed true garment TP | Known FP | Known garment FN |
| --- | --- | --- | --- | --- | --- |
| H06 | `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c` | same | 294,020 → 294,020 | 1,077 underlayer | 20,803 |
| H08 | `3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a` | `32bb5266a479ce64571f190ffebe90b50c01329598408019b363c5ab0c9f0778` | 136,780 → 137,261 | 0 known | 19,309 |

H08 strict added 484 source-supported pixels: 481 reviewed true garment, zero known negatives, three **unknown** (not counted as negative). Per-owner four/eight-neighbour component counts were preserved. This is a **reproduction of a known-character partial recovery**, not a newly accepted P0/P1 improvement or blind generalization. H06 underlayer FP and H08 major sleeve FN remain. H04 was not replayed.

## Ship gate

This patch applies to an **unmerged assembled research overlay**, not to GitHub main or a runnable PR #429 checkout by itself. Do not merge the patch or PR as a quality fix without first reconciling all source-free staged dependencies against current main, checking the actual PR-head full tests, signed source-only Phase4 semantic/critical-part quality, independent signed blind character and visual Golden/iPhone acceptance. Existing GitHub main at this verification: `4a4348990084848c981811b414e6221411271f84`.

**Formally accepted P0/P1 improvements 0/0. Unresolved major H04/H06/H08 = 3. No production owner or B/Public/C08/LocalWorker/Golden changes.**
