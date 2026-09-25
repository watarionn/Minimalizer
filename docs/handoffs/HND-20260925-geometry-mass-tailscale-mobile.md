# Minimalizer handoff — 2026-09-25 Geometry Mass + Tailscale Mobile Local Worker

## Canonical branches / commits

- `main`: `de63b24ba9516567a34e952ff562d6483342a593`
  - PR #41 merged: **Add Tailscale mobile Local Worker routing**
- Geometry Mass branch: `feature/semantic-geometric-mass-pass`
  - Geometry Mass final-complexity guard commit: `54b04f7bfe56d6bbaee3f8b2776888e30db9996e`
  - Code checkpoint after merging current `origin/main` (before this handoff-doc commit): `b827c9059ff01231a96d363ba8d92b9889aa5e8c`
- Geometry Mass worktree:
  - `C:\Users\watar\Documents\Minimalizer-geometric-mass`
- Main worktree:
  - `C:\Work\Projects\Minimalizer`

## Geometry Mass current design

`LayeredPersonConfig.semantic_geometric_mass` remains **default OFF**.

Goal:
- do not slightly perturb already-simple parts;
- target only genuinely jagged semantic body polygons;
- keep broad angular masses rather than rounded contour-following geometry.

Current safety stack:
1. candidate polygon fit uses semantic-plane safety constraints;
2. strict paint-coverage guard;
3. minimum vertex savings gate;
4. final tail is evaluated both with and without Geometry Mass;
5. Geometry Mass is accepted only when final cleanup:
   - does not increase visible shape count; and
   - reduces polygon vertices by at least 6.

Important implementation helpers in `minimalize_engine/v2/pipeline.py`:
- `_build_semantic_geometric_mass`
- `_semantic_geometric_mass_is_safe`
- `_guard_semantic_geometric_mass`
- `_semantic_scene_complexity`
- `_semantic_geometric_mass_final_is_simpler`

## Current authoritative A/B

Use `docs/handoffs/data/HND-20260925_geometry_mass_ab.json` as the current compact checkpoint.

- Otonose-Kanade:
  - 38 -> 38 polygon vertices
  - output unchanged
- Omaru-Polka:
  - 441 -> 441
  - output unchanged
- Sakura-Miko:
  - 643 -> 514
  - 129 vertices removed
  - visible shapes 8 -> 8
  - color delta -0.0000540
  - edge delta +0.0048428
  - silhouette delta -0.0004260

This is the desired current behavior: simple cases are skipped; Miko's highly jagged lower-body geometry is simplified.

## Mori regression found and fixed

Approved case order 10, Mori-Calliope exposed a failure mode before the final-complexity guard:

- baseline right_arm: 2 visible shapes / 362 vertices
- Geometry Mass path: 3 visible shapes / 566 vertices

The mass candidate itself looked simpler, but downstream render-dead / cleanup visibility changed and the final scene became more complex.

Fix:
- compare the fully-finished baseline tail vs mass tail;
- reject mass if visible shape count grows or final vertex savings are < 6.

After fix:
- Mori right_arm baseline = mass = 2 shapes / 362 vertices.

Reference incident data is preserved as:
- `docs/handoffs/data/HND-20260925_pre_final_complexity_guard_batch1_ab_REFERENCE_ONLY.json`

Do **not** treat the old Mori numbers as current behavior.

## Approved-68 audit warning / next step

The first batch scan file:
- `docs/handoffs/data/HND-20260925_pre_guard_candidate_scan_REFERENCE_ONLY.json`

is **not authoritative**.

Reason:
- it wrapped `_build_semantic_geometric_mass()` and counted candidate changes **before**
  `_guard_semantic_geometric_mass()` and the final-complexity guard.
- It therefore reported Riona, Shiori, and Mori as changed even when final output later rolled back.

Next chat should rebuild the Approved-68 scan so it records **final accepted output only**:
- one Geometry Mass ON run per case;
- compare final `person_part_presets` complexity against a baseline-tail or otherwise record only post-guard accepted mass results;
- only run expensive baseline A/B for cases whose final accepted output truly changes.

Do not continue from the old `changed_cases=3 / savings=1027` value.

## difficult7 / reproducibility

Pipeline + RTMLib were tested for reproducibility on Miko:
- same guidance, repeated pipeline run: PNG SHA identical, pixel diff 0;
- regenerated RTMLib guidance with same model/session: output still identical.

Earlier sign differences in Miko deltas were caused by changing Geometry Mass implementations between experiments, not runtime nondeterminism.

## Tailscale mobile Local Worker

PR #41 is merged and Railway production is on:
- `de63b24ba9516567a34e952ff562d6483342a593`

Production URL:
- `https://minimalizer-web-production-a2bc.up.railway.app/`

PC local mode:
- `?localWorker=1`
- connects to `http://127.0.0.1:28765`

Mobile / remote mode:
- `?localWorker=tailscale`
- connects to `https://ywshtmr.tail8fd68c.ts.net:28765`
- Tailscale Serve proxies tailnet-only HTTPS to `127.0.0.1:28765`
- **Tailscale Funnel is not enabled** for this port.

Validated browser result metadata:
- `Minimalizer 2.0 Local · Tailscale Local Worker · rembg+rtmlib · 40 shapes · 400x400`

Validated:
- PC Tailscale online;
- iPhone node `iphone-15-pro` online on same tailnet;
- Tailscale health endpoint returns 200 / ready=true;
- real Raden image POST returns `v2-local-worker`, `compute=local-worker`, `analysis=rembg+rtmlib`, RTMLib selected true;
- user confirmed successful real use from mobile Chrome while away from home.

Scripts merged into main:
- `scripts/install_tailscale_mobile_worker.ps1`
- `scripts/uninstall_tailscale_mobile_worker.ps1`

## Raden mobile stress case / Google Drive

The Raden source and route-diagnosis assets are in Google Drive under:
- `Google Drive/Minimalizer/_transfer/`

Important files:
- `Juufuutei-Raden_pr-img_05.webp`
- `Juufuutei-Raden_localworker_fail_20260925.png`
  - this was proven pixel-identical to Railway fallback, not Local Worker
- `Juufuutei-Raden_mobile_tailscale_localworker_20260925.png`
  - latest user-confirmed successful mobile Tailscale Local Worker output

This latest mobile output is still low quality visually, but the compute route is now known-good. Future work should treat it as a **quality** case, not a routing case.

## Local artifact locations still useful through RDC

- `artifacts/geometry_mass_ab/`
- `artifacts/geometry_mass_difficult7/`
- `artifacts/geometry_mass_approved68/`
- `artifacts/user_stress/raden_20260925/`
- `artifacts/raden05_route_probe/`

The handoff JSON copies in GitHub are the durable minimum needed to avoid losing the audit context.

## Immediate next action

1. Start from `feature/semantic-geometric-mass-pass`.
2. Confirm branch is clean and based on current main.
3. Run relevant regression tests.
4. Replace the invalid Approved-68 pre-guard scan with a **post-final-guard accepted-change scan**.
5. For true changed cases only, run A/B vs Approved reference and create visual comparison sheets.
6. If stable across Approved-68, decide whether `semantic_geometric_mass` can move toward default-on / production integration.
7. Continue improving visual quality; mobile Tailscale transport is considered closed unless a routing regression appears.
