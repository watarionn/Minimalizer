# Nao Assignment: Golden Comparison G7/G8 Bridge

/goal Challenge Guarded DiffMin and prepare the blind multi-character generalization gate without tuning on blind outcomes.

/plan
1. Verify DiffMin is default OFF and cannot run on a G3 hard-gate FAIL candidate.
2. Verify same-renderer baseline/candidate is mandatory.
3. Attack primitive identity/count preservation with add/delete/substitute cases.
4. Verify post-refinement G3 hard gates still dominate.
5. Prepare G8 blind benchmark cases without Golden images and without modifying G2-G7 rules after seeing outcomes.
6. Record per-case hard gates and G6 dimensions; no aggregate score may hide a failed character.
7. Report branch, commit SHA, exact tests, artifacts, and any generalization risk for Rinka review.

Hard boundary:
- DiffMin refines parameters of existing authored geometry only
- no semantic-part creation/deletion/substitution
- no missing-required-feature rescue
- default OFF
- G8 blind cases must not become tuning targets
