# Semantic Art Mixer v1 / role-separated Art Modes (2026-10-08)

**Status: Independent research PoC implemented and real-image tested. NOT integrated into MinimalizerLocal's UI, Minimalizer Core, or MinimalizerPublic.**

## Design direction adopted
The user likes the existing **19 Art Mode styles**, but notes Mosaic variants share overlapping roles. **Do not delete any of the 19 reference outputs.** Instead, model the styles as building blocks with four independent concerns:

- **Shape**: where colored regions/tiles come from (mosaic, Voronoi, pixel blocks, geometric blocks).
- **Stroke**: observed original-derived lines (contour, sparse outline, hatch).
- **Texture**: overlaid original-derived dot patterns, optional.
- **Color**: an independent protection/controller layer, **not another mosaic style**. Source-derived locked cells can coexist with any supported Shape/Stroke/Texture recipe.

Implement the independent, headless research component at `tools/research/semantic_art_mixer_v1.py` with a validated role registry and four built-in recipes. It loads only already-existing original-derived research images and verifies the SHA-256 of each PNG against its *own original research manifest*. It does not invoke experimental generators or modify the production Worker.

## Four proven combination recipes

| Recipe | Shape | Stroke | Texture | Color |
| --- | --- | --- | --- | --- |
| `voronoi_ink_dots` | imgrit Voronoi | vsketch Contour | pyfreeform Dots | Original Tie Lock |
| `mosaic_sparse` | mosaicpic Classic | vsketch Sparse | None | Original Tie Lock |
| `pixel_hatch_dots` | Pixora Mean | vsketch Hatch | pyfreeform Dots | Original Tie Lock |
| `geometric_ink` | generativepy Geometric Blocks | vsketch Contour | None | Original Tie Lock |

Each recipe produces paired `*_without_lock.png` and `*_tie_lock.png`. The independent gallery includes the original plus all eight result images.

## Color protection: what is and is not proven

**GC001 only.** The original Kyoko source is 340×340, SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`, and was visually inspected. The green necktie is identified via a manually specified region `x=144..195, y=219..339`, a deterministic original HSV-green observation, and largest connected component. This yielded **1,960 connected pixels**.

The Color role restores the original RGB *exactly* for all these observed pixels, after the selected Shape/Stroke/Texture passes. It additionally restores original-source RGB in that bounded region wherever the rendered image introduces green outside the observed original green mask. No painting, generated fill, missing-part synthesis or color invention occurs.

| Recipe | Previously changed necktie RGB pixels | After protected | New green outside original mask before | After |
| --- | ---: | ---: | ---: | ---: |
| voronoi_ink_dots | 1960 | **0** | 533 | **0** |
| mosaic_sparse | 1959 | **0** | 530 | **0** |
| pixel_hatch_dots | 1956 | **0** | 197 | **0** |
| geometric_ink | 1957 | **0** | 346 | **0** |

The results establish a **correct source-colored connected-region restoration within a manually defined necktie ROI**, not automatic semantic understanding, silhouette fidelity, arm separation, face-feature retention, or unchanged colors in other parts of the image. The line density of Voronoi/Contour and Pixel/Hatch is still visually busy. **Do not claim Core quality PASS.**

A prior real mosaicpic `pin(...)` test showed a single observed green cell survived Classic→Dithered reconvert. This Mixer **does not import or call mosaicpic's API**: it uses existing mosaicpic source-color artwork as the Shape input and a reusable deterministic original-color post-pass. Both are separate complementary findings; do not conflate them.

## Evidence and files

Output private Drive folder: `chatGPT及びCodex用/Minimalizer/SemanticArtMixer_v1_20261008/`, folder ID `1_VfNMbmI4KoIWihxyz4xC38Qq3aZTK58`.

- 1 original preview PNG.
- 8 recipe previews (each before/after Color Lock).
- `gallery_shape_stroke_texture_color.png`, compared visually.
- `manifest.json` containing original/asset hashes, detailed measured per-recipe color metrics, output hashes and the gallery digest.
- Reproducible script and unit regression tests in GitHub, not dependent on the user re-uploading any source image.

Gallery SHA-256 `36bfa1cbdf963185a6a5b53bcfbdb2e331e3b1226fb315e80f6cbe378874d3c5`.

## Validation completed

- `python -W error -m pytest tests/test_semantic_art_mixer_v1.py -q`: **13 passed** (synthetic tie-mask/outside-ROI/transparent-stroke/invalid-recipe tests). Initial 30% mask-area guard rejected legitimate narrow tie ROI and a synthetic tie fixture; revised to 70%, then passed.
- Real `GC001_source.png` run: **4 recipes generated**, before/after metrics verified, all protected necktie RGB mismatch counts and newly green excess counts **zero**.
- Run repeated with warnings treated as errors: **all eight preview PNGs had identical hashes**, complete gallery SHA identical, LocalWorker `/health` remained `ready=true`.
- Output paths exist under the user's **chatGPT及びCodex用** Drive-mounted directory. **Cloud-backend sync should be verified separately** before claiming full remote preservation.
- No LocalWorker, Public, RRM or deployment code was edited by this PoC.

## Remaining gates and next step

1. Ask the user to review the four paired real Kyoko outputs. These are research options; keep all 19 previous results.
2. Separate `Shape/Stroke/Texture` selector UI from `Color Lock` (and add source-part masks for arms, clothes, face) in a Local-only gated design stage. Do not ship controls to Public.
3. Extend Color Lock from this manual Kyoko tie ROI to a source-image-coordinate mask/anchor interface, without guessing missing parts, then evaluate across independent Golden images. Protect original silhouette, arm/torso negative space, clothing colors and tie area as distinct gates.
4. Only promote a candidate to actual Local PWA after multi-input image-quality tests. Pyfreeform's GPL-derived runtime should remain outside any Public distribution and be reviewed before integration.

### Exact reproduction

`python -W error tools/research/semantic_art_mixer_v1.py --root <PRIVATE_DRIVE_MINIMALIZER_DIR> --out <PRIVATE_DRIVE_OUTPUT_DIR>`

The optional `--recipes path/to/recipes.json` accepts a list of 1–32 dicts with exactly `id,shape,stroke,texture,color`, validating each role against a finite list of allowed available assets. Source originals and prior artworks are never generated within this Mixer.
