# SA7.21 Head-Crop Normalization Study — 2026-10-06

Status: FAIL / EYEWEAR SPIKE PAUSED

Using SA7.19 small anyglasses classifier, source-derived alpha-person crop heights 16%, 18%, 20%, 22%, and 25% were evaluated after SA7.20 moved into development evidence.

No crop ratio recovered Kaela pr-img-02 above the frozen 0.80 gate; its best tested value remained below 0.50. Ratios also shifted false-positive scores on Fauna/Gura materially.

Conclusion: simple full-person-relative crop normalization is not a robust independent eyewear witness. Do not tune further on GC001.

Current eyewear status:
- Grounding-DINO: proposal only.
- SA7.15: safety/filter only.
- dedicated small classifier: promising but not generalized enough for independent promotion.
- renderer: no eyewear promotion without independent evidence.

Decision: pause the eyewear spike as a separately resumable research track. Resume core SA7 semantic geometry work on hair and clothing so one conditional accessory does not block Minimalizer as a whole.
