# L02 H06 neutral sleeve topology shadow, 2026-10-26

**Research candidate only. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** Do not wire to production owner inference, replace Golden, or modify Lane B/Public/C08/LocalWorker.

## P0 hypothesis and safeguards

The signed H06 coat's frozen Run30 owner contains a large class32 region of pale, near-neutral source pixels misowned as coat. A source-only neutral-white HSV proposal (S <= 41/255, V >= 189/255, connected class32 components >= 32 px) removes only class32 pixels; frozen class10 coat seed is immutable. The proposal refuses mixed jacket/coat owners, source-alpha escape, owner/class mismatch, high-neutrality coat seed, excessive removal, or topology-restoration budget failure. A minimum-path restoration reconnects pre-existing frozen 4-connected garment fragments through original source-owner pixels, without generating pixels or creating new owner labels. Original 4/8 component counts must match exactly.

**These thresholds were developed on exposed H06/H08 evidence and are not an unseen-character PASS.** No human mask, polygon or coordinates are read by the proposal; human review enters only after the candidate is frozen for postscore. Unknown pixels remain unknown. This is not a semantic underlayer detector, and topology-count equality does not prove all critical-part shapes are preserved.

## Actual signed known-case replay (twice, byte-identical)

Verified archive SHA-256: reviewed original `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, frozen Run30 owner `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, sleeve observer `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`. Signed H06 WebP source SHA `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`; H08 source SHA `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`.

| Known signed case | Candidate action | Reviewed known underlayer FP removed | Reviewed known arm FP removed | Reviewed true garment removed | Unknown removed | Frozen owner 4/8 components |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| H06 Run30 owner | 10,903 neutral pixels proposed, 148 topology bridges restored, net 10,755 removed | **10,077** | **92** | 330 | 256 | **9/8 → 9/8** |
| H08 Run30 owner | Mixed jacket/coat, explicit abstention | 0 | 0 | 0 | 0 | **27/20 → 27/20** |

H06 candidate owner uint8 C-order SHA-256 `3257ed1aefde4a4de7c313f62e95c6c27d22d731eba606b21a41b1ee1340adf5`; H08 unchanged owner SHA `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`. The H06 candidate still retains **1,249 known underlayer FP** (11,326-10,077) and **133 known arm FP** (225-92); it loses 330 reviewed true coat pixels. The H06 visual comparison showed large neutral cuffs excluded but the overall body/garment omissions persist. H04 not replayed: original signed source dimensions differ from Run30 owner and no unauthenticated resizing was applied.

**Baseline limitation:** These deltas compare to historical signed **Run30**, not the newer integrated H06 owner. Previous research reported H06 1,077 known FP for a different later owner candidate. The new proposal cannot be called an improvement over main without exact newest-owner composition and visual comparison. This candidate is a promising known-source P0 *hypothesis*, not a formally accepted P0 fix.

## Integration gate

Source-free focused regression **10 PASS** locally; two signed known-source replays deterministic. Need exact GitHub blob readback, PR head CI, current-main composed H06 owner comparison, H04 authenticated alignment, 4/8 critical-part identity (not merely counts), independent unseen signed blind cohort, model licence and user Golden/iPhone acceptance. Do not merge into production inference or claim Phase4 PASS. Officially accepted rendered P0/P1 improvements **0/0**; unresolved H04/H06/H08 **3**.

Private **lossless uint8 owner PNG** and source-dependent visual comparison were saved to the existing non-shared Drive evidence folder and independently downloaded again. The PNG byte SHA-256 is `3814cfa600d08abd3d1f684fe0766fe6b5446ab6660b288b3c12c4e959c32247`; decoding the cloud copy reproduces the exact H06 candidate owner SHA `3257ed1aefde4a4de7c313f62e95c6c27d22d731eba606b21a41b1ee1340adf5`. The private visual JPEG cloud copy SHA-256 is `3d0dd3d2cffa77901981c7df454a07a74dbd4ee475da7d57cf4492a5ec977720`. The local NPZ/ZIP transport copy is **not** claimed uploaded. No private images, NPZ, masks, human annotation geometry, or coordinates belong in GitHub.
