from __future__ import annotations

import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from minimalizer_zerobase.parts.artifacts import PART_COLORS
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.subject.artifacts import canonical_json_sha256, sha256_file

from .graph import StructuralLayoutGraph, graph_validation

RELATION_COLORS = {
    "attached_to": (45, 235, 105),
    "above": (40, 220, 245),
    "below": (40, 220, 245),
    "inside": (175, 105, 255),
    "contains": (175, 105, 255),
    "overlaps": (255, 160, 55),
    "surrounds": (255, 160, 55),
    "left_of": (110, 205, 245),
    "right_of": (110, 205, 245),
    "in_front_of": (245, 70, 205),
    "behind": (245, 70, 205),
}

PART_LABELS = {
    "head": "HD",
    "hair": "HR",
    "face": "FC",
    "neck": "NK",
    "torso": "TS",
    "left_arm": "LA",
    "right_arm": "RA",
    "lower_body": "LB",
    "major_clothing": "CL",
    "accessory_or_held_object": "AC",
}


def _anchor_points(graph: StructuralLayoutGraph) -> dict[str, tuple[int, int]]:
    return {
        anchor.anchor_id: (
            int(round(anchor.xy_pixel[0])),
            int(round(anchor.xy_pixel[1])),
        )
        for anchor in graph.anchors
    }


def render_structure_graph_overlay(
    source: Image.Image,
    part_masks: dict[str, np.ndarray],
    graph: StructuralLayoutGraph,
) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    if rgb.shape[:2] != (graph.height, graph.width):
        raise ValueError("source dimensions must match the structural graph")
    canvas = np.clip(rgb.astype(np.float32) * 0.72, 0, 255).astype(np.uint8)
    bgr = cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR)

    for part in graph.present_parts:
        mask = np.asarray(part_masks[part]).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        color = PART_COLORS[part]
        cv2.drawContours(bgr, contours, -1, color[::-1], 1, cv2.LINE_8)

    points = _anchor_points(graph)
    relation_priority = {
        "above": 0,
        "inside": 1,
        "overlaps": 2,
        "surrounds": 3,
        "left_of": 4,
        "right_of": 4,
        "attached_to": 5,
        "behind": 6,
        "in_front_of": 6,
    }
    relations = sorted(
        graph.relations,
        key=lambda item: (relation_priority.get(item.relation_kind, 9), item.relation_id),
    )
    for relation in relations:
        start = points[relation.source_anchor_id]
        end = points[relation.target_anchor_id]
        if start == end:
            continue
        color = RELATION_COLORS.get(relation.relation_kind, (235, 235, 235))[::-1]
        thickness = 2 if relation.relation_kind == "attached_to" else 1
        cv2.arrowedLine(
            bgr,
            start,
            end,
            color,
            thickness,
            cv2.LINE_AA,
            tipLength=0.10,
        )

    center_anchors = [anchor for anchor in graph.anchors if anchor.kind == "centroid"]
    for anchor in center_anchors:
        point = points[anchor.anchor_id]
        color = PART_COLORS[anchor.part_id]
        cv2.circle(bgr, point, 4, (20, 20, 20), -1, cv2.LINE_AA)
        cv2.circle(bgr, point, 3, color[::-1], -1, cv2.LINE_AA)
        label = PART_LABELS.get(anchor.part_id, anchor.part_id[:2].upper())
        cv2.putText(
            bgr,
            label,
            (point[0] + 5, point[1] - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.32,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    legend = (
        ("attach", RELATION_COLORS["attached_to"]),
        ("spatial", RELATION_COLORS["above"]),
        ("contain", RELATION_COLORS["inside"]),
        ("around", RELATION_COLORS["surrounds"]),
        ("front/back", RELATION_COLORS["in_front_of"]),
    )
    overlay = bgr.copy()
    cv2.rectangle(overlay, (4, 4), (105, 69), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.68, bgr, 0.32, 0.0, bgr)
    for index, (label, color) in enumerate(legend):
        y = 15 + index * 12
        cv2.line(bgr, (10, y), (28, y), color[::-1], 2, cv2.LINE_AA)
        cv2.putText(
            bgr,
            label,
            (34, y + 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.30,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), mode="RGB")


def write_phase5_artifacts(
    source_path: str | Path,
    phase4_dir: str | Path,
    part_masks: dict[str, np.ndarray],
    graph: StructuralLayoutGraph,
    output_dir: str | Path,
    *,
    config: dict,
    phase4_stage: dict,
    canonical_source: dict | None = None,
    visual_source_kind: str = "canonical-source",
) -> dict:
    source_path = Path(source_path)
    phase4_dir = Path(phase4_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as source:
        source_copy = source.copy()

    graph_path = output_dir / "05_structure_graph.json"
    overlay_path = output_dir / "05_structure_graph_overlay.png"
    preview_path = output_dir / "preview.png"
    metrics_path = output_dir / "metrics.json"
    stage_path = output_dir / "stage.json"

    graph_payload = graph.to_dict()
    graph_path.write_text(
        json.dumps(graph_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    overlay = render_structure_graph_overlay(source_copy, part_masks, graph)
    overlay.save(overlay_path, format="PNG")
    shutil.copyfile(overlay_path, preview_path)

    validation = graph_validation(graph)
    relation_counts: dict[str, int] = {}
    for relation in graph.relations:
        relation_counts[relation.relation_kind] = (
            relation_counts.get(relation.relation_kind, 0) + 1
        )
    metrics = {
        "present_parts": list(graph.present_parts),
        "part_count": len(graph.present_parts),
        "anchor_count": len(graph.anchors),
        "relation_count": len(graph.relations),
        "relation_counts": relation_counts,
        **validation,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    phase4_inputs = {
        "stage.json": sha256_file(phase4_dir / "stage.json"),
        "metrics.json": sha256_file(phase4_dir / "metrics.json"),
    }
    for name in PART_NAMES:
        path = phase4_dir / "part_masks" / f"{name}.png"
        phase4_inputs[f"part_masks/{name}.png"] = sha256_file(path)

    outputs = {
        "05_structure_graph.json": sha256_file(graph_path),
        "05_structure_graph_overlay.png": sha256_file(overlay_path),
        "preview.png": sha256_file(preview_path),
        "metrics.json": sha256_file(metrics_path),
    }
    source_record = canonical_source or {
        "path": source_path.name,
        "sha256": sha256_file(source_path),
        "width": graph.width,
        "height": graph.height,
    }
    stage = {
        "phase": 5,
        "stage": "structural_layout_graph",
        "producer": "minimalizer-zerobase2-phase5",
        "producer_version": "1.0",
        "source": source_record,
        "inputs": {
            "phase4": phase4_inputs,
            "visual_source": {
                "path": source_path.name,
                "sha256": sha256_file(source_path),
                "kind": visual_source_kind,
            },
        },
        "config": config,
        "config_sha256": canonical_json_sha256(config),
        "analyzer_provenance": {
            "source_stage": "phase04-semantic-part-decomposition",
            "structural_provider": phase4_stage.get("structural", {}).get("provider"),
            "structural_model": phase4_stage.get("structural", {}).get("model"),
            "phase4_config_sha256": phase4_stage.get("config_sha256"),
        },
        "coordinate_space": graph_payload["coordinate_space"],
        "determinism_policy": "seedless-pure-mask-geometry-v1",
        "graph": graph_payload,
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
