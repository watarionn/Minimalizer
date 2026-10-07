# SA10.31 Handoff (2026-10-08)
Repository watarionn/Minimalizer, branch feat/sa1026-external-adoption. Last confirmed commit e0920aa (SA10.30). SA10.31 NOT implemented. Do not merge or deploy unverified candidates.

CRITICAL USER CORRECTION: Minimalizer must NOT draw, invent, restore, or overlay eyes, mouth, or any other missing face parts. AnimeSeg is source OBSERVATION only, never render authority. Preserve actual source features by adjusting/splitting/recoloring EXISTING primitives using observed source contours and color boundaries. No generated pixels, img2img, inpainting, source pixel paste, or inferred anatomy. Previous proposal for post-repair facial polygon overlays is REJECTED.

SA10.28 commit 4e2a8da: source alpha clipped AnimeSeg constraints.
SA10.29 commit f5ad47d: opt-in AnimeSeg detail candidate groups.
SA10.30 commit e0920aa: real GC001 comparison runner. Actual result baseline 11 primitives, candidate 11 primitives, retained face detail 0, identical PNG hashes, HOLD_NO_OUTPUT_DELTA, production_promotion=false. 913 tests passed. This is NOT an improvement.

GC001 local evidence:
source C:\Work\Temp\macro-gc001\GC001_source.png
Phase11 C:\Work\Temp\sa1023-gc001-clean3\GC001_source\phase_11\11_composition.json
Phase4 C:\Work\Temp\sa1023-gc001-clean3\GC001_source\phase_04\part_masks
AnimeSeg C:\Work\Temp\sa1026-animeseg-gc001-v457\animeseg_mask.png
SA10.30 results C:\Work\Temp\sa1030-gc001\metrics.json and baseline/ and animeseg_opt_in/ PNG SVG
Runner tools/run_sa1030_real_gc001_benchmark.py
Worktree C:\Users\watar\AppData\Local\Temp\Minimalizer-sa1017
Python C:\Work\Projects\Minimalizer\.venv\Scripts\python.exe

NEXT: Diagnose why structural-source-repair reduces the face to one protected primitive and drops observed source facial boundaries. Implement source-grounded refinement OF EXISTING FACE/HAIR PRIMITIVES ONLY, preserving owner, material, silhouette, connectivity, holes, Euler topology, boundary, fragmentation and primitive budget. Do not create standalone eye or mouth geometry. Re-run actual GC001 baseline/candidate SVG PNG with source boundary/color survival and hard gates. Fail closed, no production promotion until actual improvement. Do not open blind holdouts. Tests/zerobase full, compileall, git diff --check, document and push verified changes. Store permanent artifacts under GitHub or Google Drive chatGPT??Codex?/Minimalizer. Never stage unrelated untracked _animeseg_stderr.txt or _sa1016_drive/. PowerShell piping Japanese to codex exec garbles text, and English Codex prompt may be rejected by AGENTS.md; avoid repeating those failed paths.
