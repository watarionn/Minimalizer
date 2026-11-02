# Lane A L02: signed H08 class32 topology-safe positive owner shadow (2026-11-02)

**Research-only, NOT a Phase4 acceptance or production change.** This is a new source-only owner candidate, not a rendered image or unseen-character generalization. Accepted P0/P1 fixes **0/0**; H04/H06/H08 remain **3 unresolved major cases**. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.

## Frozen hypothesis before human postscore

The existing pinned Run30 positive-evidence module in PR #449 identifies source-color-supported, unowned class32 pixels, but deliberately does not assign an exclusive owner. The new module accepts that already pinned source/class/owner triple and applies an additional **topology-preserving exclusive-owner rule**, without reviewed masks, user coordinates or class-specific threshold fitting:

1. Partition positive-evidence pixels independently under 4-neighbour and 8-neighbour connectivity.
2. For each positive component, inspect its **original frozen owner** contacts. A component may join only one semantic owner (1 or 2) and only **one pre-existing connected component of that owner** under the same connectivity. Contacts with the other owner, multiple original components, or no owner all abstain.
3. Assign only pixels whose 4- and 8-neighbour component decisions agree. Recompute original and proposed component counts for both owners and both connectivities; any change fails closed. Never remove an existing owner pixel, assign outside source alpha, or generate source pixels. The pinned upstream positive evidence already enforces source RGB/alpha, class32-only, unowned-only and source/class/owner SHA integrity.

This conservative guard rejects many plausible sleeve pixels. It is intentionally not a model of garment semantics; topology preservation alone is insufficient to prove correct clothing ownership.

## Signed, known-character shadow replay

Canonical existing private Drive evidence ZIP SHA-256 pins were verified for reviewed originals (`6d7079b5...3e17598`), Run30 owner (`6ac735cc...b26ad1f5c`), and frozen SleeveSemantic class maps (`a4322f81...9918345e3d7af7`). Exact H04/H06/H08 signed source/class/owner SHA triples matched the registry. Candidate owner arrays were frozen to private files **before** loading human-reviewed masks. Postscore is known-character only; unlabelled pixels remain unknown.

| Case | Source-only positive px | New exclusive owner px | Reviewed true outerwear recovered | Known arm/underlayer/hair FP added | Unknown added | Original vs candidate 4/8 owner components |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| H04 | 6 | 0 | 0 | 0 | 0 | `[5,5,0,0]` unchanged |
| H06 | 0 | 0 | 0 | 0 | 0 | `[0,0,9,8]` unchanged |
| H08 | 31,505 | **6,047** | **5,962** | **0 known** | **85** | `[29,22,14,11]` unchanged |

H08's **labelled-only Run30 owner IoU increases 0.616561 → 0.654640** (reviewed garment FN **60,035 → 54,073**, known FP remains **0**); this is a known-character postscore, not blind quality proof. H08's 6,047 new owner pixels lie in a visible sleeve/cuff region of the signed original. The private original-versus-candidate diagnostic was inspected; no generated RGB pixels were used as evidence. The **25,458 remaining positive-evidence pixels abstain** because of component ambiguity, absent contact or topology constraints. This is a **new partial P0 sleeve recovery candidate**, not an accepted P0 fix: 85 newly assigned pixels lack human labels, independent sleeve-vs-arm/underlayer semantics and full occlusion/critical-part validation are still missing. No claim of H06 repair, H04 repair, unknown generalization or actual Phase5 replay.

## Verification and integration gates

- The new source-free helper's six isolated synthetic regression tests passed using explicit stand-in imports for the two pre-existing PR #449 modules. This is **not** a full exact-PR-head repository test. The exact new helper was independently applied to frozen signed positive arrays; all three candidate owner maps matched the prelabel-frozen shadow and all four owner connectivity counts were unchanged. The exact pinned public entrypoint still requires full PR-head execution.
- Private candidate owner NPZ, source-only evidence arrays, reviewed masks and diagnostic images must remain in the existing non-shared Drive research evidence folder, never in GitHub. Cloud upload/readback is a separate preservation gate; do not mark complete without verifying remote bytes.
- Before any PR merge or owner promotion: exact-head dependency/CI QA, full source-only owner exclusivity and critical-part/occlusion visual QA, independent model observation, unseen signed blind, model/data rights and user Golden approval. A code-level topology guard is not a substitute for these gates.
- No changes to B L04/L07, Public/C08, LocalWorker production, Golden or iPhone acceptance.

## 2026-11-02 enclosed-negative-space P0 safety correction (post-checkpoint, UNVERIFIED on signed images)

A new source-only counterexample revealed a topology defect in the preceding helper: preserving only the number of 4/8-connected *owner components* does not preserve enclosed negative-space openings. Filling an arm opening in a ring, or closing a U-shaped opening, leaves the foreground owner component count unchanged but changes its enclosed background holes. This is a possible major silhouette/occlusion regression, not a one-pixel cosmetic issue.

The research helper now excludes original 4/8-enclosed owner void pixels from positive assignments and fails closed if the proposed owner creates or destroys any enclosed hole under either connectivity. Two source-free regressions encode both cases. This conservative veto uses frozen owner topology only, no reviewed masks, new model weights, user coordinates or source pixel generation. The protected voids are not automatically classified as negative ground truth; they are simply abstained pending independent semantic evidence.

**Crucial status:** the earlier signed H08 6,047-owner-pixel candidate / 5,962 reviewed-garment postscore was measured on the **pre-correction head**. The corrected head has not yet completed exact integrated tests or private signed-image replay. Do not attribute those quality numbers to this head, assume they remain unchanged, or merge/promote on the new regression alone. Repeat H04/H06/H08 frozen replay and assess both recovered sleeve and new abstentions, then verify private cloud preservation. Accepted P0/P1 fixes remain 0/0; H04/H06/H08 remain unresolved 3/3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.

## 2026-11-02 topology-simple-point signed replay (new candidate, still HOLD)

The initial enclosed-void-only guard correctly rejected the prior H08 6,047-pixel assignment: the candidate preserved owner component counts but **created 25 enclosed owner1 voids under 4-connectivity and 16 under 8-connectivity** (owner1 holes 3→28 / 1→17). This is a genuine silhouette topology failure that was invisible to the earlier component-only tests. Do not treat the earlier 6,047-pixel candidate as safe.

A deterministic, bounded source-only 3×3 simple-point frontier now grows only pixels whose current same-owner neighborhood is connected under **both 4 and 8 connectivity**, preserving original enclosed voids and abstaining at loop closures. The final 4/8 owner component and enclosed-hole counts are independently rechecked and fail closed if changed. It never uses human labels or coordinates for candidate generation. At most 100,000 candidate pixels and 64 deterministic passes are permitted; all remaining candidates abstain.

The three existing private canonical ZIP archives (reviewed originals, frozen class IDs, Run30 owner) were materialized from the existing non-shared Drive evidence folder and their full SHA-256 pins independently matched. All **3/3 source/class/owner SHA triples** matched the pinned public registry. A standalone mirror of the updated source-only core passed seven regression scenarios, including old-owner void fill, new void closure and existing 4/8 component cases. Exact integrated PR-head QA/CI remains **UNVERIFIED**.

**Frozen candidate before human postscore:** signed H04/H06/H08 source RGB/alpha and frozen class/owner arrays were replayed with the updated algorithm. H04/H06 add zero pixels; H08 grows **5,807** previously unassigned pixels (45 bounded passes), abstaining on **240** additional pixels compared with the old 6,047 candidate. All 4/8 component counts remain H08 `[29,22,14,11]`; all 4/8 enclosed-hole counts remain `[3,1,3,1]`. The source-only candidate was saved privately before human masks were opened for scoring.

**Known-character postscore, not blind:** H08 newly assigned **5,726 reviewed outerwear**, **0 known arm/underlayer/hair false positives**, **81 unknown**. Labelled-only known IoU **0.616561→0.653133**, reviewed outerwear FN **60,035→54,309**, known FP remains 0. H04/H06 remain unchanged. This is a **partial visible-sleeve P0 candidate**, not an accepted complete P0 fix or actual rendered-image improvement. Independent semantic evidence, full critical-part/occlusion review, unknown-character blind and Golden approval remain missing.

A new PRIVATE evidence ZIP containing candidate owner maps, internal SHA manifest and private postscore receipt was generated locally and checked, but upload to the exact canonical Drive folder failed with `container_session_unavailable`. **Cloud preservation and read-after-write are NOT COMPLETE**. No private original, NPZ, mask or coordinates were committed to GitHub. Accepted complete P0/P1 fixes **0/0**; unresolved major cases **3/3**. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO. No B/Public/Worker/Golden change.
