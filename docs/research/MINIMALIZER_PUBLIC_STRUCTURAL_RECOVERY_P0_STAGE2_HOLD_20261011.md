# MinimalizerPublic StructuralRecovery P0 Stage 2: source-part evidence and overlap authority (HOLD)

2026-10-11. Continuation of Stage1 Draft PR #390, backed by the handoff Draft PR #389. **Research-only**, not a released converter or a completed human Golden review. No Local Worker, normal browser fallback route, main, original image or production deployment is changed.

## What is implemented

- `web/static/public-source-part-authority-p0.mjs`: independent source-owning part evidence gate; explicitly passed `Uint8Array` source RGBA + face owner + per-part masks and SHA-256 pins. `crypto.subtle` must be available or it fails closed. No model, network request, CSS/DOM or render imports.
- Supported candidate roles: left/right arm, tie/neckwear, collar, eyewear, bow, corset lacing, sleeve ruffle, held object and major accessory. **This vocabulary does not classify a real image.** The module requires externally supplied masks and evidence references, and each mask remains an observation until separately adjudicated. A text field of `independently_attested` is not a cryptographic signature or human approval.
- Rejects missing/duplicate/unknown owners, nonbinary/empty/incorrect-size masks, missing evidence labels, invalid or mismatched SHA pins, face collisions, source alpha unsupported pixels, missing z-order provenance, ambiguous overlapping owners, cycles, and over-budget visible ownership.
- Deterministically establishes front-to-back topology only from explicitly supplied supported edges. Overlapping owners without a complete directed order are rejected, not silently merged into whole-image clothing. Produces disjoint *visible* masks for downstream proof only. No source pixels or rendering are modified; `productPromotionAuthorized=false` is always returned.

## Verification

- Synthetic Node tests: **12 PASS**, including replay independent of input order, face redaction boundary, source/mask SHA mismatch, unsupported alpha, incomplete overlaps, cyclic occlusion and deliberate status spoofing.
- Two genuine 340×340 source originals SHA-verified against the historical source PNGs. Their historical Stage04 face PNGs are separately SHA-verified, and frozen genuine Public Facet40 outputs SHA-verified. Source/face pixels are imported only into the PRIVATE test runner, never GitHub.
- GC001: reuse the pre-existing source-green connected tie observer (`semantic_art_mixer_v1.py`, prior SA10.36). Found **1,960 source-observed candidate pixels**. This is an observation, not a new independently signed material owner. Its green tie was already largely present in frozen Facet40; it is **not an improved full-body structure**.
- Raden: observed **545 source-contrast candidate pixels** within an explicit, source-image-specific corset/lacing study window. Observed bow candidate collides with independently signed face-owner pixels and was **not drawn**. Actual lace rendering remains sparse and too weak for a quality PASS. The identified source labels are observer hypotheses pending manual source-part confirmation.
- Real two-case source/mask-bound Node replay: both PASS as `previewOnly` with **zero renderer-applied pixels**, and real historical signed arm mask with alpha fringe is independently rejected (`PASS_ABSTAIN`). This safety gate is different from the PRIVATE flat-color observer image and must not be described as product visual improvement.
- All **8 pre-manifest private analysis outputs** were reproduced byte-for-byte on a second independent execution. See the private evidence SHA manifest for exact hashes.

## Existing related work reused, rather than reimplemented

- SA7.3 fine semantic identity observer/proposal is evidence, not authority. Category and parent checks must not be bypassed.
- SA10.36 source-grounded green necktie and structured shirt panels previously achieved a visually real GC001 **research** recovery, with strong source-color and protection gates. This Stage2 does not overwrite or replace SA10.36, nor claim that the same algorithm automatically solves the Raden corset.
- Phase8 Semantic Composer explicitly resolves `in_front_of`/`behind` relations. Other spatial adjacency is not depth evidence.

## Non-promoting conclusion

The Stage2 owner-evidence *gate* and two-source observation replay are complete. **The actual P0 major-structure recovery is not complete.** No automatic source-part segmentation exists for all requested components, no independent signoff for Raden bow/corset, no full-scene source-anchored occlusion reconstruction, no verified garment shapes, and no source-bound actual product preview. Significant baseline defects still include missing goggles/collar, sleeves, bow, lacing, silhouette and face-like patches.

Next Stage3: obtain independently witnessed garment/accessory source-owner masks or refuse ambiguous ownership; reuse GC001 SA10.36 panels and signed Phase8 owner masks where technically valid; add bounded per-part contour/palette representation with correct z-order and prove real Chrome 340px/DPR2 680px no-leak, no face microfeatures, source-only RGB. Maintain original Stage8 vertex-budget failure, whole-scene Golden, iPhone Safari and production rollback as blocking release gates. Do not merge or deploy a HOLD candidate.

PRIVATE actual source images, source-derived masks and contact sheets are preserved under `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage2_20261011`, never in public GitHub.
