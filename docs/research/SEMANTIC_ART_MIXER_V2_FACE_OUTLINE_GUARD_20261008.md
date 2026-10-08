# Semantic Art Mixer v2: face-ink exclusion and source-outline guard (2026-10-08)

**Status: independent GC001 research implemented, no live production integration.**

## User feedback prompting this correction

The user compared the four v1 composite style results and observed that **silhouette readability varies dramatically** and that some outputs appear to have unnerving, newly drawn eyes. This feedback is valid: v1 loaded each entire shape raster (including non-semantic background geometry), composited unrestricted vsketch contour/hatch linework over the entire canvas, and only protected the original green necktie region. It had no specific facial exclusion and no consistent, separately controllable subject-outline support.

**Do not ship v1 eyes to MinimalizerLocal**, and do not classify v1 as a Golden/semantic visual-quality PASS. Previous v1 and 19-style archives remain preserved for comparison, not deleted or silently overwritten.

## v2 research implementation

`tools/research/semantic_art_mixer_v2_guarded.py` is a new headless, opt-in and isolated **PoC** layered on the unchanged v1 code. No generative img2img, diffusion, generative fill or predicted missing anatomy is used.

- **Face No-Ink Guard:** A manually inspected, source-coordinate face search polygon for canonical GC001; observed original skin RGB classification, largest connected component, convex hull and a one-pixel inset produce a planar face mask. It is filled with **an existing RGB triplet from the original face pixels**, flattening eyes, nose and mouth rather than generating new features. Face outline remains outside the protected interior. No vsketch ink is permitted anywhere within the entire face search polygon; dots are overwritten within the derived inner face plane. This is a *GC001-specific manually gated observation*, **not** a trained face detector or general facial segmentation.
- **Observed Outline Support:** vsketch Sparse Outline ink, whose strokes were independently derived from original GC001 edges, becomes a common *overlay support layer*. It is clipped by a coarse manually inspected subject visibility polygon and excludes the full face search polygon. That polygon is **never directly drawn as a silhouette**. The original vsketch stroke family is optional per recipe; support layer gives the combinations a more consistent source-derived outline cue.
- **Texture locality:** Optional original-derived pyfreeform dots are blended only inside the coarse subject visibility region with reduced strength.
- **Color Lock unchanged:** The existing connected green necktie region is protected after all style layers; green expansion outside the observed source tie color within the manual tie ROI is restored using **original source pixel RGB only**.
- **Safety:** All source PNG SHA-256s are checked against their original research manifests; original GC001 SHA-256 exactly `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`. The four default style recipes are the same as v1. No changes to MinimalizerLocal, MinimalizerPublic or RRM, and no new production imports.

## Real GC001 proof

Output: `chatGPT及びCodex用/Minimalizer/SemanticArtMixer_v2_Guarded_20261008/`, private Drive folder ID `16GBzk6QLzy-3RHPdNg8qWRdW70z6Zpoc`.

Observed on exact canonical 340×340 Kyoko image:

| Measurement | Voronoi Ink Dots | Mosaic Sparse | Pixel Hatch Dots | Geometric Ink |
| --- | ---: | ---: | ---: | ---: |
| Observed face-plane pixels rendered as flat original skin RGB | 4624 | 4624 | 4624 | 4624 |
| Dark artificial eye/face ink pixels inside plane after | **0** | **0** | **0** | **0** |
| Original vsketch stroke pixels suppressed in face polygon | 1541 | 1126 | 1689 | 1541 |
| Original necktie RGB mismatches after Color Lock | **0** | **0** | **0** | **0** |
| Original sparse stroke ink support candidate pixels | 17653 | 17653 | 17653 | 17653 |

The latter support pixel count measures the **observed source-outline ink candidate within the coarse subject polygon**, **not** a verified exact character silhouette or true separation of the arms from torso. The face-plane uniform color is intentionally plain, per no-generated-eye rule. The output gallery includes original, legacy v1 result and new v2 guarded result for all four recipes, plus the individual comparison PNGs and face masks. The original/source and all previous results are kept.

**Visual inspection:** new eye-like dark strokes are suppressed; face interior becomes a plain skin-colored region. The new bounded outline overlay helps keep source edge cues but Voronoi and geometric/background pattern still compete visually, and this is **not** a final aesthetic approval or Core silhouette quality gate. The shape mask remains an explicitly manual research heuristic; no generalized semantic masks or facial detector has been validated.

## Tests and boundaries

- Dedicated synthetic-fixture tests at `tests/test_semantic_art_mixer_v2_guarded.py`: original-source eye-hole flattening, no false opaque ink from transparent PNGs, necktie original RGB / no green expansion, fail-closed missing skin, no unauthorized ML/production imports.
- Existing v1 regression tests preserved at `tests/test_semantic_art_mixer_v1.py`.
- The actual source-derived v2 gallery must be re-rendered twice and compared by SHA, and the related Local/Public unit regressions rerun, before PR is merged.
- Save the actual output files to the private Drive mount; independently check when backend Drive sync becomes visible. Do not mistake a mounted file for confirmed server-side presence.

## Next design gate

1. Obtain user review of v1 versus guarded v2; neither should be put into Local PWA automatically.
2. Improve **subject/background separation and silhouette fidelity** without hallucinated features, using source-derived geometry/negative-space masks (especially arms, hair edges and jacket/tie). Generic modules must accept external observed masks, not hard-coded Kyoko coordinates.
3. Test face-plane and outline protection on independent Golden cases before reusing in Core; track unnatural flat face ovals, too-dense hatching and background Voronoi noise as open quality issues.
4. Promote independently proven mask/color/edge operations only after per-part (Shape/Color/Face) gates pass. Existing 19 style archives remain intact.

Reproduction:
`python -W error tools/research/semantic_art_mixer_v2_guarded.py --root PRIVATE_MINIMALIZER_DRIVE_DIR --out PRIVATE_V2_OUTPUT_DIR`.
