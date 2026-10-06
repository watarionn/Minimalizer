# SA7.42 Precedent Assimilation Plan — 2026-10-06

Status: ADOPTED CROSS-PHASE INTEGRATION PLAN
Canonical continuation: SA7.42 Multi-Component Background Field Geometry

## Purpose

Minimalizer should not treat CLIPasso / CLIPascene, AdaVec, LIVE, Primitive, Geometrize, StarVector, SuperSVG, and LayerPeeler as isolated SA7.42 tricks.

Their useful ideas belong to different semantic-abstraction phases. This plan maps each precedent into the existing SA2-SA10 architecture while preserving all already-adopted safety contracts.

This is an augmentation plan, not a rewrite of completed history.

## Global boundaries

- No generative img2img / fill / inpainting / missing-content redraw.
- Golden and Browser fallback v12 remain evaluation-only.
- External models/repositories may provide observer/advisor evidence but do not become semantic/render authority by default.
- No GC001-specific production coordinates, colors, masks, or hand-tuned exceptions.
- Deterministic source-only rules remain the production default.
- Existing Feature Survival, face-neutralization, anatomy, topology, source-coverage, expansion, and overlap guards remain hard constraints.
- A precedent-derived method must pass synthetic regressions, ZeroBase, fresh canonical hard gates, and visual comparison before adoption.

## Cross-phase placement

### SA2 Evidence Adapter

Best-fit precedents:
- SuperSVG
- LayerPeeler
- LIVE

Assimilation:
- add optional region/layer evidence derived from superpixel-like grouping and connected layer decomposition;
- preserve provenance so these remain evidence rather than semantic authority;
- represent disconnected components explicitly instead of collapsing one palette/role to one raster region;
- retain ordering/occlusion evidence where source-supported.

Why here:
these methods are strongest at discovering candidate regions/layers before Minimalizer decides what they mean.

Immediate relevance to SA7.42:
the background extractor must stop conflating a palette cluster with one connected component.

### SA3 Importance / Policy Engine

Best-fit precedents:
- CLIPasso
- CLIPascene
- StarVector as advisor only

Assimilation:
- introduce optional semantic-retention diagnostics that ask whether removing or merging a region materially changes source/candidate semantic identity;
- expose a semantic contribution score as observer evidence, never as a lone hard production decision;
- allow a primitive-type advisor to suggest rectangle / polygon / ellipse / line-like representations, but require deterministic rule promotion before production authority.

Why here:
CLIPasso/CLIPascene are fundamentally about what information can be removed while retaining meaning. StarVector demonstrates semantic primitive selection, but VLM output must not directly own production geometry.

### SA4 Semantic Debug Board

Best-fit precedents:
- CLIPasso / CLIPascene
- SuperSVG
- LayerPeeler

Assimilation:
- visualize candidate layers/components, semantic-retention diagnostics, source support, and suppression decisions;
- show why a component survived, merged, or was rejected;
- distinguish observed evidence from production authority.

### SA5 Face Neutralization

No direct precedent should override the current SA7.38 raster safety contract.

Possible diagnostic use:
- CLIP-like semantic checks may be evaluated later as supporting evidence only.

The existing image-level Forbidden Face Detail = 0.00% hard gate remains authoritative.

### SA6 Anatomy Guard

No major production backport from these eight precedents.

LayerPeeler/SuperSVG-style decomposition may later provide extra observer evidence around occlusion, but anatomy/topology authority remains the existing structural path.

### SA7 Geometry Re-authoring

Primary precedents:
- AdaVec
- LIVE
- Primitive
- Geometrize
- SuperSVG
- CLIPasso / CLIPascene
- StarVector as advisor only

Assimilation:

#### AdaVec
Adopt adaptive parameterization:
- primitive/path budget should follow source-supported complexity rather than fixed role count alone;
- connected components get independent representation budgets;
- geometry complexity and control-point count are bounded separately from palette/semantic role count.

#### LIVE
Adopt layer-wise construction:
- represent multiple source-supported components as independently ordered layers;
- do not force one semantic/palette role into one polygon;
- preserve deterministic layer order and source ownership.

#### Primitive / Geometrize
Adopt candidate-search discipline:
- generate a bounded deterministic set of geometric candidates;
- evaluate marginal error reduction / source-support gain;
- keep a candidate only when it improves the objective without violating hard guards;
- use deterministic schedules/seeds rather than unconstrained random search in production.

#### SuperSVG
Adopt coarse-to-fine region handling:
- use coarse source-supported regions first;
- spend additional geometry only where residual structure justifies it;
- superpixel-like evidence is an observer/candidate source, not authority by itself.

#### CLIPasso / CLIPascene
Use semantic preservation as a supporting objective:
- candidate geometry may be ranked using semantic-retention diagnostics in research;
- production adoption requires deterministic, explainable promotion and existing hard gates.

#### StarVector
Use semantic primitive-type proposals only as research/advisor evidence.
Do not execute arbitrary generated SVG/code as production authority.

### SA8 Palette Role Adapter

Best-fit precedents:
- AdaVec
- LIVE
- LayerPeeler

Assimilation:
- separate palette-cluster identity from connected component identity;
- one palette role may own multiple disconnected fields;
- source pixels remain the only production palette authority;
- do not equate color-count limits with primitive-count limits.

This is directly required by SA7.41's root-cause finding.

### SA9 Semantic Golden Teacher

Best-fit precedents:
- CLIPasso / CLIPascene
- StarVector

Assimilation:
- add semantic-retention and primitive-role agreement diagnostics to teacher tooling;
- Golden may help label SURVIVED / SIMPLIFIED / REMOVED / REAUTHORED patterns;
- no Golden raster/coordinates flow into production.

### SA10 Expanded Regression Gate

Best-fit precedents:
- CLIPasso / CLIPascene semantic retention
- AdaVec complexity/budget metrics
- Primitive/Geometrize primitive economy

Assimilation:
- add diagnostic metrics for semantic retention, adaptive complexity, layer/component survival, and primitive economy;
- keep hard failure categories separate from aggregate quality scores;
- no semantic metric may hide Feature Survival, face, anatomy, topology, or source-authority failures.

## SA7.42 immediate implementation synthesis

SA7.42 is the first production application of this precedent plan.

Current root cause:
`background_field_geometry.py` clusters source background colors, then `_largest_component()` collapses each palette cluster to one connected component.

Replace that conceptual model with:

Source border-connected background
-> source palette clusters
-> all connected components per retained cluster
-> component eligibility guards
-> per-component geometry candidates
-> adaptive global field budget
-> deterministic ranking
-> canonical background layers

### Immediate borrowed ideas

From LIVE:
- one palette role may become multiple independent layers/components.

From AdaVec:
- palette-cluster count and geometry/field budget are separate;
- representation budget adapts to source-supported component complexity/importance.

From Primitive / Geometrize:
- fields are selected by bounded marginal value under hard safety constraints rather than "largest only".

From CLIPascene:
- simplicity remains a first-class objective; adding all source fragments is not the goal.

### SA7.42 production ranking contract

Production ranking must remain source-only and explainable.

Initial deterministic ranking dimensions:
1. passes existing minimum field ratio
2. zero subject overlap
3. source coverage
4. expansion ratio
5. source component area / field support
6. deterministic palette-cluster order
7. deterministic component order

Semantic/perceptual model scores are research diagnostics only for SA7.42 and cannot decide production inclusion.

### SA7.42 expected structural changes

- replace largest-component-only extraction with multi-component enumeration;
- keep max source palette clusters separate from max rendered fields;
- preserve existing 3% field-ratio threshold;
- preserve source-coverage >= current contract;
- preserve expansion <= current contract;
- preserve zero subject overlap;
- introduce an explicit global rendered-field cap;
- assign stable cluster_index and component_index IDs;
- deterministic output ordering;
- update background scene provenance with cluster/component counts.

### SA7.42 required tests

- one palette cluster with two large disconnected components -> both survive when global field budget allows;
- one palette cluster with one large + one sub-threshold component -> small component rejected;
- multiple palette clusters do not consume the field budget merely by existing;
- subject-overlapping component fails closed;
- deterministic repeat output;
- global field cap is enforced deterministically;
- legacy single-component cases remain stable;
- no background component is allowed to mutate subject pixels.

## Deferred precedent work after SA7.42

### Candidate next stage: SA7.43 Adaptive Primitive Budget

Use AdaVec-inspired complexity allocation across semantic roles and components.

Goal:
replace fixed per-role geometry counts with source-supported adaptive budgets while retaining hard upper bounds.

### Candidate next stage: SA7.44 Layer-wise Residual Re-authoring

Use LIVE / SuperSVG / Primitive / Geometrize ideas.

Goal:
coarse first, then add only source-supported residual layers whose marginal value justifies their complexity.

### Candidate next stage: SA7.45 Semantic Retention Observer

Use CLIPasso / CLIPascene ideas.

Goal:
introduce an optional observer metric for "did simplification preserve what the image is about?" without granting the model production authority.

### Candidate next stage: SA7.46 Primitive-Type Advisor Research

Use StarVector ideas.

Goal:
evaluate whether semantic primitive-type suggestions improve deterministic grammar design. Advisor output remains research-only until converted into explicit tested rules.

### Candidate next stage: SA7.47 Layer / Occlusion Evidence Research

Use LayerPeeler-style layer reasoning and SuperSVG region evidence to improve SemanticPart decomposition and occlusion understanding.

## Decision

Do not reopen SA2-SA10 as broad rewrites.

Instead:
1. preserve their completed contracts;
2. backport precedent-derived observer/schema capabilities only where they naturally belong;
3. use SA7.42 as the first concrete production synthesis;
4. promote successful ideas through focused later SA7.x stages;
5. update the long-term architecture so future implementations know the correct conceptual home of each idea.

Current execution point remains:

**SA7.42 Multi-Component Background Field Geometry**
