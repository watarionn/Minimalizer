# L02 2026-10-28: signed H08 palette/contact replay and dependency staging (HOLD)

**Scope:** Lane A \`research/local-*\` only. Source-free evidence; no original image, private owner, human mask, polygon, NPZ, visual board or model weights in GitHub. This is an **exposed historical Run30 experiment**, not current-main composed-owner replay, blind generalization, accepted Phase4 or production change.

## Source and dependency provenance

- Current main re-read at start: \`4a4348990084848c981811b414e6221411271f84\`.
- Canonical non-shared Drive: \`chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence\`. ReviewedEvidence ZIP SHA-256 \`6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598\`; Run30 owner \`6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c\`; SleeveSemantic \`a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7\`; AnimeSeg \`9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26\`.
- Historical source-free staging ZIP \`c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc\`; **98/98** internal SHA-256 manifest entries matched.
- Two missing, non-production source-only dependencies staged on PR #445, with **Git blob-exact** source archive readback: \`local_l02_sleeve_no_merge_shadow.py\` blob \`422cde9a48c24b03e3a2541c4637d4ab85dd847f\`; \`local_l02_source_palette_sleeve_shadow.py\` blob \`b42ac51a067c3ef60e25f07914edc22c1b425c48\`. Corresponding tests blob \`8a2d540f60b7a16433e13c7e19905a4d67bbf721\` and \`19d0d76ac4e69518f157b9f979d55a249cfe3f7f\`.
- Existing main \`local_l02_guarded_sleeve_geodesic_shadow.py\` and \`local_l02_hue_extended_owner_shadow.py\` blobs **exactly match** the staging archive imports. Historical cross-owner prune is **not** asserted blob-identical to current main. No production call site wired.
- Isolated exact-archive tests: **13 targeted PASS + 5 subtests**, **235 archive tests PASS + 31 subtests**. Not exact-PR-head CI.

## Signed historical Run30, source-only proposal frozen before reviewed postscore

The candidate is the archive's fixed 8-color / 95th-quantile / 1024-pixel source-LAB hypothesis, not retuned in this run. AnimeSeg class 10 means generic clothes, not outerwear truth. New pixels are restricted to original source alpha and class32. After the palette proposal, the **historical archive** contact-prune gate was applied. Human reviewed labels were opened **only after** proposal generation and hashing.

| Reviewed-only | H06 Run30 | H06 proposal | H08 Run30 | H08 palette + archive contact-prune |
| --- | ---: | ---: | ---: | ---: |
| True outerwear owner pixels | 291,088 | 291,088 | 96,535 | **133,755** |
| Missing reviewed outerwear | 23,735 | 23,735 | 60,035 | **22,815** |
| Known false-owner pixels | 11,551 | 11,551 | 0 | **0** |
| Known arm false-owner | 225 | 225 | 0 | **0** |

H08 adds **37,325** original-source pixels, of which **37,220** are reviewed outerwear, **0** are labelled negatives and **105 remain unknown**, not proven positive. H08 output owner SHA-256: \`c3fb9591cb53936f7dc4802a795ab275e1bffbae3ca8cc5f0af9f3b38a811285\`. The archive contact-prune blocked 127 new orthogonal and 262 diagonal cross-owner edges, removed 315 proposed pixels and 2 detached pixels, erased **0** frozen owner pixels. The no-merge stage retains frozen 4/8 component identity; cross-owner contact verification returned no new contacts. H06 is unchanged (owner SHA \`4be9ae240b8d32cc6b0923371f5c5b3a6159196ba819aa0b7044c06740a7b317\`).

Independent private full-image visual comparison shows additional H08 sleeve/jacket coverage but **visible major silhouette and sleeve gaps remain**. H06 underlayer/arm false ownership remains severe. H04 was not newly replayed. These metrics are on **known/exposed** images and are not current-main improvement; do not double-count them as accepted P0/P1.

## Preserve and merge decision

A private H06/H08 lossless owner/visual/receipt ZIP was built and SHA-256 checked locally (\`36dd24cc0b918f509f87abf4ac880acecda6866dd1dbc796ed277e8122e7259d\`), but both attempts to upload it to the existing non-shared Drive folder failed with \`container_session_unavailable\`. **Cloud preservation/read-after-write is NOT verified.** No private data was placed on GitHub. Retain this source-free receipt and rerun authorized private upload through a working connector before claiming preservation.

**Accepted P0 fixes 0; P1 fixes 0; unresolved major H04/H06/H08 3.** PR #445 remains Draft/unmerged. Remaining blockers: reconcile historical/current-main cross-owner audit version, stage remaining dependencies, exact current-main composed-owner reconstruction, H04/H06/H08 critical-part and semantic owner quality, independent unseen signed blind, exact-head CI, Golden and physical iPhone owner acceptance. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No Lane B L04/L07, Public/C08, production LocalWorker or Golden edits.
