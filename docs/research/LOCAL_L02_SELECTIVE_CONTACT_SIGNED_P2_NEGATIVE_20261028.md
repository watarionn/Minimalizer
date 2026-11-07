# L02 signed conservative vs selective contact: P2 negative (2026-10-28)

**Lane A research only. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** This is a source-free known-character evaluation, not an accepted P0/P1 fix or unseen-character validation. No source pixels, images, private arrays, masks, coordinates, or annotations are stored here.

## Provenance and procedure

- GitHub main independently read as `4a4348990084848c981811b414e6221411271f84`; PR #445 staged research head at the start `ffeffa1cbc56aa97975bd443cb3144066813f0da` (Draft, unmerged).
- Canonical Drive `chatGPT及びCodex用/Minimalizer` source-free archive `LaneA_L02_20261023_2253_SelectiveSignedOptIn_Integrated_SOURCEFREE.zip`, SHA-256 `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`.
- Private ReviewedEvidence, Run30 owner, SleeveSemantic, AnimeSeg archive SHA pins independently matched `6d7079b5…e17598`, `6ac735cc…d1f5c`, `a4322f81…3d7af7`, `9a3f27ed…eb1e26`. Internal reviewed/owner/AnimeSeg member manifests verified 19/7/5. Signed source was loaded before proposals. Labels were used only for postscore, not inference.
- The source-free archive's isolated tests passed **235 pytest + 31 subtests**. This is **not** exact PR-head CI.
- The fixed archive implementation was run in both `conservative` and opt-in `selective` contact modes. No threshold changes, model retraining, hand-annotation injection, or image generation.

## Actual known-case results

| Case and stage | Reviewed garment TP | Known FP | Known FN | Owner SHA-256 |
| --- | ---: | ---: | ---: | --- |
| H06 conservative composed | 294,020 | 1,077 underlayer | 20,803 | `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c` |
| H06 selective composed | 294,020 | 1,077 underlayer | 20,803 | identical |
| H08 conservative composed | 136,780 | 0 | 19,790 | `3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a` |
| H08 selective composed | 136,812 | 0 | 19,758 | `8ffb3df614bfcb189874ad54fe801ea3c2d27872577a761a1a365ed7d3711596` |

H08 selective retains **51 additional source-supported pixels**, of which **32** are reviewed garment and **19 unknown**; known FP remains zero. The per-owner 4/8 component counts were unchanged. H06 owner output is byte-identical between modes, so its serious underlayer defect is not addressed.

**Decision: do not promote selective contact as P0/P1 repair.** The H08 32-pixel known-only gain is P2 and is backlogged. H08 still lacks 19,758 reviewed garment pixels in this historical composed lineage; H06 retains 1,077 known underlayer FP. These figures are not current-main Phase4 results and must not be conflated with later strict-class32 stage or other historical baselines.

## Integration blockers and next work

The archived `local_l02_selective_signed_comparison.py` also contains a source-free receipt-key defect: it accesses `postscore()['FN']` although the loader returns `known_FN`. Repair that before staging this comparison runner. The archive's canonical strict replay carries a stale H08 composed SHA; PR #429 has a **separate guarded-stage pin repair**, not permission to substitute pins silently.

Prioritize H08 class32 sleeve semantic recovery and H06 underlayer owner separation, exact-main composed provenance and critical-part Phase4 tests. A strict source-only proposal must preserve original alpha, frozen owner, 4/8 topology and avoid underlayer/arm regression. Unknown signed blind, full exact-head CI, human Golden and physical iPhone acceptance remain pending.

**Accepted P0/P1 improvements 0/0; unresolved major H04/H06/H08 3. No merge, no production activation, no B L04/L07, Public/C08, LocalWorker or Golden changes.**

## 2026-10-28 signed-comparison runner defect repaired in PR #445

The 2026-10-23 source-free staging archive (external SHA-256 `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`) was re-read; its 98/98 internal SHA-256 entries matched. The archived comparison runner incorrectly indexed `postscore()['FN']`; the authenticated postscore contract emits `known_FN`. PR #445 now stages the byte-identical historical no-merge replay dependency, the corrected comparison runner and a negative/ordering regression test. Their Git blob SHAs are `e2097a31c943623018f3483b323dbcaa4785283c`, `67f39bfac9e756b1755c737263fda8ed5af7c892`, `900b2d27be5289b3c5c4559c44112915812f3292` respectively, all read back from the remote.

An isolated source-free archive with exactly these three files passed **236 pytest + 31 subtests**, including a regression requiring both H06/H08 conservative/selective proposals to be frozen before any human-label postscore. This is **not** exact PR-head GitHub CI. Four pinned private archives were independently SHA-verified (review/owner/AnimeSeg manifests 19/7/5), and H06/H08 **historical Run30 baseline** postscore was re-read: H06 TP 291,088 / known FP 11,551 (underlayer 11,326, arm 225) / known FN 23,735; H08 TP 96,535 / known FP 0 / known FN 60,035. Full conservative/selective real replay exceeded the execution budget and therefore **did not establish a new signed candidate result**. No source pixels, mask, coordinates or private artifact were committed.

**Accepted P0/P1 improvements remain 0/0; H04/H06/H08 unresolved 3.** This corrects a reproducibility/integration blocker only. The historical strict composed SHA lineage mismatch remains separate; never silently rewrite its pin. Current-main full owner reconstruction, actual semantic P0 repair, Phase4 source-only critical-part quality, unseen signed blind, exact-head CI and user Golden/iPhone acceptance remain pending. PR stays Draft and unmerged. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.
