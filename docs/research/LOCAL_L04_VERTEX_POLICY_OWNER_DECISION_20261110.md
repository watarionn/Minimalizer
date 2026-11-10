# Local L04 vertex policy owner decision packet (2026-11-10)

**Decision status: OWNER_DECISION_REQUIRED / L04 HOLD / production NO_GO**

This is a source-free decision packet. It does not change the current vertex
policy, the Stage8 artifacts, LocalWorker, Public/C08, Golden, or iPhone state.
Its purpose is to make the remaining L04 decision concrete instead of hiding it
inside a test failure.

## What is already verified

The current Lane B candidate has passed the source-free structural gate and the
focused test suite. The private candidate metrics are:

| Case | Expanded SVG vertices | Current inherited cap | Result |
|---|---:|---:|---|
| H06 | 72,201 | 1,887 | over cap |
| H08 | 56,249 | 1,412 | over cap |

The source-preserving candidate also records zero source-owner mismatch, zero
protected-face/arm mismatch, and zero Chromium silhouette XOR for the private
candidate. These facts make it a reviewable candidate, not a formal release
approval. The current gate intentionally keeps `L04_formal=HOLD` even when
triple hashes and raster equality pass.

## The three valid choices

### A. Keep the inherited cap

Keep H06 `1,887` and H08 `1,412` as hard limits.

- Current candidate remains rejected by L04.
- No policy change is needed.
- Completion requires a new source-preserving representation that fits both
  caps while retaining exact source and browser parity.

### B. Approve a versioned Local-specific cap

Create an explicit Local policy revision that permits the measured geometry.
The owner must specify all of the following in a signed, source-free policy
receipt:

- whether the cap is per-case (`72,201` for H06 and `56,249` for H08) or one
  common cap (`72,201` for both);
- whether every expanded SVG path vertex is counted, including holes,
  fragments, and support geometry;
- maximum SVG bytes, parse time, render time, and memory for the Local device;
- required Chromium 1x/2x parity and failure behavior;
- rollback target and the fact that this policy applies only to Local L04, not
  Public/C08 or Lane A quality.

After that receipt exists, the exact private source/Stage8/SVG triple must be
replayed under the approved policy. A policy change alone is not a quality
PASS.

### C. Reject the current representation and redesign the encoding

Keep the inherited caps and replace the expanded-SVG representation with a
source-preserving encoding whose measured cost fits the existing limits.

- No cap waiver is needed.
- The new encoding must pass the same source, alpha, RGB, browser, security,
  and rollback gates.
- A smaller byte size or fewer named shapes is not evidence of a lower vertex
  cost unless the gate counts the expanded geometry itself.

## Required owner operation

The owner should create one decision receipt containing:

```text
policy: A | B | C
scope: Local L04 only
H06 cap: <integer or unchanged>
H08 cap: <integer or unchanged>
counting_rule: <expanded geometry rule>
runtime_limits: <bytes/time/memory>
rollback_target: <release identifier>
authorization: <owner identity and timestamp>
```

Until that receipt is read back and authenticated, PR #451 remains Draft and
`L04_formal=HOLD`. No code path may silently treat `72,201` as an approved cap.

## Independence boundary

This decision concerns only Lane B's representation budget. It does not relax
Lane A's observer capability gate, semantic owner requirements, Phase4/Phase5,
human visual review, or the handoff requirement that A supply a completed
Stage8/SVG set.
