# Local L04 runtime measurement (2026-11-10)

This is a source-free measurement of the exact private H06/H08 expanded SVG
candidate. No image, mask, coordinate, or SVG bytes are stored in GitHub.
The measurement uses the private artifact SHA values only.

## Method

- Browser: Google Chrome `157.0.8103.40`
- Driver: Selenium with headless Chromium
- Viewport: 2000 x 2000 CSS pixels
- Device scale factors: 1 and 2
- Checks: document readiness, SVG node count, in-memory screenshot generation,
  and the Chrome process tree resident set size
- No vertex-count cap was applied

## Results

| Case | SVG SHA-256 | SVG bytes | DPR | readyState | SVG nodes | load ms | screenshot bytes | Chrome tree RSS MiB |
|---|---|---:|---:|---|---:|---:|---:|---:|
| H06 | `95a02a56a378759599aeb765d35a18c464fa8dcb8f50a7a65713b42cf0bf7296` | 1,680,144 | 1 | complete | 14,749 | 118.82 | 34,355 | 467.84 |
| H06 | same | 1,680,144 | 2 | complete | 14,749 | 139.74 | 99,909 | 558.22 |
| H08 | `410267167396abf0dacb3dcde28872d1bd3e9de3d40ee6f0f8f87028b3e4bb28` | 1,305,135 | 1 | complete | 11,354 | 116.56 | 33,885 | 458.78 |
| H08 | same | 1,305,135 | 2 | complete | 11,354 | 102.67 | 96,144 | 560.81 |

## Interpretation

- Both cases completed parsing and screenshot generation at DPR1 and DPR2.
- No vertex-cap failure occurred; vertex counts remain diagnostic only.
- The observed Chrome process RSS is about 459--561 MiB. It is not adopted as
  a hard limit because this is a desktop headless browser measurement, not the
  LocalWorker/iPhone runtime.
- If a runtime guard is later needed, it must be measured on the actual target
  runtime and expressed as an explicit bytes/time/memory/timeout contract.

## Gate status

The source-preserving candidate's v2 triple readback is eligible for independent
review with exact source owner, protected face/arm, and silhouette checks. This
measurement does not authorize production, Golden, or iPhone release.
