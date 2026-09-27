from __future__ import annotations
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).parents[1]
CORPUS = Path(r"C:\Users\watar\Documents\GitHub\_worktrees\minimalizer-approved78-cut-calibration\_eval_assets\approved78_full")
LEGACY = Path(r"C:\Users\watar\AppData\Local\Temp\minimalizer_pose_line_gated_eval_20260919\outputs_v2_approved78")

def fg_mask(rgb: np.ndarray) -> np.ndarray:
    return np.any(rgb < 245, axis=2)

def metrics(image: np.ndarray, reference: np.ndarray) -> dict:
    ref = cv2.resize(reference, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_AREA)
    a, b = fg_mask(image), fg_mask(ref)
    inter = int(np.count_nonzero(a & b))
    union = int(np.count_nonzero(a | b))
    iou = inter / union if union else 1.0
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    refgray = cv2.cvtColor(ref, cv2.COLOR_RGB2GRAY)
    refedges = cv2.Canny(refgray, 40, 120)
    return {
        "silhouette_iou": round(iou, 6),
        "foreground_ratio": round(float(a.mean()), 6),
        "foreground_ratio_error": round(abs(float(a.mean()) - float(b.mean())), 6),
        "edge_density": round(float((edges > 0).mean()), 6),
        "edge_density_error": round(abs(float((edges > 0).mean()) - float((refedges > 0).mean())), 6),
    }
def render_zero(scene: dict) -> np.ndarray:
    h, w = int(scene["height"]), int(scene["width"])
    out = np.full((h, w, 3), 255, dtype=np.uint8)
    for item in sorted(scene["primitives"], key=lambda x: (x["z_order"], x["primitive_id"])):
        color = item["fill_ref"]
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        p = item["parameters"]
        x, y, bw, bh = [int(round(v)) for v in p["bbox"]]
        x2, y2 = min(w - 1, x + max(0, bw - 1)), min(h - 1, y + max(0, bh - 1))
        if item["primitive_type"] == "rectangle":
            cv2.rectangle(out, (max(0,x), max(0,y)), (x2,y2), rgb, -1)
        elif item["primitive_type"] == "capsule":
            radius = max(1, int(round(p.get("radius", min(bw,bh)/2))))
            cv2.rectangle(out, (max(0,x), max(0,y)), (x2,y2), rgb, -1)
            if p.get("axis") == "vertical":
                cx = max(0, min(w-1, x + bw//2))
                cv2.circle(out, (cx, max(0,y)), min(radius,bw//2), rgb, -1)
                cv2.circle(out, (cx, y2), min(radius,bw//2), rgb, -1)
            else:
                cy = max(0, min(h-1, y + bh//2))
                cv2.circle(out, (max(0,x), cy), min(radius,bh//2), rgb, -1)
                cv2.circle(out, (x2, cy), min(radius,bh//2), rgb, -1)
        else:
            raise RuntimeError(f"unsupported migration raster primitive: {item['primitive_type']}")
    return out
def main() -> int:
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for case in manifest["cases"]:
        i = int(case["order"])
        ref_path = CORPUS / "references" / case["approved_file"]
        if hashlib.sha256(ref_path.read_bytes()).hexdigest() != case["approved_sha256"]:
            raise RuntimeError(f"approved reference SHA mismatch: {i:02d}")
        ref = cv2.cvtColor(cv2.imread(str(ref_path)), cv2.COLOR_BGR2RGB)
        scene = json.loads((ROOT / "artifacts" / "approved78" / f"{i:02d}" / "08_vector_scene.json").read_text(encoding="utf-8"))
        zero = render_zero(scene)
        legacy_path = LEGACY / f"{i:02d}_{case['character']}__baseline.png"
        legacy = cv2.cvtColor(cv2.imread(str(legacy_path)), cv2.COLOR_BGR2RGB)
        rows.append({
            "index": i, "character": case["character"],
            "zerobase": metrics(zero, ref),
            "legacy2": metrics(legacy, ref),
            "zerobase_primitive_count": len(scene["primitives"]),
        })
    ziou = np.array([x["zerobase"]["silhouette_iou"] for x in rows])
    liou = np.array([x["legacy2"]["silhouette_iou"] for x in rows])
    zfg = np.array([x["zerobase"]["foreground_ratio_error"] for x in rows])
    lfg = np.array([x["legacy2"]["foreground_ratio_error"] for x in rows])
    report = {
        "schema_version": 1,
        "case_count": len(rows),
        "all_reference_sha256_verified": True,
        "comparison": "ZeroBase deterministic SLIC baseline vs current stored Minimalizer 2.0 baseline, each against Approved-78 reference",
        "aggregate": {
            "zerobase_mean_silhouette_iou": round(float(ziou.mean()), 6),
            "legacy2_mean_silhouette_iou": round(float(liou.mean()), 6),
            "zerobase_silhouette_wins": int(np.count_nonzero(ziou > liou)),
            "legacy2_silhouette_wins": int(np.count_nonzero(liou > ziou)),
            "zerobase_mean_foreground_ratio_error": round(float(zfg.mean()), 6),
            "legacy2_mean_foreground_ratio_error": round(float(lfg.mean()), 6),
            "zerobase_foreground_ratio_wins": int(np.count_nonzero(zfg < lfg)),
            "legacy2_foreground_ratio_wins": int(np.count_nonzero(lfg < zfg)),
            "zerobase_mean_primitive_count": round(float(np.mean([x["zerobase_primitive_count"] for x in rows])), 6),
        },
        "cases": rows,
    }
    out = ROOT / "docs" / "zerobase" / "MIGRATION_APPROVED78_COMPARISON.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
