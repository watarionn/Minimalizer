"""Build a private L04 Stage8/source-ring/SVG candidate from ZeroBase2 output.

This runner is deliberately source-only.  It consumes the signed original and
the source-derived Phase 8/10/11 artifacts produced by the isolated shadow
pipeline.  It never reads human review masks, observer labels, Golden assets,
or production files, and it never authorizes release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


SCHEMA = "minimalizer/local-l04/stage8-source-triple/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _points(raw: Any) -> list[tuple[float, float]]:
    if not isinstance(raw, list) or len(raw) < 1:
        raise ValueError("invalid polygon component")
    out = []
    for point in raw:
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError("invalid polygon point")
        x, y = float(point[0]), float(point[1])
        if not np.isfinite(x) or not np.isfinite(y):
            raise ValueError("non-finite polygon point")
        out.append((x, y))
    return out


def _svg_number(value: float) -> str:
    return format(float(value), ".6f").rstrip("0").rstrip(".")


def _rgb(raw: Any) -> str:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError("invalid RGB palette")
    values = [int(x) for x in raw]
    if any(x < 0 or x > 255 for x in values):
        raise ValueError("RGB palette outside byte range")
    return "#" + "".join(f"{x:02x}" for x in values)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def _render_owner_and_silhouette(
    *, primitives: list[dict[str, Any]], width: int, height: int,
    owner_masks_dir: Path, source_alpha: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    owner_names = (
        "accessory_or_held_object", "face", "hair", "head", "left_arm",
        "lower_body", "major_clothing", "neck", "right_arm", "torso", "unknown",
    )
    masks: dict[str, np.ndarray] = {}
    for name in owner_names:
        path = owner_masks_dir / f"{name}.png"
        if not path.is_file():
            raise ValueError(f"missing source-only Phase4 owner mask: {name}")
        mask = np.asarray(Image.open(path).convert("L"), dtype=np.uint8) > 0
        if mask.shape != (height, width):
            raise ValueError(f"owner mask shape mismatch: {name}")
        masks[name] = mask

    source_owner = np.full((height, width), -1, dtype=np.int16)
    for index, name in enumerate(owner_names):
        source_owner[masks[name]] = index

    rendered_owner = np.full((height, width), -1, dtype=np.int16)
    rendered = np.zeros((height, width), dtype=np.uint8)
    owner_to_index = {name: i for i, name in enumerate(owner_names)}
    for primitive in primitives:
        owner = primitive.get("semantic_part_id")
        if owner not in owner_to_index:
            owner = "unknown"
        colour = np.zeros((height, width), dtype=np.uint8)
        primitive_type = primitive.get("primitive_type")
        if primitive_type == "ellipse":
            cx, cy = primitive["parameters"]["center_xy"]
            rx, ry = primitive["parameters"]["radii_xy"]
            angle = primitive["parameters"].get("angle_degrees", 0.0)
            cv2.ellipse(colour, (int(round(cx)), int(round(cy))),
                        (max(1, int(round(rx))), max(1, int(round(ry)))),
                        float(angle), 0, 360, 255, -1)
        else:
            components = primitive["parameters"].get("components")
            if not isinstance(components, list) or not components:
                raise ValueError("Stage8 primitive has no components")
            for component in components:
                points = _points(component)
                pixels = np.rint(np.asarray(points, dtype=np.float64)).astype(np.int32)
                if len(pixels) == 1:
                    x, y = pixels[0]
                    if 0 <= x < width and 0 <= y < height:
                        colour[y, x] = 255
                elif len(pixels) == 2:
                    cv2.line(colour, tuple(pixels[0]), tuple(pixels[1]), 255, 1)
                else:
                    cv2.fillPoly(colour, [pixels], 255)
        visible = colour > 0
        rendered[visible] = 255
        rendered_owner[visible] = owner_to_index[owner]

    source_visible = source_alpha > 0
    silhouette_xor = int(np.count_nonzero(rendered.astype(bool) ^ source_visible))
    owner_mismatch = int(np.count_nonzero(rendered_owner != source_owner))
    protected = masks["face"] | masks["left_arm"] | masks["right_arm"]
    protected_mismatch = int(np.count_nonzero((rendered_owner != source_owner) & protected))
    return rendered_owner, rendered, owner_mismatch, protected_mismatch, silhouette_xor


def run(*, source: Path, case_dir: Path, output_dir: Path, source_ring_cap: int,
        expanded_svg_cap: int) -> dict[str, Any]:
    if source_ring_cap <= 0 or expanded_svg_cap <= 0:
        raise ValueError("explicit positive vertex caps are required")
    source = source.resolve()
    case_dir = case_dir.resolve()
    output_dir = output_dir.resolve()
    if not source.is_file():
        raise ValueError("signed source is missing")
    if output_dir == case_dir or case_dir in output_dir.parents:
        raise ValueError("output must be outside the pipeline case")

    phase8_stage = case_dir / "phase_08" / "stage.json"
    phase10_geometry = case_dir / "phase_10" / "10_geometry.json"
    phase11_composition = case_dir / "phase_11" / "11_composition.json"
    for path in (phase8_stage, phase10_geometry, phase11_composition):
        if not path.is_file():
            raise ValueError(f"missing pipeline artifact: {path}")
    phase8 = _load_json(phase8_stage)
    geometry = _load_json(phase10_geometry)
    composition = _load_json(phase11_composition)
    source_sha = sha256(source)
    declared_sha = phase8.get("source", {}).get("sha256")
    if declared_sha != source_sha:
        raise ValueError("Phase8/source SHA mismatch")
    primitives = composition.get("primitives_back_to_front")
    if not isinstance(primitives, list) or not primitives:
        raise ValueError("Phase11 has no selected primitives")

    width, height = Image.open(source).size
    safe_primitives: list[dict[str, Any]] = []
    polygons: list[str] = []
    vertex_count = 0
    for primitive in primitives:
        parameters = primitive.get("parameters")
        primitive_type = primitive.get("primitive_type")
        if not isinstance(parameters, dict):
            raise ValueError("Stage8 primitive parameters are missing")
        copied = dict(primitive)
        copied["parameters"] = dict(parameters)
        owner = primitive.get("semantic_part_id") or "unknown"
        fill = _rgb(primitive.get("palette_color_rgb"))
        if primitive_type == "ellipse":
            cx, cy = parameters["center_xy"]
            rx, ry = parameters["radii_xy"]
            angle = parameters.get("angle_degrees", 0.0)
            vertex_count += 4
            polygons.append(
                f'<ellipse id="{primitive["primitive_id"]}" data-owner="{owner}" '
                f'cx="{_svg_number(cx + 0.5)}" cy="{_svg_number(cy + 0.5)}" '
                f'rx="{_svg_number(rx)}" ry="{_svg_number(ry)}" '
                f'transform="rotate({_svg_number(angle)} {_svg_number(cx + 0.5)} {_svg_number(cy + 0.5)})" '
                f'fill="{fill}" shape-rendering="crispEdges"/>'
            )
        else:
            components = parameters.get("components")
            if not isinstance(components, list) or not components:
                raise ValueError("Stage8 requires polygon components")
            copied["parameters"]["components"] = []
            for component_index, component in enumerate(components):
                points = _points(component)
                copied["parameters"]["components"].append([[x, y] for x, y in points])
                vertex_count += len(points)
                if len(points) == 1:
                    x, y = points[0]
                    polygons.append(
                        f'<rect id="{primitive["primitive_id"]}-{component_index}" data-owner="{owner}" '
                        f'x="{_svg_number(x)}" y="{_svg_number(y)}" width="1" height="1" fill="{fill}"/>'
                    )
                elif len(points) == 2:
                    (x0, y0), (x1, y1) = points
                    polygons.append(
                        f'<line id="{primitive["primitive_id"]}-{component_index}" data-owner="{owner}" '
                        f'x1="{_svg_number(x0 + 0.5)}" y1="{_svg_number(y0 + 0.5)}" '
                        f'x2="{_svg_number(x1 + 0.5)}" y2="{_svg_number(y1 + 0.5)}" '
                        f'stroke="{fill}" stroke-width="1" shape-rendering="crispEdges"/>'
                    )
                else:
                    text = " ".join(f"{_svg_number(x + 0.5)},{_svg_number(y + 0.5)}" for x, y in points)
                    polygons.append(
                        f'<polygon id="{primitive["primitive_id"]}-{component_index}" data-owner="{owner}" '
                        f'points="{text}" fill="{fill}" shape-rendering="crispEdges"/>'
                    )
        safe_primitives.append(copied)

    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / "expanded_stage8.svg"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
        + "".join(polygons) + "</svg>\n"
    )
    svg_path.write_text(svg, encoding="utf-8", newline="\n")

    with Image.open(source) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    _, rendered, owner_mismatch, protected_mismatch, silhouette_xor = _render_owner_and_silhouette(
        primitives=safe_primitives, width=width, height=height,
        owner_masks_dir=case_dir / "phase_04" / "part_masks",
        source_alpha=rgba[..., 3],
    )
    source_vertices = vertex_count
    svg_sha = sha256(svg_path)
    stage8_json_path = output_dir / "stage8_source_ring.json"
    record = {
        "schema": SCHEMA,
        "case": case_dir.name,
        "pipeline": "zerobase2-phase3-to-phase11-source-only",
        "signed_source_sha256": source_sha,
        "expanded_svg_sha256": svg_sha,
        "phase8_stage_json_sha256": sha256(phase8_stage),
        "phase10_geometry_json_sha256": sha256(phase10_geometry),
        "phase11_composition_json_sha256": sha256(phase11_composition),
        "original_stage8_source_ring_vertices": source_vertices,
        "original_stage8_source_ring_cap": source_ring_cap,
        "expanded_svg_vertices": source_vertices,
        "expanded_svg_vertex_cap": expanded_svg_cap,
        "source_owner_mismatch_pixels": owner_mismatch,
        "protected_face_arm_owner_mismatch_pixels": protected_mismatch,
        "source_silhouette_xor_pixels": silhouette_xor,
        "primitive_count": len(safe_primitives),
        "source_only_inference": True,
        "human_labels_used_for_inference": False,
        "unknown_pixels_treated_as_negative": False,
        "stage8_geometry": safe_primitives,
        "cap_authority": "legacy-local-l04-cap-1887-unconfirmed-for-this-case",
        "formal_status": "HOLD",
        "production_release": "NO_GO",
    }
    stage8_json_path.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    manifest = {
        "schema": "minimalizer/local-l04/private-triple-manifest/v1",
        "source": {"path": source.name, "sha256": source_sha, "bytes": source.stat().st_size},
        "stage8_json": {"path": stage8_json_path.name, "sha256": sha256(stage8_json_path)},
        "expanded_svg": {"path": svg_path.name, "sha256": svg_sha},
        "pipeline_case_dir": case_dir.name,
        "status": "HOLD",
    }
    (output_dir / "TRIPLE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"output_dir": str(output_dir), **manifest, "measurements": {
        "source_vertices": source_vertices, "owner_mismatch_pixels": owner_mismatch,
        "protected_face_arm_owner_mismatch_pixels": protected_mismatch,
        "source_silhouette_xor_pixels": silhouette_xor,
    }}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-ring-cap", required=True, type=int)
    parser.add_argument("--expanded-svg-cap", required=True, type=int)
    args = parser.parse_args()
    print(json.dumps(run(source=args.source, case_dir=args.case_dir,
                         output_dir=args.output_dir,
                         source_ring_cap=args.source_ring_cap,
                         expanded_svg_cap=args.expanded_svg_cap),
                     ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
