"""SA10.33 real Phase12 full-scene reproduction and export authority gate.

This script recomputes the original selected candidate in memory and compares
its *actual mask replay* against serialized vector geometry and saved preview.
Nothing is patched, regenerated as an input, or promoted to production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.evaluation.source_silhouette_anatomy_gate import (
    evaluate_source_silhouette_anatomy,
)
from minimalizer_zerobase.image_io import read_cv_image
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import apply_face_raster_guard
from minimalizer_zerobase.simplification import StyleSimplificationPolicy, simplify_composed_scene
from minimalizer_zerobase.simplification.artifacts import _candidate_render
from minimalizer_zerobase.reviewed_sa10.phase7_geometry_authority import (
    WATCH_OWNERS, mask_fidelity, owner_fidelity, zorder_visibility,
)
from tools.run_sa1032_gc001_owner_audit import audit_records, scene_records


def _json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return payload


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(
    *,
    case_dir: Path,
    source_path: Path,
    phase12_dir: Path,
    benchmark_path: Path | None = None,
) -> dict:
    phase04_dir = case_dir / "phase_04"
    phase11_dir = case_dir / "phase_11"
    phase04_stage = _json(phase04_dir / "stage.json")
    phase11_stage = _json(phase11_dir / "stage.json")
    phase12_stage = _json(phase12_dir / "stage.json")
    saved_scene = _json(phase12_dir / "12_simplification.json")
    scene = _json(phase11_dir / "11_composition.json")
    source_sha = _sha(source_path)
    matching_source_contract = all(
        stage.get("source", {}).get("sha256") == source_sha
        for stage in (phase04_stage, phase11_stage, phase12_stage)
    )
    source = read_cv_image(source_path, cv2.IMREAD_UNCHANGED)
    if source is None or source.ndim != 3:
        raise ValueError("GC001 source must be readable image")
    if source.shape[2] == 4:
        source_rgba = cv2.cvtColor(source, cv2.COLOR_BGRA2RGBA)
    elif source.shape[2] == 3:
        source_rgba = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
    else:
        raise ValueError("unsupported original source channel count")
    height, width = source_rgba.shape[:2]
    masks: dict[str, np.ndarray] = {}
    for owner in PART_NAMES:
        raw = cv2.imread(str(phase04_dir / "part_masks" / f"{owner}.png"), cv2.IMREAD_GRAYSCALE)
        if raw is None or raw.shape != (height, width):
            raise ValueError(f"Phase04 source-owned mask missing/wrong size: {owner}")
        masks[owner] = raw > 0

    policy = StyleSimplificationPolicy()
    result = simplify_composed_scene(scene, policy=policy, source_rgba=source_rgba, source_part_masks=masks)
    selected = result.selected
    if selected is None:
        raise ValueError("Phase12 selected no candidate; fail closed")
    records = scene_records(saved_scene)
    saved_record_equality = (
        json.dumps(list(selected.primitives), sort_keys=True, ensure_ascii=False)
        == json.dumps(records, sort_keys=True, ensure_ascii=False)
    )
    selection_equal = saved_scene.get("selected_name") == selected.name
    policy_digest = hashlib.sha256(
        json.dumps(policy.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    config_equal = policy_digest == phase12_stage.get("config_sha256")
    original_image_matches = phase12_stage.get("outputs", {}).get("preview.png") == _sha(phase12_dir / "preview.png")
    original_scene_matches = phase12_stage.get("outputs", {}).get("12_simplification.json") == _sha(phase12_dir / "12_simplification.json")

    # Reproduce the genuine rendered output, including the authorized face color guard.
    rendered_rgb = _candidate_render(result, selected)
    guarded = apply_face_raster_guard(rendered_rgb, source_rgba[..., :3], masks["face"])
    preview = cv2.imread(str(phase12_dir / "preview.png"), cv2.IMREAD_COLOR)
    if preview is None or preview.shape != guarded.rgb.shape:
        raise ValueError("cannot compare saved Phase12 preview")
    preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
    preview_pixel_equal = bool(np.array_equal(preview_rgb, guarded.rgb))

    metadata = {
        "source_contract": matching_source_contract,
        "policy_config_sha256_equal": config_equal,
        "selected_profile_equal": selection_equal,
        "selected_serialized_records_equal": saved_record_equality,
        "preview_bytes_sha256_valid": original_image_matches,
        "scene_bytes_sha256_valid": original_scene_matches,
        "selected_render_preview_pixel_equal": preview_pixel_equal,
        "selected_name": selected.name,
        "selected_primitive_count": len(selected.primitives),
        "source_hash": source_sha,
        "preview_pixel_delta": int(np.count_nonzero(np.any(preview_rgb != guarded.rgb, axis=2))),
        "guard_changed_outside_face_pixels": guarded.changed_outside_face_pixels,
    }

    primitive_masks = selected.primitive_masks
    by_owner: dict[str, list[dict]] = {}
    for p in selected.primitives:
        if p.get("semantic_part_id") in WATCH_OWNERS:
            by_owner.setdefault(p["semantic_part_id"], []).append(p)

    parts: dict[str, dict] = {}
    for owner in WATCH_OWNERS:
        owned = by_owner.get(owner, [])
        if len(owned) != 1:
            parts[owner] = {"status": "HOLD_MISSING_OR_AMBIGUOUS_OWNER", "count": len(owned)}
            continue
        primitive = owned[0]
        if primitive.get("source_mask_replay") is not True or primitive.get("source_mask_owner") != owner:
            parts[owner] = {"status": "HOLD_SOURCE_REPLAY_PROVENANCE", "primitive_id": primitive.get("primitive_id")}
            continue
        actual = primitive_masks[primitive["primitive_id"]]
        vector = rasterize_primitive_candidate(primitive, width=width, height=height)
        report = owner_fidelity(masks[owner], actual, vector)
        report["primitive_id"] = primitive["primitive_id"]
        report["source_mask_replay"] = True
        report["ring_count"] = len(primitive.get("parameters", {}).get("rings", []))
        report["component_count"] = len(primitive.get("parameters", {}).get("components", []))
        report["status"] = "OBSERVED_ONLY" if owner.endswith("_arm") else "RESEARCH_DIAGNOSTIC_ONLY"
        parts[owner] = report

    source_union = np.logical_or.reduce(list(masks.values()))
    actual_union = np.logical_or.reduce([
        primitive_masks[p["primitive_id"]]
        for p in selected.primitives if p.get("structural_support_only") is not True
    ])
    recorded_benchmark = _json(benchmark_path) if benchmark_path else None
    historical = recorded_benchmark.get("baseline", {}).get("anatomy", {}) if recorded_benchmark else {}
    global_gate = evaluate_source_silhouette_anatomy(source_union, actual_union, fragmentation_penalty=0.0)
    historical_match = None if not historical else {
        "source_mask_pixels": global_gate["source_evidence"]["mask_pixels"] == historical.get("source_evidence", {}).get("mask_pixels"),
        "candidate_mask_pixels": global_gate["candidate_evidence"]["mask_pixels"] == historical.get("candidate_evidence", {}).get("mask_pixels"),
        "source_topology": list(global_gate["source_evidence"]["topology"]) == list(historical.get("source_evidence", {}).get("topology", [])),
        "candidate_topology": list(global_gate["candidate_evidence"]["topology"]) == list(historical.get("candidate_evidence", {}).get("topology", [])),
        "iou": abs(global_gate["metrics"]["silhouette_iou"] - historical.get("metrics", {}).get("silhouette_iou", -1)) <= 1e-12,
    }
    owner_audit = audit_records(records)
    zorder = zorder_visibility(list(selected.primitives), primitive_masks)
    source_to_actual = mask_fidelity(source_union, actual_union)
    export_drift = [
        owner for owner, report in parts.items()
        if "export_consistency_pass" not in report or not report["export_consistency_pass"]
    ]
    source_topology_drift = [
        owner for owner, report in parts.items()
        if "raw_source_topology_pass" not in report or not report["raw_source_topology_pass"]
    ]
    reproducibility_pass = (
        all(v is True for v in (
            matching_source_contract, config_equal, selection_equal, saved_record_equality,
            original_image_matches, original_scene_matches, preview_pixel_equal,
        ))
        and owner_audit["status"] == "OWNER_AUDIT_PASS"
        and len(selected.primitives) == 11
        and guarded.changed_outside_face_pixels == 0
        and (historical_match is None or all(historical_match.values()))
    )
    blockers = []
    if not reproducibility_pass:
        blockers.append("NON_REPRODUCIBLE_BASELINE")
    if global_gate["hard_failures"]:
        blockers.extend(global_gate["hard_failures"])
    if source_topology_drift:
        blockers.append("OWNER_SOURCE_TOPOLOGY_DRIFT")
    if export_drift:
        blockers.append("SERIALIZED_VECTOR_RENDER_DRIFT")
    visible = zorder["pre_face_guard_owner_visibility"]
    if any(visible.get(arm, {}).get("visible_pixels", 0) == 0 for arm in ("left_arm", "right_arm")):
        blockers.append("ARM_NOT_VISIBLE_PRE_FACE_GUARD")
    blockers.append("UNVERIFIED_MULTICASE_AND_HUMAN_VISUAL_GATE")

    return {
        "schema": "sa10.33-phase7-full-scene-authority-v1",
        "provenance": metadata,
        "owner_audit": owner_audit,
        "parts": parts,
        "global": {
            "source_to_render": source_to_actual,
            "global_anatomy_gate": global_gate,
            "historical_sa1030_match": historical_match,
        },
        "zorder": zorder,
        "serialized_export_drift_owners": export_drift,
        "source_topology_drift_owners": source_topology_drift,
        "reproduction_pass": reproducibility_pass,
        "hard_blockers": sorted(set(blockers)),
        "promotion_authorized": False,
        "status": "RESEARCH_COMPLETE_NO_GO" if reproducibility_pass else "HOLD_REPRODUCTION",
        "safety": {
            "generative_pixels": 0,
            "input_pixel_edit": False,
            "scene_mutation": False,
            "arm_geometry_mutation": False,
            "canonical_material_cleaning_only_diagnostic": True,
            "requires_visual_review": True,
            "requires_independent_cases": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--phase12-dir", type=Path, required=True)
    p.add_argument("--benchmark", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    evidence = observe(
        case_dir=args.case_dir, source_path=args.source,
        phase12_dir=args.phase12_dir, benchmark_path=args.benchmark,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "status": evidence["status"],
        "reproduction_pass": evidence["reproduction_pass"],
        "blockers": evidence["hard_blockers"],
        "owner_io_u": {
            owner: report.get("source_to_render", {}).get("iou")
            for owner, report in evidence["parts"].items()
        },
        "source_topology_drift_owners": evidence["source_topology_drift_owners"],
        "export_drift_owners": evidence["serialized_export_drift_owners"],
        "global": evidence["global"]["global_anatomy_gate"],
        "zorder": evidence["zorder"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not evidence["reproduction_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
