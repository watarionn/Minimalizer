# L02 sleeve-parent color/attachment exploratory shadow (2026-10-16)

**Research implementation and three-case diagnostic: complete. Semantic owner authority: NOT approved. L02/Golden HOLD; production NO_GO.**

## Problem and hypothesis

In signed H04/H06/H08 sources, SegFormer-B2 Fashion distinguishes `jacket=5`, `coat=10` and `sleeve=32`. Earlier jacket/coat-only IoUs were 0.614489 / 0.825905 / 0.616561. Adding every sleeve gives 0.8665 / 0.8919 / 0.9113 on the *same* human labelled set, but introduces H06 known-negative FPR ~0.63 and H08 ~0.157. The sleeve class includes underlayer and arms. The original 3-character bilateral model consensus also misses jacket in H04; neither blindly taking union nor intersection is acceptable.

An **exploratory source-only** color-parent attachment candidate uses only signed original RGBA, its source alpha, and the independently pretrained pinned SegFormer 47-class output. The pure function `propose(rgba, classids)` chooses class5/10 seeds, extracts class32 sleeve components with 8-connected component topology, retains components touching class5/10 within 1px source neighborhood, and then selects those source sleeve pixels whose OpenCV LAB distance to the nearest source class5/10 pixel is strictly below **30**. Output is always source-alpha clipped; if the model has no valid jacket/coat seed, it ABSTAINS. It cannot receive human polygons or manual masks. `score` uses partial user labels separately **after** inference. *30 was selected during exploratory probing on these exact H04/H06/H08 cases*, so these numbers **cannot be called independent holdout generalization** and the threshold must not be promoted as canonical by looking at the test score.

## Actual private data, source-only exploratory results

| Signed source | Existing jacket/coat IoU | Exploratory label-only IoU | Explicit known-negative FP rate | Known arm false-positive pixels |
|---|---:|---:|---:|---:|
| H04 | 0.614489 | **0.866317** | 0.021133 | 236 |
| H06 | 0.825905 | **0.852027** | 0.012342 | 51 |
| H08 | 0.616561 | **0.756734** | 0.014440 | 217 |

Compared with blanket sleeve union, known-negative leakage is far lower, especially for H06/H08. Nevertheless, compared with jacket/coat-only the above additional known-arm and nonjacket false positives remain **explicit semantic safety failures**. Positive recall and label IoU on three cases used to choose this research heuristic cannot establish transfer quality. No owner allocation, signed masks or original pixels were overwritten. The research path remains a diagnostic, not a rendering pipeline.

A separate source-only private class32 inference from pinned SegFormer weights SHA `47313d9daf8f759b803b0bf449a4719bcd5b5a46eacad343e99e9660f8cedec1` produced per-case native class ID arrays with fixed SHA. An independent offline Python implementation recomputed all three proposals twice with exactly the same source-free metric payload SHA `ffe1bdb9e831b4cb5cb8ec0f2e4a540ab759924d71c273b91de5da46eab3a2a4`; ZIP container checksums may differ due timestamps. **10/10 synthetic checks on the independent core mirror PASS**, including source-alpha, no jacket seed, connected/disconnected sleeves and unknown separation. A matching 10-test suite has been committed to GitHub, but that exact repository test file and full repository CI were *not executed* in this session because the PC command path was unavailable; do not conflate these.

## Evidence and archival

Private original/source masks remain in existing `chatGPT及びCodex用/Minimalizer` Drive. The new prediction artifact [Exploratory source-color sleeve private evidence](https://drive.google.com/file/d/1_7K8vEhDRdR-2Mt0ZH3wpNbPhSziT1md/view) has been **uploaded through the connected Drive action and downloaded back through the same provider**. ZIP SHA-256 `a1bbd358db2f113c39ad04c3b8e51466bd4753d617d1b3a9fd1da3c2f077fd2c`; the archive contains aggregate diagnostic JSON and H04/H06/H08 NPZ predictions, not public samples. Supporting per-class evidence [private class32/source semantic ZIP](https://drive.google.com/file/d/1DGXpI128WUUpOZ0KuUhzYYyqfDcEqoCh/view). The public repository contains **only** source-free code, fixtures, metrics and handoff; no signed source pixels, polygons, masks or weights.

## Engineering decision and next work

- **RESEARCH COMPONENT READY, OWNER AUTHORITY REJECTED.** The technique reveals the neglected sleeve class and how ownership may be inferred from source RGB, but additional false positives and lack of untouched person holdouts prevent promotion.
- Independently frozen hypothesis must next be evaluated on additional, genuinely unseen signed characters with explicit outerwear/arm positives/negatives, without changing a threshold after seeing labels. Validate color different uniforms, hair occlusion, long coats and hands/gloves.
- Do not transfer pixels into protected H04/H06/H08 anatomical owners without original Phase4 immutable owner and topology proof. L03 pinned Phase4→5, Stage8 and Golden stay on quality gate HOLD. In parallel, non-destructive L07 PWA operational checks are independently actionable.
- User reported SegFormer licence conditions resolved. This does not mean human Golden quality or automatic production approval. Public/C08, LocalWorker and scheduled **production** campaign are unchanged. No generated face parts or visible missing pixels.

Next mainline engineering step: independent transfer gate on new character evidence and owner-safe sleeve/arm occlusion attribution, while continuing safe L07 read-only testing.
