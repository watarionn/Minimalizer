# Phase 17 Structure Voronoi / Approved 18 audit

## Purpose
Phase 17 now partitions the upper-body subject mask from structural anchors rather than splitting color regions first.
The partition seeds are:

- torso spine under the located face
- left shoulder-to-hand arm seed
- right shoulder-to-hand arm seed

Pixels inside the recovered subject mask are assigned to the nearest structural seed.
This is a structure-first partition; color is applied only after the partition is accepted.

## Approved 18 audit
The exact 18 source images and the 18 approved geometric references were used for the audit.
17/18 images produced bilateral arm seeds.
A ratio gate is required because bilateral seeds alone are not sufficient.
## Acceptance gate
Use Structure Voronoi only when all of these are true:

- bilateral arm seeds exist
- torso ratio within partitioned body: 0.22 to 0.55
- left arm ratio: at least 0.08
- right arm ratio: at least 0.08

The ratios use `torso + left_arm + right_arm` as the denominator, not the full image or full subject mask.

Expected Approved-18 behavior with the current audit:

- Voronoi accepted: 14 / 18
- fallback: Gigi-Murin, Hakos-Baelz, Koganei-Niko, Shiori-Novella

Fallback is intentional. A rejected partition must not be forced into the Structure Voronoi path.
## Safety / regression rules

- Structure Voronoi is only an experimental Phase 17 path. Production remains Phase 16.
- A missing arm seed must fall back instead of inventing the opposite arm.
- Extreme torso ratios must fall back instead of swallowing sleeves into the torso.
- Partition masks must stay inside the subject mask and must not overlap each other.
- The shadow path and comparison renderer use the same face-first processing order.

Current relevant regression result after the exact-18 gate update: `67 passed`.
