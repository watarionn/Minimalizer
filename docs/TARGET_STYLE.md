# Minimalizer Target Style

## Status

This document defines the current visual quality target for future Minimalizer quality work.

Formal target name: **Rinka Reference / 凛夏手本版**

The target is not a pixel-perfect reproduction requirement. It is a design-direction reference for what a successful high-quality minimalization should preserve, simplify, and discard.

## Canonical visual reference

Google Drive file:

- file name: `Minimalizer_目標スタイル_超ミニマル幾何学版_20260908.png`
- folder: `chatGPT及びCodex用`
- Drive file ID: `1muN6Lf5IHL8N64i57GAti255xu0sp0xY`
- reference URL: `https://drive.google.com/file/d/1muN6Lf5IHL8N64i57GAti255xu0sp0xY/view?usp=drivesdk`

When ChatGPT/Codex has access to the user's Google Drive, use this file as the primary visual reference for the target style.

## Core objective

Transform an input image into a **highly reduced geometric poster** while preserving the image's identity through large-scale composition, silhouette, color blocking, and a small number of distinctive structural cues.

The goal is not merely to remove detail. The goal is to decide **which information carries the image's identity**, preserve that information, and aggressively remove lower-value visual noise.

## Target visual principles

### 1. Macro composition first

Preserve:

- dominant subject placement;
- major diagonal/vertical/horizontal composition;
- large foreground/background mass relationships;
- the most important negative-space structure;
- a few scene-defining environmental cues.

Prefer a small number of large shapes over many locally accurate fragments.

### 2. Straight-line geometric construction

Target output should strongly prefer:

- straight edges;
- polygons;
- angular planes;
- simplified hard-edged silhouettes.

Curves should be omitted or converted into a small number of straight segments when the image remains readable.

### 3. Face detail is optional and OFF by default for this target

For the Rinka Reference style:

- eyes, nose, mouth, eyebrows, and other facial micro-features are omitted by default;
- the head/face should remain readable through silhouette, hair framing, skin-color block, pose, and placement;
- face details should only be retained when they are essential to the identity of the source and explicitly enabled.

This is consistent with the existing product direction that face primitives are optional rather than core.

### 4. Hair is represented by major flow and color blocks

Preserve:

- overall hair silhouette;
- major direction/flow;
- distinctive parting or large color split;
- a small number of identity-bearing strands or blocks.

Remove:

- fine strands;
- repeated highlights;
- tiny strand intersections;
- texture that does not change the large silhouette.

### 5. Hands become symbols, not anatomy studies

Hands should be simplified aggressively:

- do not render individual fingers in the default Rinka Reference output, even for a fully opened hand;
- collapse each visible hand into one compact angular hand symbol;
- preserve gesture direction through arm orientation, hand placement, and the single hand block rather than digit count;
- remove tiny joints, nail detail, finger gaps, and local contour noise.

A fingerless one-block hand is preferred to a partial three/four-finger silhouette. The latter can look uncanny and is not part of the target style.

### 6. Clothing becomes major masses

Preserve:

- garment silhouette;
- major light/dark separation;
- one or two distinctive accessories or structural cues;
- large folds only when they define pose or volume.

Remove or merge:

- repeated ruffles;
- lace micro-detail;
- small folds;
- repeated trim;
- tiny buttons and ornaments;
- near-duplicate dark facets.

The final outfit should read as a small hierarchy of large geometric masses.

### 7. Background is semantic shorthand

The background should be simplified more aggressively than the main subject.

Keep only enough structure to communicate the scene, such as:

- one or two frames for a gallery;
- a horizon or mountain block for a landscape;
- one architectural plane for an interior;
- one accent object when it anchors the composition.

Remove repeated decorations, small text, clutter, and low-value objects.

### 8. Limited palette

Prefer a compact palette that preserves the source's dominant color relationships.

Color reduction should prioritize:

- subject/background separation;
- signature accent colors;
- major light/dark contrast;
- compositional balance.

Avoid retaining multiple colors that differ only slightly when they serve the same visual role.

### 9. Eliminate low-value fragments

Strongly suppress:

- thin slivers;
- extremely narrow rectangles;
- isolated micro-shapes;
- tiny repeated fragments;
- shapes whose removal does not materially change silhouette, identity, or composition.

This is a core implementation direction for the next quality phase.

### 10. Preserve image identity through hierarchy, not detail count

A good result should still feel recognizably derived from the source even after most details are removed.

Identity should come from:

1. composition;
2. silhouette;
3. dominant color blocks;
4. a small set of distinctive shapes;
5. gesture/pose;
6. only then, optional local details.

## What this means for implementation

Future quality work should increasingly rank candidate shapes by **global visual value** rather than by local contour fidelity alone.

Promising implementation directions include:

- stronger macro-shape selection;
- more aggressive thin/sliver rejection;
- grouping adjacent fragments into one role-bearing shape;
- subject/background-specific simplification strength;
- gesture-preserving hand abstraction;
- garment mass consolidation;
- background semantic compression;
- straight-line polygon preference;
- optional faceless output mode or target-style preset.

Do not implement source-image-specific hacks to reproduce this one reference. Improvements must generalize across the existing regression corpus and future inputs.

## Acceptance mindset

When comparing future output to the Rinka Reference, ask:

- Is the source still recognizable from the large shapes?
- Did we remove details that do not carry identity?
- Are hands fingerless geometric symbols, and is clothing simplified enough?
- Is the background quieter than the subject?
- Are there unnecessary thin rectangles or slivers?
- Is the shape hierarchy intentional and poster-like?
- Does the image feel designed rather than merely traced?

The long-term target is: **input image -> intentional geometric poster**, not simply input image -> fewer contours.


## Phase 8 implementation note: semantic macro rescue

If the normal target-style path demonstrably collapses an opaque character image into multiple giant color slabs, the renderer may switch to semantic macro reconstruction. This is a fallback, not the default path.

The fallback must be evidence-gated and general: detect the failure from composition/shape ratios, recover the subject through Character Structure, and rebuild only a few large semantic masses. Preserve hand/prop gesture cues and distinctive outfit color blocks while preventing head, hair, torso and limbs from being flattened into one polygon. See `RINKA_PHASE8_SUBJECT_PARTITION.md` for the current gates and evaluation rules.


## Phase 9 implementation note: semantic primitive optimization

After the Phase 8 failure gate accepts semantic macro rescue, Phase 9 may construct an explicit Semantic Shape Tree and fit a very small number of part-local simple primitives. The tree keeps face, hair, outfit, limbs, props, and distinctive accessories structurally separate and supplies per-part primitive budgets.

Primitive choice balances raster fidelity with geometric simplicity. Part-aware priors may favor an ellipse-like face or trapezoid-like garment mass, but fidelity guards prevent the preferred family from overriding a clearly better representation. Large outfit primitives are area-limited through scaling and re-evaluation so intentional simplification cannot recreate the giant-slab failure.

Distinctive head-region color cues may be retained conservatively when they are small, saturated, separated from skin/hair/background, and not redundant with another selected cue. See `RINKA_PHASE9_SEMANTIC_PRIMITIVES.md` for the current architecture, rejected experiments, and corpus evidence.

## Phase 11 implementation note: stricter geometric poster abstraction

Phase 11 adopts the expanded faceless geometric reference family reviewed on 2026-09-10. Priority order is: (1) faceless output, fingerless hand symbols, and stronger micro-detail removal; (2) larger hair planes and clothing color blocks; (3) geometric background generation, presets, and UI exposure.

Checkpoint 1 makes faceless behavior explicit in post-processing, turns every recognized hand into one six-vertex beveled polygon per known side, and removes a narrow class of decorative crumbs only after identity-bearing masses exist. Checkpoint 2 then removes short repeated hair strand/bang lines when a nearby filled hair plane already carries identity, simplifies filled hair contours only under raster/area/centroid guards, and flattens nearby same-family garment colors into larger poster blocks while keeping signature accents separate. This is target-style-only behavior; the stable Minimalizer path is unchanged. See `RINKA_PHASE11_GEOMETRIC_POSTER_ABSTRACTION.md`.
