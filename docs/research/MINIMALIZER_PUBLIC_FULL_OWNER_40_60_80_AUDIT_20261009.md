# MinimalizerPublic 11-owner whole-character budget audit (2026-10-09)

**Research diagnostic completed / source-signed geometry protected / full-character Golden and production NO-GO.** Extension of draft PR #324.

Two frozen SHA-signed Stage8 source contour JSONs were retrieved privately from `chatGPT及びCodex用/Minimalizer/SA1034_Phase8_ExactReplay_20261008`. Their hashes remain GC001 `7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08` and Raden `be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f`. The original source PNG SHA was checked and unchanged. Original signed owner z-order was preserved per character. No signed ring points or source portraits are committed in this public report.

## Signed owner geometry cost

Each source has 11 Stage8 owner masks; 10 are painted, one head owner is structural support. Replacing every painted mask with ONE exact, hole/diagonal-safe SVG compound path plus ONE observed RGB base undercoat takes **20 shapes**, but the boundary paths have large hidden complexity:

| Case | Original immutable Stage8 rings | Immutable Stage8 cap | New 10 exact painted boundary paths | Color shapes left under 40 |
|---|---:|---:|---:|---:|
| GC001 | 3,604 | 1,887 | **5,353 vertices** | 20 |
| Raden | 2,370 | 1,412 | **3,586 vertices** | 20 |

This is **not a source ring budget solution**. One compound SVG path is not equivalent to one vertex; original Stage8 input complexity remains immutable and on HOLD.

## Actual research-only 40/60/80 full-scene Chromiums

An isolated diagnostic rendered all 10 source-signed owners, true original z-order, source-visible alpha guard, one original RGB base per owner and greedily allocated source-observed RGB rectangles. Facial microfeature overlays were forbidden (0 face color plane overlays); face remains a flat observed fill, which is NOT yet human-approved and may look like an unwanted skin plate. No raster <image>, generated fill, img2img or synthetic anatomy was used.

| Case | 40-shape union-masked original-source RGB MAE | 60 | 80 |
|---|---:|---:|---:|
| GC001 | 48.651273 | 44.038568 | 41.146877 |
| Raden | 25.142569 | 22.626297 | 21.330076 |

Actual Chromium 144, 340x340 @ DPR1/DPR4: 6 full-scene SVG candidates all had **0 alpha outside all ten original source-visible role masks and 100% union coverage**. These are geometry-parity checks only, **NOT** a Golden/identity/costume correctness PASS. Stage8 z-overdraw, topology semantics, retained details, and color readability require independent full-scene review. Human Golden remains PENDING.

## Critical visual findings / release decision

- The 40-shape full scene is deliberately crude: hair, tie, clothing motifs and arm color facets are overly simplified. Some GC001 torso paint and Raden hair have blocky planes, and the flat face plate fails to establish intended faceless styling quality.
- The new exact-vector clip shape count meets an isolated diagnostic DOM element count (40/60/80) but its expanded vector **vertex** count fails original historical caps for both sources.
- No feature flag, deployment or production edit was performed. Current production is unchanged.
- Need a different source-authorized compression approach or an explicit, separately approved **versioned policy migration**, plus real human Golden, mobile Safari and full-harness tests before integration. Never waive Stage8 caps silently.

Relevant reproducibility code and signed real-image contact sheets reside in private user-facing `MinimalizerPublic_Compact_SignedPlanes_20261009.zip` (no raw Stage8 source ring JSON is to be published to GitHub). Research-only code includes `full_owner_prepare.py`, `full_owner_complexity.mjs`, `full_scene_trial.mjs`, and `full_scene_browser.py`.
