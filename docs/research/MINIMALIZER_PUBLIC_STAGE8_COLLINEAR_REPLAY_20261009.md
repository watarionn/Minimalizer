# Signed Stage8 collinear replay and degeneracy classification (2026-10-09)

Research-only source-immutable test with the two signed SA10.34 original Stage8 JSONs. No source-generated pixels or facet deletion.

## Actual source-ring outcome

| Test | GC001 | Raden |
|---|---:|---:|
| Stage8 historical ring vertices | 3,604 | 2,370 |
| Measured collinear occurrences | 45 | 15 |
| Forward straight interiors in rings with >=4 points | **0** | **0** |
| Collinear zero/reversal occurrences | 45 | 15 |
| Degenerate rings of only 1-2 points | 110 | 13 |
| Total vertices inside 1-2 point rings | 163 | 17 |
| Collinear deletion attempts eligible under strict forward straight criterion | 0 | 0 |
| Proven safe vertices removable | **0** | **0** |

The earlier 45 and 15 collinear counts must never be presented as safe deletions. They include reversals or degenerate arrangements. The conservative replay tool thus had **zero legitimate straight-middle removal attempts** and did not alter source rings. No owner fill raster, topology or Chromium DPR4 proof was claimed for an edited image. The old Stage8 caps GC001 1887 and Raden 1412 stay failed.

## Verification

`tools/research/public_geometry_js/stage8_collinear_replay.py` checks original source ring geometry and refuses candidate release without independent owner-fill parity and topology verification. `stage8_ring_degeneracy.py` separately records counts of undersized and zero/reverse rings. Source images and source-ring JSON remain in private Drive, never copied to GitHub. Production unchanged; Golden HOLD.

## Next

Analyze what **single-pixel and two-pixel rings** actually own in the source via signed per-owner mask, considering topology and occlusion. Do not simply drop all degenerate rings; they may be required to retain 1px semantic color, costume markings and disconnected hair points. Only experiment with topology-preserving alternatives under strict source replay.
