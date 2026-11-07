# L02 H06 independent arm-observer replay, 2026-11-07

**Research evidence only. No owner promotion, Phase4 approval, Golden change or production release.**

This note records a source-free replay of two independently pinned SCHP observers against the exact signed H06 source. The class maps were frozen before any reviewed-mask comparison and were preserved outside GitHub. No human labels, owner masks or annotation geometry were inference inputs.

## Immutable input and model pins

- Signed encoded H06 source SHA-256: `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`.
- Decoded RGBA source SHA-256: `c4c4891542c80d9d2f61c45c1b6794722e5dfceed837179ae83352995e4522b5`.
- SCHP-ATR18 revision: `a54fa65e7e4f27f21011f652ffc0053ebb24b292`.
- SCHP-ATR18 ONNX SHA-256: `4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5`.
- SCHP-LIP20 revision: `3cc2b2d00b16840652c1b7845fd78466dae7f157`.
- SCHP-LIP20 ONNX SHA-256: `871c9e209dc67d6be61c73dcc79cb49e638fcf5bbc35a19b4c7429eba0bfc046`.

Both runs used CPU-only offline inference, the existing fail-closed adapters, the declared white-alpha composite and fixed source-size projection. No generated pixels were created.

## Frozen source-only outputs

| Observer | Frozen class-map SHA-256 | Relevant opaque output | Result at the current five-pixel H06 shadow delta |
| --- | --- | --- | --- |
| ATR18 raw `logits` | `334b4037bf25eed152339a435a031bc2a073fff1459574470523b56046c980a3` | upper-clothes 315,765; left-arm 1,420; right-arm 6,320; bag 0 | classes are `0, 4, 0, 0, 0`; no arm class |
| LIP20 `logits` | `4d025535f1d2e1bac65f534e757e10a5c312ca5213ce4b4d2d0c4aaa72f23db9` | coat 85,206; arm/glove/upper-clothes 0 | all five are class `0`; no coat or arm class |

The five-pixel delta refers only to the already-frozen source-only candidate count; no private coordinates are stored in this repository. The observer outputs do not provide a positive arm/coat owner signal at those pixels. Their class-0 absence cannot be used as a negative semantic label, so the observers do not authorize a larger H06 removal or an owner reassignment.

The A shadow now has a source-only post-proposal guard, `protect_independent_garment_observers`. It restores a candidate erasure when ATR18 explicitly predicts `upper_clothes` or LIP20 explicitly predicts `upper_clothes/coat`, after verifying the frozen private class-map SHA. It never promotes an owner and never treats observer absence as negative evidence. On exact H06 replay, this guard restored one ATR18-positive pixel and changed the candidate from five removals to four.

The requested ATR dual-head replay was attempted with the same authenticated model bytes. The exact model exposes only `logits`; the adapter-required `parsing_logits` output is absent. The adapter returned `UNEXPECTED_SCHP_ATR_INTERFACE_OR_PROVIDER` and no dual-head map was accepted. This is a fail-closed interface finding, not a quality result.

## Gate result

- Existing H06 class32 shadow remains the bounded candidate: correct-garment loss `0`, four pixels removed after the observer guard, four reviewed wrong-owner pixels and zero unknown pixels removed after freeze.
- Independent ATR/LIP evidence authorizes protection of one explicit garment-positive pixel, but adds no new H06 owner removal and no accepted P0/P1 improvement.
- Human labels remain postscore-only; unknown pixels remain unknown, not negative.
- `Phase4=FAIL`, `L02=HOLD`, `Golden=HOLD`, `production=NO_GO`.

The private class maps and source-free receipts were uploaded to the existing private research evidence folder and downloaded again. Array SHA-256 and receipt pins matched after readback. No private image, NPZ, coordinate or annotation geometry is included here.

## Exact-head source-free QA readback

At PR #449 HEAD `b4163e95368cbb8fe68f7431e5945bf0e754d7fd`, the five A-only
class32 shadow suites were rerun with the repository research path explicitly
added to `PYTHONPATH`: **66 passed, 4 subtests passed**. This covers the
color-positive, frontier-positive, robust-frontier, topology/palette and
topology-positive modules. Python compilation and `git diff --check` also pass.

The broader historical `tests/test_local_l02_*.py` collection is not a valid
single-suite result in the stock interpreter: six unrelated legacy tests stop
during collection because their optional scikit-learn dependency is absent.
That environment limitation does not weaken the focused PR-head result above;
those legacy tests were not silently counted as passed.
