# SA1060M / C02b7c1: independent semantic anchor evidence gate

**2026-10-10: VALIDATOR IMPLEMENTED AND TESTED. C02b7c semantic anchor acquisition is IN_PROGRESS. C02 quality remains HOLD.**

## Problem and scope

The prior C02b7b source-boundary observer measures declared owner masks against source Canny edges, alpha, raster cores and declared part overlaps for GC001 and Raden. Those observations do not supply independent semantic part labels. Existing pose-only wrist confidence (0.462252) is also below its acceptance bound, and prior appearance-only pruning destroyed original-source edges. Simply renaming a detector 'independent' or selecting one historical Phase04 revision would not supply owner truth.

The new `c02b7c_independent_owner_evidence_gate.py` is a **read-only, fail-closed gate** accepting *externally produced* source-only semantic/pose part anchors. Each supplied observation must identify its signed original-source SHA, case, observer identity and family, model/annotator lineage digest, inference run digest, original-source-only input provenance, declared calibrated confidence, permitted owner, and 340x340 pixel anchor location. It rejects wrong cases/SHAs, Stage8/mask-derived or color/alpha/Canny-only origins, invalid coordinates or confidence, tampering, duplicate runs, and observer family/lineage reuse. At least two independent **claimed** observer identities, method families and lineages must assign the same owner at the same location with self-reported confidence >= 0.85. Conflicts and low confidence abstain. Even strong agreement generates **review-only** counts and **never** modifies source pixels or owners.

**This does not verify observers actually ran independently or that confidence is calibrated.** The gate can validate syntactic/provenance claims but cannot replace a trusted observer registry, independently approved annotations, semantic Golden or Chrome quality. Agreement of two self-declared observers is not a truth certificate. There is no auto-edit or deployment path in this implementation.

## Test verification

- **20/20 PASS** against both private original signed GC001 and Raden PNGs and full, exact Stage8 scenes, including deterministic two-case abstention, SHA tampering rejection, cross-source substitution rejection, 340x340 constraints, unknown owners, invalid confidences, evidence-source anti-correlation, conflicting labels, duplicated runs, same model family, same lineage, same observer identity, and positive **REVIEW_ONLY** synthetic claims.
- **16 PASS / 4 SKIP** in a public fixture-free checkout. Tests that require signed originals explicitly SKIP rather than inventing substitutes.
- Verified source SHA and original Stage8 immutable scene SHA:
  - GC001 source `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e` and signed Stage8 `7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08`
  - Raden source `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00` and signed Stage8 `be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f`
- Actual signed replay without independent observer submissions: **GC001 = ABSTAIN_NO_INDEPENDENT_ANCHORS, Raden = ABSTAIN_NO_INDEPENDENT_ANCHORS**. Exactly zero mask changes. No observer model was run and no independent semantic owner truth is claimed.
- Test files and report are source-free. The coordinate-free JSON contains hashes, outcome and counts only. Signed raster images, Stage8 source coordinates, and review boards stay private.

## Decisions and next actions

1. Complete **C02b7c2** by obtaining actual independent source-only part/pose observation(s) for GC001 and Raden from two distinct, auditable model or human-annotation families. Record model weights and licensing, reproducibility, calibrated confidence, and evidence SHA per observer. Do not promote anonymous or correlated predictions as proof.
2. Feed actual signed observations to this gate and visually inspect candidate evidence. Merely attaining a syntactic review-only agreement cannot authorize mask changes. Generate source-supported read-only proposed corrections only after separate independent semantic validation.
3. Validate any proposed candidate on GC001 and Raden, approved 18/78 corpus, real canonical Chromium DPR1/DPR2, source-owner/silhouette/hair/clothing preservation, and candidate-specific human Golden.
4. Independently resolve C03 **original** Stage8 source ring limits (GC001 3604/1887, Raden 2370/1412) without substituting compact output-SVG budgets. C04 human Golden 12 criteria are PENDING. C05–C08 remain BLOCKED.

No source was modified. No generated fill. No facial microfeatures were added. `release_authorized=false`, `deployment_verified=false`, `production_changed=false`.
