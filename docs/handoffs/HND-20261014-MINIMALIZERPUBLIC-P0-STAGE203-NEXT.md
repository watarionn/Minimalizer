# Handoff: MinimalizerPublic StructuralRecovery P0 after Stages194–203

Date: 2026-10-14 JST
PR: https://github.com/watarionn/Minimalizer/pull/393
CI: https://github.com/watarionn/Minimalizer/actions/runs/38532909112
**CI at Stage203 docs head 73f293c: 668/668 PASS, 0 fail.**

## Current authority
Operator out-of-band confirms A and B worked independently; use as operator attestation only, not automated identity verification. Human classification ground truth is not yet manually adjudicated. Four immutable private source-pinned original review JSON inputs remain owner-only. Reviewers can be recontacted for signed/explicit v2 corrected labels with original hashes preserved.

## What was implemented
`web/static/public-stage194-203-recovery-p0.mjs` and `tests/js/test_public_stage194_203_p0.mjs` (+26 tests):
194 taxonomy; 195 pixel-complete A/B classification; 196 32px queue; 197 revision SHA audit; 198 explicit operator per-pixel evidence proposals; 199 conservative tri-state silhouette; 200 exact bitmap rectangle cover; 201 strictly observed per-role original RGB; 202 cost/cap diagnostics; 203 fail-closed release gates.

Full research suite 668 tests PASS (hosted Actions as of this handoff); no development of ordinary public website or Local Minimalizer occurred. The conservative source-only rectangle prototype was replayed with private SHA-pinned GC001/Raden originals; source-only pixels exact, ambiguous pixels explicitly excluded, no generative fill. Private technical baselines: GC001 47,448 agreed-person pixels, 7,072 unresolved, 1,573 rects / 6,292 rectangle vertices; Raden 47,888 agreed-person pixels, 22,690 unresolved, 883 rects / 3,532 vertices. Historical full-body numeric caps GC001 1,887 and Raden 1,412 are not achieved by these rectangle candidates; compare representation categories carefully.

Full private replay and source-derived SVG/label-state masks are in:
https://drive.google.com/drive/folders/1xBVlBwyvisj7ti_SzR5Lk0FUJYW2jcHV
Owner-only ZIP SHA256 `5b90f5edebf9e67305600b19eb4003e73cabee84267e59147099691ee6aecd49`; upload and readback hash matched. DO NOT COPY any private original art, per-pixel private labels or source-derived previews into public GitHub or public CI.

## Next work
- Stage204+: have operator/person manually adjudicate private source-art disagreement areas. PRIORITY Raden garment/sleeve large components, GC001 garment/accessory; then residual subject/background hair/skin edges and all original opaque abstentions.
- Re-audit corrected immutable v2 A/B results, no automatic agreement promotion. Classify complete wholebody and source background before compositing.
- Develop source-exact contour/region frontier that can reduce vertices vs rectangle approach while proving no spill/replay loss; original silhouettes must not be invented or distorted.
- Improve source-only internal colors, fabric/sleeve layering, neckwear and hair subject to mask authority.
- Fullbody Golden visual QA, actual iPhone Safari acceptance, full RGB/shape tests, rollback rehearsal, explicit owner approval and safe deployment.

**Status: Golden HOLD, PR #393 Draft/unmerged, no release authorized. Previous roadmap estimate 205–211 was conditional and should be re-estimated after class adjudication and numeric SVG gates.**
