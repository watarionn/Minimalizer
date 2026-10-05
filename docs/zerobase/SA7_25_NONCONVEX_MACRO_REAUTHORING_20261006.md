# SA7.25 Non-Convex Macro Re-authoring — 2026-10-06

Status: GC001 DEBUG PASS / RENDERER INTEGRATION NEXT

SA7.24 proved convex macro fitting unsafe for GC001 hair. SA7.25 replaces convex-hull fitting with non-convex external-contour approximation while preserving the source-support guard.

A key design correction separates:
1. semantic primitive count budget, from
2. silhouette vertex budget inside each primitive.

Reducing both at once caused helmet-like expansion and silhouette loss. The v1 contract now permits up to 24 contour vertices while still limiting hair to <=3 semantic masses and major clothing to <=2.

GC001 debug result:
- hair: 1 mass, 20 vertices, source mass 17,633 px, final raster 15,391 px
- major clothing: 2 masses, 9 and 12 vertices, final areas 1,872 and 327 px

The previous dangerous hair expansion is gone and all proposals pass SA7.24 source-support guards.

No renderer integration in this stage. Next stage may experimentally connect these macro primitives behind hard topology/anatomy/face gates and must pass the normal visual delta/four-way requirements before adoption.
