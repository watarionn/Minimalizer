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

## Required owner-side inputs

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
acceptance until the owner-side gates above are read back and independently
verified.
