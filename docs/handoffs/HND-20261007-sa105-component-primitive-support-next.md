# Handoff — SA10.5 GC001 Component-to-Primitive Support — 2026-10-07

Status: SA10.4 CONTRACT COMPLETE / SA10.5 NEXT

Goal: derive explicit GC001 represented-component and source-supported-primitive counts from scene/provenance, not from allocation count alone.

Requirements:
- use SA7.43/SA7.44 source masks and emitted macro geometry;
- establish role-local overlap/support for each emitted primitive;
- count a source component as represented only with explicit deterministic support;
- count a primitive as source-supported only with explicit overlap/support evidence;
- preserve thresholds as measurement-contract parameters, not quality gates;
- feed the resulting evidence into SA10.4;
- reassemble GC001 SA10 diagnostics;
- no Golden pixels, DINO score, or teacher labels may create support evidence.
