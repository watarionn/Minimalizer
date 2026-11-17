# Local L02 Sapiens2 source-only observation — 2026-11-17

## Purpose

Run a new source-only observation on the signed H04/H06/H08 originals using a
GPU-enabled isolated environment. This is a supporting observation for the
six-capability L02 observer work; it is not a Phase4 approval or a production
candidate.

## Fixed inputs and runtime

- Observer: `facebook/sapiens2-seg-0.4b`
- Model revision: `449b3c5335e6722bb94990abdd1aa6e612432f22`
- Checkpoint SHA-256:
  `b85fdb50b7d6123a967d5ee4a505e222baff8d2f7ad6bbf353578c1a61dfbac9`
- Source-only inference: `true`
- Human masks used in inference: `false`
- Owner arrays used in inference: `false`
- Unknown treated as negative: `false`
- Private receipt SHA-256:
  `92c60db40980e34afa43484bf54d544045e92768a44d1085a7e6e526a911b07e`

The private receipt and NPZ observations remain outside this repository.

Drive preservation and readback:

- Folder: `L02_Sapiens2_SourceOnly_20261117`
- Folder ID: `1-8AYHzPOiLjPXAInagiLfFx1zfCwzYQB`
- Receipt file ID: `1FMXbobnyrvHpi97mjPvVC5Inw4wRM8Um` (2,037 bytes)
- H04 NPZ file ID: `1rMPMIfi8s4L8rwnXYs3VOqsKDALRCB-O` (13,189 bytes)
- H06 NPZ file ID: `1g6dsRMJyEnRbU0OcSFwqzyiBF-PX8qX5` (26,091 bytes)
- H08 NPZ file ID: `1imd9XlMBaxvGer_ZUX9i5-Jpd0jNmXAW` (22,238 bytes)

All four files were fetched again from Drive after upload; names, MIME types,
parent folder, and byte sizes matched the local upload set. The SHA-256 values
below are the local bytes recorded in the receipt and are not inferred from
Drive metadata alone.

## Source binding and observations

| Case | Signed source SHA-256 | Shape | Arm pixels | Garment pixels | Outside-alpha pixels |
|---|---|---:|---:|---:|---:|
| H04 | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` | 1400×453×4 | 393 | 179035 | 0 |
| H06 | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` | 2000×2000×4 | 86 | 542016 | 0 |
| H08 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` | 2000×2000×4 | 100 | 394027 | 0 |

Private NPZ SHA-256:

- H04: `18e7695360514762e91a01826ed5b606a469437d5f8c702eac8f3a23279856bd`
- H06: `102e5cdd2f8ffcdff81a93dc89adb4e7299307a9cc8136e34ae7ca6dac20082f`
- H08: `3ea0a6f46c381b561d75a58701be7d094709b2122b125cff0ae1fce47c577f4b`

## Gate interpretation

This run proves a reproducible source-only arm/garment observation for all
three signed sources. It does **not** provide sleeves, underlayer-vs-outerwear
ownership, pairwise occlusion, or person-internal instance grouping. The
existing six-capability gate therefore remains `CAPABILITY_HOLD`, and Phase4
and Phase5 remain `HOLD`/`NO_GO`.

The next A implementation must either extend this observer with those missing
capabilities or train/introduce a separate observer on an admissible,
source-bound dataset. It must then be rerun with the same three-case,
source-only contract before any owner evaluation is requested.
