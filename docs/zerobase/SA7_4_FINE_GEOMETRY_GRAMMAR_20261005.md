# SA7.4 Fine-Part Geometry Grammar — 2026-10-05

Status: GRAMMAR FOUNDATION PASS / RENDERER EXPERIMENT REJECTED

## Goal

Translate explicit fine SemanticParts into bounded deterministic primitive grammar before any renderer integration.

## Accepted foundation

Added `semantic_abstraction/fine_geometry_grammar.py`.

The grammar:

- consumes SA7.3 promoted fine SemanticParts,
- reserves required primitive minimums before lower-priority fine parts,
- keeps the primitive budget bounded and deterministic,
- maps eyewear to a maximum of 2-3 bounded ellipse/polygon candidates,
- maps hair_front/hair_side/collar/tie/headwear/major_accessory to bounded coarse polygons,
- derives colors only from source-supported pixels,
- never creates face geometry,
- keeps observer evidence separate from semantic authority.

Priority is semantic rather than area-only. Eyewear receives its required two-primitive reservation before lower-priority fine parts when the budget is tight.

## Verification

- focused SA7.4 + renderer safety tests: 10 PASS before visual experiment review
- full ZeroBase after implementation: 520 PASS
- git diff --check: PASS
- final branch removes all renderer behavior changes before merge

## GC001 renderer experiment

An experimental renderer connection was evaluated locally and is explicitly rejected.

Observed:

- semantic geometry count: 7
- eyewear primitives: 2
- the first eyewear evidence component was near-white and the second was a small brown component
- filling those components as ellipses did not read as goggles
- the resulting head region produced an eye-like white shape and failed visual review

Decision: VISUAL FAIL. Do not merge renderer integration and do not adopt the image.

This is a useful failure: the grammar cannot repair incorrect semantic evidence. Eyewear must be observed as frame/lens structure before geometry is authorized.

## Safety decision

The branch is returned to production-neutral state before PR:

- grammar module retained
- grammar tests retained
- renderer restored byte-for-byte to main
- renderer test restored to main
- no visual adoption
- no four-way artifact is required for merge because no behavior-changing renderer code remains

## Next: SA7.5 Eyewear Structural Observer

1. represent eyewear evidence as frame/lens structural components rather than generic color components,
2. require paired/bounded upper-face evidence where appropriate without assuming every eyewear item is paired,
3. distinguish bright frame from face/eye-like holes,
4. retain source support and head|hair composite authority,
5. expose structure to the SA7.4 grammar,
6. synthetic non-GC001 fixtures first,
7. GC001 debug overlay second,
8. renderer integration only after the semantic evidence is visually credible,
9. then rerun Visual Delta >= 1.5%, missing=0, forbidden facial detail=0.00%, actual four-way, and version history.

No GC001-specific coordinates, colors, or names may enter production logic.
