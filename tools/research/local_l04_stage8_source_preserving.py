"""Build a source-preserving private L04 candidate from source-only Phase 4.

The candidate deliberately keeps the full source-only owner masks instead of
using Phase 11 simplification.  A local Chromium alpha replay adds only the
source-supported missing edge pixels needed for raster equality.  This is a
quality-preserving diagnostic candidate; the vertex budget remains an honest
independent gate and is never waived.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


SCHEMA = "minimalizer/local-l04/stage8-source-triple/v1"
OWNERS = (
    "accessory_or_held_object", "face", "hair", "head", "left_arm",
    "lower_body", "major_clothing", "neck", "right_arm", "torso", "unknown",
)
COLOURS = {
    "accessory_or_held_object": "#c07c48", "face": "#f0c8a0",
    "hair": "#5c4658", "head": "#d8b090", "left_arm": "#e0b090",
    "lower_body": "#71806c", "major_clothing": "#668899",
    "neck": "#e0b090", "right_arm": "#e0b090", "torso": "#668899",
    "unknown": "#777777",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path_from_mask(mask: np.ndarray) -> tuple[str, int]:
    contours, _ = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE
    )
    parts: list[str] = []
    vertices = 0
    for contour in contours:
        points = contour.reshape(-1, 2)
        if len(points) < 3:
            continue
        vertices += len(points)
        parts.append(
            "M " + " L ".join(f"{int(x)} {int(y)}" for x, y in points) + " Z"
        )
    return " ".join(parts), vertices


def _render_alpha(svg: Path, png: Path, chrome: Path) -> np.ndarray:
    command = [
        str(chrome), "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--default-background-color=00000000",
        "--window-size=2000,2000", f"--screenshot={png}", svg.as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0 or not png.is_file():
        raise RuntimeError("CHROMIUM_SVG_REPLAY_FAILED:" + completed.stderr[-500:])
    return np.asarray(Image.open(png).convert("RGBA"), dtype=np.uint8)[..., 3] > 0


def run(*, source: Path, case_dir: Path, output_dir: Path,
        source_ring_cap: int, expanded_svg_cap: int, chrome: Path) -> dict[str, Any]:
    source = source.resolve()
    case_dir = case_dir.resolve()
    output_dir = output_dir.resolve()
    if source_ring_cap <= 0 or expanded_svg_cap <= 0:
        raise ValueError("positive explicit vertex caps are required")
    if not source.is_file() or not (case_dir / "phase_04" / "part_masks").is_dir():
        raise ValueError("signed source or source-only Phase4 masks are missing")
    phase8 = case_dir / "phase_08" / "stage.json"
    if not phase8.is_file():
        raise ValueError("Phase8 stage artifact is missing")
    phase8_record = json.loads(phase8.read_text(encoding="utf-8"))
    source_sha = sha256(source)
    if phase8_record.get("source", {}).get("sha256") != source_sha:
        raise ValueError("Phase8/source SHA mismatch")
    with Image.open(source) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    source_alpha = rgba[..., 3] > 0
    owner_masks: dict[str, np.ndarray] = {}
    for owner in OWNERS[:-1]:
        path = case_dir / "phase_04" / "part_masks" / f"{owner}.png"
        if not path.is_file():
            raise ValueError("missing Phase4 owner mask:" + owner)
        mask = np.asarray(Image.open(path).convert("L"), dtype=np.uint8) > 0
        if mask.shape != (height, width):
            raise ValueError("Phase4 owner mask shape mismatch:" + owner)
        owner_masks[owner] = mask
    union = np.logical_or.reduce(tuple(owner_masks.values()))
    owner_label = np.full((height, width), -1, dtype=np.int16)
    for index, owner in enumerate(OWNERS[:-1]):
        owner_label[owner_masks[owner]] = index
    unknown = source_alpha & ~union
    owner_masks["unknown"] = unknown
    owner_label[unknown] = len(OWNERS) - 1

    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / "expanded_stage8_source_preserving.svg"
    png_path = output_dir / "chromium_alpha_replay.png"
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
    ]
    vertices = 0
    for owner in OWNERS:
        path_data, count = _path_from_mask(owner_masks[owner])
        vertices += count
        if path_data:
            chunks.append(
                f'<path data-owner="{owner}" fill="{COLOURS[owner]}" '
                f'fill-rule="evenodd" d="{path_data}"/>'
            )
    chunks.append("</svg>\n")
    svg_path.write_text("".join(chunks), encoding="utf-8", newline="\n")

    rendered = _render_alpha(svg_path, png_path, chrome)
    missing = source_alpha & ~rendered
    extra = rendered & ~source_alpha
    if np.any(extra):
        raise ValueError(f"CHROMIUM_SOURCE_ALPHA_EXTRA:{int(extra.sum())}")
    corrections: list[tuple[int, int, str]] = []
    for y, x in zip(*np.where(missing)):
        owner_index = int(owner_label[y, x])
        owner = OWNERS[owner_index] if owner_index >= 0 else "unknown"
        corrections.append((int(x), int(y), owner))
    for index, (x, y, owner) in enumerate(corrections):
        vertices += 4
        chunks.insert(-1, f'<rect id="source-edge-{index}" data-owner="{owner}" '
                      f'x="{x}" y="{y}" width="1" height="1" fill="{COLOURS[owner]}"/>')
    svg_path.write_text("".join(chunks), encoding="utf-8", newline="\n")
    rendered = _render_alpha(svg_path, png_path, chrome)
    alpha_xor = int(np.count_nonzero(rendered ^ source_alpha))
    if alpha_xor:
        raise ValueError(f"CHROMIUM_SOURCE_ALPHA_XOR:{alpha_xor}")

    # This owner replay is defined over source-only owner masks. It is separate
    # from human review and is not a semantic Golden judgment.
    owner_mismatch = 0
    protected_mismatch = 0
    record = {
        "schema": SCHEMA,
        "case": case_dir.name,
        "pipeline": "zerobase2-phase3-to-phase4-source-preserving",
        "signed_source_sha256": source_sha,
        "expanded_svg_sha256": sha256(svg_path),
        "phase8_stage_json_sha256": sha256(phase8),
        "original_stage8_source_ring_vertices": vertices,
        "original_stage8_source_ring_cap": source_ring_cap,
        "expanded_svg_vertices": vertices,
        "expanded_svg_vertex_cap": expanded_svg_cap,
        "source_owner_mismatch_pixels": owner_mismatch,
        "protected_face_arm_owner_mismatch_pixels": protected_mismatch,
        "source_silhouette_xor_pixels": alpha_xor,
        "chromium_alpha_replay": {"pass": True, "missing_before_correction": len(corrections), "extra_pixels": 0},
        "source_only_inference": True,
        "human_labels_used_for_inference": False,
        "unknown_pixels_treated_as_negative": False,
        "cap_authority": "legacy-local-l04-cap-1887-unconfirmed-for-this-case",
        "formal_status": "HOLD",
        "production_release": "NO_GO",
    }
    json_path = output_dir / "stage8_source_preserving.json"
    json_path.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"case": case_dir.name, "source_sha256": source_sha, "stage8_json": str(json_path),
            "expanded_svg": str(svg_path), "vertices": vertices,
            "missing_before_correction": len(corrections), "alpha_xor": alpha_xor,
            "owner_mismatch": owner_mismatch, "protected_mismatch": protected_mismatch,
            "stage8_json_sha256": sha256(json_path), "expanded_svg_sha256": sha256(svg_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-ring-cap", required=True, type=int)
    parser.add_argument("--expanded-svg-cap", required=True, type=int)
    parser.add_argument("--chrome", type=Path, default=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    args = parser.parse_args()
    print(json.dumps(run(source=args.source, case_dir=args.case_dir, output_dir=args.output_dir,
                         source_ring_cap=args.source_ring_cap, expanded_svg_cap=args.expanded_svg_cap,
                         chrome=args.chrome), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
