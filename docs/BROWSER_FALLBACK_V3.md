# Browser Fallback v3

Status: **REGION MERGE PARITY PASS / FULL BROWSER QUALITY HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**. Railway remains the hosted fallback.

## Goal

v3 ports the canonical Minimalizer 2.0 Region Merge hierarchy and Minimal hierarchy cut into the browser fallback.

The browser-only target architecture remains:

```text
Local Worker
  -> Browser Fallback
  -> Railway (temporary escape hatch)
```

This phase does not remove Railway.

## Why v3 was needed

Browser v2 brought spatial segmentation statistics close to canonical Python V2:

- Browser v2 initial regions: 647.2
- Python unguided initial regions: 670.6
- Browser v2 shapes: 40
- Python selected regions: 40
- Browser v2 palette: 8
- Python palette: 7.6
- Browser v2 vertices: 1058.8
- Python vertices: 1000.8

The remaining first-bad-stage was the Region Merge approximation.

v2 directly merged active regions until the shape budget was reached.
Canonical Python V2 instead:

1. builds RegionStats and boundary evidence;
2. evaluates adjacent pairs with canonical merge costs;
3. performs safe consolidation;
4. builds a complete hierarchical merge tree;
5. computes cumulative visual loss;
6. solves the Minimal hierarchy cut with dynamic programming.

v3 ports that structure.

## Canonical merge-cost port

Browser v3 now includes the non-semantic canonical evidence available without Local Worker analysis providers.

### Color

Canonical SSE-based color cost:

```text
delta_sse = (n_left * n_right / (n_left + n_right)) * ||mean_left - mean_right||^2
per_pixel = delta_sse / (n_left + n_right)
color_cost = 1 - exp(-per_pixel / 25)
```

### Boundary

Each adjacent-region edge stores 32-bin gradient histograms.

Boundary cost uses the same quantile composition as Python V2:

- structural: 0.45 * q75 + 0.55 * q90
- raw: 0.40 * q90 + 0.60 * q98
- final: max(structural, 0.35 * raw)

### Topology

Shared boundary ratio and the canonical thin-neck exponential cost are retained.

### Geometry

Merged convex-hull inflation is evaluated with the canonical `hull_inflation_tau = 0.25`.

The convex hull is evidence for merge cost only. It is not used as final rendered geometry.

### Protection and redundancy

Browser v3 retains the available canonical major-mass protection and small redundant-region reward.

Semantic, anchor, subject, pose, line, and model-derived evidence are zero when the browser route has no corresponding trusted analysis input.

## Safe consolidation

The browser ports the canonical safe-consolidation gates:

- safe area ratio: 0.0008
- safe color cost: 0.08
- safe boundary cost: 0.15
- safe topology cost: 0.25
- safe shared boundary ratio: 0.35
- safe soft protection: 0.02

The same heap re-evaluation behavior is used so stale merge candidates cannot be applied after graph changes.

## Full merge hierarchy

After safe consolidation, Browser v3 continues hierarchical merging until each connected graph is reduced to its root.

Every merge records:

- children;
- raw merge cost;
- monotonic hierarchy height;
- stage;
- merged RegionStats.

This creates the same kind of merge tree used by canonical Python V2.

## Minimal hierarchy cut

The first v3 prototype cut the tree by replaying merge order until 40 regions remained.

That was rejected.

It caused a five-case regression:

- proxy SSIM: 0.8180
- proxy edge IoU: 0.2157
- mean vertices: 1569.8

The canonical path does not use chronological replay.

The final v3 ports the Minimal dynamic-programming cut:

- target range: 24 to 40
- max hierarchy height: 1.00
- complexity lambda: 1.10
- target weight: 1.10
- visual loss weighted by merge cost and sqrt(area ratio)

The final selected cut is reconstructed from the lowest-objective DP state.

## Canonical Lab edge map

Browser v3 also ports the canonical raw merge edge calculation:

1. Sobel x/y on all three Lab channels;
2. magnitude from all channel gradients;
3. 99th-percentile normalization;
4. clip to [0, 1].

A 17 x 23 cross-language parity fixture produced:

- maximum absolute error: **1.1920928955078125e-7**
- mean absolute error: **1.1395005827807836e-8**
- allclose at 1e-5: **PASS**

The browser SLIC path still uses the existing v2 structural approximation in this phase. The canonical raw edge map is used for Region Merge evidence.

## Five-case full Browser v3 benchmark

With the complete browser route, including browser-owned preprocessing and SLIC:

- mean processing: **365.6 ms**
- mean initial regions: **647.2**
- mean safe merges: **0.4**
- mean vertices: **1519.6**
- selected regions: **40**
- palette: **8**
- Browser v3 vs Python unguided proxy SSIM: **0.8335**
- Browser v3 vs Python unguided proxy edge IoU: **0.2243**
- Browser v3 vs Railway SSIM: **0.8229**
- Browser v3 vs Railway edge IoU: **0.2068**

For comparison, Browser v2 final was:

- proxy SSIM: **0.8364**
- proxy edge IoU: **0.2188**
- vertices: **1058.8**

v3 therefore slightly improves edge overlap but does not improve overall full-image similarity. This is not sufficient for Railway graduation.

## Canonical-input parity probe

To isolate Region Merge from upstream browser preprocessing, the same five canonical Python cases were exported at the Region Merge input boundary:

- analysis RGBA;
- analysis Lab;
- raw edge;
- structural edge;
- canonical SLIC labels.

Those exact arrays were then passed into Browser v3 `runCanonicalRegionHierarchy()`.

### Result: exact parity

For all five cases, Browser v3 matched Python V2 exactly for:

- safe merge count;
- hierarchy merge count;
- merge evaluation count;
- cut objective;
- normalized visual loss;
- maximum selected hierarchy height;
- final 40-region partition.

Final partition comparison:

- boundary IoU: **1.0000 / 5 cases**
- Browser -> Python region purity: **1.0000**
- Python -> Browser region purity: **1.0000**
- exact boundary map equality: **5 / 5**

Representative exact values include:

| Case | Safe | Hierarchy | Evaluations | Cut objective | Normalized loss | Max height |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Raden | 0 | 628 | 10606 | 0.4932455053 | 0.4232932001 | 0.4770075906 |
| Subaru | 0 | 537 | 8276 | 0.5691127782 | 0.4873283915 | 0.6060536111 |
| Noel | 0 | 789 | 12256 | 0.6977835195 | 0.6420873170 | 0.5474829729 |
| Elizabeth | 0 | 626 | 8955 | 0.4884878157 | 0.4183123771 | 0.5504364025 |
| Night River | 0 | 768 | 13240 | 0.6444579140 | 0.5872407488 | 0.5800207118 |

This proves that the remaining full-browser discrepancy is upstream of Region Merge.

## Automated parity gates

Browser v3 tests now lock:

- canonical SSE color-cost formula;
- canonical boundary histogram quantiles;
- conservative safe-consolidation thresholds;
- deterministic SLIC behavior;
- deterministic complete merge hierarchy;
- Minimal DP hierarchy cut;
- exact Python/Browser merge hierarchy parity on identical inputs;
- canonical Lab edge numerical parity;
- v1 mask-faithful contour contract;
- adaptive SLIC retry;
- 400px large-map stack safety;
- opt-in Browser routing with Railway still default.

Final focused regression:

- **68 passed**
- JavaScript syntax: PASS
- `git diff --check`: PASS

Real Chrome wrapper smoke:

```text
File
 -> browser-fallback-v3
 -> 622 superpixels
 -> full hierarchy
 -> 40-region cut
 -> palette 8
 -> PNG Response
```

PASS.

## Gate result

### Browser Region Merge: PASS

The canonical merge-cost, hierarchy, and Minimal cut stage is considered ported successfully.

### Canonical raw Lab edge: PASS

Cross-language numerical parity is within floating-point noise.

### Full Browser fallback quality: HOLD

The full Browser route does not yet match the Python unguided proxy closely enough.

### Railway graduation: HOLD

Railway remains the final escape hatch.

## New first-bad-stage

The next discrepancy is now definitively upstream:

**structural preprocessing -> structural Lab/edge -> SLIC input fidelity**

Canonical Python V2 performs:

```text
analysis RGB
 -> L0 gradient smoothing
 -> structural RGB
 -> structural Lab
 -> structural Lab edge
 -> SLICO
```

Browser v3 still uses its lighter v2 structural approximation for SLIC.

This changes the initial SLIC partition before the now-canonical Region Merge receives it.

## Browser Fallback v4 target

Do not retune Region Merge or contour first.

v4 should focus on the preprocessing boundary:

1. reproduce or faithfully approximate canonical L0 gradient smoothing in-browser;
2. build structural Lab separately from analysis Lab;
3. use the canonical 3-channel Lab edge map for structural edge evidence;
4. feed SLICO-lite from structural Lab + structural edge;
5. compare Browser SLIC labels directly with Python canonical SLIC labels;
6. rerun Region Merge parity after those inputs converge.

Region Merge v3 should be treated as a fixed downstream contract while v4 works upstream.
