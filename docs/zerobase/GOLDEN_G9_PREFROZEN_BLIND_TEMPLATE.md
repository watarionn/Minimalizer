# G9 Pre-frozen Blind Semantic Template

Status: FROZEN BEFORE FRESH CORPUS SELECTION

The previous G8 corpus revealed that freezing source hashes without freezing per-case semantic evaluation authority is insufficient. G9 fixes the ordering by freezing a generic semantic template before selecting any fresh blind images.

The template is intentionally limited to semantic roles already emitted by the frozen Phase E Grounded-SAM observer: hair, face-skin, limb, and accessory. It does not encode character names, colors, costume identities, coordinates, Golden images, or post-outcome observations.

Rules:
1. The template SHA and observer configuration are frozen before fresh corpus membership is selected.
2. Fresh cases inherit this template mechanically; only case_id and source hash may vary.
3. No feature, disposition, importance, palette role, relation, prompt, or threshold may change after corpus selection.
4. Hair is the only required feature because it is the stable identity-bearing semantic role supported by the frozen observer. The remaining observer roles are optional evidence and cannot rescue a missing required hair feature.
5. A fresh suite must contain at least three source images and no Golden image.
6. Once sources are sealed, execute exactly once through frozen observer -> blind binder -> production bridge -> authorized geometry -> same renderer.
7. Any inability to bind or render is recorded as HOLD/REJECT. Human semantic substitution is forbidden.

This template is a generic observer-capability benchmark, not a claim that four broad roles fully capture character identity. Fine-grained identity semantics remain a separate future capability milestone.
