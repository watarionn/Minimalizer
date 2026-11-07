# L02 PR #445 exact-head H08 replay on pinned 2026-10-23 staged composed/strict owners (2026-10-27)

**Research-only, known H08, Phase4 FAIL / L02 HOLD / L03 NO_GO / Golden HOLD / production NO_GO.** This is **not** a current-main complete replay or an accepted P0/P1 fix. No source image, human annotation, mask, coordinates, NPZ, private archive contents, or visual board is included.

## Reproducible source-only provenance

- GitHub main at check: `4a4348990084848c981811b414e6221411271f84`. PR #445 base `4a4348990084848c981811b414e6221411271f84`, head before this report `0032ea4c502006053cbf97ba353a4d7040fe898d`, Draft/unmerged.
- The PR #445 implementation was copied byte-exactly for isolated execution: Git blob `db4e66f24a767d6c5759c7c634243e3060bfeb80`, verified against the remote file. No modifications to its algorithm or thresholds.
- The **historical source-free 2026-10-23 integrated staging archive** was retrieved from the canonical non-shared Drive. It is not the current GitHub main and contains unmerged dependencies. Four private signed inputs were independently retrieved; relevant ZIP digests matched existing frozen manifests, including reviewed `6d7079b5…e17598`, Run30 `6ac735cc…f5c`, sleeve `a4322f81…d7af7`. Loader verified the reviewed/owner/AnimeSeg internal manifests **19/7/5**, signed source and observer provenance. Private source data stayed outside GitHub.
- The archive's historical H08 canonical strict replay expects composed SHA `82313762a406ec225cf4a79675772c9bc71fefa77d6d48e6613b48cebf884552`. But the archive's later contact-veto implementation deterministically produces `3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a`, matching its own 2026-10-23 bounded-component report. **This is a version/stage provenance mismatch, not a reason to silently replace the historical pin.** The old wrapper correctly fails closed with `COMPOSED_BASELINE_SHA_MISMATCH`.
- For this **separate, explicitly identified staging lineage only**, the contact-veto output and its strict-class32 successor were independently frozen and verified before invoking PR #445. Strict successor SHA: `32bb5266a479ce64571f190ffebe90b50c01329598408019b363c5ab0c9f0778`. This pin is not interchangeable with Run30, the older canonical wrapper, or current-main output.

## Signed H08 known-only result

The exact PR #445 code was executed **twice** against both stage-specific pinned inputs. The two runs produced identical candidate owner SHA and known-only aggregate scores. Human labels were opened only after each source-only proposal was fixed and hashed.

| Frozen stage | Reviewed outerwear TP before → after | Known false owner FP | Known arm FP | Missing reviewed outerwear after | New source pixels (reviewed TP / known FP / unknown) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Contact-veto staged composed | 136,780 → **140,514** (+3,734) | 0 → 0 | 0 → 0 | 16,056 | 3,874 total (3,734 TP, 0 FP, 140 unknown) |
| Strict enclosed-class32 successor | 137,261 → **140,692** (+3,431) | 0 → 0 | 0 → 0 | **15,878** | **3,570 total (3,431 TP, 0 FP, 139 unknown)** |

Strict-lineage candidate SHA `96294ba7bc00f4194f2b12d9a4f0925525cbf8e745646fe2315bcbb129edb5f2`; contact-veto-lineage candidate SHA `e2505582d59bf6dd0943d4fe31c9796c3543e633ab8df13a86e5d7b04f2a37ff`. Both preserve frozen owner pixels, original alpha and owner 1/2 4-/8-neighbour component identity. New additions are class32 only. Unknown pixels are **not** counted as correct or incorrect. These gains are **against the explicitly pinned unmerged 2026-10-23 staging lineages**, not against current main.

## Visual quality and acceptance

A private full-source comparison was rendered and examined. The H08 jacket/sleeve remains visibly incomplete; the new retained pixels do not close the large sleeve/shoulder gaps. The existing H06 underlayer/coat confusion and H04 false owner remain unresolved. No unseen signed character was used; the PR #445 distance constants were already exposed-case selected. No Golden or user/iPhone acceptance is inferred.

Private lossless owner PNG, visual JPEG and receipt were generated with SHA-256 and checked locally. Upload into the existing non-shared Drive evidence folder failed with `container_session_unavailable`; **cloud preservation/read-after-write is not verified**. The private outputs must not be published to GitHub. No code/production/Lane B/Public/C08/Golden changes are authorized by this report.

**Accepted P0 improvements 0, P1 improvements 0; H04/H06/H08 unresolved 3.** PR remains Draft and unmerged. Next gates: stage/version-specific full dependency integration with a separately pinned main-derived composed owner, H06/H04 regression, independent semantic arm/underlayer separation and visual critical-part retention, exact-head full CI, genuinely unseen signed blind, and human Golden/iPhone acceptance. A passing 4/8 topology or increased known-case TP alone is not a Phase4 semantic PASS.
