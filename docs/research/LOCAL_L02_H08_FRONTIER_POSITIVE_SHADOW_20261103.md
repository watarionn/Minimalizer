# Lane A L02: bounded source-only H08 sleeve frontier shadow (2026-11-03)

**Research candidate only. Accepted P0/P1 fixes: 0/0. H04/H06/H08 unresolved: 3/3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Why this experiment is different

The existing Run30 H08 class32 positive-evidence map contains 31,505 unassigned source-color-supported pixels. The older all-or-nothing original-component contact gate admits 5,807 pixels; a single ambiguous contact can veto an entire otherwise useful component. The new A-only frontier helper considers individual pixels instead, admitting a candidate only when the *current* 4-connected neighbours and 8-neighbour owner set identify exactly one owner. It also checks both local foreground connectivity and negative-space connectivity, preserves every original 4/8 enclosed void, and verifies whole-image 4/8 owner component and hole counts before returning. It never overwrites an original owner, synthesizes RGB, or consumes human annotations. The 32-pass budget is a bounded exploratory rule, not a learned or blind-validated hyperparameter.

## Authenticated known-image experiment, not unseen generalization

Four canonical private Drive ZIPs were retrieved and their full SHA-256 pins verified: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; Run30 owner `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`; DeepFashion2 `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04` (not an inference input). Signed source bytes and Run30 frozen class/owner array SHA triples were checked for H06/H08. The H04 source-only positive count and zero assignment were also checked. The existing positive-evidence formula was independently reconstructed; its H04/H06/H08 positive counts matched 6/0/31,505. The *new frontier module* was executed against those frozen arrays. This is not a byte-for-byte execution of the complete PR-head import chain or the canonical repository QA.

Before loading human labels, candidate owner NPZ outputs were frozen and SHA-256 recorded. Human labels were used **only afterward** for the following postscore:

| Case | New owner pixels | Reviewed outerwear | Reviewed known non-outerwear | Unknown | Owner 4/8 topology |
| --- | ---: | ---: | ---: | ---: | --- |
| H04 | 0 | 0 | 0 | 0 | unchanged |
| H06 | 0 | 0 | 0 | 0 | unchanged |
| H08 | **17,815** | **17,724** | **0** | **91** | unchanged |

H08 assigns 8,964 pixels to owner1 and 8,851 to owner2. Its original and proposed owner component counts are both `[29,22,14,11]`, and enclosed-hole counts are both `[3,1,3,1]` (owner1 4/8, owner2 4/8). The 32-pass cap leaves 13,690 positive pixels unassigned. Compared with the earlier **5,807-pixel** topology-safe candidate, this is **12,008 more assigned source pixels**, but both are known-case research shadows, not accepted full-character fixes. A private source-only visual crop showed additional H08 sleeve fabric while significant sleeve gaps remain. No new RGB was generated.

**Unbounded growth is unsafe:** a separate 96-pass diagnostic on the same exposed H08 produced 21,904 assigned pixels but 25 known non-outerwear false positives. Neither the 32-pass result nor any threshold chosen after inspecting these labels may be presented as unseen generalization. The 32-pass experiment was defined before its postscore, but is still known-character research.

## Verification and preservation

- Source-free module and six isolated negative/contract tests added to PR #449; local isolated tests **6/6 PASS**, with stubs for pre-existing imported observers. The exact committed new source/test Git blob SHA must be read back. **Full exact-PR-head canonical QA has not run.**
- Private candidate ZIP with H06/H08 owner NPZ, source visual and private manifest was generated, internal member SHA checked, total ZIP SHA-256 `4addca85286bce322a3e7d6d84da88f7c448a77bbabb8a4f83a58a3af86d0583`. Upload to the existing non-shared Drive `10_Artifact_Library/03_Private_Research_Evidence` failed with `container_session_unavailable`; **NOT cloud-preserved; no read-after-write**. No private image/mask/NPZ or annotation is committed to GitHub.
- No independent sleeve-vs-arm/underlayer semantic authority; 91 unknown pixels are not negatives. Source-only Phase4 owner exclusivity and topology are necessary but insufficient for critical-part, occlusion, and whole-character quality PASS. H06 true coat preservation and major H04/H06/H08 missing regions remain unresolved.

**Next gates:** full PR-head QA and dependency validation, canonical private cloud preservation/readback, independent licensed garment/arm/underlayer semantics, source-only Phase4 critical-part/occlusion PASS, then Phase5 real-source replay, genuinely unseen signed blind, model/data rights and human Golden approval. No Lane B, Public/C08, LocalWorker production, Golden, or iPhone acceptance changes.


## 2026-11-03 signed-source traversal-order P1 owner instability (new, FAIL)

The 32-pass row-major frontier result is **not invariant to pixel traversal order**. This is a meaningful owner-identity risk even though both results retain 4/8-connected component counts and enclosed-hole counts. Independent NumPy/SciPy mirror runs used the **same SHA-pinned H08 signed source, class map and Run30 owner**, with only the source-only candidate traversal reversed; no human coordinates or masks entered inference.

| H08 source-only variant | Newly assigned | Reviewed outerwear (postscore) | Reviewed non-outerwear (postscore) | Unknown |
| --- | ---: | ---: | ---: | ---: |
| Raster, existing research shadow | 17,815 | 17,724 | 0 | 91 |
| Reversed raster, independent mirror | 16,959 | 16,762 | **25** | 172 |

The two candidate maps differ at **9,503 pixels**, including **479 pixels assigned to conflicting nonzero owner IDs**. Both retain frozen 4/8 component counts `[29,22,14,11]` and hole counts `[3,1,3,1]`. A source-only 4-neighbour geodesic audit also found **121 raster-assigned pixels closer to the opposite frozen owner** and **21 equal-distance ties**. These are uncertainty signals, not ground-truth owner labels. The human masks were loaded **only after** candidate maps and the source-only diagnostic were frozen. No unknown pixel was scored as negative.

A two-order intersection is **not** a safe automatic repair: the raw intersection assigns 12,396 pixels but increases 4/8 component counts to `[70,63,18,15]`. Pruning all new disconnected islands restores original component/hole counts but retains only 3,632 pixels, less than the earlier 5,807-pixel shadow. A 4-neighbour geodesic-priority alternative preserves topology with 11,447 assigned pixels (11,398 reviewed outerwear, zero reviewed non-outerwear, 49 unknown), but is not a proven quality improvement or independent semantic observer. **Do not choose the most favorable postscore or promote either alternative.**

**Source-only code safety correction:** the PR frontier helper now supports a private reverse traversal and its pinned wrapper automatically emits `scan_order_stability=FAIL`, `scan_order_changed_px`, `scan_order_owner_conflict_px`, and `scan_order_quality_gate=FAIL` whenever traversal changes ownership. Two new source-free negative/positive regressions exercise competing-owner ambiguity and a stable one-owner strip. The returned owner remains the original research shadow; this audit does not promote, overwrite or rewrite Golden. The independent mirror confirmed the signed H08 instability; **full exact-PR-head Python QA and signed replay of the newly committed wrapper remain unverified**.

H06 was also checked with a predeclared source-only two-pixel medial-axis corridor guard. It protected only 16 additional reviewed true-coat pixels while retaining 906 more known false-owner pixels compared with the independent 7,296-pixel baseline removal. **Rejected** as a worse tradeoff, not added to the inference code.

**Accepted P0/P1 quality fixes 0/0; unresolved H04/H06/H08 3/3.** H08 traversal-order stability is an additional **FAIL** for Phase4 semantic ownership, independent of unchanged topology. No blind generalization, licence clearance, Golden approval or production authorization. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO. Source originals, owner arrays, labels and coordinate-bearing diagnostics remain private; no B/Public/Worker change.
