# MinimalizerPublic P0: Stage31–35 source-owned reviewer boundary (DRAFT HOLD)

Date: 2026-10-12 (JST). Public-only **research** branch, PR #390, not a production feature. Main, live Public route and Local Minimalizer unchanged. No generative fill/img2img, no source-absent drawing. No eyes, nose, mouth. Human Golden absent.

## Stage31: SHA-pinned independent eligibility

`public-annotation-authority-p0.mjs`: the caller separately passes original RGBA/face/background/left/right arm bytes and their SHA-256 pins. Revalidate all byte inputs, strict 0/255 masks, reject *all* left/right historical overlaps even when no annotations exist. Exclude source-alpha !=255, face, background. Output is a SHA-pinned eligibility mask and disjoint owner counts, not a semantic mask or approval. No auto-paint entrypoint.

## Stage32: deterministic original-source review priority

`public-annotation-boundary-queue-p0.mjs`: score 20px tiles via original pixel RGB contrasts, edge/face/background/alpha contacts, and source signed owner boundary counts. Output coordinate boxes and summary counts only, no inferred skin/sleeve/hair labels, generated pixels, source RGBA or background-mutation operation. This is a triage aid for independent original-image annotation.

## Stage33: dual-draft comparator with source lineage

`public-annotation-dual-review-p0.mjs` reuses Stage26 `validateManualReviewDraft` twice, verifies all source pins independently, rejects identical label data to avoid counting exact duplicate drafts as independent, records disagreements, always abstains on unknown and labels outside source authority. Even agreement is untrusted. Fake reviewer signatures and a locally modified second draft do **not** constitute independent human review.

## Stage34: separate release gate

`public-annotation-stage34-gate-p0.mjs` enumerates failed reviews for both independently named cases and tracks unseen original source pixels and real Public/iPhone/vertex cap/rollback/Human Golden deficits. ALWAYS returns productPromotionAuthorized=false even with all caller booleans set true; only external independently verified trust infrastructure could assess production readiness.

## Actual original GC001/Raden replay (no original images in repo)

Read originals, historical signed arm/face masks and observed background from private Stage26–30 ZIP. Check all inputs against original SHA-256.

| Metric | GC001 | Raden |
| --- | ---: | ---: |
| Eligible historical arm-owner pixels | 9,160 | 20,177 |
| Boundary edges (4-connected) | 1,244 | 1,256 |
| 20px review-priority tiles found | 47 | 76 |
| Synthetic parser-test dual labels | 49 | 49 |
| Deliberately modified synthetic disagreement | 1 | 1 |
| Independently attested semantic pixels | 0 | 0 |

The `49` test annotations are synthetic parser exercise fixtures carried from Stage29. They are **not** human-labelled anatomy or certified hair/sleeve/skin pixels. Stage34 returned 13 pending conditions. Neither RGB error reduction nor source hash proves semantic validity. Never adopt Stage18 candidate based on these metrics.

Original Stage8 full body SVG vertex budgets still fail: GC001 3604 > 1887, Raden 2370 > 1412. Original source full-character silhouette/arms/collar and face-outside-original-mask still require Golden; real Public secure-origin WebCrypto, Safari iPhone and rollback remain unverified.

## Verification

30 new Stage31–34 Node tests: **30 PASS / 0 fail locally**. Includes SHA pin mutation, excluded alpha/face/background, overlap regardless of label, unreviewed ROI boxes, two draft conflict and forged flag, source-outside paint veto and always-HOLD gate. Stage35 combines with existing 136 PR regression checks via GitHub Actions, checked separately against actual decoded runner logs; do not claim combined PASS without that log.

Private files, original SHA manifests, actual source material, synthetic draft fixtures and private replay outputs must stay in Google Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage31_35_20261012` only. PUBLIC zip is source-free. Avoid replacing user's historical signed owner masks with a guess.
