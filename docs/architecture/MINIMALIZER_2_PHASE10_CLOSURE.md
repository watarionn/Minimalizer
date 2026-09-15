# Minimalizer 2.0 Phase X Closure

Date: 2026-09-15
Base implementation commit: `1c882ef3eb0960eafdc8b3a355fe31a755733cce`
Closure branch: `feature/minimalizer-2-phase10-closure`

## Closure decision

Phase X Regression / Debug is accepted for the Minimalizer 2.0 architecture v1 implementation.
The structural pipeline, regression infrastructure, hard invariants, canonical 18-case corpus runner, and known-issue sentinels are operational.

This closure does not claim pixel-perfect agreement with the Approved Geometric References. The architecture specification explicitly does not require that. The remaining visible gap is calibration: Minimalizer 2.0 is still more detailed and jagged than the approved coarse geometric style.

## Canonical 18-case mechanical regression

Preset: `minimal`
Cases completed: 18 / 18
Hard invariant failures: 0

Aggregate results:

- minimum contour IoU: `0.9191919192`
- mean contour IoU: `0.9427570240`
- palette count range: `7..11`
- visual group count range: `21..60`
- mean runtime: `10.0241 s`
- maximum runtime: `12.8217 s`
The lowest contour IoU case was `Natsuiro-Matsuri` at `0.9191919192`, still above the configured `0.90` guard.

The corpus source images and Approved References remain external regression assets and are not committed as generated/debug payloads.

## Human A/B smoke review

Smoke cases reviewed:

1. Kikirara-Vivi
2. Otonose-Kanade
3. Hakos-Baelz

For all three cases, Current Minimalizer reduced the image to approximately 18 large shapes but lost major person-part relationships and became dominated by abstract triangular fragments. Minimalizer 2.0 retained substantially better face/hair/torso/arm/outfit readability.

Against the Approved Geometric References, Minimalizer 2.0 is structurally closer than Current Minimalizer but remains too detailed. The main visible differences are excess small regions, jagged contour detail, and facial/accessory detail that the approved references intentionally omit.

A/B result: PASS for structural/readability improvement, with calibration follow-up required for coarseness.

## Known-issue sentinels

Dedicated V2 regression sentinels now exist for:

- `face_right_gouge`
- `thin_rectangle_noise`
- `characteristic_accent_loss`
- `hair_skin_color_collapse`
- `subject_background_leakage`
The characteristic-accent sentinel exposed a real closure defect: two different high-confidence characteristic anchor IDs could still merge when their mean colors were close. Region Merge now treats distinct high-confidence anchors as a hard barrier independent of mean-region DeltaE. DeltaE remains part of the soft anchor cost, but is no longer required for the hard identity guard.

## Reproducible corpus runner

`tools/run_v2_visual_regression.py` provides a canonical command-line entry point for the 18-case corpus. It accepts external input/reference directories and does not require large regression assets in Git.

The runner performs a decode preflight before starting the expensive corpus run. This specifically rejects HTML or other invalid payloads saved with `.png` names, an issue found during Phase X closure.

Example:

```text
python tools/run_v2_visual_regression.py \
  --input-dir <18-source-directory> \
  --reference-dir <18-approved-reference-directory> \
  --output-dir <regression-output-directory> \
  --preset minimal \
  --artifact-level standard
```

## Quality-gate status

- Synthetic / V2 automated regression: PASS
- Full 18-case mechanical corpus: PASS
- Hard invariant failures: `0`
- High-confidence characteristic-anchor silent loss guard: PASS
- Critical subject/background merge guard: PASS
- Known-issue regression sentinels: PASS
- Current Minimalizer vs Minimalizer 2.0 human smoke A/B: PASS
- Pixel-perfect reference agreement: not required by architecture v1

## Next quality focus

Do not reopen Region Merge architecture merely to reduce visual detail. The next calibration work should preserve the now-passing structural and coverage guards while reducing excess small contour detail and moving final output toward larger, cleaner geometric planes.
