# HND-20261005 Minimalizer GC001 Visual Development Handoff

## Canonical restart point
- Repository: watarionn/Minimalizer
- Canonical branch: main
- Latest adopted visual commit: a60aaa12ff22c2f6384a598442964710ce939d87
- Latest adopted visual stage: Silhouette Proportion Recomposition
- Do NOT continue from experimental FAIL branches listed below.

## Current hard gates
Every meaningful visual stage must satisfy all of:
1. Visual Delta >= 1.5% versus latest adopted Minimalizer image.
2. Feature Survival PASS, missing=0.
3. Forbidden Facial Detail ratio = 0.00%.
4. Four-way comparison must be assembled from actual artifacts:
   Source | Browser fallback v12 | current Minimalizer | Rinka Golden.
5. Browser fallback v12 is the regression floor. A stage is not visually accepted merely because it differs.
6. Update a separate chronological Minimalizer Version History for accepted visual stages.
7. Never use generative reconstruction/img2img/fill/inpainting. Golden/v12 are evaluation references only.

## Latest adopted results
### Face Safe
- PR #131 merged.
- main squash SHA: 9b3ed4f9ad13ee8967f8dbd3df8e5436b267f8b2
- Forbidden Facial Detail: 4.31% -> 0.00%.
- Head is excluded from internal global/perceptual detail proposals.
- Drive stage ID: 1_YNEgPrzIG20isdmbfkn5kZa0epiYw4X

### Required Feature Reservation
- PR #132 merged.
- main squash SHA: f113968f9b9422c542ffd0983a9cbb2fc0563eed
- Generic compact high-contrast identity accents are reserved/restored after perceptual competition.
- Feature Survival: missing=1 -> 0, PASS.
- Face remains 0.00%.
- Visual delta only 0.42%, so this is an architectural/safety stage, not a numbered visual improvement.
- Drive stage ID: 1V54jePpRXoNH1C0Du7Ff2-9F3SLAIKKa

### Silhouette Proportion Recomposition
- PR #133 merged.
- main SHA: a60aaa12ff22c2f6384a598442964710ce939d87
- ZeroBase: 473/473 PASS at adoption.
- Visual Delta: 4.99% PASS.
- Feature Survival: PASS, missing=0.
- Forbidden Face: 0.00%.
- Drive stage ID: 1k_xMLpvgtdMb36vYIKEyLTTCFubaz251
- This is the current visual baseline.

## Rejected experiments after Silhouette Mass
These were implemented/tested but MUST NOT be treated as accepted progress.

### feature/whole-body-shape-hierarchy
- Found and fixed duplicate hierarchical_shape_mass definition.
- Full ZeroBase after fix: 476 passed.
- GC001: Survival PASS missing=0; Face=0.00%; Visual Delta=0.1903%.
- REJECTED: Visual Delta < 1.5%. Not merged.

### feature/coarse-part-blocks
- Full ZeroBase: 476 passed.
- GC001: Survival PASS missing=0; Face=0.00%; Visual Delta=1.0779%.
- REJECTED: Visual Delta < 1.5%. Not merged.

### feature/primitive-budget-compression
- Removed redundant generic major-color paint layer in experiment.
- Updated obsolete tests to surviving authority layers.
- Full ZeroBase: 474 passed.
- GC001: Survival PASS missing=0; Face=0.00%; Visual Delta=1.1739%.
- REJECTED: Visual Delta < 1.5%. Not merged.

## What changed in our strategy
Three post-baseline experiments showed that incremental shape bands or deleting one redundant layer only moves ~0.2-1.2%.
Do not lower the 1.5% threshold to make them pass.
Next work should be architectural: reorganize the final renderer into a small number of dominant subject/garment shapes plus protected identity accents, rather than stacking another local motif.
The useful lesson is: add less, replace more.

## Recommended next stage
Working name: Dominant Shape Composition / Renderer Layer Collapse.
Goal:
- Collapse overlapping renderer layers into a bounded small set of major subject shapes.
- Preserve semantic mask authority.
- Keep Required Feature Reservation as late protected foreground.
- Keep head as base silhouette only; no internal face detail proposals.
- Avoid GC001-specific colors/coordinates.
- Target a clearly visible >=1.5% delta, while retaining missing=0 and Face=0.
- Only merge after actual four-way visual comparison.

## Canonical GC001 Drive folder
Folder ID: 1b5G4rD7ma7qIuTnUvbJnVouJfGXraWy9
Path: chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205

Critical references:
- Source: GC001_source.png, ID 1LxHHizN1nC9JVpbHegqMtO38O6xWwjpj
- Browser fallback v12: GC001_browser_fallback_v12.png, ID 1quWr3R5j-Jqmhgn8Lp-eu_DPOgUD6I9U
- Golden: GC001_golden_rinka.jpeg, ID 1jnYf6RXRoN8o37DnGE11FRertooeADzY
- Latest adopted stage: GC001_silhouette_mass_stage_20261005.png, ID 1k_xMLpvgtdMb36vYIKEyLTTCFubaz251

## Local execution notes
- Dirty canonical checkout C:\Work\Projects\Minimalizer must not be modified for experiments.
- Use clean detached worktrees under C:\Work\Temp.
- Python: C:\Work\SharedAI\minimalizer-observers\Scripts\python.exe
- GC001 workspace: C:\Work\Temp\macro-gc001
- Phase4 masks: C:\Work\Temp\macro-gc001\artifacts\GC001\phase_04\part_masks
- Chrome headless is available for SVG rasterization.
- Remove/recreate experimental worktrees as needed.

## Preservation / process rules
- GitHub is source/doc/schema authority.
- Google Drive is visual artifact authority.
- Save to the deepest project folder, then list/fetch exact artifact to verify.
- Never claim a visual improvement from tests/metrics alone.
- Never merge a meaningful visual stage before the actual four-way comparison.
- Record mistakes with cause, impact, fix, and prevention.
