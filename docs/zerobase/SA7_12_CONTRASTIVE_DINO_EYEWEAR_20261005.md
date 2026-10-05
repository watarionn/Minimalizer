# SA7.12 Contrastive DINO Eyewear Evidence — 2026-10-05

Status: NON-TARGET CONTRAST PASS / GC001 FEATURE-LOCAL HOLD / PRODUCTION-NEUTRAL

## Reference bank
The original HoloMenImages.zip was recovered from the conversation upload and inspected before GC001 feature-local evaluation.

Frozen references:
- positive: Friend-A glasses
- positive: Hyakuto Kyoko forehead goggles
- negative: Izuki Michiru
- negative: Harusaki Nodoka
- negative: Watson Amelia
- positive holdout: Kaela Kovalskia forehead goggles
- negative holdout: Raora Panthera

Reference images were preserved under the canonical Google Drive Prototype_Bank/SA7_11_20261005/references folder before target evaluation.

## Failed baseline
Raw positive-centroid crop embeddings were rejected:
- Kaela positive cosine: 0.997600
- Izuki negative cosine: 0.996916
The representation mostly encoded anime-face similarity.

The 28x28 internal feature-cell approach was also rejected on non-target data because Kaela positive cells did not separate from Raora negative cells.

## Contrastive bank
A positive-minus-negative normalized direction was introduced.
Bank SHA-256:
31f0675436fe63c4498a8655f2396e32dab5dd07ee2b468270c17b9ed80b4e65

Non-target holdout:
- Kaela score: 0.0344963
- Raora score: -0.0582623
- margin: 0.0927586
- required margin frozen before target: 0.05
PASS.

The sliding-crop threshold was frozen from non-target crop scores before GC001:
-0.0118829645

## GC001 one-shot evaluation
After the bank and threshold were frozen, GC001 was evaluated once.

Result:
- eligible independent DINO windows: 1
- DINO feature-local evidence passing threshold: 0
- SA7.9 region evidence records: 10
- SA7.5 structural: paired=false, confidence=0.259110
- SA7.6 fusion: promoted=false
- reason: insufficient_independent_roles

No threshold, crop size, bank membership, or reference was changed after observing GC001.

## Decision
SA7.12 does not authorize renderer integration.
The DINO witness is currently too weak on GC001 at the frozen setting. This is a useful negative result: region evidence exists, but a genuinely independent feature-local witness does not yet corroborate it.

Next work should improve observer generalization using additional non-target holdouts, not tune on GC001.
