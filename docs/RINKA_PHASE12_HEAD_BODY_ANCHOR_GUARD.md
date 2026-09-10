# Rinka Reference Phase 12: Head / Body Anchor Guard

## Goal

Phase 12 addresses a newly observed opaque-thumbnail failure class where a plausible portrait is reduced to a few giant slabs and the face/hair/body relationship disappears.

The target rule is semantic rather than anatomical detail: face features remain omitted, but the **face plane itself**, a **major hair mass**, and at least one **body/torso mass** must survive.

## Trigger strategy

The normal Phase 10 segmentation path is unchanged. When segmentation reaches `confidence_gate`, its candidate mask/RGBA is now retained as inactive evidence. Phase 12 may reuse it only when the normal Rinka baseline is visibly collapse-like.

Two guarded collapse patterns are accepted:

- `three_slab`: three unusually dominant filled shapes plus strong portrait-center evidence;
- `two_slab_poster`: two near-quarter-canvas slabs, very high center fill, and stronger border/background evidence.

The gate is generic. It does not use filenames, character names, or fixed source colors.

## Anchor reconstruction

After a Phase 12 rescue candidate is rebuilt through the existing six-color subject-plane scaffold:

- a faceless skin-colored hexagonal face slab is recovered from the upper-center subject region;
- if a warm/blond portrait connects face/hair/arm into one broad skin-like component, a conservative central geometric face fallback is allowed;
- a large bright low-chroma hair mass is recovered behind the face as a small polygon;
- Phase 12 face/hair anchors cannot be swallowed by ordinary mass consolidation.

## Repair quality gate

A candidate repair is accepted only when all macro anchors survive and the rebuilt subject remains spatially credible:

- face anchor present;
- hair anchor present;
- at least one torso/body anchor present;
- subject-plane coverage >= 0.64;
- outside-subject overdraw <= 0.04.

Any failure restores the pre-Phase-12 baseline output. The rescue therefore cannot become a general lower-confidence segmentation path.

## Current validation

The supplied white-hair regression activates `three_slab` and now keeps a 6-vertex face slab, a 5-vertex major hair plane, and torso masses. The supplied red-poster regression activates `two_slab_poster`; its previous 7-shape collapsed result is replaced only after the same anchor/coverage gate passes.

The fixed 16-image corpus remains intentionally unaffected: Phase 12 rescue activates 0/16 times. Existing Phase 11 corpus metrics remain about 31.10% mean shape reduction and 21.59% mean vertex reduction, with geometric backgrounds on 15/16 and all 45 generated poster panels surviving.

Closure validation on 2026-09-11: 265 passed / 2 known missing-fixture deselections repository-wide, dedicated Phase 12 tests 6/6, compileall passed, Web JavaScript syntax passed, `git diff --check` passed, and real-Uvicorn smoke returned HTTP 200 for Standard, both Rinka presets, and Color Strip.
