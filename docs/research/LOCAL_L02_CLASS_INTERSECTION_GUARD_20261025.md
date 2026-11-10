# Lane A L02: independent support must intersect the high-risk pixels (2026-10-25)

**Scope:** source-free research gate only. No image/NPZ/coordinates, no production owner inference, no B/Public/C08/Golden changes. L02 HOLD, Phase4 FAIL, L03 NO_GO, Golden HOLD, production NO_GO.

## P0 risk corrected

In the previous v1 gate, `max(0, risky_total - independent_supported_total)` was used as the entire veto. That is only a mathematical *lower bound*. For example, a frozen source proposal with 20 SegFormer class7 pants pixels and 20 class30 lapel pixels could have 20 independent outerwear-supported pixels **all on class30**. The v1 lower bound is zero and returned `NOT_AUTHORIZED_BY_THIS_AUDIT`, even though **none** of the 20 class7 pixels has independent support. This is a source-only accounting error, not a claim of a new signed H06 pixel improvement.

The v2 audit keeps the old lower bound as a diagnostic but fails closed on missing class intersections. Only an explicitly verified per-class independent-support intersection may reduce a high-risk class veto. The sum of per-class intersections must equal the aggregate independent support, and no per-class intersection may exceed its frozen added count. The verified same-class intersection merely removes this *particular* veto; it never promotes Phase4 or quality. Human-unlabelled pixels stay unknown, not negative. The default H08 class30/32 opt-in has no high-risk class and remains unchanged.

## Verification and integration gates

Source-free synthetic negatives cover (1) independent support entirely on another class, (2) missing class intersection, (3) partial class overlap, (4) invalid provenance and accounting, and (5) the previously rejected H06 12,955px pants/background proposal. Existing high-risk v1 code has no known production callers; this is a stricter research-only guard, not a live inference change. Full repository CI and new signed-source replay are separate gates. **New signed-image P0/P1 improvements: 0/0.** Known unresolved H04/H06/H08: 3. No unseen-character generalization claim.
