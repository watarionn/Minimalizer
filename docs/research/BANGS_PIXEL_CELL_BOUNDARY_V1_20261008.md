# Bangs Pixel-Cell Boundary v1 / 2026-10-08

**Actual GC001 experiment complete. Local-only source-fringe geometric fidelity significantly improved; full-character appearance remains HOLD/NO-GO.**

The user repeatedly identified a central-right bang that is cut between the eyes. Original GC001 has a verified 694-pixel connected orange component, 390 of which Phase04 incorrectly attributes to the face. Prior v3 source SVG recovered 601 pixels; subpixel raster trials improved to 603 with zero overflow outside observed hair. Epsilon=0 failed to recover those lost pixels.

## Implementation

`tools/research/bangs_pixel_cell_boundary.py` traces the foreground **pixel-cell occupancy** rather than original-center contour directly. It pads the binary region, upsamples 2× with NEAREST and extracts OpenCV contours, then maps coordinates onto the original reference scale using a quarter-pixel grid. That creates a closed source-derived contour capturing more of the thin ends. The converter still drops contours whose cv2 area is less than 2 at doubled scale, and records the effect in the final coverage. No new hair inference; no facial skin plane, subject-wide plate, drawn face features, neural image generation, original raster embed, or production integration.

Three equal-source trials (source region 694 pixels, 15 SVG contours and 485 vertices for each):

| SVG raster variant | Original source covered | Missing pixels | Pixels outside source |
| --- | ---: | ---: | ---: |
| **340 native (best)** | **687/694 (98.99%)** | **7** | **0** |
| 680 then nearest | 681/694 | 13 | 0 |
| 680 then bicubic | 686/694 | 8 | 0 |

The +84 source-pixel gain over strict-zero-excess best prior trial (603→687) is **real and significant**. However 485 vertices are much heavier than the previous 102, and the remaining 7 pixels are not resolved. This approach has **only** proven a better local hair footprint, NOT an improved complete Kyoko/face silhouette or an accepted production Minimalizer image. Quarter-pixel coordinates are an artifact of the doubled OpenCV grid; the trial empirically verifies source coverage rather than claiming a mathematically exact pixel-cell union.

The initial unit test incorrectly assumed generated coordinates were `.5`; the actual polygon coordinates include `.25` and `.75`. That test was corrected rather than modifying real rendering to satisfy a mistaken assertion. **24 related research tests PASS** after correction.

## Artifacts

Stored under canonical private Google Drive `chatGPT及びCodex用/Minimalizer/BangsPixelCellBoundary_20261008/` (folder ID `1jLwEF8YK1gGsjnEskgXJkQJq75bomddL`). Includes 3 source-only hair SVGs, 3 rendered PNGs, a source-versus-three-renders gallery and manifest with actual SHA-256s. Confirm cloud-side sync separately from local mounted Drive writes.

## Next gate

- Protect observed source geometry and hairstyle continuity while **compressing the 485-vertex contour** (topology-preserving boundary run-length/corner merging) with measured minimum 687/694 coverage and zero extra pixels.
- Investigate remaining 7 missed source pixels, including tiny mask components lost by filtering.
- Integrate into *source-owned* actual hair/forehead masks, not into a face-painted base; validate the actual complete reference character and Golden on independent source before Local PWA/Public release.
