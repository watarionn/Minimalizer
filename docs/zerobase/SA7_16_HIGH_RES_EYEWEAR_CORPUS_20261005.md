# SA7.16 High-Resolution Eyewear Corpus — 2026-10-05

Status: CORPUS REPAIRED / PRIOR THUMBNAIL LABELS INVALIDATED / NO NEW MODEL DOWNLOAD

## Audit
No eyewear-specific detector was found in the existing local model cache or current Minimalizer repository.

The original HoloMen collection workflow was then re-audited. The archive contains official full-body `pr-img` assets in addition to 340px list thumbnails. These are substantially higher resolution (453x1400 through 2000x2000 in the inspected set).

## Critical label correction
Manual inspection of the high-resolution assets showed that the SA7.13 thumbnail corpus contained label errors:
- Sorashina Sopia was treated as eyewear-positive, but the visible paired circular objects are head accessories rather than eyewear.
- Shiranui Flare's inspected variant contains no eyewear.

Therefore SA7.13's generalization FAIL remains historical evidence, but its corpus is INVALIDATED for judging eyewear recall. It must not be used to tune or reject future observers.

## Visually verified v1 corpus
Positive:
- Friend-A pr-img-01: eyeglasses, SHA256 7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3
- Hyakuto Kyoko pr-img-01: forehead goggles, SHA256 7300bf4f9b2baf4dd5452448bb9ec460004e82763a22a2eeecba4057d7b1c1a5
- Kaela Kovalskia pr-img-01: forehead goggles, SHA256 e84df7cd5fcae2eecf5e661645dd8e71cf2278a5324aa1f3faa0bf5fde98acee

Negative:
- AZKi pr-img-01: SHA256 d65d8c75dc4a10fa8612b1cdebd8e88caa63b85eda90b74f1769599f7fd653a4
- Gawr Gura pr-img-01: SHA256 ab6021ccb415629a1df2fd25c96f6c522d899b36c94b3f6a5d446bd5bbafbbfa
- Ceres Fauna pr-img-01: SHA256 6b4772cd5c98516537d72883beb3a674ec01d9b1b9a2eff6b7ae53516192910a
- Nanashi Mumei pr-img-01: SHA256 ca2ee36c165def2509c20f4134e03acd0e48dc50f0d5245c21ec8f67ebeb162a
- Shiranui Flare pr-img-01: SHA256 5238a9fe9f75f600b8e2a1f284bd2c2bde013ab0177acbc23dea3f2acbb71348
- Sorashina Sopia pr-img-01: paired head accessory negative, SHA256 a7aee514c72491a5bcd1715ce0790460eb3af13d702b81d8c11960852e207790

All labels require `manual_visual_hires` provenance in the new corpus contract.

## Decision
Use high-resolution official source evidence before adding another detector dependency. SA7.17 will re-evaluate geometry/region verification on this corrected corpus. GC001 remains sealed until a non-target high-resolution gate passes.
