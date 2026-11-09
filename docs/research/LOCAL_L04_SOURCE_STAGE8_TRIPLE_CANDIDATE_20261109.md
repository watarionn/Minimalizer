# Local L04 source-only Stage8 triple candidate (2026-11-09)

This is a source-free reproducibility record for a private candidate. It does
not promote L04, Golden, LocalWorker, Public/C08, or production.

## Processing

`tools/research/local_l04_stage8_from_zerobase2.py` builds a private three-file
candidate from the signed original and the source-only ZeroBase2 Phase 8/10/11
artifacts. Human review masks, observer labels, Golden assets, and production
files are not read by inference or geometry generation. Unknown pixels are not
treated as negative. The runner is fixed at commit
`7817f7a4c60c9ac00a40025c236adba19d0f9960`.

The upstream source-only shadow result was mixed: H08 completed Phase 3–12 with
the selected candidate passing (`11` primitives, silhouette IoU `0.999711`),
while H06 reached Phase 8–11 but Phase 12 failed because the selected candidate
lost the `neck` owner on `35` source pixels. This is a concrete FAIL, not a
reason to waive the gate.

## Triple hashes

| Case | Signed source | Stage8 JSON | Expanded SVG |
|---|---|---|---|
| H06 | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` | `2a84f4689cd8f282d98783ee86ec2c95bc31ecdb6815d4f08f127308fdeebeee` | `4c82ccdb11460fef5b207e5e54d6b401f9dc38375f228a142ce3ed2fa96861ac` |
| H08 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` | `078a00f01d339c203bfa53d8d3f9a3597a35cbfcd2d665bbe40122f8d8041db4` | `9ad447aae6abb0eea1b7f23ea2df87ff3b4a36fc76efb513ca539580b365c1c6` |

The private ZIP `MinimalizerLocal_L04_FormalStage8Triple_20261109_PRIVATE.zip`
was uploaded to the owner-private Drive folder and fetched back byte-for-byte:
Drive ID `1O9MgLHjQGiJlglJ7GAtXiQl7gnFS8D7o`, `258330` bytes, SHA-256
`feebb08c58d810bae33758b2859e3de3acc13df539a4efa4773694b65426fc77`.

## Gate result

The three artifact hashes and cross-links verified for both cases. Numerical
eligibility did not pass:

| Case | Source-owner mismatch | Protected face/arm mismatch | Silhouette XOR |
|---|---:|---:|---:|
| H06 | 146475 | 15919 | 68864 |
| H08 | 152791 | 25736 | 22401 |

Therefore `L04_formal=HOLD`, `human_visual_golden=HOLD`, and
`production_release=NO_GO`. The inherited `1887` cap was recorded as
unconfirmed for these Local cases; it is not an independent policy approval.

Next concrete correction: repair the source-only owner/geometry construction,
starting with H06 neck retention and the face/arm ownership collisions, then
rerun the same triple gate. No production or Golden state changed.
