# SA10.55: Default faceless SVG output contract and signed research parity

2026-10-09. **Research faceless-style gate PASS, historical Stage8 source ring gate FAIL, full character Golden/human review HOLD, production UNCHANGED.**

## Why this stage exists

The actual accepted Minimalizer target style (`docs/TARGET_STYLE.md`, section "Face detail is optional and OFF by default") does **not** draw eyes, nose, mouth or eyebrows by default. SA10.50–54 source-original eyes and facial color geometry were useful **research diagnostics**, but were incorrectly being treated as if those facial details should be included in the default shipped SVG. This stage separates diagnostics from default final paint and blocks accidental visible facial microfeatures. Exceptions explicitly enabled by product policy are outside this research stage and must not bypass its default gate.

## Inputs and immutable authorities

- Authenticated 7-file Raden and 8-file GC001 signed source sets from the SA10.49 hash-locked evidence layer.
- Exact immutable SA10.54 private baseline SVG SHA-256: Raden `11bfc1eb83116981ae6d4f07688af0c0aa165e074af10bf29881c16c938188f5`, GC001 `8ebbb1a44c4f893190c8f536c86397b52d13cbd1a6af3d2f3c60e8a46bf67cbb`.
- Real Chromium 144.0.7559.96, 340×340, device scale factor 1. No model, inpaint, generated paint, image embedding, or hardware worker.

## Implemented target-style rule

`tools/research/sa1055_faceless_output_contract.py` is a **standalone research converter and output gate**, not a claim that the public site already runs this code. It SHA-verifies the original source and previous research SVG, finds the signed final face painter (exactly one `url(#sa1041-original-face-guard)` group and last in z-order), and conservatively removes **only** the existing source-observed facial-color `path` children. It retains that group's original signed source-pixel skin-colored rectangle, every signed SVG mask, all visible source-owner hair and clothing, Stage9/37 source-owned color planes, background, z-order and signed arms. No replacement face ellipse, custom simulated skin, additional SVG path, second face mask or face-wide subject underlay is created.

The canonical research SVG carries `data-minimalizer-target-style="faceless_subject"` and `data-minimalizer-face-features="off"`. A fail-closed `audit_default_faceless()` requires exactly one rect under the final signed face guard; refuses extra eye/other face SVG shapes, feature marker leakage, external raster objects, SVG `<use>`, style/CSS injection and an undeclared target-style mode. These restrictions apply to the two signed source variants in this research stage; a future integrated production adapter must invoke the gate on actual production output.

For visual-level assurance, complete Chromium output must be **bit-for-bit unchanged outside the signed original face** and in both signed arm masks. The face interior eroded by 1px must render *only one authenticated source pixel RGB*, with zero surviving internal face-color variants. Source-original RGB MAE may increase intentionally because faceless abstraction discards visible eyes, nose and mouth. Do not use this increase to claim a quality regression or a facial anatomical improvement. No identity certification is claimed.

## Signed Chromium results

| Metric | Raden | GC001 |
| --- | ---: | ---: |
| SA10.54 expanded SVG vertex count | 1,412 | 1,882 |
| Facial detail paths removed | 16 | 23 |
| **Real source face paths' vertices reclaimed** | **103** | **172** |
| **SA10.55 complete expanded vertex count** | **1,309** | **1,710** |
| Original deployed SVG cap | 1,412 | 1,887 |
| Remaining vertex room | **103** | **177** |
| Signed outside-face RGB pixels changed | **0** | **0** |
| Both arms' RGB pixels changed | **0** | **0** |
| Nonuniform pixels inside eroded source face | **0** | **0** |
| Signed skin RGB source evidence | **PASS** | **PASS** |
| Face detail output gate | **PASS** | **PASS** |

The remaining 103/177 vertices are **budget room, not already accepted new hair or apparel geometry**. Reallocation is reserved for SA10.56. All signed source SVGs and former research candidates remain immutable.

## Real tests and reproducibility

- `tests/zerobase/test_sa1055_faceless_output_contract.py`: **9/9 PASS**, covering signed authorities, SHA-tamper refusal, exact macro/mask/color inventory, deliberate reinserted eye path rejection, unapproved SVG objects, duplicate face guards, original-source/output separation, and full two-character Chromium rendered invariants.
- Two independent complete executions: **8/8 SHA-256 identical generated SVG, PNG, composite review board and metrics JSON**, with a 2-case source-inclusive comparison board. Results are from real signed original images, not invented test data.
- Google Drive authorized private folder `chatGPT及びCodex用/Minimalizer/SA1055_DefaultFacelessOutputGate_20261009` contains the original-inclusive review board, private research/full SVGs, code, tests, report and integrity manifest. **No signed artwork, vector coordinate geometry, or original-inclusive images enter public GitHub.** GitHub receives only reproducible tool code, tests, documentation and coordinate-free numeric metrics.

## Honest release boundaries

- PASS: Source authority, Chromium exact protection, default faceless drawing condition, true expanded SVG budget, repeatability.
- NOT DONE: Reallocation of freed vertices into better hair/cloth (SA10.56), head/hair/arms silhouette quality (SA10.57), separate Stage8 original source ring policy (SA10.58), multi-image human/Golden review (SA10.59), standard production integration/Phase15 certification (SA10.60), deployment/device check (SA10.61).
- **This research converter is not yet wired to the canonical production renderer. Production is deliberately UNCHANGED, human artistic Golden HOLD.** The current comparison image still reveals serious hair/apparel/torso geometry simplifications versus signed originals. Do not treat this stage's structural pass as artistic or production approval.

## Reproduce privately

```bash
python tools/research/sa1055_faceless_output_contract.py \
  --raden /signed/Raden --gc001 /signed/GC001 \
  --raden-svg /private/SA1054/raden_source_chroma.svg \
  --gc001-svg /private/SA1054/gc001_source_chroma.svg \
  --out /private/SA1055

SA1055_RADEN_ROOT=/signed/Raden SA1055_GC001_ROOT=/signed/GC001 \
SA1055_RADEN_BASE=/private/SA1054/raden_source_chroma.svg \
SA1055_GC001_BASE=/private/SA1054/gc001_source_chroma.svg \
pytest -q tests/zerobase/test_sa1055_faceless_output_contract.py
```
