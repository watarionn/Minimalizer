# L02 H06 class25 foreground-bag / reviewed-outerwear occlusion conflict (2026-11-01)

**A-only, source-free postscore diagnosis. REVIEW_REQUIRED; not a repair, not an owner proposal, not unseen generalization.** The H04/H06/H08 signed-image P0 frontier is still FAIL, accepted P0/P1 fixes **0/0**, unresolved cases **3**. Do not change signed user annotation, owner masks, Golden, LocalWorker, Lane B or Public/C08.

## Verified lineage

- GitHub main at investigation: `131416b5f6edb99d86e1fe035e6877fe440db76e`; A-only Draft PR #445 head before this note: `be0ec4849a3ab2b74529b2f7d804ed08ea0034f1`. The current PR contains 81 changed files, all within `tools/research/`, `tests/`, `docs/research/`.
- Existing non-shared Drive `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence` source archives re-fetched and ZIP SHA-256 independently verified: signed ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, frozen Run30 owner `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, SegFormer SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, historical DeepFashion2 observer `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`.
- H06 original encoded source pin remains `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`. Source RGB/alpha, owner, frozen model class maps and the independently stored DeepFashion2 prediction were used. No new model inference, image synthesis, threshold tuning or private-image upload to GitHub.
- Official pinned SegFormer Fashion `id2label`: **class25 = "bag, wallet"**, not coat. See https://huggingface.co/sayeed99/segformer-b2-fashion/blob/main/config.json . The model prediction is not automatically ground truth.

## Source-only conflict diagnostic (known-case exploratory, not blind)

On the **historical Run30 H06** owner (not the later composed/strict frontier), all **22,087** class25 source-alpha pixels were unassigned. **6,586** of them were simultaneously predicted positive by the independent DeepFashion2 outerwear observer, despite SegFormer calling them bag/wallet. The 6,586-pixel overlap forms one connected component in both 4- and 8-neighbour graphs. A *counterfactual* union with Run30 owner would not increase the owner component count (4-neighbour **9→9**, 8-neighbour **8→8**). This is only an observer-disagreement diagnostic: **no owner was modified or promoted**.

H04 and H08 have zero class25 pixels in these frozen SegFormer maps, so the same diagnostic yields zero there. A no-op on those two cases does not prove unseen safety or current strict-owner quality.

## Independent human postscore and private visual review

**Chronology caveat:** The class25/DeepFashion2 source-only overlap was first identified without human labels, but the exposed H06 human postscore was consulted during exploration **before the final mask SHA was frozen**. Thus this is a known-case exploratory audit, **not a blinded freeze-then-evaluate experiment**. The mask formula itself takes no human labels as inputs. Of the 22,087 class25 pixels, **9,913** fall in reviewed `outerwear` positives and **12,174** are unreviewed/unknown. All 6,586 DeepFashion2-positive conflict pixels are also inside the reviewed `outerwear` polygon mask. This would look like 6,586 rescued true positives in a *polygon-only metric*.

**But a private original-RGB overlay visually places that conflict component on the foreground crossbody handbag.** H06's seven reviewed polygons annotate coat, innerwear and hands, **not a separate accessory/bag occlusion**. Therefore the overlap is an **evaluation-occlusion/semantic-label conflict**, not verified missing coat. A model can agree with a reviewed polygon and still be wrong about the visible foreground object. The previously reported H06 residual **9,913 class25 "missing garment" pixels** are not all verified visible coat; at least the 6,586 overlap warrants explicit review. Do **not** automatically relabel these as bag negatives either: preserve the user-authored polygons and mark the disputed interpretation as `REVIEW_REQUIRED`/unknown pending authorized independent evidence.

The private full-frame/crop overlay and conflict receipts were packaged locally as `LaneA_L02_H06_Class25BagOcclusion_Audit_PRIVATE_20261101.zip`, SHA-256 `1ec8fa3f731354022f1715f9e5ee223f89cce1414af2ddaf69a924c5308c04de`. **Upload to the canonical Drive folder failed with `container_session_unavailable`; cloud preservation/read-after-write is NOT verified.** The underlying original archives remain in canonical Drive. No private coordinates, masks, pixels or previews are in this public document.

## Evidence chronology correction and next gates

**2026-11-01 self-audit correction:** The first version incorrectly said the postscore was opened only after mask freeze. Cause: conflating the source-only expression's initial selection with the later formal SHA freeze. Impact: the chronology could falsely imply blind evaluation. Correction: explicitly state that human postscore preceded the final SHA freeze, retain the diagnostic-only status, and prohibit quality-credit/owner promotion. Prevention: record candidate-expression selection time, freeze/hash time, and human-label access time separately in future runs. This correction does not change any pixel or score.

## Engineering decision

1. **Reject class25/DeepFashion2-positive union as an owner repair.** It would risk assigning visible handbag pixels to coat. This explains why class25 should not be added merely because exposed H06 polygon postscore looks favorable. Do not change the frozen class allowlist or Golden labels.
2. Preserve the existing reviewed mask unchanged. Add an **evaluation-only occlusion-conflict review gate** before counting H06 class25 as verified visible outerwear. Any future scoring revision must separately record original polygon metrics, disputed foreground occlusion and unknown pixels, without retroactively changing signed human approval.
3. Independently obtain positive coat-versus-bag and coat-versus-underlayer semantic evidence on genuine signed source, then execute exact current PR-head source-only owner/Phase4 topology and critical-part gates. H06 frozen class32 **1,077 known underlayer FP** remains a separate unresolved defect. H08 sleeve and H04 regression remain unresolved.
4. Run genuine unseen signed blind only after freezing a candidate; review model rights, formal QA, Phase4 PASS, then Phase5 exact replay and human Golden. iPhone acceptance is post-production deployment, never a pre-deployment blocker.

**Accepted signed-image P0=0 / P1=0; H04/H06/H08 unresolved=3. This is a newly identified evaluation integrity risk, not a quality fix. No merge or production change. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**
