# L02 dark-seed bright-island shadow: signed H04 accessory conflict (2026-10-26)

**Lane A only, dormant research. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Purpose and provenance

The exposed H04 original visibly has a light ID badge and blue lanyard over a dark jacket. A frozen SegFormer class5 jacket seed erroneously owns parts of those accessories. This candidate **only abstains** on sufficiently large bright source-color islands inside a dark jacket/coat seed, restoring minimal original-owner paths to preserve 4/8 connectivity. It does not add pixels, reassign owner IDs, use human coordinates in inference, or alter a production module.

Existing non-shared Drive evidence folder: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence/`. Exact private archive SHA-256:

- ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598` (19/19 member hashes).
- SleeveSemanticIndependent `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`.
- Run30 KnownCase OwnerMasks `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c` (7/7 member hashes).
- AnimeSeg Offline384 `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26` (5/5 member hashes, reference-only; not an input to this proposal).

All three signed original image **raw-file** SHA-256 matched the independent ReviewedEvidence audit. The source-only proposal for H04/H06/H08 was frozen and hashed **before opening the human evaluation masks**. Human review is postscore only; unknown is not a negative.

## Known-character result (historical Run30 owner baseline, NOT latest-main replay)

| Case | Run30 correct garment TP | Candidate TP | Run30 known FP | Candidate known FP | Owner 4/8 components |
| --- | ---: | ---: | ---: | ---: | --- |
| H04 | 49,386 | 49,381 | 4,423 | 3,642 | 5/5 -> 5/5 |
| H06 | 291,088 | 291,088 | 11,551 | 11,551 | 9/8 -> 9/8 |
| H08 | 96,535 | 96,535 | 0 | 0 | 27/20 -> 27/20 |

H04: **786 original-owner pixels abstained**, including **781 explicitly known non-outerwear** and **5 reviewed true garment**; **0 unknown removed**. An initial bright-island removal split the coat into more components; restoring 16 source-supported path pixels prevented that topology regression. The private visual board shows the removed area concentrated around the badge/lanyard, not a repaired whole-body silhouette. H06/H08 are byte-identical to their Run30 owners because the dark-seed eligibility guard abstained. The unguarded bright-island method was explicitly rejected: it erased 96,620 known H06 coat pixels and 9,452 known H08 garment pixels.

Candidate owner raw uint8 SHA-256: H04 `dfd05c84c3f4b1c92a5f9833c900f4f8cf2a43082403abd57ede4418995d3fc8`; H06 `4be9ae240b8d32cc6b0923371f5c5b3a6159196ba819aa0b7044c06740a7b317`; H08 `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`.

## Review, limits, and integration decision

- This is a **known-character-explored** color policy, including its dark-seed luminance eligibility. It is NOT an unseen-character transfer PASS. No claim that its threshold is independent of H04/H06/H08 exploration.
- **H04 has a promising visible accessory-ownership reduction** on Run30, but the five lost true pixels and the exact current-main owner comparison still require review. It does **not** resolve H04's remaining 3,642 known FP, H06 underlayer confusion, or H08 sleeve gaps.
- Source-free code and six negative tests are on this research branch; all **6 focused tests PASS** on the exact Git blobs. Whole-repository CI is **unverified** (GitHub Actions unavailable); do not count test volume as a quality gate.
- No private image, NPZ, mask, hand coordinates, or source pixels are committed. Private H04 visual board and owner PNG were generated locally for review, but **cloud upload/read-after-write did not complete** because the Library upload connector returned `container_session_unavailable`. They are **not** claimed preserved on Drive.
- Do not merge or activate this shadow as a quality fix until exact current-main H04/H06/H08 composed-owner replay, source-only Phase4 owner/connection/critical-part PASS, independent signed unseen-character blind, complete tests, and human visual/Golden review. Do not alter Lane B, Public/C08, production LocalWorker, Golden, or release flags.

**Quality accounting:** exploratory H04 known accessory misownership improved 1 exposed case, but **accepted P0 0 / accepted P1 0**; H04/H06/H08 major unresolved cases **3**. New production owner 0; merge 0. Continue priority H06 underlayer/coat and H08 large sleeve, not P2 micro-adjustment.


## 2026-10-26 signed H04 exact-blob owner replay and private preservation status

- The exact PR #443 source-only module was independently reconstructed and its Git blob SHA-1 checked against the PR: `2e51d870d88b52b4f00e17ee2ed55bbe5d7131c6`. This is a direct replay of that Git blob, not an inferred implementation.
- The signed H04 embedded source bytes from the canonical non-shared ReviewedEvidence archive matched SHA-256 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`. The Run30 H04 uint8 owner reconstructed from the canonical owner ZIP matched `5b56899313d57b1677cb6c30676fe2e60c9fa141331a379aff7ee7a0e6101b5e`, **the exact H04 owner SHA previously recorded for current main**. This closes the H04 baseline identity question; it does **not** mean the complete current-main Phase4 pipeline was newly executed.
- PR #443's exact source-only candidate was frozen before human review masks were opened. Its owner SHA-256 matched the original report: `dfd05c84c3f4b1c92a5f9833c900f4f8cf2a43082403abd57ede4418995d3fc8`. Postscore independently reproduced 786 abstained pixels: 781 explicitly known non-outerwear, 5 reviewed true outerwear, 0 unknown; reviewed outerwear TP 49,386→49,381 and known FP 4,423→3,642. Four/eight-neighbour owner component counts remained 5/5. No new source pixels or owner-ID promotions.
- A new private signed-source/Run30/candidate crop was inspected. The light badge/lanyard misownership is **partially reduced**, but the badge and coat boundaries are still visibly incomplete; no whole-character P0 defect is resolved. H06/H08 remain unresolved, and this exposed-case rule is not blind transfer evidence.
- A lossless private candidate-owner PNG, source comparison PNG and private receipt were generated. Upload to the **existing** non-shared Drive folder was attempted through the mounted Google Drive Library route, but all three uploads returned `container_session_unavailable`. **Cloud preservation and read-after-write are NOT verified; do not treat these artifacts as delivered.** No alternate public storage, raw source, mask or coordinate upload was attempted. The source-free code and this aggregate report remain in the A-only GitHub Draft branch.

**Integration verdict remains Draft/HOLD:** formally accepted P0 0, P1 0, known major unresolved 3; no merge or production owner change. Missing: independent unseen signed blind, critical-part/semantic owner PASS, full exact-head CI, source replay/visual Golden and owner iPhone acceptance. Lane B, Public/C08, LocalWorker and Golden untouched.
