# L02 signed Run30 owner-colour prototype: independent-positive cross-character negative (2026-10-30)

**Decision: REJECT / P0 FAIL.** This is a new, frozen **source-only** proposal tested on the already exposed H06/H08 signed sources, **not** an accepted repair, a current strict/frontier improvement, an unseen-character blind, or Phase4 approval. No inference-time human labels, annotation coordinates, generation, inpainting, added source pixels, or Golden changes. All private arrays, originals and proposal maps remained in the existing private research working context, never in this repository.

## Authenticated provenance and frozen algorithm

- GitHub main at evaluation: `4a4348990084848c981811b414e6221411271f84`; Draft PR #445 before this note: `ef103f03f22f78241e00c3f4845a4504c7aad0d7`.
- Canonical non-shared Drive: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence/`.
- Signed ReviewedEvidence ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 owner ZIP `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, SleeveSemantic ZIP `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, AnimeSeg ZIP `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`, DeepFashion2 ZIP `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`. Existing member SHA manifests rechecked 19/19, 7/7, 5/5. DeepFashion2 weight bytes were **not** reauthenticated.
- Original encoded source SHA-256 H06 `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`; H08 `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`.
- Source-only candidate algorithm fixed **before opening any human review mask**: start from frozen Run30 4-connected owner; intersect independent DeepFashion2 outerwear positive with original source alpha and unowned pixels. For each existing owner, sample up to 5,000 deterministic interior RGB points, convert to CIELAB, fit 5 MiniBatchKMeans colour prototypes (seed 0); keep source-derived clusters representing >=5% of the sample with distance cutoff equal to the smaller of the cluster's 95th-percentile distance and Delta-E 18. Admit only 4-connected candidate components touching exactly one existing owner component, touching no other owner even diagonally, and preserving each owner's 4/8 component counts. No SegFormer-class allowlist expansion, human coordinates, or human-labelled tuning.
- Run twice from source-only inputs with identical candidate SHA-256: H06 `2d7c700400a639c65c7f2c1ed7e3149ae4264e5d73316bea6e8cd9654da8b584`; H08 `ec8234ad4da61f181785772adeac8799bc17c07525c9edfbe93751ebcf7642c1`. Human-reviewed masks were opened **after** these digests were frozen, for postscore only.

## Postscore on previously exposed signed cases (historical Run30, not current strict)

| Metric | H06 frozen Run30 | H06 proposal | H08 frozen Run30 | H08 proposal |
| --- | ---: | ---: | ---: | ---: |
| Reviewed true outerwear TP | 291,088 | **296,580** | 96,535 | **97,110** |
| Reviewed outerwear FN | 23,735 | 18,243 | 60,035 | 59,460 |
| Known false owner FP | 11,551 | 11,551 | 0 | **117** |
| Known underlayer FP | 11,326 | 11,326 | 0 | 0 |
| Known arm FP | 225 | 225 | 0 | **117** |
| Newly admitted source-alpha pixels | 0 | 5,756 | 0 | 4,916 |
| New reviewed true / known false / unknown | n/a | **5,492 / 0 / 264** | n/a | **575 / 117 / 4,224** |

4/8 owner component counts unchanged: H06 owner2 **9/8**; H08 owner1 **29/22**, owner2 **14/11**. No new cross-owner contact detected; original owner pixels and original-alpha boundary preserved. These topology checks are necessary, **not** sufficient semantic quality proof.

**Why FAIL:** Although this previously untested colour-prototype admission recovers 5,492 reviewed H06 garment pixels without adding a known false owner there, it also imports **117 known H08 arm pixels** and leaves **4,224 H08 newly owned pixels unreviewed**. H06's pre-existing **11,551 known false owner** (including 11,326 underlayer) is not repaired. The apparent H06 recovery is a known-case exploratory result, not a safe cross-character fix or an improvement over the later strict stage. No postscore-derived class-purity threshold, per-character exception, or retuning is authorized.

## Disposition and next integration gate

**Reject promotion of this candidate.** Do not commit its private maps, widen class25/0/7 allowlists from this postscore, or interpret unchanged connectivity as correct arm/underlayer ownership. The positive DeepFashion2 signal and owner-colour agreement remain insufficient to distinguish H08 arm from outerwear; the missing piece is independent affirmative pixel/subpart-level outerwear-versus-arm/underlayer evidence with explicit ABSTAIN, tested without known-case fitting. Run exact PR-head source-only Phase4 owner exclusivity/contact/critical-part QA, then signed strict replay and visual comparison; preserve H04 regression, true unseen signed blind, owner-PC QA and human Golden approval. Physical iPhone acceptance is **post-deployment**, not a pre-deployment GO blocker.

**Accepted P0=0, P1=0; H04/H06/H08 unresolved=3. New inference code accepted=0, main merges=0. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** Lane B, Public/C08, production LocalWorker and Golden untouched.
