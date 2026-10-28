# L02 strict-owner H08 LAB-reach signed research (2026-10-28)

**Research candidate only. No accepted P0/P1 repair, no Phase4 or release approval.** Source-free. The signed originals, reviewed masks, owner arrays, source coordinates and diagnostic board are **not** included in GitHub.

## Provenance and isolation

- GitHub main independently read at `4a4348990084848c981811b414e6221411271f84`. PR #445 remains Draft/unmerged. Source-only modules and tests are staged on the A-only research branch, not connected to production.
- Non-shared Drive original folder: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`. The folder's Google permission metadata was read: `shared=false`, owner-only.
- Authenticated source archives: ReviewedEvidence ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; Run30 owner ZIP `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; SleeveSemantic ZIP `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`; AnimeSeg ZIP `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Reviewed/Run30/AnimeSeg internal manifests passed 19/7/5.
- Source-free historical staging ZIP SHA-256 `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`. H08 composed SHA `3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a`; strict owner SHA `32bb5266a479ce64571f190ffebe90b50c01329598408019b363c5ab0c9f0778`. These were reconstructed from the historical source-only staging archive, **not from a complete exact-current-main checkout**.

## Source-only proposal, frozen before human postscore

The dormant `local_l02_strict_lab_reach_shadow.py` uses only the authenticated source RGBA, frozen class map and SHA-pinned strict owner. It reuses the previously exposed PR #445 OpenCV-LAB/spatial thresholds (20/20, competing-owner margin 5); **no threshold was selected from this run's human masks**. It admits only previously unowned, fully opaque class32 pixels, cuts new cross-owner contacts, prunes joins/orphans, and verifies frozen-owner immutability and 4/8 component identity. It does not generate or inpaint pixels, infer from annotations, or change any production call site.

The source-only candidate was frozen and SHA-256 hashed **before** opening human labels: `34679ecdbdc6db8bdbe6245d1575cbe8e1ff10875e59f759d4f459d67432a2c9`. It proposes 4,027 original-source pixels and changes zero frozen-owner pixels. An independent implementation and the staged module produced the **same exact owner SHA**. Four source-free targeted tests PASS locally. This is not full PR-head CI.

## Signed H08 reviewed-only postscore

| H08 metric | Historical strict baseline | Strict + fixed LAB reach |
| --- | ---: | ---: |
| Reviewed outerwear true pixels | 137,261 | **141,127** |
| Reviewed outerwear missing pixels | 19,309 | **15,443** |
| Known non-outerwear false-owner pixels | 0 | **0** |
| Known arm / underlayer FP | 0 / 0 | **0 / 0** |
| New source-supported owner pixels | 0 | **4,027** |

Of the 4,027 new pixels, **3,866 are reviewed outerwear, 0 are known negatives and 161 are unreviewed/unknown**. Unknown is not a positive or negative. The known-only IoU changes 0.876675 → 0.901367, but this is **not** blind generalization. Visual side-by-side review still shows major sleeve/garment incompleteness. The source-only candidate is meaningful research coverage, **not an accepted P0 fix**.

## Remaining gates and preservation

- H04/H06 exact strict-stage regression for this new module was **not** executed. The H06 strict-stage replay attempt timed out; no H06 no-op or quality PASS is claimed.
- The source-free historical archive and current-main contact/transition audit interface have not been assembled into a complete exact-main source-only owner reconstruction for this candidate. Full current PR CI, Phase4 semantic owner/critical-part quality, independent unseen signed blind cohort, Phase5, Golden and physical iPhone acceptance are still pending.
- A private derived-owner/receipt/visual ZIP was prepared locally with SHA-256 `8880278fc1e3af5b731be7e343f7350321abae0aa093fea2ed1bf74e59eb2e1e`, but the upload into the existing non-shared Drive folder failed with `container_session_unavailable`. **Cloud preservation/read-after-write is NOT verified.** Do not claim the private evidence is durable or publish its bytes to GitHub.
- Accepted P0 improvements **0**, P1 improvements **0**. Unresolved H04/H06/H08 **3**. No main merge, no B L04/L07, Public/C08, production LocalWorker or Golden changes.

**L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** Next: exact-current-main source-only owner replay, H04/H06 regression, source-only Phase4 critical-part/connectivity review, then genuinely unseen signed blind and full CI before considering any promotion.
