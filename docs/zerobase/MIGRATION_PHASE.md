# ZeroBase Migration Phase

Status: **CLOSED / INITIAL QUALITY HOLD — SUPERSEDED BY PRODUCTION QUALITY COMPLETION**

## Evidence

- Approved-78 source corpus: 78/78 SHA-256 verified.
- Approved-78 reference corpus: 78/78 SHA-256 verified.
- ZeroBase deterministic stage captures: 78/78 generated.
- Saved-Evidence replay: 78/78 deterministic.
- Phase 12 artifact-presence gate: 78/78 replayable in the verified local capture.
- Large replay artifacts remain local/ignored; the committed capture report records the reproducible evidence.

## Approved-78 production comparison

| Metric | ZeroBase | Minimalizer 2.0 |
| --- | ---: | ---: |
| Mean silhouette IoU | 0.395515 | 0.411292 |
| Silhouette wins | 16 | 52 |
| Mean foreground-ratio error | 0.541351 | 0.462800 |
| Foreground-ratio wins | 4 | 64 |

## Decision

Production switch is **not authorized**.

The ZeroBase foundation is deterministic and replayable, but the current deterministic baseline regresses against Minimalizer 2.0 on both migration-quality dimensions. The observed foreground occupancy is especially weak.

The current production pipeline is SLIC-region driven and does not yet provide a production-grade foreground/subject-semantic selection path. As a result, background regions remain eligible drawable regions. Objective-weight tuning alone must not be used to conceal this structural gap.

## Gate

The dedicated MigrationGate fails closed unless:

1. all 78 source bindings are SHA-256 verified;
2. all 78 Approved references are SHA-256 verified;
3. all 78 saved-Evidence replays are deterministic;
4. ZeroBase mean silhouette IoU does not regress versus Minimalizer 2.0;
5. ZeroBase mean foreground-ratio error does not regress versus Minimalizer 2.0.

Current result: switch_authorized = false.

Minimalizer 2.0 remains production. The next engineering campaign is production-quality foreground/subject-semantic integration, followed by the same Approved-78 Migration Gate rerun.


## Superseding result

Production Quality Completion subsequently integrated canonical alpha foreground evidence and reran all 78 cases. The current authoritative migration result is recorded in `PRODUCTION_QUALITY_COMPLETION.md` and `MIGRATION_GATE.json`: `switch_authorized=true`. The HOLD above is retained as the historical pre-fix audit.
