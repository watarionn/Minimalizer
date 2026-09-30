# Browser Fallback v9

Status: **CANONICAL PALETTE PARITY PASS / FULL BROWSER QUALITY IMPROVED / RAILWAY GRADUATION HOLD**

Date: 2026-10-01
Branch: `feature/browser-fallback-v9-palette-parity-20261001`
Production default: **unchanged**. Browser fallback remains opt-in, lite remains its default structural profile, and exact spectral remains quality-first opt-in.

## Goal

v9 closes the palette selection / medoid fidelity gap isolated after v8 fixed analysis resizing.

By the start of v9, the no-resize character cases already matched Python through:

- source raster;
- exact structural preprocessing;
- OpenCV-compatible Lab;
- canonical SLIC;
- Region Merge;
- Minimal hierarchy cut.

Yet the final Browser render still differed materially from the Python unguided proxy.

The earliest remaining downstream stage was palette consolidation.

## Initial palette diagnosis

The old Browser palette path used:

- a fixed 8-color target;
- region mean Lab;
- Euclidean color distance;
- k-means-like farthest seeding and refinement;
- representative region selection after cluster refinement.

Python V2 instead uses:

- deterministic per-region source-pixel sampling;
- robust region medoids;
- CIEDE2000;
- a palette merge hierarchy;
- protected major-region relationships;
- deterministic hierarchy cut;
- protected-relationship repair.

On the three no-resize character cases, region partitions already matched Python exactly.

Before v9, assigned palette RGB comparison was:

| Case | Python palette | Browser palette | Exact assigned region colors |
| --- | ---: | ---: | ---: |
| Raden | 7 | 8 | 0 / 40 |
| Subaru | 8 | 8 | 0 / 40 |
| Noel | 7 | 8 | 0 / 40 |

Mean assigned RGB absolute errors were:

- Raden: **14.50**
- Subaru: **18.40**
- Noel: **21.96**

Palette was therefore a major downstream mismatch.

## Canonical Browser palette

v9 adds a Browser implementation of the relevant Python unguided palette contract.

### Robust region medoid

For each selected region:

1. collect region pixels in deterministic raster order;
2. sample at most 1024 pixels using the canonical evenly-spaced index rule;
3. compute the per-channel Lab median;
4. select the 64 samples nearest that median with stable ordering;
5. score each candidate against all sampled pixels using CIEDE2000;
6. select the minimum-total-distance source pixel;
7. preserve its observed RGB as the representative color.

### CIEDE2000

Browser v9 implements the same CIEDE2000 formula used by Python palette sampling and hierarchy construction.

### Protected relationships

For the unguided Browser path, v9 reproduces the relevant Python relationships:

- adjacent major regions;
- distinct major color masses.

Characteristic anchors, semantic tags, and subject-class protections are absent from the unguided proxy path and are therefore not synthesized in Browser fallback.

### Palette hierarchy

The Browser palette hierarchy now uses:

- CIEDE2000 representative distance;
- source-region pixel counts for representative medoid weighting;
- deterministic node-id tie ordering;
- major-region relationship cost;
- canonical merge replay.

### Minimal palette cut

Python Minimal auto mode targets the midpoint of the `(6, 9)` palette range:

- initial desired count: **7**

Protected-relationship repair may split a selected palette node afterward.

This is why Subaru ends at 8 colors while Raden and Noel remain at 7.

The old fixed Browser 8-color contract is no longer used by the canonical path.

## Exact palette parity

On identical post-merge selected regions:

### Raden

- Python palette count: **7**
- Browser palette count: **7**
- Python relationships: **40**
- Browser relationships: **40**
- repairs: **0 / 0**
- exact assigned RGB: **40 / 40**
- assigned RGB MAE: **0.0**

### Subaru

- Python palette count: **8**
- Browser palette count: **8**
- Python relationships: **37**
- Browser relationships: **37**
- Python repairs: **1**
- Browser repairs: **1**
- exact assigned RGB: **40 / 40**
- assigned RGB MAE: **0.0**

### Noel

- Python palette count: **7**
- Browser palette count: **7**
- Python relationships: **17**
- Browser relationships: **17**
- repairs: **0 / 0**
- exact assigned RGB: **40 / 40**
- assigned RGB MAE: **0.0**

The selected palette RGB lists themselves also match Python exactly in all three cases.

This establishes canonical palette parity for the tested no-resize exact-upstream cases.

## Browser metadata

v9 exposes the palette path in both response headers and metadata.

Headers:

- `X-Minimalizer-Palette-Count`
- `X-Minimalizer-Palette-Method: canonical-medoid-hierarchy`
- `X-Minimalizer-Palette-Repairs`

Metadata:

- `paletteCount`
- `paletteMethod`
- `paletteRelationshipCount`
- `paletteRepairCount`

The legacy Browser palette implementation remains available internally as a rollback/debug path but is not the normal v9 analysis route.

## Five-case benchmark

### Lite default

v9 lite:

- mean processing: **1172.1 ms**
- mean initial regions: **643.6**
- mean vertices: **1507.6**
- mean palette count: **7.4**
- mean palette relationships: **25.2**
- mean palette repairs: **0.4**
- proxy SSIM: **0.8524**
- proxy edge IoU: **0.2652**
- proxy MAE: **9.6686**
- Railway SSIM: **0.8424**
- Railway edge IoU: **0.2546**

v8 lite:

- proxy SSIM: **0.8513**
- proxy edge IoU: **0.2636**

Lite remains around the one-second class and changes only modestly in aggregate because its approximate L0 route still changes the upstream selected regions.

### Exact opt-in

v9 exact:

- mean processing: **9153.4 ms**
- mean initial regions: **652.0**
- mean vertices: **1546.4**
- mean palette count: **7.4**
- mean palette relationships: **30.0**
- mean palette repairs: **0.4**
- proxy SSIM: **0.9065**
- proxy edge IoU: **0.3353**
- proxy MAE: **2.8992**
- Railway SSIM: **0.8563**
- Railway edge IoU: **0.2827**

v8 exact:

- proxy SSIM: **0.8817**
- proxy edge IoU: **0.3069**

Palette parity therefore produces another meaningful end-to-end gain.

The measured exact runtime varies significantly with local browser execution conditions, so the v9 number should not be interpreted as an algorithmic speed improvement over v8.

## Exact per-case highlights

### Raden

- palette: **7**
- relationships: **40**
- repairs: **0**
- proxy SSIM: **0.9006**
- proxy edge IoU: **0.2919**
- proxy MAE: **2.1230**

### Subaru

- palette: **8**
- relationships: **37**
- repairs: **1**
- proxy SSIM: **0.9351**
- proxy edge IoU: **0.3562**
- proxy MAE: **2.0931**

### Noel

- palette: **7**
- relationships: **17**
- repairs: **0**
- proxy SSIM: **0.8988**
- proxy edge IoU: **0.3159**
- proxy MAE: **2.7225**

### Elizabeth

- palette: **7**
- relationships: **18**
- repairs: **0**
- proxy SSIM: **0.9242**
- proxy edge IoU: **0.3933**
- proxy MAE: **4.1126**

### Night River

- palette: **8**
- relationships: **38**
- repairs: **1**
- proxy SSIM: **0.8738**
- proxy edge IoU: **0.3192**
- proxy MAE: **3.4449**

## Interpretation

The exact Browser route now reaches **0.9065 SSIM** against the Python unguided proxy, with mean RGB MAE below **3**.

This does not mean the Browser route has reached Railway parity.

The pairs are different:

- Python unguided proxy vs Railway baseline: SSIM **0.9067**, edge IoU **0.5332**
- Browser v9 exact vs Railway: SSIM **0.8563**, edge IoU **0.2827**

The remaining large edge gap shows that the dominant residual is now geometric / raster rather than palette color selection.

## Real wrapper smoke

A generated scaled fixture was processed through real Chrome `minimalizeFile()`.

Both lite and exact report:

- mode: `browser-fallback-v9`
- analysis resize: `opencv-inter-area`
- palette method: `canonical-medoid-hierarchy`

The palette method and repair count agree between response headers and metadata.

Lite retains:

- structural path: `l0-lite-jacobi`

Exact retains:

- structural path: `spectral-exact`

## Validation

Focused v9 palette / spectral / migration suite:

- **29 passed**

Final Browser / migration / Web / Local Worker regression:

- **78 passed**
- one existing Starlette/httpx deprecation warning
- JavaScript syntax: PASS
- `git diff --check`: PASS

The v9 suite includes a direct Subaru Python/Browser palette parity regression that requires:

- exact assigned region RGB;
- exact palette count;
- exact protected relationship count;
- exact repair count of 1.

## Gate

### Canonical palette selection: PASS

The tested exact-upstream no-resize cases match Python exactly.

### Robust medoid selection: PASS

Selected source-pixel representatives match Python.

### Protected relationship repair: PASS

Subaru's one required split is reproduced exactly.

### OpenCV resize / Lab / SLIC / Region Merge: PASS

Inherited from v8 / v7 / v6 and prior parity phases.

### Full Browser quality: IMPROVED

Exact Browser color agreement is now very close to the Python proxy.

### Railway graduation: HOLD

The edge / geometry gap remains too large.

## Next first-bad-stage

The next primary stage is now:

**contour simplification and raster geometry fidelity**

The Browser currently uses its own:

- boundary-ring extraction;
- contour simplification;
- Canvas polygon fill / even-odd rasterization.

Python uses its own contour and primitive/raster path, including OpenCV contour simplification behavior.

The next phase should isolate geometry before changing any more color logic.

## v10 target

Recommended sequence:

1. compare Python and Browser contour loops on identical selected labels;
2. compare vertex counts and vertex coordinates before simplification;
3. compare simplification epsilon / stopping decisions;
4. reproduce OpenCV `approxPolyDP` behavior where needed;
5. compare rasterized region masks independently of palette;
6. separate contour mismatch from Canvas fill/rasterization mismatch;
7. rerun five-case edge IoU after each parity step.

The small Elizabeth Browser/OpenCV WebP decode residual remains tracked separately.

Large-image Browser memory hardening from v8 also remains an operational prerequisite before Railway can be removed.

Railway should remain available until geometry parity and Browser memory hardening are closed.
