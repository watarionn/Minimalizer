# MinimalizerPublic StructuralRecovery P0 Stage9 — source integrity and non-regression veto (2026-10-11)

**ENGINEERING QA PASS / BOTH NEW GEOMETRY CANDIDATES REJECTED.** `web/static/public-structural-qa-p0.mjs` independently checks RGB deviation outside source-observed feature masks, unmodified alpha, face-only suppression accounting, source-observation coverage, candidate primitive vertices and squared-error change on original source (excluding the deliberately simplified face). These metrics *cannot* stand in for human Golden or semantic quality.

| case | P0 rectangle coverage | P0 candidate RGB loss reduction vs frozen Facet40 outside face | historical Stage5 reported improvement | verdict |
|---|---:|---:|---:|---|
| GC001 | 42.97% | +0.02365% | +0.150% | REJECT sparse and regressing |
| Raden | 34.94% overall | +1.11962% | +2.806% | REJECT sparse and regressing |

`vetoRegressingGeometry` refuses candidates if any off-observation modification, coverage under 60%, or RGB loss worsens relative to a prior research candidate. **Neither candidate passes**; fallback remains the old Stage5/6 research outputs, which are also NOT production-approved. Review images show that the small rectangles destroy shape cohesion rather than solving it.

Two independently hashed, true-original 340x340 comparisons and replay metadata live only in private Drive, not public GitHub. Negative controls tested: source hash tamper, unsigned observation, duplicate/overlap, malformed masks, face crossing, wrong vertices, off-source rectangle, loss-regression and false quality authorization.
