# Campaign C02b2: GC001 source-color threshold sensitivity (research HOLD)

2026-10-09. **C02b2 research observation complete, C02 quality gate not passed.** Not a production authorization. Source, masks, SVG, renderer and production remain untouched.

## Frozen source evidence
Pinned immutable GC001 SHA `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`, Phase03/04 ZIP SHA `89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434`, authentic Phase04 right-arm SHA `8829b6865a50abee2fac820cfe250c35e3089a8f5eb4c3754b633a7d1327ac58`. Prior C02b1 pose-only solution remains HOLD because wrist confidence 0.462252 is below 0.60.

Diagnostic alternative to pose-only masking: compare original right-arm owner's pixel colors to original border modal opaque background color in OpenCV LAB. Filter by fixed color-distance threshold, count connected components and Canny original-source edge pixels lost. **This is a negative research probe, not semantic ground truth or a reusable filter.**

| LAB distance > | Owner pixels retained (original 6486) | Connected components | Original source Canny edge pixels excluded |
|---|---:|---:|---:|
| 0 | 5631 | 3 | 72 |
| 4 | 5603 | 4 | 87 |
| 8 | 5579 | 4 | 94 |
| 12 | 5435 | 3 | 161 |
| 20 | 5143 | 15 | 293 |
| 32 | 4785 | 39 | 434 |

At all six thresholds, the original exact background-RGB overlap 533 disappears, **but** the source right-arm owner is split into multiple disconnected fragments; original-image edges are deleted too. An orange-pixel deletion rule must **NOT** be treated as valid structural-arm correction. Edge loss alone does not prove arm semantic loss, and RGB equality does not prove background ownership.

Local original-input research test suite: **6/6 PASS** (SHA-bound original/snapshot, deterministic two-run pixel-board and metrics, source/snapshot tamper fail-closed, no promotion). These tests have not been run by CI and do not imply real Chrome, Raden control, full Golden or resolved original Stage8 ring budget.

## Non-promoting gate
`pose_only: HOLD`, `color_only: HOLD`, `C02: IN_PROGRESS`, `C03: HOLD`, `C04: HOLD`, `C05_C08: BLOCKED`, `release_authorized: false`, `production_changed: false`.

## Recovery note
The experiment files were generated during this turn in temporary workspace, but part of the Drive upload failed with `container_session_expired`. **Do not claim those research inputs, scripts, metrics and board are durably saved to canonical Drive unless independently read back.** Reconstruct/reverify from authenticated snapshots if they cannot be recovered; source evidence above is the reproducible numerical record.

## Next C02b3
Use independent source-semantic/edge observer with source SHA binding and confidence checks (do not lower low-confidence pose gates). Analyze Raden and additional independent cases, then actual Chromium on reversible SVG candidate and separate signed Stage8-vs-expanded deployed vertex caps. Obtain real human visual review; no facial microfeatures, no invented pixels or raster-embedded SVG.
