# Lane A L02: H08 geodesic two-order robust frontier shadow (2026-11-03)

**Research-only known-case candidate, not accepted image quality. Accepted P0/P1 fixes 0/0, H04/H06/H08 major defects unresolved 3/3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No B L04/L07, Public/C08, LocalWorker production or Golden change.

## Engineering change

The previous H08 17,815-pixel frontier candidate in PR #449 was rejected by its pinned wrapper because reversing scan order changes 9,503 owner pixels, including 479 conflicting nonzero owner IDs. Its fail-closed return of the unchanged frozen owner remains in force.

A separate A-only research candidate, tools/research/local_l02_class32_robust_frontier_shadow.py, now computes source-only four-neighbour geodesic distances from both frozen owners through the pinned class32 positive-evidence map. Ties and unreachable pixels abstain. An 8-pixel geodesic owner-distance margin is an **exposed H08 known-case hypothesis, selected after examining known-case outcomes**, not a blind-tuned or validated generalization threshold. It is not independent sleeve-vs-arm/underlayer semantic evidence.

The candidate applies local 4/8 foreground and background topology constraints in two traversal orders, retaining only pixels assigned the identical nonzero owner by both. Disconnected fragments are pruned. Whole-image 4/8 owner component and enclosed-hole counts must remain unchanged; otherwise the exact frozen owner is returned with quality=FAIL. No original owner overwrite, pixel generation, human annotation/coordinates in inference, or Phase4 promotion. Two-order consensus is not proof of invariance to every traversal or semantic correctness.

## Authenticated known-character comparison

The canonical private Drive ReviewedEvidence, SleeveSemantic and Run30 owner archives were retrieved and their full SHA-256 pins checked:

- ReviewedEvidence: 6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598
- SleeveSemantic: a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7
- Run30 owner: 6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c

Signed source bytes, class and frozen owner SHA triples matched the pinned PR-head constants for H04/H06/H08. The independently reconstructed source-only positive observer produced 6/0/31,505 positive pixels respectively. The **exact new core function** was executed on those frozen arrays. Human-reviewed masks were opened only after freezing candidate outputs for postscore. Unknown pixels were not treated as negatives.

| Exposed case | New owner px | Reviewed correct outerwear | Reviewed known non-outerwear FP | Unknown | 4/8 topology |
| --- | ---: | ---: | ---: | ---: | --- |
| H04 | 0 | 0 | 0 | 0 | unchanged |
| H06 | 0 | 0 | 0 | 0 | unchanged |
| H08 | **18,280** | **18,184** | **0** | **96** | unchanged |

H08 two geodesic-order traversals disagreed at 412 pixels before consensus and disconnected-fragment pruning. The final candidate owner SHA-256 (raw C-order bytes) is 66d36b7c8a8def761d591d0b1dff20ba85b2da38a5aae2e5ed1498442eb5c70d. Frozen and candidate owner 4/8 component counts are [29,22,14,11]; hole counts [3,1,3,1]. New module locally executed SHA-256: 0dd3d9754a8ac0eef1670a171c5db5a945ae7e3d02d737ed4bc32a8e67d2a67f.

A private visual board shows a substantial **partial** H08 sleeve owner recovery relative to frozen Run30, but whole sleeve/arm/garment semantics remain unresolved. The previous 17,815-pixel candidate was rejected, so 18,280 vs 17,815 must not be claimed as an accepted 465-pixel gain. The new candidate is **not adopted**, and H06 false garment ownership / correct garment loss remain unresolved.

## Verification, preservation and next gates

- The new source module and eight isolated source-free tests ran locally: **8/8 PASS**, compileall PASS. Existing imported observers were stubbed in these tests. Signed replay executed the exact new core but used an independently reconstructed pinned positive-evidence function. **Full exact PR-head canonical QA and exact full import-chain replay are still pending.** Synthetic test counts are not quality PASS.
- A private ZIP with H08 candidate owner NPZ, signed-source visual comparison and manifest was generated, member SHA checked: LaneA_L02_H08_RobustFrontier_KnownCase_PRIVATE_20261103.zip, full SHA-256 01e9ecb0b4d126d036969330f78a0b20351a2331503b756a43588b3278b5633a. Upload to the established non-shared Drive evidence folder failed twice with container_session_unavailable. **Not cloud-preserved; no cloud read-after-write.** No private image, mask, annotation, coordinates or owner NPZ in GitHub.
- This known-case hypothesis has no truly unseen signed blind evaluation, independent licensed garment/skin/underlayer observer, Phase4 critical-part and occlusion PASS, full-model/data rights signoff or Golden human review.

**Next:** exact PR-head QA and full signed replay, private Drive cloud preservation/readback, independent licensed sleeve/arm/underlayer semantic observer, H06 correct-garment preservation and H04 FP repair. Source-only Phase4 semantic/critical-part/occlusion PASS is mandatory before Phase5 real-source replay. Keep L02/L03/Golden/production gates HOLD/NO_GO.
