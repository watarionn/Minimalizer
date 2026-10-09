# SA10.60D / Campaign C02b1: Original-keypoint arm corridor source diagnosis

Date 2026-10-09 JST. **NONPROMOTING RESEARCH COMPLETE; arm artistic gate HOLD, source Stage8 budget HOLD, human Golden PENDING, production unchanged.**

## Question and independent source

The signed historical GC001 right_arm mask (6,486 px) includes flowing side-hair/background-like regions. C02a recovered actual Phase03 subject and Phase04 semantic-part stage manifests as a private SHA-locked ZIP. Rather than recoloring arms or deleting every pixel sharing the background color, C02b1 checks **original source-observed** rtmlib wholebody COCO17 shoulder/elbow/wrist pose and measures how much of the existing arm mask falls inside a source-relative pose-support corridor. No new pixel, image infill, SVG plane, or face feature is created. The old Stage04 masks are unchanged and the new corridors exist only in the private review board as separate proposals.

- Source GC001 original SHA pinned to `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`.
- Stage03/04 original ZIP SHA pinned to `89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434`.
- Actual current original Phase04 right_arm is **binary identical** to the historically signed 6,486-pixel right_arm (even though archived PNG encoding differed). Face and historical left_arm masks are never altered or overwritten.
- COCO17 right shoulder/elbow/wrist source indices 6/8/10 and shoulder span determine a deterministic corridor. Factors tested are exactly 0.20, 0.27, 0.34 of shoulder span for radius. The result is **intersection only** with the frozen arm mask, so no source pixel is added.

## Actual original-case result

| Pose radius multiplier | Corridor thickness | Retained right_arm pixels | Excluded pixels | Original exact background-connected RGB pixels remaining | Connected parts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 49 px | 3,096 | 3,390 | 0 / 533 | 1 |
| 0.27 | 66 px | 3,823 | 2,663 | 0 / 533 | 1 |
| 0.34 | 83 px | 4,551 | 1,935 | 0 / 533 | 1 |

**Critical gate failure: recorded original wrist confidence is only 0.462252** (threshold 0.60). All three proposals fail the **pose-evidence gate**, even though the synthetically observed overlap is gone. The source-border-connected exact RGB is not itself a complete semantic ground truth. The corridor can delete genuine hair/sleeve/arm or change silhouette. Therefore the candidates are NOT approved and must not be integrated into production, nor described as a solved arm correction.

## Tests, private storage and next decision

- 9/9 focused synthetic and real original-case tests PASS. Invalid factors, masks/shapes/NaNs, low-confidence wrists, protected-authority output isolation and no-add geometry are checked. Actual signed GC001, originally saved stage JSON/ZIP and two independent fresh executions yield deterministic private board + JSON. True SVG vertex accounting and full Chromium quality render **NOT RUN** because the input pose-confidence gate does not pass.
- Private original source-image board, three green corridor overlays, full data and actual traced source positions live only in `chatGPT及びCodex用/Minimalizer/Campaign_SA1060_to_Production_20261009/C02_Phase03_Phase04_Provenance_20261009`, alongside C02a immutable 19-file raw-source snapshot.
- Public GitHub contains no source raster, traced mask/landmark arrays or candidate SVG. Only reproducible source-bound research code, unit/integration checks and *coordinate-free* numerical report.

**Next C02b2:** seek more reliable independent arm/garment/hair structure such as original observed image/edge + semantic segmentation with confidence and cross-character controls, rather than automatically trusting a wrist keypoint whose original score is below threshold. Then test real Chromium with literal geometric SVG costs, signed facial/arm/whole silhouette and independent Raden/Approved holdouts before Artistic Golden. Stage8 2,370/1,412 and 3,604/1,887 historical rings still FAIL; separate policy decision required unless an actually topology-preserving under-cap source geometry is demonstrated. Authentic human Golden remains PENDING. C05–C08 cannot be passed by this color/pose study.
