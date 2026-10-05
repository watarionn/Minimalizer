# SA7.26 Experimental Macro Renderer Integration — 2026-10-06

Status: PRODUCTION CONTRACT PASS / VISUAL ADOPTION HOLD

A guarded renderer replacement API now consumes only upstream-authorized SA7.25 macro primitives and replaces hair / major_clothing roles in a VectorScene. Unknown roles, missing required roles, and missing palettes fail closed. Golden raster is never consumed.

Focused renderer + macro tests: 8 PASS.

GC001 research-only legacy-SVG experiment:
- hair: 1 macro mass
- major_clothing: 2 macro masses
- changed-pixel ratio vs adopted Silhouette Proportion baseline: 9.6903% (>=1.5% gate)
- source-supported feature survival remains missing=0 because protected identity/arm/face layers were retained
- forbidden face detail remains 0.00%

Important: the legacy GC001 SVG experiment identified old hair/clothing carrier polygons by local SVG indices. That adapter is case-specific and MUST NOT enter production or be treated as visual adoption evidence.

Decision:
- merge the generic source_region_id-based renderer replacement contract after full regression;
- keep visual baseline unchanged;
- SA7.27 must integrate through canonical semantic VectorScene/source_region_id authority, then rerun hard gates and actual four-way comparison.

Drive evidence folder: Semantic_Abstraction/SA7_26_20261006.
