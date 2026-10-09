# SA10.60 preflight: immutable Stage8, visual Golden, and production decision separation

Date: 2026-10-09. **Research preflight COMPLETE; source Stage8 HOLD; human Golden HOLD; Phase15 NOT RUN; production UNCHANGED.** This does not mark all of SA10.60 integration complete.

## Baseline and authority

- Base: merged PR #316, main `5242239c95fae968c44ed4567f99d64b520515ae`.
- Code: `tools/research/sa1060_release_preflight.py`; synthetic regression: `tests/zerobase/test_sa1060_release_preflight.py`.
- Actual input metrics: SHA-signed SA10.58 Stage8 report and SA10.59 two-case research review, stored privately in the approved project Drive and coordinate-free versions in `docs/research/evidence/`.
- Private visual boards, original images, candidate SVGs and review template remain in `chatGPT及びCodex用/Minimalizer/SA1059_TwoSourceVisualGoldenReview_20261009`, [approved folder](https://drive.google.com/drive/folders/1McAwnpwHeAUSMy-adwULfU2B0y2gqyep). **Do not publish source pixels or traced coordinates.**
- Existing `docs/TARGET_STYLE.md` default: no visible eyes/nose/mouth/brows. Preserve evidence for face/skin/hair and arm masks; do not add new face plates or generate pixels.

## Read-only preflight engineering

The CLI accepts the two immutable-source-derived *numeric* evidence JSON files, optionally the unapproved human review form, and writes a deterministic coordinate-free report. It never touches signed inputs, makes no SVG changes, invokes no production path, and returns **exit code 2 on HOLD**. It checks historical Stage8 **source** ring costs independently of compact **deployed** SVG costs, reconciles signed source hashes across the two reports, checks real owner-replay mask-collision counters and face/arm interstage guards, and flags missing human validation, corpus expansion and Phase15 runtime/device validation. A forged `PASS` status in evidence or a manually edited all-PASS review form cannot turn this research tool into release authorization; genuine human signoff is explicitly out of band.

Real frozen evidence yields:
- Raden: original Stage8 **2370/1412 FAIL**, research SVG **1409/1412 PASS**; compressed owner mismatches **186**, protected-arm ownership mismatches **11**.
- GC001: original Stage8 **3604/1887 FAIL**, research SVG **1873/1887 PASS**; compressed owner mismatches **467**, protected-arm ownership mismatches **5**.
- Both human identity judgments **PENDING**; only **2** independent signed Golden originals and **6** Chromium candidate replays.
- Preflight returns **HOLD, 9 blockers, no production authorization**. See `docs/research/evidence/sa1060_release_preflight_20261009.json`.

Synthetic regressions: **9/9 PASS**. The same preflight ran against both real private SA10.58 and SA10.59 numeric files; observed HOLD and explicit exit 2. Full Chromium end-to-end replay was **not** rerun during this stage; SA10.59 prior 8/8 and 14/14 replay evidence remains the signed baseline, not a freshly repeated claim.

## Stage8 resolution paths (neither approved yet)

**A. Source-preserving geometry.** Experiment with new generalized encodings or geometry optimizers using signed owner masks. Require original-source owner label preservation, protected face and both arms, topology, true old Stage8 ring occurrence caps **and** separate true expanded SVG caps. Rerender in real Chromium and check source source-visible silhouette/contact and full visual identity. SA10.58's finite 12-epsilon search failed; it was **not** a proof against other algorithms. No lossy proposal can be substituted for the immutable source by copying its under-cap vertex count.

**B. Versioned policy decision.** If A proves unacceptable, prepare a separately reviewed, explicit versioned contract: immutable historical Stage8 input complexity recorded honestly as over-budget; final/expanded output SVG complexity as a distinct bound; new allowed exceptions, source owner protections, compatibility, rollback, human authorization and release audit clearly documented. The present owner has **not** approved this policy. Do not retroactively modify the old authority, silently waive caps, or use this preflight report as an approval.

## Quality/coverage and production gates

1. Continue source-observed faceless fixes, starting with GC001's two arms, shoulder/sleeve interfaces, missing costume structure and hair flow, then Raden's garment masses. Follow semantic-first and first-bad-stage analysis; SHA-pin every candidate, keep signed face/arms unchanged unless new source-evidenced corrections are separately reviewed, and compare to the originals in Chromium.
2. Obtain authentic **human** assessments for each of the six checklist criteria on both source images. The tool's visual observations are diagnostics only, not signed votes.
3. Expand from 2 independent authenticated sources toward the established Approved-18 review and Approved-78 Phase14 gate. New cases require independent source provenance and reproducible artifacts; do not inflate corpus size with 3 versions of the same source.
4. Resolve Stage8 via A or an **explicit user-approved** B before integration. Maintain the old Stage8 record and all rejected candidate provenance.
5. Only then start SA10.60 Phase15 integration tests, and thereafter SA10.61 live device/rollback validation. Audit actual runtime routing before cutover: `AGENTS.md` says Minimalizer 2.0 is default while an older Phase15 status file includes an owner-preferred ZeroBase2 update dated 2026-10-07. Neither statement alone proves the live route today. No web worker, switch, deployment or RDC operation was made here.

## Reproduce

```bash
python tools/research/sa1060_release_preflight.py \
  --stage8 /private/SA1058/sa1058_metrics.json \
  --golden /private/SA1059/sa1059_metrics.json \
  --out /separate/path/sa1060_preflight.json
# Expected exit status: 2 (HOLD), never a release approval

python -m pytest -q tests/zerobase/test_sa1060_release_preflight.py
```

No new external dependency. This research-only preflight does not modify production code, configuration or existing Stage8 policy.
