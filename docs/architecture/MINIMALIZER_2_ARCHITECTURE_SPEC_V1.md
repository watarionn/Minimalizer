# Minimalizer 2.0 Architecture Specification v1

Status: Adopted Architecture  
Version: 1.0  
Primary target preset: `minimal`  
Core principle: AI-free visual decomposition and progressive information reduction

This document is the canonical architecture specification for Minimalizer 2.0. Earlier phase documents remain useful as design history, but implementation decisions for the 2.0 core should follow this specification when they conflict.

## 1. Purpose

Minimalizer 2.0 does not directly convert an input image into rectangles or polygons. It progressively decomposes and simplifies visual information:

```text
Pixel
  -> Micro Structure
  -> Superpixel / Initial Region
  -> Merged Region
  -> Simplified Contour
  -> Primitive
  -> Consolidated Palette
  -> Minimal Scene
```

The target is to reconstruct an image with as few colors, visual planes, and simple contours as practical while preserving recognizability.

For character and human images, prioritize:

- composition
- silhouette
- pose
- face and hair as large planes
- torso
- arms and legs
- major clothing masses
- characteristic colors
- large accessories

Aggressively reduce:

- individual hair strands
- fingers
- minor shadows
- highlights
- frills
- tiny decorations
- tiny background fragments
- thin noisy shapes

## 2. Architecture principles

The following are architecture contracts.

1. AI is not a mandatory dependency of the core pipeline.
2. Do not discard information too early.
3. Do not reduce the palette before region formation.
4. Do not fit primitives before region merging.
5. Region Merge is the central quality-determining stage.
6. Never remove a region only because it is small.
7. Never merge regions only because their colors are similar.
8. Characteristic Color analysis is generated once and shared across the pipeline.
9. Do not rerun Region Merge for each preset.
10. Presets cut the same hierarchy at different information levels.
11. Polygon is a valid successful representation, not a failure fallback.
12. Final colors should normally be source-derived colors.
13. Debug mode must not change algorithmic results.
14. Full visual regression is part of the quality architecture, not an optional afterthought.

## 3. Canonical pipeline

```text
Source RGB
 |
 +-- Characteristic Context
 +-- Optional Subject Segmentation
 |
 v
Analysis Resize
 |
 v
ImageBundle
 |
 +-- analysis_rgb
 +-- analysis_lab
 +-- structural_rgb
 +-- structural_lab
 +-- raw edge
 +-- structural edge
 +-- subject probability/confidence
 +-- alpha
 |
 v
Structural Preconditioning
 |
 v
SLICO Oversegmentation
 |
 v
Initial Label Map
 |
 v
Initial Region Annotation
 |
 v
Region Adjacency Graph
 |
 v
Safe Consolidation
 |
 v
Constrained Hierarchical Region Merge
 |
 v
RegionMergeTree
 |
 v
Hierarchy Cut Family
 |
 +-- Detailed
 +-- Balanced
 +-- Minimal
 +-- Ultra Minimal
 |
 v
RegionSelection
 |
 v
Contour Simplification
 |
 v
Primitive Fitting
 |
 v
Palette Consolidation
 |
 v
Importance Analysis / Detail Budget
 |
 v
Scene Assembly
 |
 v
SVG / PNG
```

Regression and Debug span the entire pipeline.

## 4. Recommended package structure

```text
minimalize_engine/
└─ v2/
   ├─ types.py
   ├─ preprocessing.py
   ├─ characteristic.py
   ├─ pipeline.py
   │
   ├─ region_merge/
   │  ├─ types.py
   │  ├─ segmentation.py
   │  ├─ graph.py
   │  ├─ cost.py
   │  ├─ hierarchy.py
   │  └─ cut.py
   │
   ├─ contour/
   │  ├─ types.py
   │  ├─ boundary_graph.py
   │  ├─ simplify.py
   │  └─ validation.py
   │
   ├─ primitive/
   │  ├─ types.py
   │  ├─ candidates.py
   │  ├─ scoring.py
   │  └─ fit.py
   │
   ├─ palette/
   │  ├─ types.py
   │  ├─ sampling.py
   │  ├─ hierarchy.py
   │  └─ consolidate.py
   │
   ├─ detail_budget/
   │  ├─ types.py
   │  ├─ importance.py
   │  └─ budget.py
   │
   └─ regression/
      ├─ types.py
      ├─ runner.py
      ├─ metrics.py
      ├─ compare.py
      └─ debug.py
```

Existing reusable candidates include:

- `subject_segmentation.py`
- `palette/feature_palette.py`
- `characteristic_color_strip.py`
- `analysis/shape_cleanup.py`
- `target_style.py`

Existing shape-level merging must not become the core Region Merge 2.0 implementation.

## 5. Shared core types

```python
RegionId: TypeAlias = int
EdgeKey: TypeAlias = tuple[RegionId, RegionId]
BBox: TypeAlias = tuple[int, int, int, int]  # x0, y0, x1, y1; exclusive max
LabelMap: TypeAlias = NDArray[np.int32]
```

Region IDs are never reused. Every merge creates a new monotonic ID.

## 6. ImageBundle

The earlier name `source_lab` is retired because that array is computed at analysis resolution, not source resolution.

```python
@dataclass(frozen=True, slots=True)
class ImageBundle:
    source_rgb: NDArray[np.uint8]

    analysis_rgb: NDArray[np.uint8]
    structural_rgb: NDArray[np.uint8]

    analysis_lab: NDArray[np.float32]
    structural_lab: NDArray[np.float32]

    edge_raw: NDArray[np.float32]
    edge_structural: NDArray[np.float32]

    subject_prob: NDArray[np.float32] | None = None
    subject_confidence: NDArray[np.float32] | None = None

    alpha: NDArray[np.float32] | None = None

    scale_x: float = 1.0
    scale_y: float = 1.0
```

Rules:

- `analysis_lab` is the source for region color statistics and palette sampling.
- `structural_lab` is used only for segmentation, boundary, and structural analysis.
- Structural smoothing must never directly determine final fill colors.

## 7. Analysis resolution and canonical Lab

Default:

```text
analysis_max_side = 768
```

Images smaller than this are not enlarged. Downsampling uses `INTER_AREA`.

```python
scale_x = source_width / analysis_width
scale_y = source_height / analysis_height
```

Core Lab representation:

```text
CIELAB, D65
L*: 0..100
a*: approximately -128..127
b*: approximately -128..127
```

OpenCV's uint8 Lab encoding must not leak into the core API.

## 8. Characteristic Context

Characteristic analysis is computed once and shared by Region Merge and Palette Consolidation.

```python
@dataclass(frozen=True, slots=True)
class CharacteristicAnchor:
    id: int
    lab: NDArray[np.float64]
    confidence: float


@dataclass(frozen=True, slots=True)
class CharacteristicContext:
    anchors: tuple[CharacteristicAnchor, ...]
    anchor_map: NDArray[np.int32] | None = None
    confidence_map: NDArray[np.float32] | None = None
```

`anchor_map` is at analysis resolution and uses `-1` for no anchor.

Existing feature-palette and characteristic-strip logic should be reused instead of introducing another anchor detector.

### 8.1 CharacteristicSupport

A region may contain support for multiple anchors after merging, so a single `anchor_id` is insufficient.

```python
@dataclass(frozen=True, slots=True)
class CharacteristicSupport:
    anchor_id: int
    support_mass: float
    confidence: float
```

Region convenience properties may expose `primary_anchor_id` and `primary_anchor_confidence`, but the full support set remains available.

## 9. RegionAnnotation

```python
@dataclass(frozen=True, slots=True)
class RegionAnnotation:
    characteristic_supports: tuple[CharacteristicSupport, ...] = ()
    semantic_tag: str | None = None
    semantic_confidence: float = 0.0
```

Annotations are produced after initial labels exist and before the initial RegionGraph is built.

## 10. Structural Preconditioning

Default structural smoother:

```text
L0 Gradient Smoothing
lambda = 0.010
kappa = 2.0
```

Initial calibration range for lambda:

```text
0.006, 0.008, 0.010, 0.012, 0.015
```

Structural smoothing is used to suppress microtexture while preserving important edges. It is never used as a final rendering operation.

Fallback smoother support may exist, but silent fallback should not be the default because it harms reproducibility.

## 11. Edge maps

Keep two normalized edge maps:

- Raw Edge: rescues important boundaries weakened by smoothing.
- Structural Edge: represents major structural boundaries after microtexture suppression.

Use Lab-channel gradients rather than grayscale only. Normalize robustly, initially around the 99th percentile, to `0..1`.

## 12. Oversegmentation

Default:

```text
SLICO
```

Alternatives:

- MSLIC, comparison candidate
- SLIC, explicit compatibility option
- Felzenszwalb, experimental comparison provider

Oversegmentation does not attempt to produce final meaningful regions. Its goal is to preserve enough boundary candidates for Region Merge to make informed decisions.

### 12.1 Superpixel target

```python
target_superpixels = analysis_area / 900
```

General clamp:

```text
400..1200
```

For small images, also ensure average superpixel area does not fall below approximately 64 px².

Approximate OpenCV region size:

```python
region_size = round(sqrt(analysis_area / target_superpixels))
```

Initial SLIC iteration count: `10`.

### 12.2 Connectivity

Use 4-connectivity.

Do not use `enforceLabelConnectivity()` as the standard cleanup because it absorbs small components before Region Merge can evaluate them.

Instead:

1. split physically disconnected components that share a label,
2. sequentially relabel to `0,1,2,...`,
3. store as `np.int32`.

### 12.3 Adaptive retry

If structural edge coverage is below `0.75`, allow one finer retry using approximately:

```text
region_size * 0.80
```

Keep the retry only if edge coverage improves without pathological region explosion.

## 13. RegionStats

```python
@dataclass(frozen=True, slots=True)
class RegionStats:
    id: RegionId
    pixel_count: int

    sum_lab: NDArray[np.float64]
    sum_sq_lab: NDArray[np.float64]

    sum_x: float
    sum_y: float
    sum_xx: float
    sum_yy: float
    sum_xy: float

    bbox: BBox
    perimeter_px: float

    hull_xy: NDArray[np.float32]
    hull_area: float

    subject_prob_sum: float = 0.0
    subject_confidence_sum: float = 0.0

    characteristic_supports: tuple[CharacteristicSupport, ...] = ()

    semantic_tag: str | None = None
    semantic_confidence: float = 0.0
```

Derived properties include:

- `mean_lab`
- `lab_sse`
- `color_variance`
- `centroid`
- `subject_ratio`
- `subject_confidence`
- `solidity`
- `elongation`
- `principal_axis`

Use pixel-center coordinates `x + 0.5`, `y + 0.5` for moments.

RegionStats must not contain source-region lineage sets. Lineage belongs to the merge tree.

## 14. RegionEdge

```python
@dataclass(frozen=True, slots=True)
class RegionEdge:
    a: RegionId
    b: RegionId
    shared_boundary_px: float
    raw_gradient_hist: NDArray[np.int64]
    structural_gradient_hist: NDArray[np.int64]
    alpha_boundary_fraction: float = 0.0
```

Default gradient histograms use approximately 32 bins across `0..1`. Histograms can be added during merges, preserving useful boundary quantile information better than means alone.

## 15. RegionGraph

```python
@dataclass(slots=True)
class RegionGraph:
    nodes: dict[RegionId, RegionStats]
    edges: dict[EdgeKey, RegionEdge]
    adjacency: dict[RegionId, set[RegionId]]
    initial_labels: LabelMap
    next_region_id: RegionId
```

`initial_labels` is immutable throughout hierarchical merging.

`apply_merge()` is the only function allowed to mutate graph nodes, edges, adjacency, the next ID, and merge-tree state.

## 16. Region Merge concept

Region Merge is not a color-similarity merger. It estimates the visual information loss caused by removing an existing boundary.

```python
@dataclass(frozen=True, slots=True)
class MergeEvaluation:
    allowed: bool
    total_cost: float

    color_cost: float
    boundary_cost: float
    structure_cost: float
    topology_cost: float
    anchor_cost: float
    geometry_cost: float

    soft_protection: float
    redundancy_reward: float

    blocked_by: tuple[str, ...] = ()
```

### 16.1 Merge weights

Initial calibration:

```text
0.30 Color
0.25 Boundary
0.15 Structure
0.10 Topology
0.10 Anchor
0.10 Geometry
-0.15 Redundancy
+ Soft Protection
```

```python
base_cost = (
    0.30 * color_cost
    + 0.25 * boundary_cost
    + 0.15 * structure_cost
    + 0.10 * topology_cost
    + 0.10 * anchor_cost
    + 0.10 * geometry_cost
)

total_cost = clamp(
    base_cost + soft_protection - 0.15 * redundancy_reward,
    0.0,
    1.35,
)
```

## 17. Color Cost

Use Ward-style increase in squared error:

```text
DeltaSSE = (nA * nB / (nA + nB)) * ||muA - muB||²
```

Normalize per merged pixel:

```text
Ec = DeltaSSE / (nA + nB)
```

Then:

```text
Ccolor = 1 - exp(-Ec / tau)
```

Initial `tau = 25`.

This naturally makes a tiny shading fragment easier to absorb than two equally large distinct masses while still allowing other protection terms to preserve important small accents.

## 18. Boundary Cost

Approximate gradient quantiles from edge histograms.

Structural strength uses roughly q75/q90. Raw rescue uses stronger quantiles around q90/q98.

```python
boundary_cost = max(
    structural_strength,
    0.35 * raw_strength,
)
```

Strong edge alone is not a hard barrier.

## 19. Hard Barriers

A hard barrier returns:

```python
allowed = False
total_cost = inf
```

Initial hard barriers:

### 19.1 Subject/background

High-confidence subject on one side and high-confidence background on the other:

```text
subject >= 0.80
background <= 0.20
confidence >= 0.80
```

### 19.2 Alpha

Initial threshold:

```text
alpha_boundary_fraction >= 0.80
```

### 19.3 Characteristic anchor conflict

Distinct high-confidence characteristic supports with approximately:

```text
DeltaE >= 18
```

### 19.4 Semantic conflict

Only with high-confidence semantic information, initially around `0.90`.

Serializable configuration uses:

```python
semantic_hard_pairs: tuple[tuple[str, str], ...]
```

not nested frozensets.

## 20. Soft Protection and Redundancy

Soft Protection includes major-mass protection and characteristic-accent protection. Initial total cap is about `0.35`.

Redundancy rewards evidence that a boundary is unnecessary, especially when a region is:

- small,
- similar in color,
- separated by a weak edge,
- substantially enclosed by the neighbor.

Smallness alone never justifies removal.

## 21. Safe Consolidation

Before general hierarchy construction, allow only extremely safe consolidation of obvious oversegmentation fragments.

Initial calibration:

```text
area ratio <= 0.0008
color cost <= 0.08
boundary cost <= 0.15
structure cost <= 0.05
anchor cost <= 0.05
topology cost <= 0.25
shared boundary ratio >= 0.35
soft protection <= 0.02
```

This is not a generic micro-region deletion pass.

## 22. RegionMergeTree

```python
@dataclass(frozen=True, slots=True)
class MergeTreeNode:
    region_id: RegionId
    left_id: RegionId | None
    right_id: RegionId | None
    raw_merge_cost: float
    hierarchy_height: float
    stage: str
    stats: RegionStats


@dataclass(slots=True)
class RegionMergeTree:
    nodes: dict[RegionId, MergeTreeNode]
    leaf_ids: frozenset[RegionId]
    roots: set[RegionId]
    merge_sequence: list[RegionId]
```

The result may remain a forest because hard barriers can prevent a single root. Do not create an artificial root.

Hierarchy height is monotonic:

```python
hierarchy_height = max(
    raw_merge_cost,
    left.hierarchy_height,
    right.hierarchy_height,
)
```

## 23. RegionMergeResult is preset-independent

The earlier API where `run_region_merge()` accepted a preset is retired. It contradicted the single-hierarchy architecture.

```python
@dataclass(frozen=True, slots=True)
class RegionMergeResult:
    initial_labels: LabelMap
    tree: RegionMergeTree
    initial_region_count: int
    safe_merge_count: int
    hierarchy_merge_count: int
    metrics: RegionMergeMetrics
```

```python
def run_region_merge(
    bundle: ImageBundle,
    *,
    annotations: Mapping[RegionId, RegionAnnotation] | None,
    config: RegionMergeConfig,
) -> RegionMergeResult:
    ...
```

## 24. Hierarchy Cut

All presets share one RegionMergeTree.

Initial soft region-count targets:

```text
Ultra Minimal   25..45
Minimal         40..70
Balanced        65..110
Detailed        100..170
```

Initial maximum hierarchy heights:

```text
Ultra Minimal   0.85
Minimal         0.70
Balanced        0.55
Detailed        0.40
```

Targets are guidance, not commands. Critical structure is never destroyed solely to hit a target count.

### 24.1 Visual loss correction

Hierarchy height and cumulative visual loss serve different purposes.

`hierarchy_height` is the maximum local danger in a subtree and acts as a cut guard.

Optimization uses cumulative merge loss so a large subtree with many merges is not undercounted.

```python
merge_loss = (
    node.raw_merge_cost
    * sqrt(node_area_ratio)
    * protection_weight
)

cumulative_loss(node) = (
    cumulative_loss(left)
    + cumulative_loss(right)
    + merge_loss(node)
)
```

Leaf cumulative loss is zero.

### 24.2 Cut objective

```python
objective = (
    visual_loss
    + complexity_lambda * normalized_region_count
    + target_weight * target_penalty
)
```

Initial `target_weight = 0.25`.

Tree-DP with Pareto pruning is the preferred implementation.

### 24.3 Nested presets

Preset cuts must be nested along ancestry:

```text
Detailed -> Balanced -> Minimal -> Ultra Minimal
```

A coarser preset can only replace detailed nodes with their ancestors, never jump to unrelated branches.

```python
@dataclass(frozen=True, slots=True)
class HierarchyCutFamily:
    detailed: HierarchyCut
    balanced: HierarchyCut
    minimal: HierarchyCut
    ultra_minimal: HierarchyCut
```

## 25. RegionSelection

Preset-specific labels do not belong in RegionMergeResult.

```python
@dataclass(frozen=True, slots=True)
class RegionSelection:
    preset: str
    cut: HierarchyCut
    labels: LabelMap
    region_ids: frozenset[RegionId]
```

```python
def materialize_region_selection(
    merge_result: RegionMergeResult,
    cut: HierarchyCut,
) -> RegionSelection:
    ...
```

Materialization builds a leaf-to-selected-region LUT and applies it to the immutable initial label map. This is the first time the selected pixel labels are materialized after initial segmentation.

## 26. Contour Simplification

Input is `ImageBundle + RegionMergeResult + RegionSelection`.

Contour Simplification must preserve region topology while removing unnecessary boundary detail.

Do not run RDP independently on each region polygon because shared boundaries would diverge, creating gaps and overlaps.

### 26.1 BoundaryGraph

```python
@dataclass(slots=True)
class BoundaryGraph:
    vertices: dict[int, BoundaryVertex]
    chains: dict[int, BoundaryChain]
    region_chains: dict[RegionId, list[OrientedChainRef]]
```

A shared boundary chain is simplified once and reused by both neighboring regions.

Protect:

- multi-region junctions,
- image-border anchors,
- strong structural corners,
- high-protection characteristic/semantic boundaries.

Use 4-connectivity consistently.

### 26.2 Simplification flow

```text
Boundary Extraction
  -> Boundary Graph
  -> Protected Anchor Detection
  -> Micro Cleanup
  -> Topology-aware RDP
  -> Candidate Ladder
  -> Validation
  -> Fallback
```

Candidate epsilon ladder:

```text
1.00, 0.75, 0.50, 0.25, 0.00
```

Initial epsilon ratios:

```text
Ultra Minimal   0.030
Minimal         0.022
Balanced        0.014
Detailed        0.008
```

Clamp approximately `0.75..18 px`.

### 26.3 Contour guards

Required guards:

- topology unchanged,
- no self intersections,
- area-change limit,
- IoU limit,
- centroid-shift limit,
- directional-coverage limit,
- shared-boundary consistency.

Use 8-direction radial coverage:

```text
0, 45, 90, 135, 180, 225, 270, 315 degrees
```

This is the primary generic protection against the known face-outline gouging problem.

Face candidates use approximately `0.65` of the normal directional-loss allowance. Major masses use approximately `0.80` of the normal allowance.

Contour Simplification never removes a region.

## 27. Primitive Fitting

Initial primitive set:

- Polygon
- Oriented Rectangle
- Ellipse
- Capsule
- Trapezoid

Polygon is always a valid baseline candidate.

The purpose is not to maximize primitive conversion rate. Replace a polygon only when the simpler primitive produces enough complexity reduction with sufficiently small visual error.

### 27.1 Candidate metrics

Evaluate candidates using a common raster comparison against the simplified contour:

- IoU
- undercoverage
- overcoverage
- neighbor leakage
- critical-neighbor leakage
- centroid shift
- directional underfit/overfit
- symmetric boundary distance
- protected-boundary error
- junction/contact retention
- complexity gain

Initial critical-neighbor leakage limit is about `0.01`.

### 27.2 Complexity model

Initial calibration:

```text
Rect       1.00
Ellipse    1.10
Trapezoid  1.15
Capsule    1.20
Polygon    1.00 + 0.18 * vertex_count
```

Initial primitive adoption margin: `0.03`.  
Initial minimum complexity gain: `0.35`.

Candidates compete using the same scoring framework. There is no fixed rule saying rectangle is preferred first.

### 27.3 Semantic hints

Semantic hints only adjust candidates or guards. The pipeline must function without them.

Examples with high-confidence hints:

- Face: ellipse/polygon favored, rectangle and capsule disabled.
- Hair: polygon/trapezoid favored.
- Limbs: capsule/polygon favored.
- Torso/clothes: trapezoid/rect/polygon favored.

## 28. Palette Consolidation

Final palette sampling uses:

```text
RegionSelection.labels + ImageBundle.analysis_lab
```

Do not resample from primitive geometry because primitive overdraw would contaminate region color statistics.

### 28.1 Representative color

Default representative is a robust medoid derived from deterministic samples of the original analysis-resolution region pixels.

Initial maximum samples per region: `1024`.

Avoid creating new colors by averaging cluster colors. Palette entries should normally be colors actually observed in the source image.

### 28.2 Palette hierarchy

Palette consolidation also uses hierarchical merging, but unlike Region Merge it has no spatial adjacency restriction. Distant regions can share the same palette color.

Initial palette merge cost:

```text
0.65 Color Difference
0.15 Anchor
0.10 Semantic
0.10 Relationship Risk
```

Use CIEDE2000 as the default intended color-distance metric.

### 28.3 Characteristic protection

Initial high-confidence anchor threshold: `0.80`.

Anchor equivalence:

```text
DeltaE <= 6
```

Clearly distinct anchors:

```text
DeltaE >= 12
```

Distinct high-confidence anchors are normally reserved as separate palette colors.

### 28.4 Color relationships

Explicitly preserve important pairwise relationships, including:

- adjacent major regions,
- characteristic boundaries,
- subject/background relationships,
- semantic boundaries,
- major masses.

Store original `DeltaE`, original `DeltaL`, and relationship protection.

Contrast collapse example:

```text
original DeltaE >= 12
assigned DeltaE <= 5
```

Protected relationships reject such collapse.

Where original lightness difference is significant, initially around `|DeltaL| >= 12`, protected relationships should not fully reverse the light/dark ordering.

### 28.5 Palette targets

Soft target ranges:

```text
Ultra Minimal   4..6
Minimal         6..9
Balanced        8..12
Detailed        12..18
```

These are not fixed-K constraints. Protected colors may force budget overflow.

Palette modes:

```text
auto
characteristic
area
fixed
```

Default: `auto`.

If a cut breaks a critical relationship, repair by splitting the problematic palette cluster. Do not invent colors via hue or saturation edits.

## 29. Detail Budget

Detail Budget is separate from Hierarchy Cut.

Hierarchy Cut controls structural region information. Detail Budget controls final visual-detail information after geometry and palette decisions.

### 29.1 Coverage-safety correction

Core partition regions cannot simply be hidden. Hiding them can create transparent holes.

Formal detail actions:

```text
RETAIN
COLLAPSE_STYLE
HIDE_OVERLAY
```

- `RETAIN`: normal visible shape.
- `COLLAPSE_STYLE`: keep coverage geometry, but assign the same palette entry as a compatible fallback neighbor so the visual boundary disappears.
- `HIDE_OVERLAY`: only valid for explicit overlay shapes with a known coverage parent.

Core partition regions do not use `HIDE_OVERLAY`.

### 29.2 Importance

Initial importance formula:

```text
0.25 Area
0.20 Structural
0.20 Characteristic
0.15 Contrast
0.10 Semantic
0.10 Pose
```

Protect:

- structural masses,
- high characteristic support,
- silhouette contributors,
- important pose structures,
- critical semantic structures.

Never collapse the last strong support for a high-confidence characteristic anchor.

### 29.3 Shape-count semantics

Track both:

```text
draw_geometry_count
visual_group_count
```

Because style-collapsed adjacent coverage shapes may still need separate geometry paths, the primary Detail Budget should use `visual_group_count` rather than raw geometry count.

Initial visual-group soft ranges:

```text
Ultra Minimal   20..40
Minimal         35..60
Balanced        55..95
Detailed        90..150
```

Budget overflow is allowed when protection makes a target unsafe.

## 30. Scene Assembly contract

Detailed rendering policy is outside the v1 core, but the interfaces need a minimal contract.

```python
@dataclass(frozen=True, slots=True)
class SceneShape:
    region_id: RegionId
    geometry: PrimitiveGeometry
    palette_id: int
    visible: bool = True


@dataclass(frozen=True, slots=True)
class SceneModel:
    width: int
    height: int
    shapes: tuple[SceneShape, ...]
    palette: tuple[PaletteEntry, ...]
```

Style collapse is represented by a palette-ID override while coverage remains present.

Deferred renderer-specific topics:

- z-order optimization,
- exact SVG path union,
- anti-hairline rendering strategy,
- primitive-overlap rendering policy.

These do not block Region Merge 2.0 implementation.

## 31. Regression and Debug System

Official corpus name:

```text
Minimalizer 2.0 Visual Regression Corpus
```

Corpus v1 contains the 18 approved geometric-reference pairs:

1. Kikirara-Vivi
2. Isaki-Riona
3. Koganei-Niko
4. Vestia-Zeta
5. Todoroki-Hajime
6. Shishiro-Botan
7. Shiori-Novella
8. Natsuiro-Matsuri
9. Otonose-Kanade
10. Mori-Calliope
11. Momosuzu-Nene
12. Koseki-Bijou
13. Kobo-Kanaeru
14. Houshou-Marine
15. Hakos-Baelz
16. Gigi-Murin
17. Aki-Rosenthal
18. Raora-Panthera

Main regression preset: `minimal`.

### 31.1 Three layers

1. Invariant Regression: mechanical contracts, hard failures.
2. Metric Regression: quality shifts, warnings or failures depending on severity.
3. Visual Regression: human comparison against approved references and baselines.

Approved Reference and Approved Baseline are different concepts:

- Approved Reference: human-created target style example.
- Approved Baseline: approved Minimalizer implementation run.

Baselines are never auto-promoted.

### 31.2 Run manifest

Every regression run records at least:

- run ID,
- timestamp,
- code revision,
- config hash,
- Python version,
- OpenCV version,
- platform,
- preset,
- complete phase configs,
- source hash,
- reference hash.

### 31.3 Debug artifacts

Debug stage views should include:

```text
Source
Analysis
Structural
Raw Edge
Structural Edge
Superpixels
RAG
Merge Hierarchy
Hierarchy Cut
Merged Regions
Contour
Primitive
Palette
Budget
Final
Reference
```

Artifact levels:

```text
none
summary
standard
full
```

Normal regression uses `standard`.

### 31.4 Decision logs

Each major decision must be explainable using the values actually used by the core algorithm.

Examples:

- Why did these regions merge?
- Why was this boundary protected?
- Why was this contour candidate rejected?
- Why did this region remain polygonal?
- Why was an ellipse selected?
- Why was this palette color reserved?
- Why was this detail collapsed?

Debug mode is observational only and must not change the output.

### 31.5 Smoke corpus

Initial smoke candidates:

- Kikirara-Vivi
- Otonose-Kanade
- Hakos-Baelz

These cover similar-color hair with a distinct accent, white clothing with structural accents, and multicolor structure with small characteristic colors.

### 31.6 Known-issue regressions

Maintain dedicated cases for at least:

```text
face_right_gouge
thin_rectangle_noise
characteristic_accent_loss
hair_skin_color_collapse
subject_background_leakage
```

### 31.7 Main metrics

Track at least:

- initial region count,
- selected region count,
- micro-region ratio,
- thin-region ratio,
- vertex count,
- contour IoU,
- maximum directional loss,
- primitive conversion rate,
- polygon fallback rate,
- neighbor leakage,
- palette count,
- characteristic-anchor recall,
- contrast retention,
- lightness-flip count,
- visual-group count,
- total complexity,
- subject/background leakage,
- runtime.

No single metric is a sufficient quality score.

Where reliable semantic hints exist, additional character-readability metrics may include:

- head readability,
- hair/face separation,
- torso readability,
- limb separation,
- pose preservation,
- signature-color retention,
- accessory retention.

`None` is valid when semantic information is unavailable.

### 31.8 Performance

Track phase timings separately. Initial warning candidate is roughly `1.5x` baseline runtime. Performance must never disable quality guards automatically.

### 31.9 Regression execution policy

Full 18-case visual regression is primarily a local/manual operation. Normal lightweight validation should focus on:

- unit tests,
- synthetic regression,
- invariant tests.

Do not commit large quantities of generated regression PNGs or full debug artifacts to Git.

## 32. Public APIs

```python
def prepare_image_bundle(
    source_rgb: NDArray[np.uint8],
    *,
    subject_prob=None,
    subject_confidence=None,
    alpha=None,
    config: RegionMergeConfig,
) -> ImageBundle:
    ...
```

```python
def oversegment(
    bundle: ImageBundle,
    *,
    config: RegionMergeConfig,
) -> LabelMap:
    ...
```

```python
def annotate_initial_regions(
    bundle: ImageBundle,
    labels: LabelMap,
    *,
    characteristic: CharacteristicContext | None = None,
    semantic=None,
) -> Mapping[RegionId, RegionAnnotation]:
    ...
```

```python
def build_region_graph(
    bundle: ImageBundle,
    labels: LabelMap,
    *,
    annotations=None,
    config: RegionMergeConfig,
) -> RegionGraph:
    ...
```

```python
def run_region_merge(
    bundle: ImageBundle,
    *,
    annotations=None,
    config: RegionMergeConfig,
) -> RegionMergeResult:
    ...
```

```python
def build_cut_family(
    merge_result: RegionMergeResult,
    *,
    policies: Mapping[str, CutPolicy],
) -> HierarchyCutFamily:
    ...
```

```python
def materialize_region_selection(
    merge_result: RegionMergeResult,
    cut: HierarchyCut,
) -> RegionSelection:
    ...
```

```python
def simplify_region_contours(
    bundle: ImageBundle,
    merge_result: RegionMergeResult,
    selection: RegionSelection,
    *,
    config: ContourSimplificationConfig,
) -> ContourSimplificationResult:
    ...
```

```python
def fit_region_primitives(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    *,
    config: PrimitiveFitConfig,
) -> PrimitiveFittingResult:
    ...
```

```python
def consolidate_palette(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    primitive_result: PrimitiveFittingResult,
    *,
    characteristic: CharacteristicContext | None = None,
    config: PaletteConfig,
) -> PaletteConsolidationResult:
    ...
```

```python
def analyze_shape_importance(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    primitive_result: PrimitiveFittingResult,
    palette_result: PaletteConsolidationResult,
    *,
    config: DetailBudgetConfig,
) -> Mapping[RegionId, DetailShapeInfo]:
    ...
```

```python
def apply_detail_budget(
    shape_info,
    palette_result,
    *,
    policy: DetailBudgetPolicy,
    config: DetailBudgetConfig,
) -> DetailBudgetResult:
    ...
```

## 33. Full preset and image APIs

```python
@dataclass(frozen=True, slots=True)
class PresetPipelineResult:
    preset: str
    selection: RegionSelection
    contour: ContourSimplificationResult
    primitives: PrimitiveFittingResult
    palette: PaletteConsolidationResult
    detail_budget: DetailBudgetResult
    scene: SceneModel
```

```python
def run_preset_pipeline(
    bundle: ImageBundle,
    merge_result: RegionMergeResult,
    cut: HierarchyCut,
    *,
    characteristic: CharacteristicContext | None,
    config: PipelineConfig,
) -> PresetPipelineResult:
    ...
```

```python
@dataclass(frozen=True, slots=True)
class MinimalizerV2Result:
    bundle: ImageBundle
    characteristic: CharacteristicContext | None
    region_merge: RegionMergeResult
    cut_family: HierarchyCutFamily
    presets: Mapping[str, PresetPipelineResult]
```

```python
def minimalize_v2(
    source_rgb: NDArray[np.uint8],
    *,
    presets: tuple[str, ...] = ("minimal",),
    config: PipelineConfig | None = None,
) -> MinimalizerV2Result:
    ...
```

## 34. PipelineConfig

```python
@dataclass(frozen=True, slots=True)
class PipelineConfig:
    region_merge: RegionMergeConfig
    contour: ContourSimplificationConfig
    primitive: PrimitiveFitConfig
    palette: PaletteConfig
    detail_budget: DetailBudgetConfig
```

All config objects must be JSON-serializable for manifests and reproducibility.

Preset names are shared across phases:

```text
ultra_minimal
minimal
balanced
detailed
```

Each phase still owns separate numeric calibration parameters. One global numeric detail value must not silently replace phase-specific policies.

## 35. Phase responsibility matrix

### Structural Preconditioning

Does:
- suppress microtexture for analysis.

Does not:
- reduce palette,
- merge regions,
- remove shapes.

### Oversegmentation

Does:
- collect important boundary candidates.

Does not:
- absorb small regions by policy,
- decide final regions.

### Region Merge

Does:
- decide which boundaries can safely disappear.

Does not:
- fit primitives,
- determine final palette.

### Hierarchy Cut

Does:
- select how far the common merge hierarchy is used.

Does not:
- arbitrarily delete regions.

### Contour Simplification

Does:
- remove unnecessary contour detail.

Does not:
- merge regions,
- perform primitive fitting.

### Primitive Fitting

Does:
- simplify geometry representation.

Does not:
- remove regions,
- determine final colors.

### Palette Consolidation

Does:
- simplify color relationships and assignments.

Does not:
- alter geometry.

### Detail Budget

Does:
- reduce final visual-detail differences in a coverage-safe manner.

Does not:
- rerun Region Merge,
- create uncovered holes by hiding core coverage regions.

## 36. Global invariants

The following require automated tests.

1. `initial_labels` never changes during Region Merge.
2. Region IDs are never reused.
3. Region adjacency is symmetric.
4. Edge keys are canonical.
5. No self edge exists in RegionGraph.
6. Every active RegionStats has `pixel_count > 0`.
7. All required internal statistics remain finite.
8. Region color statistics come from `analysis_lab`.
9. `structural_lab` never directly determines final color.
10. Shared contour boundaries agree for both neighboring regions.
11. Simplified contours have no invalid self intersections.
12. Contour Simplification does not reduce region count.
13. Primitive Fitting does not remove regions.
14. Critical neighbor leakage remains under the configured guard.
15. High-confidence characteristic anchors cannot silently disappear.
16. Every final retained region has a palette assignment.
17. Detail Budget cannot create coverage holes in core regions.
18. Debug on/off produces identical algorithmic output.
19. Same input and same config produce deterministic results.
20. Preset region hierarchy remains nested.

## 37. Cross-phase contradictions resolved in v1

### A. `source_lab` naming

Problem: the name suggested source resolution while the array was actually analysis-resolution Lab.

Resolution: rename to `analysis_lab`.

### B. Preset inside Region Merge

Problem: `run_region_merge(preset=...)` contradicted the rule that all presets share one merge tree.

Resolution: Region Merge is preset-independent. Presets begin at Hierarchy Cut.

### C. `merged_labels` inside RegionMergeResult

Problem: selected labels depend on the hierarchy cut.

Resolution:

```text
RegionMergeResult = shared hierarchy
RegionSelection   = preset-specific labels
```

### D. Hierarchy visual loss undercounting

Problem: using only selected-node hierarchy height undercounted cumulative information loss in large subtrees.

Resolution: use cumulative subtree merge loss for the objective, while hierarchy height remains the hard cut guard.

### E. Single characteristic anchor per region

Problem: merged regions can retain evidence from multiple characteristic colors.

Resolution: use `tuple[CharacteristicSupport, ...]` and optional primary-anchor convenience properties.

### F. Characteristic recomputation

Problem: recalculating anchors separately for Region Merge and Palette could produce conflicting identities.

Resolution: share one `CharacteristicContext` across the whole pipeline.

### G. Palette color source

Problem: resampling colors from primitive geometry can include overdraw pixels.

Resolution: derive representative colors only from `RegionSelection.labels + analysis_lab`.

### H. Detail Budget coverage holes

Problem: hiding an ordinary partition region can create transparency holes.

Resolution: core regions use `COLLAPSE_STYLE`, while only explicit overlay shapes may use `HIDE_OVERLAY`.

### I. Shape count ambiguity

Problem: geometry paths can remain separate after visual style collapse.

Resolution: track both `draw_geometry_count` and `visual_group_count`; budget mainly against visual groups.

### J. Config serialization

Problem: nested frozensets are awkward for JSON manifests.

Resolution: use canonicalized tuple pairs for semantic hard-pair configuration.

### K. Initial annotation timing

Problem: Characteristic Context existed but its projection into initial regions was not explicitly placed in the pipeline.

Resolution:

```text
Oversegmentation
  -> annotate_initial_regions()
  -> RegionGraph
```

### L. Independent preset optimization

Problem: independent preset cuts could produce non-nested structures.

Resolution: generate a `HierarchyCutFamily` under nested constraints from detailed to coarse.

## 38. Calibration parameters, not architecture contracts

The following are expected to change through the 18-case corpus without requiring an architecture version bump:

- L0 lambda,
- superpixel density,
- merge weights,
- merge thresholds,
- color SSE tau,
- hull-inflation tau,
- thin-neck tau,
- cut lambdas,
- cut target ranges,
- contour epsilon,
- contour guards,
- primitive guards,
- primitive complexity weights,
- palette target ranges,
- palette DeltaE thresholds,
- importance weights,
- Detail Budget thresholds.

Architecture-version changes are appropriate for modifications to:

- pipeline order,
- phase responsibilities,
- core data models,
- shared-boundary architecture,
- RAG architecture,
- merge-tree architecture,
- source-color semantics,
- preset shared-hierarchy model,
- coverage-safety model.

## 39. Implementation order

### Phase I: Core types

Implement:

- `ImageBundle`
- `CharacteristicSupport`
- `RegionAnnotation`
- `RegionStats`
- `RegionEdge`
- `RegionGraph`
- merge-tree types

### Phase II: Preprocessing / Oversegmentation

Implement:

- resize,
- canonical Lab conversion,
- L0 structural copy,
- edge maps,
- SLICO,
- connectivity split.

### Phase III: Initial RAG

Implement:

- RegionStats creation,
- RegionEdge creation,
- adjacency construction.

### Phase IV: Region Merge

Implement:

- merge costs,
- hard barriers,
- safe consolidation,
- hierarchical merging.

### Phase V: Hierarchy Cut

Implement:

- cumulative visual loss,
- nested cut family,
- RegionSelection materialization.

### Phase VI: Contour

Implement:

- BoundaryGraph,
- shared-boundary simplification,
- guards.

### Phase VII: Primitive

Implement:

- candidate generation,
- candidate validation,
- scoring and selection.

### Phase VIII: Palette

Implement:

- deterministic medoid sampling,
- palette hierarchy,
- relationship validation and repair.

### Phase IX: Importance / Detail Budget

Implement:

- importance analysis,
- style collapse,
- coverage-safe budget processing.

### Phase X: Regression / Debug

Minimal regression infrastructure begins with Phase I and grows with each phase. It is not deferred until the end.

## 40. First implementation slice

The first implementation slice is:

```text
types.py
+ graph.py
```

Required initial unit tests:

- RegionStats generation,
- RAG construction,
- adjacency symmetry,
- edge histogram construction,
- `merge_region_stats`,
- `merge_region_edges`,
- `apply_merge`,
- monotonic Region IDs,
- immutable `initial_labels`.

Do not proceed into contour, primitive, or palette implementation before this slice is stable.

## 41. Minimalizer 2.0 core completion definition

The architecture is considered implemented when the following pipeline connects with consistent contracts:

```text
Source
  -> SLICO
  -> RAG
  -> Region Merge Tree
  -> Nested Hierarchy Cut
  -> Shared Boundary Contour
  -> Primitive Fitting
  -> Palette Consolidation
  -> Coverage-safe Detail Budget
  -> Scene Model
```

Quality gates:

- Synthetic Suite passes.
- Full 18-case corpus completes.
- Hard invariant failures = 0.
- No major loss of high-confidence characteristic anchors.
- No critical subject/background leakage accidents.
- Known-issue regressions pass.
- Current Minimalizer vs Minimalizer 2.0 human A/B review is completed.

Pixel-perfect agreement with the approved references is not required.

## 42. Final architecture principle

Minimalizer 2.0 quality is determined less by how cleverly it can draw shapes than by how correctly it decides what information can be discarded.

Each phase has one principal role:

```text
Structural Preconditioning
  = quiet micro detail

Oversegmentation
  = collect decision material

Region Merge
  = remove unnecessary boundaries

Hierarchy Cut
  = choose structural information level

Contour Simplification
  = reduce boundary information

Primitive Fitting
  = simplify geometry representation

Palette Consolidation
  = simplify color relationships

Detail Budget
  = reduce final visual detail safely

Regression / Debug
  = detect what changed, where, and why
```

Minimalizer 2.0 therefore does not try to make the image small as early as possible. It first preserves enough evidence, then removes information progressively where the evidence says removal is safe.
