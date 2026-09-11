from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cv2
import numpy as np

from minimalize_engine import minimalize_rinka_reference
from minimalize_engine.io.image_exporter import export_png
from minimalize_engine.io.svg_exporter import export_svg


DEFAULT_MANIFEST = ROOT / "tests" / "assets" / "approved18_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_rgb(path: Path, size: int = 128) -> np.ndarray:
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Could not decode image: {path}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA)


def _diagnostic_similarity(output_path: Path, approved_path: Path) -> dict:
    output = _load_rgb(output_path)
    approved = _load_rgb(approved_path)
    output_blur = cv2.GaussianBlur(output, (9, 9), 0).astype(np.float32)
    approved_blur = cv2.GaussianBlur(approved, (9, 9), 0).astype(np.float32)
    mae = float(np.abs(output_blur - approved_blur).mean() / 255.0)
    color_similarity = max(0.0, 1.0 - mae)

    output_gray = cv2.cvtColor(output, cv2.COLOR_RGB2GRAY)
    approved_gray = cv2.cvtColor(approved, cv2.COLOR_RGB2GRAY)
    output_edges = cv2.Canny(output_gray, 70, 150) > 0
    approved_edges = cv2.Canny(approved_gray, 70, 150) > 0
    union = int(np.logical_or(output_edges, approved_edges).sum())
    edge_iou = float(np.logical_and(output_edges, approved_edges).sum() / union) if union else 1.0
    edge_density_delta = abs(float(output_edges.mean()) - float(approved_edges.mean()))

    return {
        "coarse_color_similarity": round(color_similarity, 6),
        "edge_iou": round(edge_iou, 6),
        "edge_density_delta": round(edge_density_delta, 6),
    }


def _facial_feature_count(scene) -> int:
    tokens = ("eye", "iris", "pupil", "mouth", "lip", "eyebrow", "brow", "nose", "eyelash")
    count = 0
    for shape in scene.shapes:
        tags = " ".join((shape.source_role or "", shape.semantic_type or "", shape.character_part or "")).lower()
        if any(token in tags for token in tokens):
            count += 1
    return count


def evaluate(args: argparse.Namespace) -> dict:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    input_dir = Path(args.input_dir)
    approved_dir = Path(args.approved_dir) if args.approved_dir else None
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for entry in manifest["entries"]:
        input_path = input_dir / entry["input_file"]
        if not input_path.exists():
            raise FileNotFoundError(input_path)
        input_hash_ok = _sha256(input_path) == entry["input_sha256"]
        if not input_hash_ok:
            raise ValueError(f"Input SHA-256 mismatch: {entry['input_file']}")

        scene = minimalize_rinka_reference(
            input_path,
            level=int(args.level),
            analysis_max_side=int(args.analysis_max_side),
            preset=args.preset,
        )
        stem = Path(entry["input_file"]).stem
        png_path = out_dir / f"{stem}_{args.preset}.png"
        svg_path = out_dir / f"{stem}_{args.preset}.svg"
        export_png(scene, png_path)
        export_svg(scene, svg_path)

        target = scene.metadata.get("target_style", {}) or {}
        macro = target.get("macro_subject_guard", {}) or {}
        face15 = target.get("phase15_face_fallback", {}) or {}
        phase12 = target.get("phase12_anchor_guard", {}) or {}
        face_carrier = bool(face15.get("face_plane_created")) or bool(phase12.get("face_anchor_created"))
        feature_count = _facial_feature_count(scene)

        row = {
            "order": entry["order"],
            "character": entry["character"],
            "input_hash_ok": input_hash_ok,
            "version": target.get("version"),
            "preset": target.get("preset"),
            "shape_count": len(scene.shapes),
            "macro_guard_enabled": bool(macro.get("enabled")),
            "macro_anchor_count": int(macro.get("shape_count", 0) or 0),
            "macro_candidate_reason": macro.get("candidate_reason"),
            "face_carrier_present": face_carrier,
            "phase15_face_fallback": bool(face15.get("face_plane_created")),
            "phase12_face_anchor": bool(phase12.get("face_anchor_created")),
            "facial_feature_shape_count": feature_count,
        }
        row["structural_gate_pass"] = bool(
            row["macro_guard_enabled"] and face_carrier and feature_count == 0
        )

        if approved_dir is not None:
            approved_path = approved_dir / entry["approved_file"]
            if not approved_path.exists():
                raise FileNotFoundError(approved_path)
            approved_hash_ok = _sha256(approved_path) == entry["approved_sha256"]
            if not approved_hash_ok:
                raise ValueError(f"Approved SHA-256 mismatch: {entry['approved_file']}")
            row["approved_hash_ok"] = True
            row.update(_diagnostic_similarity(png_path, approved_path))
        rows.append(row)

    summary = {
        "count": len(rows),
        "macro_guard_enabled": sum(int(row["macro_guard_enabled"]) for row in rows),
        "face_carrier_present": sum(int(row["face_carrier_present"]) for row in rows),
        "phase15_face_fallback": sum(int(row["phase15_face_fallback"]) for row in rows),
        "phase12_face_anchor": sum(int(row["phase12_face_anchor"]) for row in rows),
        "structural_gate_pass": sum(int(row["structural_gate_pass"]) for row in rows),
        "mean_shape_count": round(float(np.mean([row["shape_count"] for row in rows])), 6) if rows else 0.0,
    }
    if rows and "coarse_color_similarity" in rows[0]:
        summary.update({
            "mean_coarse_color_similarity": round(float(np.mean([row["coarse_color_similarity"] for row in rows])), 6),
            "mean_edge_iou": round(float(np.mean([row["edge_iou"] for row in rows])), 6),
            "mean_edge_density_delta": round(float(np.mean([row["edge_density_delta"] for row in rows])), 6),
        })

    result = {
        "manifest": str(Path(args.manifest)),
        "settings": {
            "level": int(args.level),
            "analysis_max_side": int(args.analysis_max_side),
            "preset": args.preset,
        },
        "summary": summary,
        "rows": rows,
    }
    (out_dir / "approved18_evaluation.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Minimalizer against the Approved 18 regression manifest.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--approved-dir")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--level", type=int, default=4)
    parser.add_argument("--analysis-max-side", type=int, default=320)
    parser.add_argument("--preset", default="approved_reference")
    args = parser.parse_args()
    result = evaluate(args)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
