# Local L04 source-preserving repair (2026-11-09)

The first Phase11 simplification candidate failed source-owner and silhouette
replay. The next bounded correction uses only the signed original alpha and the
source-only Phase4 owner masks from the same ZeroBase2 run. It does not read
human review masks, observer labels, Golden assets, or production files.

`tools/research/local_l04_stage8_source_preserving.py` emits owner contours,
then performs a real local Chromium transparent-background replay. Missing
source-supported edge pixels are added as one-pixel geometric rectangles and
the replay is repeated. Extra pixels are rejected. This is a diagnostic
source-preserving candidate, not a budget waiver or release authorization.

## Result

| Case | Source-owner mismatch | Protected face/arm mismatch | Chromium silhouette XOR | Vertices | Budget |
|---|---:|---:|---:|---:|---|
| H06 | 0 | 0 | 0 | 72201 | FAIL |
| H08 | 0 | 0 | 0 | 56249 | FAIL |

The triple hash gate passed for both cases. The only numerical L04 failure in
this candidate is the inherited `1887` vertex cap, which is unconfirmed as a
Local-case policy and is not waived here. Therefore the result remains
`L04_formal=HOLD`, `human_visual_golden=HOLD`, and `production_release=NO_GO`.

H06's separate ZeroBase2 Phase12 result still has the concrete 35-pixel neck
owner loss in the simplified candidate. The source-preserving L04 candidate
keeps the Phase4 neck mask and does not silently convert that Phase12 failure
into a PASS.

Next: obtain or explicitly approve a versioned Local vertex policy, or develop
a source-preserving representation whose measured geometry really fits that
policy. No Public/C08, Golden, LocalWorker, or signed original was changed.
