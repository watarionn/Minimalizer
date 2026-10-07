# SA10.27 AnimeSeg observer PoC - 2026-10-08

## Scope

AnimeSeg (`suzukimain/AnimeSeg`) Mask2Former is connected only as an isolated
analysis observer. The parent Minimalizer interpreter never imports `torch` or
`anime_seg`. The observer emits a PNG mask, 12-class pixel counts, model
filename/repository, mask SHA-256, and explicit `authority=false` metadata.

The documented 12-class contract is: background, skin, face, hair_main,
left_eye, right_eye, left_eyebrow, right_eyebrow, nose, mouth, clothes,
accessory. The public model card documents `pip install anime_seg` and the
Mask2Former pipeline. Model v3 is the default pinned filename for this PoC;
v4 is not adopted merely because a public file exists. Weight size, revision,
and SHA must be recorded from the actual isolated environment before any
benchmark claim.

## Safety boundary

- research/observer evidence only; no semantic, geometry, render, or production authority;
- no generated visible content and no background-remover fallback;
- missing canonical Python 3.11 environment, missing weights/token, child crash,
  timeout, nonzero exit, or invalid JSON => `observer_unavailable`;
- Minimalizer production requirements and canonical venv are unchanged;
- GC001 fresh holdout remains sealed until a healthy real observer run exists.

## Current decision

PoC contract and synthetic fail-closed tests pass. Real GPU inference is HOLD:
the dedicated `C:\Work\Temp\Minimalizer-AnimeSeg\.venv` and actual public
weight presence/SHA were not assumed or fabricated. No GC001 production or
Phase 14/15 authority is changed. The next gate is a read-only runtime check,
then one fresh GC001 observer artifact with source-alpha clipping and visual
inspection before exposing the holdout.

## Actual GC001 result

Isolated environment: Python 3.11.9, anime_seg 0.3.8, torch 2.14.1+cpu. The package initially resolved transformers 5.19.0 and failed to load either Mask2Former base model. Pinning `transformers<5` resolved to 4.57.6 and restored compatibility.

Using the README-documented v3 checkpoint (`models/anime_seg_mask2former_v3.safetensors`) on canonical GC001 completed successfully with worker_returncode=0. Mask SHA-256: `ea1be2ff34d3bdbef5693ab3dbe1c60363fe6365cb42454829b96994f3520148`.

Pixel counts: background 59701; skin 3991; face 3468; hair_main 19637; left_eye 212; right_eye 292; left_eyebrow 24; right_eyebrow 56; nose 78; mouth 61; clothes 16223; accessory 11857; unknown 0.

This is a materially useful observation: GC001's current production output loses facial internals, while AnimeSeg independently finds both eyes, both eyebrows, nose and mouth plus a large hair region. The observer remains non-authoritative and does not change visible geometry yet.

Fresh holdout remains sealed in this tranche. The repository blind manifest offers IRyS/Gura/Fauna/Mumei candidates, but the canonical source bytes were not found through direct Drive search and `_sa1016_drive` is forbidden as the source. Do not substitute a tuned or uncertain file merely to claim a holdout result.

Next: convert AnimeSeg class masks into source-clipped saliency constraints for candidate generation, then run the fixed untouched holdout when canonical bytes are grounded.
