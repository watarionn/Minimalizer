# Incident: blind manifests were assumed but not frozen

Date: 2026-10-05
Impact: the sealed five-character Frozen Observer run can be executed honestly, but its evidence cannot be promoted through the feature binder into per-character G3/G4/G5 decisions without a pre-outcome semantic feature manifest.

Cause: earlier roadmap language referred to "frozen manifests", while G8 actually froze only the archive, five source members/hashes, no-Golden condition, rules commit, and adoption gate. No per-character semantic feature manifests were committed before observer outcomes.

Correction: do not create character-specific manifests after seeing the sealed outcomes. Preserve the untouched observer evidence and mark binding as HOLD.

Prevention: future blind suites must freeze source hashes AND evaluation manifests/role vocabulary before first observer execution. A suite preflight must fail if either is missing.

No production rules, thresholds, prompts, or G2-G7 behavior were changed after observing this run.
