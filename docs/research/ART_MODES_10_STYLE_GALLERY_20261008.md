# Minimalizer Art Modes / 10-style comparative atlas (2026-10-08)

Status: **GALLERY PRODUCED / REPRODUCIBILITY PASS / ALL 11 INPUTS VERIFIED / NO PRODUCTION CHANGE**.

The user requested that we collect and arrange all produced Kyoko Art Mode outputs. These images were already made in the private Minimalizer research folders and **must not be requested from the user again**. We verified all three directories on Google Drive via connector:

- Pyfreeform (4): `chatGPT及びCodex用/Minimalizer/PyFreeform_PoC_20261008/`
- Generativepy (3): `chatGPT及びCodex用/Minimalizer/Generativepy_PoC_20261008/`
- Vsketch (3): `chatGPT及びCodex用/Minimalizer/Vsketch_PoC_20261008/`

Source input: `GC001_source.png` canonical original, SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`. Sources: **11 PNGs** in total; 10 transformed styles across three libraries, plus one original.

Output folder (private): `chatGPT及びCodex用/Minimalizer/ArtModes_10Style_Gallery_20261008/`, Google Drive folder ID: `1CiO12xRCee6lINAxgJ-EDY1cOu6dRy64`.

Files created:

| File | Layout | SHA-256 |
| --- | --- | --- |
| `gallery_landscape_4x3.png` | Four columns, three rows; original + 10 styles + one legend tile | `cb679632550b27b5812150d5ac69cc1ef19e5ce417fa1976599a4d7ea68dd6de` |
| `gallery_mobile_2x6.png` | Two columns, six rows, optimized for browsing vertically on a phone | `4156b055cbb329da52905ba79c925717bab4e4d6ad62fa2c7f513f34bccceed2` |
| `manifest.json` | Original image/style lineage and SHA-256 for all eleven inputs, plus gallery output hashes | `2af2ca66c363970e6181782939c198ddc94210e12884fcc4f92c0bf38447f6d0` (initial creation) |

The source-preserving composition is implemented in `tools/research/build_art_modes_gallery.py` in the GitHub repository. It uses only Pillow resizing and poster typography. **No img2img, Generative Fill, retouching, new image content, or image-generation model**. No production MinimalizerLocal or Public runtime paths are touched.

## Gallery reading order (01–11)

01 Original source.

02–05 pyfreeform: Color Dots, Lines, Mosaic, Shapes.

06–08 generativepy: Circle Field, Geometric Blocks, Flow/Ribbons.

09–11 vsketch: Contour Line, Hatch Shade, Sparse Outline.

12 legend / 4+3+3 style breakdown.

## Reproduction and verification

`python -W error tools/research/build_art_modes_gallery.py --root PRIVATE_DRIVE_MINIMALIZER --out PRIVATE_DRIVE_GALLERY`

Two back-to-back executions on the user's authorized PC produced identical SHA-256s for **both** atlas images. The script validates image dimensions, verifies each image decodes and checks the original against its Golden source hash. Additional verification checked that **all 11 original source PNG SHA-256 hashes** still match the output `manifest.json`. The static gallery is composed from original artifacts; artwork is not altered.

The user's live UI can display this as a gallery without installing extra rendering libraries. Private cloud sync of this **new** output folder is a separate verification step; do not claim the gallery was cloud-synced merely because the mounted Drive copy exists.

## Follow-up

Ask the user to review all ten styles as a collection, without dropping the four already-favored pyfreeform styles. Potential next development is a separately approved **Local-only Art Modes selection / gallery view**, keeping Minimalizer Core and Public's browser pipeline unaffected.
