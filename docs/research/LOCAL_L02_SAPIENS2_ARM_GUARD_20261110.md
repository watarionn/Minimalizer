# Local L02 Sapiens2 arm-owner guard — 2026-11-10

This is a source-free research handoff for PR #449. It does not authorize a
Phase 4/5 promotion, Golden approval, production deployment, or a change to
the LocalWorker route.

## Change

`tools/research/local_l02_sapiens2_arm_guard_shadow.py` adds a pinned,
source-only Sapiens2 observer guard:

- explicit Sapiens2 lower/upper-arm classes can remove pixels only from an
  existing owner; hand classes veto sleeve recovery but do not authorize
  removing an existing garment owner;
- explicit garment classes, frozen cross-owner contacts, alpha-outside pixels,
  topology-breaking pixels, and all absent/unknown observations abstain;
- H08 positive evidence is vetoed at explicit arm pixels before exclusive
  owner assignment;
- source SHA and Sapiens class-array SHA are fail-closed;
- human labels are never inference inputs and unknown is never treated as
  negative.

The implementation preserves owner promotions at zero for removal and checks
4/8-connected components and enclosed holes. The H08 recovery path retains
its existing exclusive-owner and enclosed-void checks.

## Frozen source-only observer

The private Sapiens2 0.4B segmentation run was executed against signed H04,
H06, and H08 sources before any human review data was opened. The class-array
identifiers are recorded here so the code can reject drift without publishing
the arrays:

| case | signed source SHA-256 | Sapiens2 class-array SHA-256 |
| --- | --- | --- |
| H04 | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` | `dc384e30449d667854097fe0e46bd550920b6e609d9b5c6fa33e9950c6207737` |
| H06 | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` | `080ad3245586d471130afc6f4853e76739dd74fbb7c4c898795d246cc78cf83a` |
| H08 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` | `e3d54bea29d1569e16b2aa18e4a6bd34c37d76530449c73114e5511b3b3e4423` |

## Corrected class-map result

The first private exploratory run used an incorrect class set that included
foot/sock IDs and omitted the upper-arm ID. Its output was not promoted and is
discarded from the review packet. The corrected DOME 29 mapping is:

- removal authority: `Left/Right_Lower_Arm`, `Left/Right_Upper_Arm`;
- recovery veto: the same four classes plus `Left/Right_Hand`;
- garment preservation: `Apparel`, `Lower_Clothing`, `Upper_Clothing`.

The corrected candidate owner arrays were frozen before opening the
independent review arrays. The private review score is a diagnostic, not a
formal quality gate; unlabelled pixels remain unknown.

| case | frozen IoU | candidate IoU | delta | owner change |
| --- | ---: | ---: | ---: | ---: |
| H06 | 0.891885 | 0.891896 | +0.000011 | remove 4 |
| H08 | 0.616561 | 0.620336 | +0.003775 | restore 591 |
| H04 | 0.866497 | 0.866497 | +0.000000 | unchanged |

H06 known-negative FP changed from 11,551 to 11,547. H04 known-negative FP is
unchanged at 4,423. H08's 591 recovered pixels passed the existing
exclusive owner, 4/8 component, and enclosed-void checks.

The H06 four-pixel removal is the pre-existing pinned Run30 candidate; the
corrected Sapiens2 arm guard removed zero additional H06 pixels. The H08 591
pixels are the pre-existing independent-observer candidate; the corrected
Sapiens2 arm/hand veto did not change its assigned count. Therefore this
Sapiens2 observer is preserved as a fail-closed negative result, not claimed as
the missing H06/H04 quality repair.

## Current gate

The code and negative tests are preserved in commit
`84aef9c2fe0a9342730ad8a06f83ed2d4e432e2d` on Draft PR #449.

- focused A tests: `48 passed`;
- repository-wide unrelated baseline issue: the existing browser fallback
  test expects `browser-fallback-v11` while the current implementation reports
  `browser-fallback-v12`; the full suite was not claimed as PASS;
- L02: `HOLD`;
- Phase 4: `FAIL` until the candidate-specific independent review receipt is
  signed;
- Phase 5: `NO_GO`;
- Golden and production: `HOLD` / `NO_GO`.

Required next action is candidate-specific independent visual/semantic review
of the private before/after previews, followed by a Phase 4 receipt. No raw
images, masks, NPZ files, coordinates, or previews belong in GitHub.
