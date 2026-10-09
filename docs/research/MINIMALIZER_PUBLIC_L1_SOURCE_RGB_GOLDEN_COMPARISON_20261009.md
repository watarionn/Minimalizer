# MinimalizerPublic L1 discrete source-RGB medoid follow-up (2026-10-09)

**Two source signed Chromium study complete. Research PASS for color optimization, product NO-GO and human Golden HOLD.**

This updates the earlier compact-plane study with exact discrete L1 medoid selection in `tools/research/public_geometry_js/compact_signed_planes.mjs`. The chosen RGB must actually occur inside the SHA-pinned original source-owned region; it minimizes the sum of absolute RGB channel distances, rather than choosing the original RGB nearest the Euclidean channel mean. It never synthesizes additional pixels or facial details.

Two sources: original GC001 and Raden SA10.34 Stage8 signed 11-owner geometry, same signed SA10.41 RGB and original alpha, and **independently SHA-locked SA10.57 browser champion screenshots**. Fixed nonface source-owner region compares all versions over identical original pixels, excluding signed face. The MAE scale is original source RGB L1 per channel averaged; lower is better and **does not equal artistic quality**.

| Case | Frozen SA10.57 | L2 medoid 40 shapes | **L1 medoid 40** | **L1 60** | **L1 80** |
|---|---:|---:|---:|---:|---:|
| GC001 | 40.318419 | 47.306296 | **42.264762** | 37.229150 | 34.396554 |
| Raden | 24.297144 | 23.225326 | **21.655595** | 19.454877 | 18.114803 |

In actual Chromium 144.0.7559.96, all six new **full-character** 40/60/80 candidate SVGs had zero alpha outside source-visible signed owner unions and 100% union coverage at 1x and 4x. Existing source owner back-to-front z-order was retained; eyes, mouth, nose and facial microfeature overlays stayed disabled. Six candidate SVGs regenerated deterministically, with 6/6 SHA-256 repeat equality. The L1 unit tests passed 3/3.

**Critical decisions:**
- GC001 40-shape L1 color still loses numerically to the frozen SA10.57 champion (42.26 vs 40.32); do not promote.
- Raden 40-shape improves numerically, but identity and faceless visuals are not human Golden-approved.
- GC001 only beats its former champion numerically at 60+ shapes; not the 40 shape whole-scene target.
- The original Stage8 source ring budget remains FAIL/HOLD; exact new 10 painted owner masks cost 5,353 GC001 / 3,586 Raden vertices, exceeding 1,887 / 1,412 historical caps. The source Stage8 input evidence is immutable, and numeric DOM shape limits do not excuse these vertices.
- Flat face skin-colored region and blocky clothing remain subjective visual problems. No Safari/iPhone or third-original Golden.
- **No production files, Public/Local pipeline or feature flag were changed; no merge/deploy authorized.**

The independent private diagnostic comparison board and exact-source SHA artifacts are in approved Google Drive / user-facing `MinimalizerPublic_L1_FullCharacter_Research_20261009.zip` and/or prior `PublicGeometryJS_SignedClip_20261009` research folder, not in public GitHub. Raw original source image and original Stage8 JSON bytes are never included in public commits.

Next: optimize source garment/color-plane priority under a *true* full-character vertex budget, explicitly resolve Stage8 policy under an approved versioned scheme or strict provenance-equivalent geometry, obtain human Golden approval, test mobile Safari, then consider feature-flag deployment. Do not silently bypass any cap.
