from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.evaluation.structural_hard_evidence import evaluate_structural_hard_evidence
from minimalizer_zerobase.evaluation.source_shape_evidence import evaluate_source_shape_evidence, vtracer_backend_status
from minimalizer_zerobase.evaluation.saliency_perceptual import evaluate_saliency_perceptual
from minimalizer_zerobase.evaluation.material_topology import (
    TINY_COMPONENT_AREA_RATIO,
    canonical_material_mask,
    tiny_component_area_threshold,
)


CRITICAL_LAYOUT_PARTS = (
    "face",
    "hair",
    "torso",
    "left_arm",
    "right_arm",
    "lower_body",
    "major_clothing",
    "accessory_or_held_object",
)
IDENTITY_PARTS = ("face", "hair", "accessory_or_held_object")
COLLAPSE_PARTS = ("face", "hair", "torso")
HUMAN_CRITERIA = (
    "same_subject_recognizability",
    "pose_readability",
    "major_feature_retention",
    "minimal_style_consistency",
    "catastrophic_block_failure_absence",
)


@dataclass(frozen=True)
class Phase14EvaluationPolicy:
    minimum_silhouette_iou: float = 0.96
    minimum_part_layout_mean: float = 0.85
    minimum_part_layout_min: float = 0.50
    minimum_major_color_mass_score: float = 0.65
    minimum_identity_feature_retention: float = 0.90
    maximum_oversized_block_penalty: float = 0.10
    maximum_fragmentation_penalty: float = 0.20
    collapse_minimum_recall: float = 0.85
    collapse_minimum_iou: float = 0.75
    minimum_primitive_economy: float = 0.10
    layout_displacement_tolerance_ratio: float = 0.12
    color_delta_normalizer: float = 80.0
    oversized_part_expansion_ratio: float = 1.15
    tiny_component_area_ratio: float = TINY_COMPONENT_AREA_RATIO

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _read_mask(path: Path) -> np.ndarray:
    with Image.open(path) as raw:
        return np.asarray(raw.convert("L"), dtype=np.uint8) > 0


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _bbox_iou(
    first: tuple[int, int, int, int] | None,
    second: tuple[int, int, int, int] | None,
) -> float:
    if first is None or second is None:
        return 0.0
    ax0, ay0, ax1, ay1 = first
    bx0, by0, bx1, by1 = second
    iw = max(0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0, min(ay1, by1) - max(ay0, by0))
    intersection = iw * ih
    union = (
        (ax1 - ax0) * (ay1 - ay0)
        + (bx1 - bx0) * (by1 - by0)
        - intersection
    )
    return float(intersection / max(union, 1))


def _centroid(mask: np.ndarray) -> tuple[float, float] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return float(xs.mean()), float(ys.mean())


def _part_name(primitive: dict[str, Any]) -> str:
    value = primitive.get("composition_part")
    if isinstance(value, str) and value:
        return value
    value = primitive.get("semantic_part_id")
    if isinstance(value, str) and value:
        return value
    return "__unbound__"


def _selected_phase12(case_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = _load_json(case_dir / "phase_12" / "12_simplification.json")
    selected_name = payload.get("selected_name")
    candidates = payload.get("candidates")
    if not isinstance(selected_name, str) or not isinstance(candidates, list):
        raise ValueError("Phase 14 requires a selected Phase 12 candidate")
    selected = next(
        (
            item
            for item in candidates
            if isinstance(item, dict) and item.get("name") == selected_name
        ),
        None,
    )
    if selected is None:
        raise ValueError("Phase 14 cannot resolve the selected Phase 12 candidate")
    return payload, selected


def _selected_part_masks(
    primitives: list[dict[str, Any]],
    *,
    width: int,
    height: int,
    source_part_masks: dict[str, np.ndarray] | None = None,
    material_threshold: int | None = None,
) -> tuple[dict[str, np.ndarray], list[tuple[dict[str, Any], np.ndarray, str]]]:
    part_masks: dict[str, np.ndarray] = {}
    primitive_masks: list[tuple[dict[str, Any], np.ndarray, str]] = []
    for primitive in primitives:
        part = _part_name(primitive)
        replay_owner = primitive.get("source_mask_owner")
        if not isinstance(replay_owner, str) or not replay_owner:
            replay_owner = part
        if (
            primitive.get("source_mask_replay") is True
            and source_part_masks is not None
            and replay_owner in source_part_masks
        ):
            # Source replay preserves Phase 12's authority/provenance, but its
            # pixels still enter evaluation through the shared material-topology
            # contract.  Raw Phase 4 specks must not become Phase 14 fragments.
            mask = canonical_material_mask(
                source_part_masks[replay_owner],
                tiny_component_area_threshold=material_threshold,
            )
        else:
            mask = rasterize_primitive_candidate(
                primitive,
                width=width,
                height=height,
            )
        if part not in part_masks:
            part_masks[part] = np.zeros((height, width), dtype=bool)
        part_masks[part] |= mask
        primitive_masks.append((primitive, mask, part))
    return part_masks, primitive_masks


def _phase4_masks(case_dir: Path) -> dict[str, np.ndarray]:
    root = case_dir / "phase_04" / "part_masks"
    if not root.is_dir():
        raise ValueError("Phase 14 requires Phase 4 semantic part masks")
    return {
        path.stem: _read_mask(path)
        for path in sorted(root.glob("*.png"))
    }


def _layout_metrics(
    phase4_masks: dict[str, np.ndarray],
    selected_masks: dict[str, np.ndarray],
    *,
    width: int,
    height: int,
    policy: Phase14EvaluationPolicy,
) -> tuple[float, float, dict[str, dict[str, float]]]:
    diagonal = float(np.hypot(width, height))
    per_part: dict[str, dict[str, float]] = {}
    scores: list[float] = []
    for part in CRITICAL_LAYOUT_PARTS:
        baseline = phase4_masks.get(part)
        if baseline is None or not np.any(baseline):
            continue
        candidate = selected_masks.get(part)
        if candidate is None or not np.any(candidate):
            per_part[part] = {
                "centroid_score": 0.0,
                "bbox_iou": 0.0,
                "score": 0.0,
            }
            scores.append(0.0)
            continue
        first = _centroid(baseline)
        second = _centroid(candidate)
        assert first is not None and second is not None
        displacement = float(
            np.hypot(first[0] - second[0], first[1] - second[1])
            / max(diagonal, 1.0)
        )
        centroid_score = max(
            0.0,
            1.0
            - displacement
            / max(policy.layout_displacement_tolerance_ratio, 1e-6),
        )
        bbox_iou = _bbox_iou(_bbox(baseline), _bbox(candidate))
        score = float((centroid_score + bbox_iou) * 0.5)
        per_part[part] = {
            "centroid_displacement_ratio": displacement,
            "centroid_score": centroid_score,
            "bbox_iou": bbox_iou,
            "score": score,
        }
        scores.append(score)
    if not scores:
        return 0.0, 0.0, per_part
    return float(np.mean(scores)), float(np.min(scores)), per_part


def _major_color_mass_metrics(
    source_rgb: np.ndarray,
    phase4_masks: dict[str, np.ndarray],
    primitive_masks: list[tuple[dict[str, Any], np.ndarray, str]],
    *,
    policy: Phase14EvaluationPolicy,
) -> tuple[float, float, dict[str, dict[str, Any]]]:
    height, width = source_rgb.shape[:2]
    per_part: dict[str, dict[str, Any]] = {}
    deltas: list[float] = []
    for part in CRITICAL_LAYOUT_PARTS:
        baseline = phase4_masks.get(part)
        if baseline is None or not np.any(baseline):
            continue
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        coverage = np.zeros((height, width), dtype=bool)
        for primitive, mask, primitive_part in primitive_masks:
            if primitive_part != part:
                continue
            color = np.asarray(
                primitive.get("palette_color_rgb", (0, 0, 0)),
                dtype=np.uint8,
            )
            canvas[mask] = color
            coverage |= mask
        comparable = baseline & coverage
        if not np.any(comparable):
            delta = float(policy.color_delta_normalizer)
            source_median = np.median(source_rgb[baseline], axis=0)
            final_median = np.asarray((0, 0, 0), dtype=np.float64)
        else:
            source_median = np.median(source_rgb[baseline], axis=0)
            final_median = np.median(canvas[comparable], axis=0)
            source_lab = cv2.cvtColor(
                np.asarray(source_median, dtype=np.uint8).reshape(1, 1, 3),
                cv2.COLOR_RGB2LAB,
            ).astype(np.float32)[0, 0]
            final_lab = cv2.cvtColor(
                np.asarray(final_median, dtype=np.uint8).reshape(1, 1, 3),
                cv2.COLOR_RGB2LAB,
            ).astype(np.float32)[0, 0]
            delta = float(np.linalg.norm(source_lab - final_lab))
        score = max(
            0.0,
            1.0 - delta / max(policy.color_delta_normalizer, 1e-6),
        )
        per_part[part] = {
            "source_median_rgb": [
                int(round(float(value))) for value in source_median
            ],
            "final_median_rgb": [
                int(round(float(value))) for value in final_median
            ],
            "lab_distance": delta,
            "score": score,
        }
        deltas.append(delta)
    if not deltas:
        return 0.0, float(policy.color_delta_normalizer), per_part
    mean_delta = float(np.mean(deltas))
    score = max(
        0.0,
        1.0 - mean_delta / max(policy.color_delta_normalizer, 1e-6),
    )
    return score, float(np.max(deltas)), per_part


def _identity_retention(
    part_metrics: dict[str, Any],
) -> tuple[float, dict[str, float]]:
    per_part: dict[str, float] = {}
    for part in IDENTITY_PARTS:
        item = part_metrics.get(part)
        if not isinstance(item, dict):
            continue
        if int(item.get("baseline_pixels", 0)) < 8:
            continue
        per_part[part] = float(item.get("recall", 0.0))
    if not per_part:
        return 1.0, per_part
    return float(min(per_part.values())), per_part


def _oversized_block_penalty(
    phase4_masks: dict[str, np.ndarray],
    primitive_masks: list[tuple[dict[str, Any], np.ndarray, str]],
    *,
    policy: Phase14EvaluationPolicy,
) -> tuple[float, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    maximum = 0.0
    for primitive, mask, part in primitive_masks:
        baseline = phase4_masks.get(part)
        if baseline is None or not np.any(baseline):
            continue
        ratio = float(
            np.count_nonzero(mask) / max(int(np.count_nonzero(baseline)), 1)
        )
        penalty = max(
            0.0,
            ratio - policy.oversized_part_expansion_ratio,
        )
        maximum = max(maximum, penalty)
        if penalty > 0.0:
            rows.append(
                {
                    "primitive_id": primitive.get("primitive_id"),
                    "part": part,
                    "area_ratio_to_source_part": ratio,
                    "penalty": penalty,
                }
            )
    return maximum, rows


def _fragmentation_penalty(
    primitive_masks: list[tuple[dict[str, Any], np.ndarray, str]],
    *,
    subject_area: int,
    policy: Phase14EvaluationPolicy,
) -> tuple[float, dict[str, int]]:
    if policy.tiny_component_area_ratio != TINY_COMPONENT_AREA_RATIO:
        raise ValueError("Phase14 tiny component policy is canonical and immutable")
    tiny_threshold = tiny_component_area_threshold(subject_area)
    component_count = 0
    tiny_count = 0
    for _, mask, _ in primitive_masks:
        count, _, stats, _ = cv2.connectedComponentsWithStats(
            mask.astype(np.uint8),
            connectivity=8,
        )
        for label in range(1, count):
            component_count += 1
            if int(stats[label, cv2.CC_STAT_AREA]) < tiny_threshold:
                tiny_count += 1
    penalty = float(tiny_count / max(component_count, 1))
    return penalty, {
        "component_count": component_count,
        "tiny_component_count": tiny_count,
        "tiny_component_area_threshold": tiny_threshold,
    }


def _collapse_guard(
    part_metrics: dict[str, Any],
    *,
    policy: Phase14EvaluationPolicy,
) -> tuple[bool, list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    for part in COLLAPSE_PARTS:
        item = part_metrics.get(part)
        if not isinstance(item, dict):
            continue
        if int(item.get("baseline_pixels", 0)) < 8:
            continue
        recall = float(item.get("recall", 0.0))
        iou = float(item.get("iou", 0.0))
        if (
            recall < policy.collapse_minimum_recall
            or iou < policy.collapse_minimum_iou
        ):
            failures.append(
                {
                    "part": part,
                    "recall": recall,
                    "iou": iou,
                }
            )
    return bool(failures), failures


def _human_review(
    phase13_index: dict[str, Any],
    *,
    review_status: str,
    failed_criteria: Iterable[str] = (),
    reviewer: str = "",
    note: str = "",
) -> dict[str, Any]:
    if review_status not in {"pending", "pass", "fail"}:
        raise ValueError("Phase 14 human review status must be pending/pass/fail")
    failed = set(failed_criteria)
    unknown = failed - set(HUMAN_CRITERIA)
    if unknown:
        raise ValueError(
            f"unknown Phase 14 human criteria: {sorted(unknown)}"
        )
    if review_status == "pass" and failed:
        raise ValueError("passing Phase 14 review cannot name failed criteria")
    if review_status == "fail" and not failed:
        failed = {"catastrophic_block_failure_absence"}

    phase13_human = phase13_index.get("human_review", {})
    phase13_status = (
        phase13_human.get("status")
        if isinstance(phase13_human, dict)
        else None
    )
    criteria = {
        name: review_status == "pass" or (
            review_status == "fail" and name not in failed
        )
        for name in HUMAN_CRITERIA
    }
    passed = (
        phase13_status == "pass"
        and review_status == "pass"
        and all(criteria.values())
    )
    return {
        "passed": passed,
        "phase13_review_status": phase13_status,
        "phase13_first_bad_stage_id": phase13_human.get("first_bad_stage_id")
        if isinstance(phase13_human, dict)
        else None,
        "status": review_status,
        "reviewer": reviewer,
        "note": note,
        "criteria": criteria,
        "failed_criteria": sorted(failed),
    }


def _evaluate_once(
    case_dir: Path,
    source_path: Path,
    *,
    policy: Phase14EvaluationPolicy,
    human_status: str,
    failed_criteria: Iterable[str],
    reviewer: str,
    human_note: str,
) -> dict[str, Any]:
    phase12_payload, selected = _selected_phase12(case_dir)
    phase13_index = _load_json(
        case_dir / "phase_13" / "13_stage_index.json"
    )
    phase13_stage = _load_json(case_dir / "phase_13" / "stage.json")
    source_rgb = np.asarray(Image.open(source_path).convert("RGB"))
    height, width = source_rgb.shape[:2]
    coordinate = phase12_payload.get("coordinate_space", {})
    if (
        int(coordinate.get("pixel_width", -1)) != width
        or int(coordinate.get("pixel_height", -1)) != height
    ):
        raise ValueError("Phase 14 source dimensions differ from Phase 12")

    primitives = selected.get("primitives")
    metrics = selected.get("metrics")
    if not isinstance(primitives, list) or not isinstance(metrics, dict):
        raise ValueError("Phase 14 requires Phase 12 primitive metrics")

    phase4_masks = _phase4_masks(case_dir)
    subject_mask = _read_mask(
        case_dir / "phase_03" / "03_subject_mask.png"
    )
    subject_area = int(np.count_nonzero(subject_mask))
    material_threshold = tiny_component_area_threshold(subject_area)
    selected_masks, primitive_masks = _selected_part_masks(
        primitives,
        width=width,
        height=height,
        source_part_masks=phase4_masks,
        material_threshold=material_threshold,
    )

    layout_mean, layout_min, layout_parts = _layout_metrics(
        phase4_masks,
        selected_masks,
        width=width,
        height=height,
        policy=policy,
    )
    color_score, color_max_delta, color_parts = _major_color_mass_metrics(
        source_rgb,
        phase4_masks,
        primitive_masks,
        policy=policy,
    )
    part_metrics = metrics.get("part_metrics", {})
    if not isinstance(part_metrics, dict):
        raise ValueError("Phase 14 requires Phase 12 part metrics")
    identity_score, identity_parts = _identity_retention(part_metrics)
    oversized_penalty, oversized_rows = _oversized_block_penalty(
        phase4_masks,
        primitive_masks,
        policy=policy,
    )
    fragmentation_penalty, fragmentation_detail = _fragmentation_penalty(
        primitive_masks,
        subject_area=subject_area,
        policy=policy,
    )
    collapse, collapse_failures = _collapse_guard(
        part_metrics,
        policy=policy,
    )
    structural = evaluate_structural_hard_evidence(
        source_masks=phase4_masks,
        candidate_masks=selected_masks,
    )
    source_outer = np.logical_or.reduce(list(phase4_masks.values()))
    candidate_outer = np.logical_or.reduce(list(selected_masks.values()))
    shape_evidence = evaluate_source_shape_evidence(source_outer, candidate_outer)
    candidate_rgb = np.zeros_like(source_rgb)
    for primitive, mask, _ in primitive_masks:
        candidate_rgb[mask] = np.asarray(primitive.get("palette_color_rgb", (0, 0, 0)), dtype=np.uint8)
    saliency_evidence = evaluate_saliency_perceptual(source_rgb, candidate_rgb, phase4_masks)

    baseline_primitives = max(
        int(metrics.get("baseline_primitive_count", 0)),
        1,
    )
    primitive_count = int(metrics.get("primitive_count", 0))
    primitive_economy = float(
        1.0 - primitive_count / baseline_primitives
    )
    baseline_vertices = max(int(metrics.get("baseline_vertex_count", 0)), 1)
    vertex_count = int(metrics.get("vertex_count", 0))
    vertex_change_ratio = float(
        1.0 - vertex_count / baseline_vertices
    )
    silhouette = float(metrics.get("silhouette_iou", 0.0))

    checks = {
        "phase12_machine_guard": {
            "value": bool(metrics.get("pass", False)),
            "expected": True,
            "passed": bool(metrics.get("pass", False)),
        },
        "silhouette_preservation": {
            "value": silhouette,
            "minimum": policy.minimum_silhouette_iou,
            "passed": silhouette >= policy.minimum_silhouette_iou,
        },
        "part_layout_mean": {
            "value": layout_mean,
            "minimum": policy.minimum_part_layout_mean,
            "passed": layout_mean >= policy.minimum_part_layout_mean,
        },
        "part_layout_min": {
            "value": layout_min,
            "minimum": policy.minimum_part_layout_min,
            "passed": layout_min >= policy.minimum_part_layout_min,
        },
        "major_color_mass_consistency": {
            "value": color_score,
            "minimum": policy.minimum_major_color_mass_score,
            "passed": color_score >= policy.minimum_major_color_mass_score,
        },
        "identity_feature_retention": {
            "value": identity_score,
            "minimum": policy.minimum_identity_feature_retention,
            "passed": identity_score
            >= policy.minimum_identity_feature_retention,
        },
        "oversized_block_penalty": {
            "value": oversized_penalty,
            "maximum": policy.maximum_oversized_block_penalty,
            "passed": oversized_penalty
            <= policy.maximum_oversized_block_penalty,
        },
        "fragmentation_penalty": {
            "value": fragmentation_penalty,
            "maximum": policy.maximum_fragmentation_penalty,
            "passed": fragmentation_penalty
            <= policy.maximum_fragmentation_penalty,
        },
        "face_hair_torso_collapse": {
            "value": collapse,
            "expected": False,
            "passed": not collapse,
        },
        "source_anatomy": {
            "value": structural.source_anatomy,
            "expected": True,
            "passed": structural.anatomy_pass and structural.source_silhouette["passed"],
        },
        "source_topology": {
            "value": structural.to_dict()["topology"],
            "expected": True,
            "passed": structural.topology_pass,
            "authority": "hard",
            "note": "material semantic-part and semantic-union topology must match source-owned masks",
        },
        "source_shape_evidence": {
            "value": shape_evidence.get("match_shapes_i1"),
            "passed": True,
            "authority": False,
            "note": "evidence-only; source/anatomy/topology hard gates remain authoritative",
        },
        "primitive_economy": {
            "value": primitive_economy,
            "minimum": policy.minimum_primitive_economy,
            "passed": primitive_economy >= policy.minimum_primitive_economy,
        },
    }
    human = _human_review(
        phase13_index,
        review_status=human_status,
        failed_criteria=failed_criteria,
        reviewer=reviewer,
        note=human_note,
    )
    machine_pass = all(bool(item["passed"]) for item in checks.values())

    return {
        "schema_version": "1.0",
        "phase": 14,
        "case_id": case_dir.name,
        "source": {
            "path": source_path.name,
            "sha256": _sha256_file(source_path),
            "width": width,
            "height": height,
        },
        "phase12": {
            "selected_profile": phase12_payload.get("selected_name"),
            "primitive_count": primitive_count,
            "baseline_primitive_count": baseline_primitives,
            "vertex_count": vertex_count,
            "baseline_vertex_count": baseline_vertices,
            "selection_rule": phase12_payload.get("validation", {}).get(
                "selection_rule"
            ),
        },
        "phase13": {
            "pass": bool(phase13_stage.get("metrics", {}).get("pass", False)),
            "human_review_status": phase13_index.get(
                "human_review", {}
            ).get("status"),
            "first_machine_bad_stage_id": phase13_index.get(
                "first_machine_bad_stage_id"
            ),
            "human_first_bad_stage_id": phase13_index.get(
                "human_review", {}
            ).get("first_bad_stage_id"),
        },
        "scores": {
            "silhouette_preservation": silhouette,
            "part_layout_consistency_mean": layout_mean,
            "part_layout_consistency_min": layout_min,
            "major_color_mass_consistency": color_score,
            "major_color_mass_max_lab_distance": color_max_delta,
            "identity_feature_retention": identity_score,
            "oversized_block_penalty": oversized_penalty,
            "fragmentation_penalty": fragmentation_penalty,
            "face_hair_torso_collapse": collapse,
            "primitive_economy": primitive_economy,
            "vertex_change_ratio": vertex_change_ratio,
        },
        "details": {
            "part_layout": layout_parts,
            "major_color_mass": color_parts,
            "identity_features": identity_parts,
            "oversized_blocks": oversized_rows,
            "fragmentation": fragmentation_detail,
            "collapse_failures": collapse_failures,
            "source_anatomy": structural.source_anatomy,
            "source_silhouette": structural.source_silhouette,
            "structural_topology": structural.to_dict()["topology"],
            "source_shape_evidence": shape_evidence,
            "saliency_perceptual": saliency_evidence,
            "vectorization_backend": vtracer_backend_status(),
        },
        "machine_checks": checks,
        "machine_pass": machine_pass,
        "human_visual_qa": human,
        "policy": policy.to_dict(),
    }


def evaluate_phase14_case(
    case_dir: str | Path,
    source_path: str | Path,
    *,
    policy: Phase14EvaluationPolicy | None = None,
    human_status: str = "pending",
    failed_criteria: Iterable[str] = (),
    reviewer: str = "",
    human_note: str = "",
) -> dict[str, Any]:
    case_dir = Path(case_dir)
    source_path = Path(source_path)
    policy = policy or Phase14EvaluationPolicy()
    if not source_path.is_file():
        raise ValueError(f"Phase 14 source image is missing: {source_path}")

    first = _evaluate_once(
        case_dir,
        source_path,
        policy=policy,
        human_status=human_status,
        failed_criteria=failed_criteria,
        reviewer=reviewer,
        human_note=human_note,
    )
    second = _evaluate_once(
        case_dir,
        source_path,
        policy=policy,
        human_status=human_status,
        failed_criteria=failed_criteria,
        reviewer=reviewer,
        human_note=human_note,
    )
    first_hash = _canonical_json_sha256(first)
    second_hash = _canonical_json_sha256(second)
    deterministic = first_hash == second_hash

    result = dict(first)
    result["determinism"] = {
        "passed": deterministic,
        "first_evaluation_sha256": first_hash,
        "second_evaluation_sha256": second_hash,
        "method": "repeat-pure-evaluation-canonical-json-sha256",
    }
    machine_checks = dict(result["machine_checks"])
    machine_checks["determinism"] = {
        "value": deterministic,
        "expected": True,
        "passed": deterministic,
    }
    result["machine_checks"] = machine_checks
    result["machine_pass"] = all(
        bool(item["passed"]) for item in machine_checks.values()
    )
    result["pass"] = bool(
        result["machine_pass"]
        and result["human_visual_qa"]["passed"]
    )
    result["failure_policy"] = (
        "Any machine or human visual failure wins. "
        "A numeric PASS cannot override human visual FAIL."
    )
    return result


def render_phase14_eval_sheet(
    evaluation: dict[str, Any],
    source_path: str | Path,
    final_path: str | Path,
    *,
    width: int = 1200,
) -> Image.Image:
    if width < 800:
        raise ValueError("Phase 14 eval sheet width must be >= 800")
    source_path = Path(source_path)
    final_path = Path(final_path)
    scores = evaluation["scores"]
    checks = evaluation["machine_checks"]
    human = evaluation["human_visual_qa"]

    margin = 28
    title_h = 64
    image_h = 360
    row_h = 34
    metric_names = [
        "silhouette_preservation",
        "part_layout_consistency_mean",
        "part_layout_consistency_min",
        "major_color_mass_consistency",
        "identity_feature_retention",
        "oversized_block_penalty",
        "fragmentation_penalty",
        "primitive_economy",
    ]
    human_names = list(HUMAN_CRITERIA)
    height = (
        title_h
        + image_h
        + margin
        + row_h * (len(metric_names) + len(human_names) + 5)
    )
    canvas = Image.new("RGB", (width, height), (244, 244, 244))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    status = "PASS" if evaluation["pass"] else "FAIL"
    draw.text(
        (margin, 20),
        f"Phase 14 Evaluation | {evaluation['case_id']} | {status}",
        fill=(20, 20, 20),
        font=font,
    )

    thumb_w = (width - margin * 3) // 2
    for index, path in enumerate((source_path, final_path)):
        with Image.open(path) as raw:
            image = raw.convert("RGB")
            image.thumbnail(
                (thumb_w, image_h - 28),
                Image.Resampling.LANCZOS,
            )
            x0 = margin + index * (thumb_w + margin)
            y0 = title_h
            px = x0 + (thumb_w - image.width) // 2
            py = y0 + (image_h - 28 - image.height) // 2
            canvas.paste(image, (px, py))
            label = "SOURCE" if index == 0 else "PHASE 12 FINAL"
            draw.text(
                (x0, y0 + image_h - 24),
                label,
                fill=(30, 30, 30),
                font=font,
            )

    y = title_h + image_h + margin
    draw.text(
        (margin, y),
        (
            f"machine={evaluation['machine_pass']} | "
            f"human={human['passed']} | "
            f"deterministic={evaluation['determinism']['passed']}"
        ),
        fill=(20, 20, 20),
        font=font,
    )
    y += row_h

    for name in metric_names:
        value = float(scores[name])
        check = checks.get(
            {
                "part_layout_consistency_mean": "part_layout_mean",
                "part_layout_consistency_min": "part_layout_min",
                "major_color_mass_consistency": "major_color_mass_consistency",
                "identity_feature_retention": "identity_feature_retention",
                "oversized_block_penalty": "oversized_block_penalty",
                "fragmentation_penalty": "fragmentation_penalty",
                "primitive_economy": "primitive_economy",
            }.get(name, name),
            {},
        )
        draw.text(
            (margin, y),
            f"{name}: {value:.4f} | {'PASS' if check.get('passed') else 'FAIL'}",
            fill=(20, 20, 20),
            font=font,
        )
        y += row_h

    draw.text(
        (margin, y),
        f"face_hair_torso_collapse: {scores['face_hair_torso_collapse']}",
        fill=(20, 20, 20),
        font=font,
    )
    y += row_h
    draw.text(
        (margin, y),
        (
            "primitive_count: "
            f"{evaluation['phase12']['primitive_count']}/"
            f"{evaluation['phase12']['baseline_primitive_count']} | "
            "vertex_count: "
            f"{evaluation['phase12']['vertex_count']}/"
            f"{evaluation['phase12']['baseline_vertex_count']}"
        ),
        fill=(20, 20, 20),
        font=font,
    )
    y += row_h

    draw.text(
        (margin, y),
        f"Human visual QA: {human['status']} | reviewer={human['reviewer'] or '-'}",
        fill=(20, 20, 20),
        font=font,
    )
    y += row_h
    for name in human_names:
        draw.text(
            (margin + 18, y),
            f"{name}: {'PASS' if human['criteria'][name] else 'FAIL'}",
            fill=(20, 20, 20),
            font=font,
        )
        y += row_h
    if human.get("note"):
        draw.text(
            (margin, y),
            f"note: {human['note']}",
            fill=(20, 20, 20),
            font=font,
        )
    return canvas


def write_phase14_artifacts(
    source_path: str | Path,
    case_dir: str | Path,
    output_dir: str | Path,
    *,
    policy: Phase14EvaluationPolicy | None = None,
    human_status: str = "pending",
    failed_criteria: Iterable[str] = (),
    reviewer: str = "",
    human_note: str = "",
) -> dict[str, Any]:
    source_path = Path(source_path)
    case_dir = Path(case_dir)
    output_dir = Path(output_dir)
    policy = policy or Phase14EvaluationPolicy()

    evaluation = evaluate_phase14_case(
        case_dir,
        source_path,
        policy=policy,
        human_status=human_status,
        failed_criteria=failed_criteria,
        reviewer=reviewer,
        human_note=human_note,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_path = output_dir / "14_case_evaluation.json"
    sheet_path = output_dir / "14_eval_sheet.png"
    preview_path = output_dir / "preview.png"
    metrics_path = output_dir / "metrics.json"
    stage_path = output_dir / "stage.json"

    evaluation_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    sheet = render_phase14_eval_sheet(
        evaluation,
        source_path,
        case_dir / "phase_12" / "12_final.png",
    )
    sheet.save(sheet_path, format="PNG")
    sheet.save(preview_path, format="PNG")

    scores = evaluation["scores"]
    metrics = {
        "pass": bool(evaluation["pass"]),
        "machine_pass": bool(evaluation["machine_pass"]),
        "human_visual_pass": bool(
            evaluation["human_visual_qa"]["passed"]
        ),
        "determinism_pass": bool(evaluation["determinism"]["passed"]),
        "silhouette_preservation": scores["silhouette_preservation"],
        "part_layout_consistency_mean": scores[
            "part_layout_consistency_mean"
        ],
        "part_layout_consistency_min": scores[
            "part_layout_consistency_min"
        ],
        "major_color_mass_consistency": scores[
            "major_color_mass_consistency"
        ],
        "identity_feature_retention": scores[
            "identity_feature_retention"
        ],
        "oversized_block_penalty": scores[
            "oversized_block_penalty"
        ],
        "fragmentation_penalty": scores["fragmentation_penalty"],
        "face_hair_torso_collapse": scores[
            "face_hair_torso_collapse"
        ],
        "primitive_economy": scores["primitive_economy"],
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    phase4_stage = _load_json(case_dir / "phase_04" / "stage.json")
    phase12_stage = _load_json(case_dir / "phase_12" / "stage.json")
    phase13_stage = _load_json(case_dir / "phase_13" / "stage.json")
    source_contract = phase12_stage.get("source")
    coordinate_space = phase12_stage.get("coordinate_space")
    if not isinstance(source_contract, dict) or not isinstance(
        coordinate_space, dict
    ):
        raise ValueError("Phase 14 requires Phase 12 source/coordinate contracts")

    phase4_inputs = {
        path: sha
        for path, sha in phase4_stage.get("outputs", {}).items()
        if path.startswith("part_masks/")
    }
    phase4_inputs["stage.json"] = _sha256_file(
        case_dir / "phase_04" / "stage.json"
    )
    phase12_inputs = {
        name: phase12_stage["outputs"][name]
        for name in ("12_simplification.json", "12_final.png")
    }
    phase12_inputs["stage.json"] = _sha256_file(
        case_dir / "phase_12" / "stage.json"
    )
    phase13_inputs = {
        name: phase13_stage["outputs"][name]
        for name in ("13_stage_index.json", "13_debug_board.png")
    }
    phase13_inputs["stage.json"] = _sha256_file(
        case_dir / "phase_13" / "stage.json"
    )

    config = {
        "evaluation_version": "phase14-case-eval-v1",
        "policy": policy.to_dict(),
        "human_review_status": human_status,
        "failed_human_criteria": sorted(set(failed_criteria)),
        "reviewer": reviewer,
        "failure_wins": True,
    }
    inputs = {
        "source": {
            "path": source_path.name,
            "sha256": _sha256_file(source_path),
        },
        "phase04": phase4_inputs,
        "phase12": phase12_inputs,
        "phase13": phase13_inputs,
    }
    outputs = {
        path.name: _sha256_file(path)
        for path in (
            evaluation_path,
            sheet_path,
            preview_path,
            metrics_path,
        )
    }
    stage = {
        "phase": 14,
        "stage": "evaluation_redesign_calibration",
        "producer": "minimalizer-zerobase2-phase14",
        "producer_version": "0.1",
        "source": source_contract,
        "inputs": inputs,
        "config": config,
        "config_sha256": _canonical_json_sha256(config),
        "coordinate_space": coordinate_space,
        "determinism_policy": (
            "repeat-pure-evaluation-canonical-json-sha256"
        ),
        "evaluation_policy": {
            "numeric_and_human_failure_wins": True,
            "phase13_human_review_required": True,
            "render_algorithm_exceptions_forbidden": True,
        },
        "provenance_policy": {
            "generation": "forbidden",
            "inpainting": "forbidden",
            "hidden_completion": "forbidden",
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage


def build_phase14_corpus_summary(
    evaluations: Iterable[dict[str, Any]],
    *,
    corpus_name: str,
    required_case_count: int | None = None,
) -> dict[str, Any]:
    cases = list(evaluations)
    ids = [str(item.get("case_id")) for item in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Phase 14 corpus summary contains duplicate case IDs")
    if required_case_count is not None and len(cases) != required_case_count:
        raise ValueError(
            f"Phase 14 corpus {corpus_name!r} requires "
            f"{required_case_count} cases"
        )
    pass_count = sum(bool(item.get("pass")) for item in cases)
    score_keys = (
        "silhouette_preservation",
        "part_layout_consistency_mean",
        "part_layout_consistency_min",
        "major_color_mass_consistency",
        "identity_feature_retention",
        "primitive_economy",
    )
    minima = {
        key: min(
            (float(item["scores"][key]) for item in cases),
            default=0.0,
        )
        for key in score_keys
    }
    maxima = {
        "oversized_block_penalty": max(
            (
                float(item["scores"]["oversized_block_penalty"])
                for item in cases
            ),
            default=0.0,
        ),
        "fragmentation_penalty": max(
            (
                float(item["scores"]["fragmentation_penalty"])
                for item in cases
            ),
            default=0.0,
        ),
    }
    return {
        "schema_version": "1.0",
        "phase": 14,
        "corpus_name": corpus_name,
        "case_count": len(cases),
        "pass_count": pass_count,
        "fail_count": len(cases) - pass_count,
        "pass": bool(cases) and pass_count == len(cases),
        "case_ids": ids,
        "failing_cases": [
            item["case_id"] for item in cases if not item.get("pass")
        ],
        "minimum_scores": minima,
        "maximum_penalties": maxima,
        "human_visual_pass_count": sum(
            bool(item.get("human_visual_qa", {}).get("passed"))
            for item in cases
        ),
        "determinism_pass_count": sum(
            bool(item.get("determinism", {}).get("passed"))
            for item in cases
        ),
        "failure_policy": "Any failing case keeps the corpus Gate closed.",
    }


def write_phase14_corpus_summary(
    case_dirs: Iterable[str | Path],
    output_path: str | Path,
    *,
    corpus_name: str,
    required_case_count: int | None = None,
) -> dict[str, Any]:
    evaluations = []
    for case_dir in case_dirs:
        path = Path(case_dir) / "phase_14" / "14_case_evaluation.json"
        evaluations.append(_load_json(path))
    summary = build_phase14_corpus_summary(
        evaluations,
        corpus_name=corpus_name,
        required_case_count=required_case_count,
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary
