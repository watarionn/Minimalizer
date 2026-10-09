# MinimalizerPublic library convergence R1 execution report (2026-10-10)

**Scope:** research-only, Public browser serializer bridge; frozen v34 hybrid SVG; no Local Worker, production renderer, generated source content, or live Public route changes.

## Exact references

- New GitHub branch: `research/public-v34-library-convergence-r1-20261010` from `main`. PR #308 is still independent, stacked on held #306.
- Golden input: Google Drive `chatGPT及びCodex用/Minimalizer/SvgLocalRollbackV34_20261009` (v34 manifest-verified SVG + saved Chrome PNG).
- Authoritative output baseline: `chatGPT及びCodex用/Minimalizer/ConnectedSourcePlanesV32_20261009` (v32 manifest-verified fine PNG).
- Chrome **154.0.8037.98**, 340×340 RGBA, real Selenium Chrome SVG decode and canvas readback.
- SVGO original pinned **4.1.0 browser ESM**, metadata-only plugins, no `preset-default`, no path transforms. Produced candidate bytes and SHA-256 repeat-stably.

## Result

| Case | v34 source bytes | SVGO candidate bytes | Additional savings | Original vs v32 diff | Candidate vs v32 diff | Candidate vs v34 Chrome diff | Bad-overlay negative pixels |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kyoko | 41,040 | 41,040 | **0** | 0 | 0 | 0 | 115,600 |
| Noel | 54,335 | 54,335 | **0** | 0 | 0 | 0 | 115,600 |
| Ririka | 57,641 | 57,641 | **0** | 0 | 0 | 0 | 115,600 |

- `python -m pytest tests/test_public_v34_svgo_bridge.py -q`: **3 passed**.
- `node --check scripts/public_v34_svgo_candidate.mjs`: **PASS**.
- Chrome Golden gate, first run: **3/3 pass**; intentionally inserted black 340×340 rectangle correctly rejected each time.
- Second independent clean Chrome run: **3/3 pass**, byte-level `fc /b` exact repeat for **four/four evidence files** (Kyoko/Noel/Ririka candidate SVGs + JSON).
- Candidate SHA-256 is **identical to frozen original SHA-256** per case:
  - Kyoko `583b21c49b5cfca0b6a4ec1ee7399c4c26fcf1effcb32ba316919bbc0c7400be`
  - Noel `342a476aa0965f9fc8fc5d0e8f7652fa5e8241b829a1967fe4583ba29d9ff1ff`
  - Ririka `c253f524cdb2d570a6e45809f008f3fa2ccf5a4b19af7aa6a08227500d563b20`

## Engineering decision

**R1 Golden+determinism PASS, library replacement benefit NONE, v34 handwritten path encoder RETAIN.** SVGO generates the same bytes for these already tightly encoded frozen v34 SVGs. No geometry was simplified, no newly source-certified arms/clothing/staff, no alternate palette, no color change or facial feature creation. Do NOT advertise byte reduction beyond v34's pre-existing 43–53% improvement.

**Product HOLD**: Stage8 original-vertex budgets, whole-owner/source semantic authority, human Golden, Safari/DPR, full Public route and licensing are not certified by this limited R1 step. No Public production integration or deploy. Continue with R2 full-owner geometry-oracle work under strict source and pixel gates.

## Preservation

Code + roadmap + this report: GitHub research branch / Draft PR. Read-only evidence output should live at `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R1_20261010/`; source Golden remains in original folders. No need to duplicate originals or three unchanged candidate files into long-lived storage when input manifest + candidate hash identity prove exact bytes.