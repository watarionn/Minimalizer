# Existing Eyewear Observer Evidence Audit (2026-10-09)

**Executed existing GC001 AnimeSeg source mask; source evidence PASS, semantic goggles mask HOLD.** This audit deliberately reused prior real inference rather than installing/re-running GPU models or changing the production image.

## Sources and verified source hashes
- GC001 original `C:\Work\Temp\macro-gc001\GC001_source.png`: SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`.
- Stored GC001 AnimeSeg observer result `C:\Work\Temp\sa1026-animeseg-gc001-v457\animeseg_mask.png`: SHA-256 `ea1be2ff34d3bdbef5693ab3dbe1c60363fe6365cb42454829b96994f3520148`.
- Existing SA7.9 frozen Grounding DINO + SAM report at `docs/zerobase/SA7_9_EYEWEAR_OBSERVER_V1_20261005.md`. Coordinates from that frozen report were compared spatially as historical hypotheses, **not raw masks**.

## Real cross-observer findings
- AnimeSeg accessory color (128,128,0) totals **11,857** GC001 pixels, consistent with existing SA10.27 record.
- Within a broad head-goggles observation window (x 104..240, y 38..103), **3,404** pixels are tagged accessory. They form **one large connected component**, bbox x=104,y=38,width=119,height=66. These are **not certified goggles pixels**, because the semantic class covers other visual materials and the component is overbroad.
- Frozen SA7.9 two small eyewear hypotheses at [137,119,18,13] and [185,120,24,12] have **0 px overlap** with the head-goggles ROI. These lie near the *character's actual eyes*, suggesting possible eye-as-eyewear misdetections. Do not promote them to goggle geometry.
- A larger frozen SA7.9 candidate [104,33,116,61] intersects head window by 6,496 bbox px but was documented as false/ambiguous; bbox intersection alone cannot verify the lens/frame.
- GC001 SA7.5 structural observer pairing remained false, confidence 0.25911. SA7.6 independent-role fusion therefore stays HOLD.

## Decision
The independent sources now explain the original failure mode: Phase04 classifies head accessories as hair; AnimeSeg sees general *accessory* but not individual lens/frame; SA7.9 detects false small candidates near the visible eyes. None is a trustworthy pixel-perfect goggle mask. **No goggles SVG was produced; no hair ownership, skin/face plate or production MinimalizerLocal/Public changed.**

Script `tools/research/eyewear_existing_observer_audit.py` emits real source ROI highlights, accessory binary evidence and SHA-backed `manifest.json`. `tests/test_eyewear_existing_observer_audit.py` plus earlier related suites: **51 PASS**.

Canonical Drive folder: `chatGPT及びCodex用/Minimalizer/EyewearExistingObserverAudit_20261009`, ID `1oThyrHLeMuvSl_oMuPsZftJ6Z6zu-RcL`. Cloud verification pending independent list.

**Next gate:** regain independent semantic per-material evidence from source-verified frame and two lenses (e.g. human-reviewed polygon or observer whose frozen contract actually supports lens/frame), with negative controls for eye-like structures at y~119 and hair/hat intersections. Use the SA7.6 role agreement gate and hold out other subject before rendering. Never turn AnimeSeg "accessory" directly into a single orange/white goggles plate.
