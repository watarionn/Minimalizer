# MinimalizerLocal Lane A L02: signed H08 dual-owner LAB reach, Run30-only

**Research/HOLD. Not an accepted current-main improvement.** 2026-10-27. Source-only code, no hand masks/coordinates in inference, no image synthesis, no new source pixels, no face drawing, no Golden/production modification.

## Authenticated known-source experiment

Private signed archives were retrieved from the existing non-shared Drive folder `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`. Their ZIP SHA-256 pins matched ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, and AnimeSeg `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Private member manifests verified 19/7/5. Original signed WebP source hashes were checked by the replay loader. **Human visible masks were read only after source-only proposals were frozen and SHA-256 hashed.** Unreviewed pixels remain unknown.

The exact initial GitHub research module blob `cf3f7e73145a9dee25e8edca3f50cb3aae87bcb4` was reproduced locally before modification. The new owner-pin check changes only the fail-closed input contract, not the candidate pixels. The signed replay used the updated code and externally pinned historical Run30 owner SHA values.

| Reviewed-only metric | H08 signed Run30 | H08 LAB-reach candidate | H06 signed Run30 | H06 unchanged |
| --- | ---: | ---: | ---: | ---: |
| Correct garment TP | 96,535 | **99,890** | 291,088 | 291,088 |
| Known false owner FP | 0 | **0** | 11,551 | 11,551 |
| Known arm FP | 0 | 0 | 225 | 225 |
| Missing garment FN | 60,035 | **56,680** | 23,735 | 23,735 |
| Added original-alpha class32 pixels | 0 | 3,356 | 0 | 0 |

H08 new 3,356 pixels consist of **3,355 reviewed garment pixels and 1 unreviewed pixel**, not 3,356 proven positives. H08 owner1 4/8 component counts 29/22 and owner2 14/11 were unchanged. H06 has no dual-owner domain and is an exact no-op. H08 candidate uint8 C-order SHA-256 `b4e5201e22bef51b14e6aa814b745653cc91449b6d7427fc9eae7751ac351291`; baseline `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`.

**Critical comparison boundary:** the latest recorded H08 composed-owner frontier is `94122b855f70347ff6f318e02bbfa03cddd77e74e76c3772bfe59011df0b0086`, already much stronger than Run30. Passing that current-frontier SHA as the new mandatory expected owner pin while supplying Run30 produced `COMPOSED_OWNER_SHA_MISMATCH`, as intended. Therefore the +3,355 known positives are **not** an improvement over main, and must not be counted as a resolved P0 or P1 defect. A visual preview shows remaining sleeve/garment gaps, not full recovery.

## Code and gate

The source-only research function now requires a caller-supplied **externally authenticated composed-owner SHA-256**. Missing, malformed or mismatched pins fail closed before LAB or component work. A caller must independently verify signed raw source SHA and class observation provenance; calculating an expected pin from the untrusted input itself does not authenticate it. Six source-free targeted tests PASS against the modified local code, including wrong-stage pin, alpha escape, invalid owner/class and single-owner abstention. This is not full repository CI.

Private lossless owner PNG and visual JPEG were generated locally; **Drive upload failed with `container_session_unavailable`, so cloud preservation/read-after-write is NOT verified**. Do not publish those bytes, human masks or coordinates to GitHub. A future authorized private upload must target the same existing non-shared evidence folder, not a new root folder.

**Release decision:** Draft only; no merge or inference activation. Remaining gates: latest composed H08 SHA-exact replay, human visible sleeve/arm critical-part comparison, H04/H06 full current-owner regression, source-only Phase4 semantic owner exclusivity/topology, unseen signed blind, full CI, Golden and iPhone user acceptance. Accepted P0/P1 resolutions 0/0, H04/H06/H08 unresolved 3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / Local production NO_GO. No B L04/L07, Public/C08, production LocalWorker, or Golden edits.
