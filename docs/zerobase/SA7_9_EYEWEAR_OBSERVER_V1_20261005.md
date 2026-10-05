# SA7.9 Eyewear Observer v1 — 2026-10-05

Status: OBSERVER CONTRACT FROZEN / GC001 OBSERVED / FUSION HOLD

## Frozen before GC001

Observer version: `sa7.9-v1`

Prompt:
`glasses. goggles. sunglasses. eyewear.`

Detection threshold: 0.20
Text threshold: 0.20
Minimum mask pixels: 6
Maximum head|hair authority ratio: 0.70

No GC001-specific words, colors, coordinates, or thresholds are present.

Focused contract tests were run before GC001: 18 PASS across observer v1, frozen-artifact bridge, and fusion.

## Runtime

Reused existing shared CUDA runtime and local HF cache only. Offline mode was forced; no model download occurred.

Models:
- IDEA-Research/grounding-dino-tiny
- facebook/sam-vit-base

## GC001 untouched result

The frozen observer detected multiple eyewear hypotheses.

Notable source-supported candidates included two small upper-face regions:

- bbox [137,119,18,13], confidence 0.357357
- bbox [185,120,24,12], confidence 0.364791

It also emitted larger false/ambiguous head-hair candidates such as bbox [104,33,116,61].

This result was observed only after the v1 prompt and thresholds were frozen. No rule was changed in response.

## Fusion decision

SA7.5 structural evidence for GC001 remains paired=false. SA7.9 provides region-role evidence only. Under the already-frozen SA7.6 rule requiring at least two independent roles, GC001 cannot be promoted.

Decision: HOLD.

This is the intended separation:
observer detection != semantic authority.

## Next: SA7.10 Feature-Local Eyewear Evidence v1

Use the already-cached DINOv3 model as an independent feature-local observer, with its contract frozen on non-GC001/synthetic cases before GC001. It must not copy SA7.9 bboxes or use Golden information. Only independent spatial agreement may satisfy SA7.6.
