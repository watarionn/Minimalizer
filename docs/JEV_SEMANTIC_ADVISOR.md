# Jev Semantic Advisor

Status: development QA integration
Contract: `minimalizer-semantic-advisor-v1`

## Purpose

The Jev Semantic Advisor is an opt-in development QA path for the layered-person
Minimalizer pipeline.

It does not change Minimalizer output.

The advisor exists to find hidden semantic planes that may deserve human or
reference review after the deterministic simplification pipeline has hidden
them.

## Why the role is advisory-only

Several isolation generations attempted to convert Jev semantic decisions into
automatic protection decisions.

Those policies performed well on development characters but did not generalize
reliably to unseen characters.

The decisive fourth unseen holdout for the frozen v0.8 automatic-protection
policy produced:

- hidden planes: 173
- render-impacting hidden planes: 18
- true improvement cases: 5
- TP: 2
- FP: 4
- FN: 3
- precision: 33.3%
- recall: 40.0%

Automatic protection was therefore rejected.

The useful capability was retained: Jev can label a small set of
render-impacting candidates as structural mass, distinct accent, redundant
fragment, or uncertain.

## Architecture

```text
layered-person result
        |
        v
deterministic Render Impact Probe
        |
        +-- no pixel change --> ignore
        |
        v
numeric candidate export
        |
        v
optional Jev sidecar
        |
        v
QA semantic labels only
```

## Minimalizer-side responsibilities

`minimalize_engine/v2/semantic_advisor.py` is pure deterministic code.

For each hidden shape it:

1. restores only that shape in a cloned scene,
2. re-renders the semantic part,
3. discards candidates that do not change rendered pixels,
4. measures numeric runtime features,
5. measures whether the restoration moves the part toward the original source
   image,
6. returns immutable `SemanticAdvisorCandidate` records.

It never:

- mutates the source scene,
- changes `SceneShape.visible`,
- changes masks,
- changes primitive geometry,
- changes final rendering,
- uses an Approved/reference image,
- calls Jev.

## Jev boundary

The Minimalizer repository intentionally does not depend on `typesafe-sdk`.

The opt-in exporter:

```text
tools/export_jev_semantic_candidates.py
```

writes the `minimalizer-semantic-advisor-v1` JSON contract.

The external Jev sidecar labels that JSON using numeric/runtime features only.

No image bytes are sent to Jev.

Allowed labels:

- `structural_mass`
- `distinct_accent`
- `redundant_fragment`
- `uncertain`

The sidecar has no authority to:

- change render output,
- change visibility,
- merge planes,
- prune planes,
- generate primitives.

## Opt-in usage

Export candidates from an RGBA development input with source alpha:

```powershell
python tools/export_jev_semantic_candidates.py \
  --input <input.png> \
  --output <candidates.json>
```

Then run the Jev sidecar from the Jev lab:

```powershell
powershell -ExecutionPolicy Bypass -File run.ps1 \
  minimalizer_semantic_advisor.py \
  --input <candidates.json> \
  --output <labels.json>
```

This is an explicit development feature. The normal Minimalizer pipeline does
not invoke it.

## Smoke result

Using the current layered-person branch and Kikirara-Vivi:

- candidate export: 1 render-impacting hidden plane
- Jev label: `structural_mass`
- Jev confidence: 0.82
- second run: 0 API calls, 1 cache hit
- image bytes sent to Jev: false
- render authority: false

## Promotion rule

This advisor may be used for QA triage and comparison-sheet generation.

It must not be promoted to an automatic output-changing gate without a new,
pre-registered unseen holdout evaluation demonstrating generalization.
