# SA7.41 Background Residual Field Attribution — 2026-10-06

Status: EVALUATION COMPLETE / MULTI-COMPONENT GAP IDENTIFIED

SA7.41 decomposes the remaining SA7.40 background gap using the same source-derived Lab palette clustering as the production background field geometry.

Golden is used only to measure residual error after source-only field discovery.

## Key finding

The remaining background gap is not caused by a missing third palette color.

The third black source cluster is tiny:
- largest components: 74 px each
- field ratio: about 0.12%
- weighted gap: about 0.00016 per component

These black corner fragments are not meaningful next targets.

## Dominant source clusters

### Orange cluster

Current production keeps the largest component:
- 23,420 px
- safe polygon: yes
- current candidate median already matches source
- weighted gap: 0.02077

But the same source palette cluster also contains major disconnected components that are safe and currently omitted:

- 5,058 px, bbox [0,171,73,134]
  - source median [255,134,46]
  - current candidate median [255,255,255]
  - Golden median [253,130,37]
  - weighted gap 0.01207
  - safe polygon: yes

- 3,891 px, bbox [0,0,105,59]
  - source median [255,134,46]
  - current candidate median [255,255,255]
  - Golden median [253,130,37]
  - weighted gap 0.00910
  - safe polygon: yes

A 266 px component is also safe but below the existing 3% field-ratio contract and should remain omitted.

### Red cluster

Current production keeps:
- 16,819 px
- safe polygon: yes
- candidate/source palette already aligned
- weighted gap 0.01132

The same cluster also contains one major omitted safe component:
- 3,913 px, bbox [165,0,118,97]
- source median [254,35,8]
- current candidate median [255,255,255]
- Golden median [250,32,18]
- weighted gap 0.01228
- safe polygon: yes

## Root cause

SA7.33 conflated palette-cluster count with output-field count by selecting only the largest connected component from each cluster.

The source contains multiple large, disconnected components with the same semantic background palette role. Those components were silently dropped even though they satisfy the existing source-support and subject-overlap guards.

## Decision

Do not lower the minimum field-ratio threshold.

Do not promote the tiny black cluster.

Next: SA7.42 Multi-Component Background Field Geometry.

Keep at most three source palette clusters, but permit multiple major connected components per cluster under the existing:
- minimum field ratio 3%
- source coverage guard
- expansion guard
- zero subject overlap guard

Bound the global number of rendered background fields separately from the palette-cluster count.
