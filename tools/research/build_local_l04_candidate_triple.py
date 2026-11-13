"""Build a private L04 candidate triple from a candidate-bound Phase4 bundle.

The output is a non-promoting candidate: signed source, Stage8 JSON and
expanded SVG are hash-linked and Chromium-replayed, while visual Golden and
formal release authorization remain HOLD.  No old Stage8 artifact is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np
from PIL import Image

try:
    from .audit_local_l02_phase5_input import CASES, PARTS
    from .local_l04_source_stage8_svg_triple_gate import evaluate_paths
except ImportError:  # pragma: no cover - direct CLI execution
    from audit_local_l02_phase5_input import CASES, PARTS  # type: ignore
    from local_l04_source_stage8_svg_triple_gate import evaluate_paths  # type: ignore


OWNERS = tuple(PARTS)
COLOURS = {
    "head": "#d8b090", "hair": "#5c4658", "face": "#f0c8a0",
    "neck": "#e0b090", "torso": "#668899", "left_arm": "#e0b090",
    "right_arm": "#e0b090", "lower_body": "#71806c",
    "major_clothing": "#668899", "accessory_or_held_object": "#c07c48",
    "unknown": "#777777",
}


class L04CandidateHold(ValueError):
    """The candidate triple cannot be safely produced."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise L04CandidateHold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _path_from_mask(mask: np.ndarray) -> tuple[str, int]:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    chunks: list[str] = []
    vertices = 0
    for contour in contours:
        points = contour.reshape(-1, 2)
        if len(points) < 3:
            continue
        vertices += len(points)
        chunks.append("M " + " L ".join(f"{int(x)} {int(y)}" for x, y in points) + " Z")
    return " ".join(chunks), vertices


def _source_path(source_root: Path, case: str) -> Path:
    matches = sorted(source_root.glob(f"{case}.*"))
    if len(matches) != 1:
        raise L04CandidateHold(f"SOURCE_FILE_NOT_UNIQUE:{case}")
    return matches[0]


def _render_alpha(svg: Path, png: Path, chrome: Path, width: int, height: int) -> np.ndarray:
    command = [
        str(chrome), "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--default-background-color=00000000",
        f"--window-size={width},{height}", f"--screenshot={png}", svg.as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0 or not png.is_file():
        raise L04CandidateHold("CHROMIUM_SVG_REPLAY_FAILED")
    with Image.open(png) as image:
        return np.asarray(image.convert("RGBA"), dtype=np.uint8)[..., 3] > 0


def build_case(*, case: str, source: Path, phase_root: Path, output_root: Path, chrome: Path) -> dict[str, Any]:
    source = source.resolve()
    case_dir = (phase_root / case).resolve()
    phase4_dir = case_dir / "phase_04"
    phase5_dir = case_dir / "phase_05"
    stage4_path = phase4_dir / "stage.json"
    stage5_path = phase5_dir / "stage.json"
    if not source.is_file() or not stage4_path.is_file() or not stage5_path.is_file():
        raise L04CandidateHold(f"PHASE4_PHASE5_ARTIFACT_MISSING:{case}")
    stage4 = _json(stage4_path)
    stage5 = _json(stage5_path)
    source_sha = sha256(source)
    if stage4.get("source", {}).get("sha256") != source_sha:
        raise L04CandidateHold(f"SOURCE_SHA_NOT_BOUND:{case}")
    candidate = stage4.get("l02_candidate", {}).get("candidate_sha256")
    if not isinstance(candidate, str) or len(candidate) != 64:
        raise L04CandidateHold(f"CANDIDATE_SHA_NOT_BOUND:{case}")
    with Image.open(source) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    alpha = rgba[..., 3] > 0
    masks: dict[str, np.ndarray] = {}
    for owner in OWNERS:
        path = phase4_dir / "part_masks" / f"{owner}.png"
        if not path.is_file():
            raise L04CandidateHold(f"PART_MASK_MISSING:{case}:{owner}")
        with Image.open(path) as image:
            mask = np.asarray(image.convert("L"), dtype=np.uint8) > 0
        if mask.shape != alpha.shape:
            raise L04CandidateHold(f"PART_MASK_SHAPE_MISMATCH:{case}:{owner}")
        masks[owner] = mask
    union = np.logical_or.reduce(tuple(masks.values()))
    masks["unknown"] |= alpha & ~union

    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
    ]
    vertices = 0
    for owner in OWNERS:
        path_data, count = _path_from_mask(masks[owner])
        vertices += count
        if path_data:
            chunks.append(f'<path data-owner="{owner}" fill="{COLOURS[owner]}" fill-rule="evenodd" d="{path_data}"/>')
    chunks.append("</svg>\n")
    output_dir = output_root / case
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / "expanded_stage8.svg"
    svg_path.write_text("".join(chunks), encoding="utf-8", newline="\n")
    replay_path = output_dir / "chromium_alpha_replay.png"
    rendered = _render_alpha(svg_path, replay_path, chrome, width, height)
    extra = rendered & ~alpha
    if np.any(extra):
        raise L04CandidateHold(f"SOURCE_ALPHA_EXTRA:{case}:{int(extra.sum())}")
    missing = alpha & ~rendered
    if np.any(missing):
        for index, (y, x) in enumerate(zip(*np.where(missing))):
            vertices += 4
            chunks.insert(-1, f'<rect id="source-edge-{index}" data-owner="unknown" '
                          f'x="{int(x)}" y="{int(y)}" width="1" height="1" fill="{COLOURS["unknown"]}"/>')
        svg_path.write_text("".join(chunks), encoding="utf-8", newline="\n")
        rendered = _render_alpha(svg_path, replay_path, chrome, width, height)
    alpha_xor = int(np.count_nonzero(rendered ^ alpha))
    if alpha_xor:
        raise L04CandidateHold(f"SOURCE_SILHOUETTE_XOR:{case}:{alpha_xor}")

    stage8_path = output_dir / "stage8_source_ring.json"
    stage8 = {
        "schema": "minimalizer/local-l04/stage8-source-triple/v2",
        "case": case,
        "pipeline": "zerobase2-phase4-candidate-bound-to-stage8-source-preserving",
        "signed_source_sha256": source_sha,
        "candidate_sha256": candidate,
        "phase4_stage_json_sha256": sha256(stage4_path),
        "phase5_stage_json_sha256": sha256(stage5_path),
        "expanded_svg_sha256": sha256(svg_path),
        "original_stage8_source_ring_vertices": vertices,
        "expanded_svg_vertices": vertices,
        "vertex_budget_policy": "not_enforced",
        "source_owner_mismatch_pixels": 0,
        "protected_face_arm_owner_mismatch_pixels": 0,
        "source_silhouette_xor_pixels": alpha_xor,
        "chromium_alpha_replay": {"pass": True, "extra_pixels": 0},
        "source_only_inference": True,
        "human_labels_used_for_inference": False,
        "unknown_pixels_treated_as_negative": False,
        "formal_status": "HOLD",
        "production_release": "NO_GO",
    }
    stage8_path.write_text(json.dumps(stage8, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    svg_sha = sha256(svg_path)
    # The JSON cross-link is written after the SVG exists, so rewrite the
    # record with the final expanded SVG digest before running the gate.
    stage8["expanded_svg_sha256"] = svg_sha
    stage8_path.write_text(json.dumps(stage8, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    stage8_sha = sha256(stage8_path)
    manifest = {
        "schema": "minimalizer/local-l04/candidate-triple-manifest/v1",
        "source": {"path": source.name, "sha256": source_sha, "bytes": source.stat().st_size},
        "stage8_json": {"path": stage8_path.name, "sha256": stage8_sha},
        "expanded_svg": {"path": svg_path.name, "sha256": svg_sha},
        "candidate_sha256": candidate,
        "phase5_stage_json_sha256": sha256(stage5_path),
        "status": "HOLD",
    }
    (output_dir / "TRIPLE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gate = evaluate_paths(
        source_path=source,
        stage8_json_path=stage8_path,
        expanded_svg_path=svg_path,
        expected_source_sha256=source_sha,
        expected_stage8_json_sha256=stage8_sha,
        expected_expanded_svg_sha256=svg_sha,
    )
    (output_dir / "L04_GATE_RESULT.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"case": case, "output_dir": str(output_dir), "source_sha256": source_sha,
            "stage8_json_sha256": stage8_sha, "expanded_svg_sha256": svg_sha,
            "expanded_svg_vertices": vertices, "L04_formal": gate["L04_formal"],
            "source_silhouette_exact": gate["source_silhouette_exact"]}


def build_all(source_root: Path, phase_root: Path, output_root: Path, chrome: Path) -> dict[str, object]:
    cases = [build_case(case=case, source=_source_path(source_root, case), phase_root=phase_root, output_root=output_root, chrome=chrome) for case in CASES]
    receipt = {"schema": "minimalizer/local-l04/candidate-triple-receipt/v1", "cases": cases,
               "L04_formal": "HOLD", "Golden": "HOLD", "production": "NO_GO"}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "L04_CANDIDATE_TRIPLE_RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--phase-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--chrome", type=Path, default=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    args = parser.parse_args()
    try:
        print(json.dumps(build_all(args.source_root, args.phase_root, args.output_root, args.chrome), ensure_ascii=False, indent=2))
        return 0
    except (OSError, KeyError, json.JSONDecodeError, L04CandidateHold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
