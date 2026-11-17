# L02 MHP v2 training candidate assessment — 2026-11-17

## Result

The locally preserved upstream Multi-Human-Parsing repository is a possible
pretraining source for a future six-capability observer, but it is not itself
an admissible observer checkpoint or a complete six-capability dataset.

Local source tree:

```text
C:\Work\Temp\minimalizer-model-availability-20261110
```

Upstream reference:

```text
https://github.com/ZhaoJ9014/Multi-Human-Parsing
```

## What the dataset can contribute

MHP v2 describes per-person semantic regions and instance identity. Its listed
categories include left/right arm, hand, bikini/bra, jacket/windbreaker/hoodie,
t-shirt, coat, dress, robe, and other upper/lower clothing. It also provides
keypoint visibility flags with visible, occluded, and out-of-image states.

These annotations can support a separate-person pretraining split for:

- `person_instance` / `instance_grouping`;
- `arm`;
- coarse garment and underlayer initialization;
- an occlusion-related auxiliary task at keypoint level.

## Missing capability contract

The present MHP schema does not provide all required evidence:

- no explicit `sleeve` mask class;
- no pixel-level `occlusion_outerwear_underlayer` relation;
- no pixel-level `occlusion_sleeve_arm` relation;
- no pixel-level `occlusion_garment_body` relation;
- garment names do not automatically establish the Minimalizer outerwear /
  underlayer ownership semantics.

Therefore the data must not be mapped by renaming classes, and it must not be
used to infer H04/H06/H08 labels or thresholds. A supplement is required:

1. preserve MHP person identity and original split boundaries;
2. add sleeve and three pairwise pixel-relation annotations on separate
   characters or a separately authorized annotation set;
3. keep unknown separate from negative;
4. freeze the mapping, split manifest, and checkpoint before any H04/H06/H08
   inference;
5. run the existing six-capability evidence contract on all three signed
   sources with one configuration.

## Current local availability

The repository and annotation tools are present locally, but no MHP v2 image
archive or trained checkpoint is present in the local tree. No training,
checkpoint creation, or H04/H06/H08 inference was performed from this
candidate.

## Gate status

```text
MHP v2 as final six-capability observer: REJECTED
MHP v2 as pretraining candidate: CONDITIONAL
Six-capability checkpoint: NOT_AVAILABLE
A L02: HOLD
Phase4: FAIL
Phase5: NO_GO
```
