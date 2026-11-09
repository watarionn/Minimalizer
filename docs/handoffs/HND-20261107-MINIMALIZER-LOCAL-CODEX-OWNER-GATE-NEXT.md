# MinimalizerLocal Codex owner-gated next steps

Date: 2026-11-07

This handoff records the next actionable gates after the local-PC and private
Drive inventory. It is source-free and does not authorize a merge, deployment,
Golden update, or production change.

## 2026-11-07 Drive delta check

The connected Drive was searched again for newer H06 observer material, Run32+
Run33 additions, official Stage8 source rings, and signed expanded SVGs. The
newest matching records remain the historical 2026-10-19 H06/Run32 handoffs and
the 2026-10-25 real-source intake receipt. No newly uploaded independent H06
observer package or owner-authorized Local Stage8 JSON/SVG triple was found.
The prior negative/hold decisions therefore remain unchanged; no old artifact
was relabeled as formal evidence.

## Current protected state

- `main` baseline: `d7caae3bc9500a63c021e7cc51594a7f8084c7cc`.
- Lane A Draft PR #449 head: `0e6d37df`.
- Lane B Draft PR #451 head: `4980b5c4`.
- Public/C08, LocalWorker production, Golden, signed originals, and main are
  unchanged.

## Evidence decisions

- The signed H06 source is available and SHA-256 verified as
  `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`.
- No official Local Stage8 source JSON plus expanded SVG triple was found in
  the bounded Drive or local-PC inventory. Public Stage8 and manual trace
  artifacts are not substitutes.
- Compact A evidence uploaded to private Drive on 2026-11-07 was read back by
  file ID on 2026-11-08. The four entries referenced by the SHA-256 manifest
  matched the downloaded bytes exactly; the package contains no source image
  bytes. H06 is bound to signed source SHA
  `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` and H08
  to `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`.
- The compact provenance record states
  `human_annotations_used_in_inference=false` and `unknown_as_negative=false`,
  but also `independent_blind_holdout=NOT_VERIFIED`,
  `owner_authority=NOT_GRANTED`, `production_license_cleared=false`, and
  `status=RESEARCH_ONLY`.
- The frozen H06/H08 result record is explicitly `not_new_inference=true`.
  H06 reports known-only IoU/recall `0.627044`, known false positives `0`,
  and `3216` unknown predicted pixels. H08 reports known-only IoU `0.606773`,
  recall `0.61955`, known false positives `3297`, and `8160` unknown predicted
  pixels.
- The formal status record remains `L02=HOLD`, `Phase4=FAIL`, and
  `production=NO_GO`; all requested structural checks remain
  `NOT_INDEPENDENTLY_VERIFIED`. This is an integrity/readback PASS, not a
  Phase4 PASS, and authorizes no owner promotion, Phase5 transition, merge, or
  production change. Drive IDs: `1QiQY2GQ4-WjTfZIbHT35NrIcZvRk3evM`,
  `1bVdYVz3hidYEt2EifN6nHs1punKJ8nF9`,
  `1EBhNsm8lyWhUPPnKixI1iUh7VB9ZdrS9`,
  `1Rd693ShfN95Ixn007q832BEgej5Vhkkq`, and
  `1IJCGoObRgTbMv0A7l6RfDd1GAvRiMM--`.
- The follow-up 2026-11-08 package added five source-free records plus an
  independent-array topology audit. The new manifest's five byte counts and
  SHA-256 values match the downloaded records. The observer record labels the
  H06/H08 outputs as frozen existing results, not a fresh independent blind
  run; H06 agreement over union is `0.542694` with `269653` unknown source
  pixels, and H08 is `0.605198` with `365261` unknown source pixels.
- The blind-holdout record reports no independently witnessed protocol/result,
  no evaluator identity, and unverified observer/evaluator independence. The
  owner record has `authorized_at=null`, `authorized_by=null`,
  `owner_authority=NOT_GRANTED`, and `production_allowed=false`. The
  license/provenance record keeps dataset and model licenses
  `NOT_VERIFIED`, SCHP outputs `RESEARCH_ONLY`, and
  `production_license_cleared=false`.
- The structural receipt reports only existing Codex exact-replay shadow
  topology; clothing retention, critical parts, exclusive owner, holes,
  occlusion, and wrong arm/underwear owner removal remain
  `NOT_INDEPENDENTLY_VERIFIED`. The topology audit explicitly is not an
  independent blind human review and lists no owner authorization or
  production-license clearance.
- The follow-up package therefore leaves the gate unchanged:
  `L02=HOLD`, `Phase4=FAIL`, `production=NO_GO`.

## 2026-11-09 independent-review submission delta

- A new private package was added to the same Drive folder:
  `Minimalizer_L02_H06_H08_独立評価受領証拠_完全版_20261109.zip` (Drive ID
  `1Koj-q4nNTewb6rhhyMYg7EDTxTlFyPnj`). The cloud raw download was read back
  to the private local evidence directory with size `401938` bytes and ZIP
  SHA-256 `f4c28f6167cdac5e61945185d19783009e52a035c1ee1599a4e2eb73d68ff80f`.
  Its internal manifest was checked after extraction: all **13/13** listed
  files matched their declared byte counts and SHA-256 values, including the
  signed H06/H08 source bytes.
- The submission includes H06/H08 evaluation masks, a results JSON, a
  technical verification script, evaluator-independence record, license
  record, and source-free manifest. The structural checks recorded in the
  package pass for source SHA, RGBA dimensions, alpha exclusion, and unknown
  handling; `human_labels_used_for_inference=false` and
  `unknown_as_negative=false` are preserved.
- The bundled `verify_h06_h08_submission.py` was re-run against the extracted
  private package and completed with `AUDIT_CREATED`; H06/H08 source SHA,
  dimensions, RGBA/alpha bounds, and numeric 4/8 topology measurements were
  reproduced. This remains an audit/reproducibility PASS only.
- The evaluator-independence record identifies the reviewer only by a claimed
  name, marks developer separation and prior-access checks as
  `SELF_ATTESTED_ONLY` / `NOT_VERIFIED`, and records no verified signature.
  The reviewer mask audit is therefore received and preserved, but is not an
  independently authenticated review.
- The package compares the masks with **frozen developer-produced Run30
  outputs**; `new_inference=NOT_PERFORMED`, `independent_blind_model_inference`
  is `NOT_VERIFIED`, and H06/H08 are the previously specified known cases.
  Green/red coverage, 4/8 connectivity, and hole counts are numeric reference
  measurements only. Critical parts, occlusion, correct clothing retention,
  and wrong arm/underlayer owner removal remain `NOT_VERIFIED`.
- The accompanying license record keeps source rights, reviewer mask rights,
  third-party model/data licenses, and commercial distribution
  `NOT_VERIFIED`. No new signed independent execution receipt or independent
  unseen-character holdout was supplied.
- On 2026-11-09 JST the owner stated in the collaboration thread that the
  license confirmation is complete and approved. Record this as the owner-side
  commercial-use decision `USER_CONFIRMED_CLEARED`; it does not rewrite the
  Drive package's objective `NOT_VERIFIED` fields for third-party model/data
  licensing or replace primary-source license evidence.
- This is a **Drive preservation/readback PASS**, not a semantic quality PASS:
  newly verified P0/P1 improvements remain `0`, and the release gate remains
  `L02=HOLD`, `Phase4=FAIL`, `production=NO_GO`. Keep #449 Draft, do not
  promote Phase5, merge `main`, or alter Public/C08/Golden/LocalWorker.

## 2026-11-09 source-only new inference receipt

- A new isolated CPU inference was executed after the blind review masks were
  supplied, using only the SHA-pinned signed H06/H08 source WebP files. The
  inference process received neither the review JSON nor either human mask;
  `human_masks_used_in_inference=false`, `review_json_used_in_inference=false`,
  and `unknown_as_negative=false` are recorded in the private receipt.
- Model provenance was fixed to `sayeed99/segformer-b2-fashion`, revision
  `e82089f3b76fdc5522727f6e793ff3d470c15e74`, with weights SHA
  `47313d9daf8f759b803b0bf449a4719bcd5b5a46eacad343e99e9660f8cedec1`,
  config SHA `44b342a5e9301a1716dac8a56537e82acfdae8f0597069b0414b7704e39b8705`,
  and processor SHA
  `6073ac6a37530ed2a19443d6a748f5579887b3ae48f6730073954b0b38cf3fd6`.
- Source-only output SHA/counts: H06
  `5dadf0fc88f0b52c57d29151933979057651e2bd036c20eff4d3d9b2db9e3f25`,
  `336792` nonzero pixels; H08
  `8e3613bf90202a5a04a58f53b7ba66e755a601494e37fac1a5137ad06bcf4275`,
  `100349` nonzero pixels. Both predictions have zero pixels outside signed
  source alpha. H06 differs from the prior frozen Run30 owner mask by
  `46613` pixels; H08 is byte-identical at the boolean-mask level.
- Only after output SHA freeze, the corrected signed review masks were used for
  post-inference scoring. H06: IoU `0.650551`, positive recall `0.654365`,
  known-negative FP `2985`, unknown predicted `699`. H08: IoU `0.278827`,
  positive recall `0.282152`, known-negative FP `4049`, unknown predicted
  `483`. Transparent painted pixels were excluded and unknown remained
  unknown.
- This closes the **new-inference execution** evidence gap, but it is not a
  semantic owner-quality PASS: H08 remains weak, the raw class5/class10 output
  is not yet an exclusive owner repair, and no new accepted P0/P1 improvement
  is claimed. Keep `Phase4=FAIL`, `L02=HOLD`, `production=NO_GO`.

## 2026-11-09 owner correction for the independent review record

- The owner corrected the compact internal JSON's stale implementation fields:
  the supplied H06/H08 review is the signed review already stored in the
  private Drive package, not a second review artifact. Treat its signature as
  `VERIFIED`; do not rescan the Drive for another signed blind result.
- The owner confirmed all four semantic/protocol answers are YES for both
  cases: the data was unseen, labels were not available before inference, the
  evaluator was independent of development, and arm/underlayer/occlusion plus
  correct-clothing-retention meaning review was completed. The signed masks
  remain post-inference evaluation inputs only.
- The earlier `NOT_VERIFIED` / `NOT_PERFORMED` values in the internal JSON are
  retained as implementation-error history, not as the current owner decision.
  This correction changes evidence interpretation, not the source-only
  inference receipt or any production artifact.

## 2026-11-09 source-only garment protection implementation

- Added the source-free `protect_source_only_garment_prediction` guard and its
  pinned Run30 replay wrapper in
  `tools/research/local_l02_class32_topology_palette_shadow.py`. It verifies
  the signed source SHA, prediction-array SHA, source alpha bounds, and frozen
  owner provenance. It restores only positive garment predictions from a
  candidate erasure; prediction zero is never treated as a negative label and
  no owner promotion is possible.
- Focused source-free tests passed: `66 passed` across the class32 topology,
  positive topology, and owner-topology candidate suites.
- The earlier A-suite collection failure was an execution-path issue, not a
  missing research module: `tools/research` was absent from the test import
  path and the default Python lacked `scikit-learn`. With an isolated private
  inference venv (`scikit-learn 1.9.1`) and `PYTHONPATH=tools/research`, the
  complete `tests/test_local_l02*.py` suite passed: `425 passed, 46 subtests
  passed`. No repository source, production environment, or private artifact
  was changed by dependency setup.
- Private replay with the new H06/H08 inference outputs passed the source and
  prediction SHA guards. H06 retained the existing 5-pixel class32/topology
  candidate removal and restored 0 pixels; H08 made no candidate change and
  restored 0 pixels. Post-score comparison therefore accepts no new P0/P1
  improvement: H06 known-negative FP changed `3926 -> 3923`, but positive TP
  changed `378629 -> 378627`; H08 was unchanged. This is a safety/code-path
  PASS, not a semantic quality PASS.
- Keep `Phase4=FAIL`, `L02=HOLD`, `production=NO_GO`; no Golden, Public/C08,
  LocalWorker, Phase5, or `main` change is authorized by this candidate.
- A follow-up 2026-11-08 research-only package was read back from the same
  private Drive folder. Its SHA manifest matches the five downloaded
  source-free records by byte count and SHA-256. The added observer record
  explicitly says the results are frozen existing results, not a fresh
  independent blind run. H06 agreement over union is `0.542694` with `269653`
  unknown source pixels; H08 agreement over union is `0.605198` with `365261`
  unknown source pixels. The SegFormer output is null/unverified for H08.
- The added blind-holdout record states there is no independently witnessed
  blind holdout protocol or result, the evaluator identity is not recorded,
  and observer/evaluator independence is not verified. The owner-authority
  record has `authorized_at=null`, `authorized_by=null`,
  `owner_authority=NOT_GRANTED`, and `production_allowed=false`.
- The added license/provenance record keeps dataset and model licenses
  `NOT_VERIFIED`, marks SCHP outputs `RESEARCH_ONLY`, and keeps
  `production_license_cleared=false`. The structural receipt reports only
  existing Codex exact-replay shadow topology, with clothing retention,
  critical parts, exclusive owner, holes, occlusion, and wrong arm/underwear
  owner removal all `NOT_INDEPENDENTLY_VERIFIED`. The independent topology
  audit separately states it is not an independent blind human review and
  lists no owner authorization or production license clearance.
- Therefore the new package improves evidence completeness but does not
  change the gate: `L02=HOLD`, `Phase4=FAIL`, `production=NO_GO`.
- On 2026-11-08 the owner explicitly authorized the bounded H06/H08 research
  review and candidate-evaluation continuation in the collaboration thread.
  Scope is limited to reviewing the provenance package and running
  source-only candidate checks; it does not authorize a Phase4 override,
  Phase5 transition, production use, Public/C08 changes, or a `main` merge.
  The independent blind holdout and license gates remain mandatory, and the
  owner-authority Drive record has not been rewritten by this note.
- The latest 2026-11-08 Drive additions include an owner-chat authorization
  record whose scope is continued H06/H08 evidence work and non-destructive
  integration only. It explicitly does not waive independent blind review or
  provenance requirements; cryptographic owner signature and independent human
  review are both `false`, and production is not authorized by that record
  alone.
- The added evidence matrix identifies the remaining missing items as an
  independent reviewer identity/signature, semantic critical-part and
  occlusion sign-off, an authenticated signed execution receipt, primary-source
  third-party license/provenance, and complete private-Drive readback.
- Historical leave-one-character-out evaluation exists from 2026-10-16, but is
  low-performing: H06 labelled-only IoU `0.032561` and positive recall
  `0.03258`; H08 labelled-only IoU `0.017511` and positive recall `0.018105`.
  It has no reviewer identity or signed independent blind attestation and is a
  `FAIL/NO_GO` result, not a new acceptance run.
- Existing human-owner comparisons are post-score evidence only: H06 outerwear
  recall `0.924608`, nonzero-owner IoU `0.714958`, labelled fraction
  `0.552717`; H08 outerwear recall `0.616561`, nonzero-owner IoU `0.601899`,
  labelled fraction `0.319633`. Unlabelled pixels remain unknown, and H08's
  zero underlayer count is not a negative finding. The gate remains
  `HOLD_PENDING_INDEPENDENT_BLIND_REVIEW_AND_OWNER_AUTHORITY`.
- Lane A H06 remains candidate-only: four source-only removals were proposed,
  one independently observed garment pixel was restored, no accepted P0/P1
  improvement was established, and Phase4 remains `FAIL`.
- The existing local ATR18/LIP20 observer maps were read back against their
  pinned class-map SHA values and replayed with H06. The result remained
  `SHADOW_ABSTENTION`, four changed owner pixels, one observer restoration,
  `quality=UNASSESSED`, `Phase4=FAIL`, and `production=NO_GO`. Their own
  receipts do not authorize owner promotion (`owner_promotion_authorized=false`
  / research-only licensing), so they remain protective evidence only.
- Lane B L04 remains `HOLD`; the official signed original, Stage8 JSON, and
  expanded SVG triple is still absent from the bounded inventory.
- Lane B L05 owner-PC private HTTPS replay is now complete for the concurrency
  path: V2 returned a PNG and a concurrent second request returned HTTP 429
  with `Retry-After: 2`. The receipt is source-free and preserved on the B
  handoff; physical iPhone acceptance remains separate and unattempted.
- After the replay, LocalWorker was restored to the protected production
  runtime. The Draft worker was not left active on the production port.

## 2026-11-09 owner decision: remove the documentary license gate

- The owner explicitly decided that a separate documentary license-evidence
  gate is not applicable to this project because the expected evidence does
  not exist and must not become an indefinite completion blocker.
- From this point, license/provenance documentation is removed from the
  **release-blocking gate list** and is handled as an owner-accepted
  commercial-use responsibility (`USER_CONFIRMED_CLEARED`). Historical Drive
  records that say `NOT_VERIFIED` remain unchanged as historical observations;
  they are not relabeled as objective verification.
- This decision supersedes earlier wording in this handoff that listed a
  license gate as mandatory. It does not waive independent blind evaluation,
  semantic critical-part/occlusion review, exclusive-owner checks, Phase4,
  physical-device acceptance, or the A/B branch and production protections.

## 2026-11-09 exact source-only inference and candidate replay

- The corrected independent review package is treated as the signed review
  already supplied on the private Drive: signature `VERIFIED`; H06/H08 source
  was unseen; labels were not read before the source review; the reviewer was
  independent; and arm, underlayer, occlusion, important-part and garment
  meaning review were all `YES`. Unpainted mask pixels remain unknown. Earlier
  contradictory internal JSON fields are stale implementation metadata, not a
  request to locate a second review package.
- A genuinely new inference was run after the source review using only the
  two signed source images and a locally pinned `sayeed99/segformer-b2-fashion`
  revision. The inference receipt records `human_masks_used_in_inference=false`
  and `review_json_used_in_inference=false`; the masks were opened only after
  the output arrays and SHA-256 values were frozen. H06 prediction array SHA is
  `413735e90ff42381798948163c9c0966473ec616ea035684a8dc1f10962283ad` and H08
  is `2ab16a864b23a9a178faf219512e4a7dbb255a659ddb57785c16292b3d008d6d`.
- The current H06 pinned class32 candidate removes five owner pixels. The
  independent ATR18/LIP20 positive-only protection guard restores one of those
  pixels, leaving four removals; no owner promotion occurs. Source SHA,
  observer-map SHA, alpha bounds, 4/8 connectivity and enclosed-hole
  invariants all pass. The new source-only SegFormer garment guard restores
  zero pixels and leaves the five-pixel raw candidate unchanged. The guard
  therefore protects against an observed garment erasure but does not yet
  produce an accepted P0/P1 improvement.
- Post-inference H06 scoring against the supplied independent mask, with
  unknown pixels excluded, was: frozen owner IoU `0.737669`, raw candidate
  `0.737670`, ATR/LIP protected candidate `0.737672`; known-negative FP rate
  changed `0.043064 -> 0.043031`, while recall changed `0.743427 -> 0.743425`.
  This is a small diagnostic tradeoff, not a quality-gate PASS.
- The source-only candidate survey also replayed the existing H08 sleeve
  recovery hypotheses without reading masks during candidate generation.
  Topology-positive recovery admitted `5,807` owner-1 pixels and improved the
  post-inference diagnostic IoU `0.278827 -> 0.294053`; robust-frontier
  recovery admitted `18,280` pixels and reached `0.330357`. Both preserve the
  frozen 4/8 component and hole counts, but remain candidate-only: the latter
  uses an exposed known-case margin and neither candidate has independent
  sleeve-vs-arm/underlayer owner authority. They are not promoted or connected
  to production.
- Private source-free receipts for this replay are retained outside the
  repository. Repository state remains `L02=HOLD`, `Phase4=FAIL`,
  `production=NO_GO`; #449 and #451 remain Draft.

## 2026-11-09 combined H06 protection entrypoint

- Commit `499151c4` adds the source-free
  `propose_pinned_h06_with_combined_garment_guard` entrypoint. It fixes the
  integration gap without changing the removal rule: the pinned class32
  candidate runs first, ATR18/LIP20 explicit garment positives restore only
  erased frozen-owner pixels, and the separately frozen source-only model
  prediction then applies the same positive-only restoration rule. Zero or
  unknown observations never authorize deletion, and no new owner is promoted.
- The exact signed H06 replay reproduced the prior result through this single
  entrypoint: four removals remain after one ATR/LIP restoration, the new
  source-only model restores zero, and the combined candidate has the same
  diagnostic IoU `0.737672` and known-negative FP rate `0.043031` as the
  independently guarded candidate. Source SHA, prediction-array SHA, alpha,
  owner exclusivity, 4/8 components and enclosed holes passed.
- The source-free A suite at the new head is `426 passed, 46 subtests passed`.
  This remains a research candidate only; no Phase4, Phase5, main, Public,
  C08, Golden or production change follows from this integration.

## 2026-11-09 H08 independent-observer positive intersection

- Added the source-free
  `propose_pinned_h08_with_independent_observer_positive` entrypoint. It
  intersects the signed-source class32/color-positive evidence with the
  provenance-pinned H08 `deepfashion_only` positive map from the independent
  DeepFashion2 observer, then applies the existing exclusive 4/8 owner and
  enclosed-hole gate. The observer array is caller-supplied and private; its
  exact SHA is bound in code as
  `3dd9b6e01d2584247543abbe64f543e1ec1d0d55ab6231d3d7d2783a2d0cbcfa`.
  Human masks and review JSON are not accepted by the inference function, and
  absent observer pixels remain unknown rather than negative.
- Exact signed H08 replay passed source/class/owner/observer SHA checks,
  owner exclusivity, 4/8 component preservation, and enclosed-hole
  preservation. It assigned `591` pixels (`588` owner 1, `3` owner 2) in the
  private candidate. After output freeze, the supplied review mask was used
  only for postscore: IoU improved `0.278827 -> 0.280547`, recall
  `0.282152 -> 0.283892`, known-negative FP stayed `4049` and the known-
  negative FP rate stayed `0.020791`; `483` unknown predictions remained
  excluded from the score. Private receipt SHA is
  `F629B92CEA072835E8B986048714423B78D00F8897C78B67A327C86A08C33E6D`.
- Added source-free regression coverage for observer intersection and
  fail-closed observer SHA handling. The L02-focused suite is now
  `428 passed, 46 subtests passed`. This is a research candidate and a
  diagnostic improvement only: independent semantic sleeve-vs-arm/underlayer
  authority, owner promotion authorization, Phase4, Golden, and production
  remain unresolved. Keep `L02=HOLD`, `Phase4=FAIL`, and `production=NO_GO`.

## 2026-11-09 H04 inherited-observer replay rejected

- The signed H04 source and the pinned inherited soft-observer archive were
  replayed through `run_local_l02_owner_topology_shadow.py` without loading
  human masks or polygons into the runner. Source integrity, signed foreground
  union, protected-owner equality, leaf exclusivity, component counts, and
  neck-to-torso spacing all passed. The frozen candidate transferred
  `41,507` pixels to `major_clothing` (`6,331` from hair, `35,169` from torso,
  and `7` from unknown); private candidate NPZ SHA is
  `ebd6579b508a9a5b123601f186266ab4b9f71000ebe0a4e6b0f523754b02841b`.
- Post-freeze independent-mask scoring found `38,292` transferred outerwear
  pixels, `3,048` known non-outerwear pixels, and `167` unknown pixels. The
  candidate therefore does not pass semantic exclusive-owner quality.
- More importantly, the inherited observer receipt declares
  `H04_training_labels_used=true`. It is not admissible as a label-free blind
  inference input, even though the runner itself did not read the masks. The
  candidate is rejected and is not integrated, promoted, or used as a P0/P1
  fix. No private candidate artifact was copied into GitHub.

## Required owner-side inputs

## 2026-11-09 H06 frozen postscore gate

- Added the source-free generic evaluator
  `tools/research/local_l02_phase4_postscore_gate.py` and focused tests in
  `tests/test_local_l02_phase4_postscore_gate.py`. It consumes only frozen
  output receipts, independent-review attestations, structural results, and
  aggregate postscore counts. It does not accept image pixels or human masks
  as inference inputs; unknown pixels are not treated as negative.
- The exact H06 aggregate was evaluated once through this gate: candidate
  removed `4` pixels; known positive garment loss `0`; known false-owner
  removals `4`; unknown removals `0`; owner promotions `0`. Signature,
  unseen-data, pre-inference label exclusion, evaluator independence,
  semantic-review, source/prediction SHA, alpha, exclusive-owner, 4/8
  component, and 4/8 hole checks were all true. The case-level result is
  `case_phase4=PASS` with no failures.
- This is deliberately a narrow case-level result. The evaluator returned
  `phase5_authorized=false`, `L02=HOLD`, and `production=NO_GO`; it does not
  promote the campaign-level Phase4 gate, H08, Golden, merge, or production.
  The A focused suite is `433 passed, 46 subtests passed`; `git diff --check`
  passes. No private masks, NPZs, coordinates, or comparison images were
  added to GitHub.

1. Lane A: an independently provenance-pinned garment/arm/underlayer observer
   for H06/H08, bound to the exact signed source SHA and carrying its model,
   run, class-map, and output hashes. Unknown pixels must remain unknown.
   Human review masks remain post-inference evaluation only.
2. Lane B L04: the official signed original, Stage8 JSON, and expanded SVG,
   with exact SHA-256 values and cross-links. The triple must contain non-empty
   geometry, source-owner exactness, protected face/arm exactness, and exact
   silhouette measurements.
3. Lane B L05/L07: physical iPhone acceptance after an owner-authorized
   production reflection, plus the remaining browser/input/output checks.

## Release rule

Keep #449 and #451 Draft. Do not promote Phase5, merge to `main`, change
Public/C08 or production, or treat static/TestClient results as device
acceptance until the remaining owner-side gates above are read back and
independently verified.
