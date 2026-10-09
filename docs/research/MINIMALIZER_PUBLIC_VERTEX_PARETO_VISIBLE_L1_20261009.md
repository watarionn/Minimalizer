# MinimalizerPublic signed-source Stage2: vertex Pareto and 40-plane visible-color refit (2026-10-09)

**Research run completed; shape and boundary constraints remain incompatible under tested simplification family; Production NO-GO.**

## Immutable evidence
- Two signed SA10.41 original RGB PNGs (GC001 and Raden), signed Stage8 11-owner contours and their 10 painted source-visible masks, and signed SA10.57 original Chrome comparator screenshots.
- No original image bytes, owner masks, or Stage8 ring JSON copied to GitHub. The machine-checkable mask checksums are in private `verified_owner_manifest.json` in this stage's Drive package.
- All source-owner geometry and color checks use SHA-frozen originals. Test outputs are candidate-only, with face/eyes/nose/mouth microdetail painting prohibited.

## Exact cell-boundary simplification sweep, actual Chromium 144 DPR1 and DPR4

One SVG compound path per painted owner, using all preserved separated islands and holes. OpenCV `approxPolyDP` epsilon was swept *uniformly* across 10 owner paths, then rendered in actual Chromium. Positive source-pixel-center parity alone is not treated as a subpixel/full-image Golden PASS.

| Original | Unsimplified 10-owner vertices | At epsilon=1.0 | Historical vertex cap | DPR4 outside alpha | DPR4 signed union missing alpha |
|---|---:|---:|---:|---:|---:|
| GC001 | 5,353 | 1,857 | 1,887 | **5,975** | 4,734 |
| Raden | 3,586 | 774 | 1,412 | **5,110** | 4,006 |

At epsilon 0, 0.125, 0.25 and 0.375 the two whole-character union alpha footprints remain exactly covered with zero outside alpha in Chromium DPR1/DPR4, but vertices only reduce by 7 (GC001) or 2 (Raden), far above the caps. First meaningful compression epsilon 0.5 incurs GC001 DPR4 999 outside / 786 missing samples, Raden 934 outside / 680 missing. These counts are sample-level, not full pixel counts. The conclusion is **for this RDP/approxPolyDP family only**, not a theorem that no exact compact representation exists.

Owner-weighted discrete multiple-choice vertex knapsack was then tested under the historical **rendered vertex** caps (not waiving original source-ring cap):
- GC001: 1,885/1,887 vertices, 19,122 summed per-owner outside DPR4 samples, 10,475 summed missing samples.
- Raden: 1,411/1,412 vertices, 11,370 summed per-owner outside DPR4 samples, 5,472 summed missing samples.

The per-owner summed samples include owner overlap and must **not** be interpreted as unique full-scene pixel counts. All candidates violate strict zero-leak / zero-loss source-owner geometry.

Moreover, historic original Stage8 source ring vertices already exceed their own immutable limits (GC001 3,604 > 1,887, Raden 2,370 > 1,412). Reducing a *rendered SVG* path alone never resolves that input-stage source-ring gate.

## Source-visible 40-shape color refit

Keep exactly the same 10 signed owner clip paths, the same back-to-front order, the same 30 original paint rectangles (10 undercoats + 20 color rectangles); the 10 clip paths and 30 rectangles are **40 counted shapes**. Refit each rectangle and undercoat only to actual source RGB pixels in the portion that remains visible after later rectangles and foreground owners. No synthetic RGB or new geometry, no facial overlays. Re-run exact SHA-bound 40-shape inputs.

Same original nonface source ROI, actual Chromium 144 DPR1:

| Case | Frozen SA10.57 | Before refit L1 40 | After visible L1 refit 40 |
|---|---:|---:|---:|
| GC001 | 40.318419 | 42.264762 | **42.012781** |
| Raden | 24.297144 | 21.655595 | **21.575139** |

Both recolored candidates retain 0 outside alpha and 0 missing signed-source union alpha at DPR1/DPR4, and deterministic exact SVG SHA rereproduction was confirmed. **GC001 remains worse than champion**, so no production promotion. Art quality and face plate aesthetics remain human Golden HOLD.

## Research decision
- **PASS**: independent explanation of vertex budget vs signed mask error, documented infeasibility *within tested epsilon sweep*, no unsafe budget relaxations.
- **PASS**: source-visible color-only refit gives measurable improvement without increasing shape count or changing geometry.
- **HOLD/NO-GO**: full Stage8 source ring budget, original protected subpixel-owner parity at reduced vertices, GC001 champion improvement, full-character human Golden, mobile Safari and deployment gate.
- Next: source-equivalent lossless geometry encoding (count all actually processed primitives/vertices), or an **explicit user-approved versioned budget policy migration** with independently measured per-owner penalties. Improve GC001 necktie/clothing visibility with source-owned motifs, without drawing face components.

All production routes and feature flags remain untouched. Preserve artifacts in `chatGPT及びCodex用/Minimalizer`; only safe checksum metadata and research code belong in GitHub.
