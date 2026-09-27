from __future__ import annotations
import hashlib
import json
import shutil
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.production import ProductionPipeline

CORPUS = Path(r"C:\Users\watar\Documents\GitHub\_worktrees\minimalizer-approved78-cut-calibration\_eval_assets\approved78_full")
OUT = ROOT / "artifacts" / "approved78"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("case_count") != 78 or len(manifest.get("cases", [])) != 78:
        raise RuntimeError("Approved-78 full corpus must contain exactly 78 cases")
    pipeline = ProductionPipeline()
    audit = []
    for case in manifest["cases"]:
        index = int(case["order"])
        source = CORPUS / "inputs" / case["input_file"]
        if not source.is_file():
            raise FileNotFoundError(source)
        if sha256(source) != case["input_sha256"]:
            raise RuntimeError(f"source SHA mismatch: {index:02d}")
        raw = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
        if raw is None:
            raise RuntimeError(f"failed to read source: {source}")
        if raw.ndim != 3 or raw.shape[2] != 4:
            raise RuntimeError(f"migration corpus source lacks canonical alpha: {index:02d}")
        rgba = cv2.cvtColor(raw, cv2.COLOR_BGRA2RGBA)
        space = CoordinateSpace(rgba.shape[1], rgba.shape[0])
        evidence = SLICRegionAdapter(min_foreground_ratio=0.5).analyze(rgba, space)
        case_dir = OUT / f"{index:02d}"
        pipeline.run(evidence, case_dir)
        shutil.copyfile(case_dir / "05_palette_scene.json", case_dir / "scene.json")
        shutil.copyfile(case_dir / "06_candidates.json", case_dir / "candidates.json")
        before = sha256(case_dir / "09_vector_scene.svg")
        replay = pipeline.replay(case_dir)
        after = sha256(case_dir / "09_vector_scene.svg")
        if before != after:
            raise RuntimeError(f"non-deterministic replay: {index:02d}")
        audit.append({
            "index": index,
            "character": case["character"],
            "source_file": case["input_file"],
            "source_sha256": case["input_sha256"],
            "source_rule": manifest["source_rule"]["1-18" if index <= 18 else "19-78"],
            "evidence_count": len(evidence),
            "primitive_count": len(replay.vector_scene.primitives),
            "svg_sha256": after,
        })
        print(f"DONE {index:02d} {case['character']}", flush=True)

    report = {
        "schema_version": 1,
        "corpus": manifest["name"],
        "case_count": len(audit),
        "source_rule": manifest["source_rule"],
        "all_source_sha256_verified": True,
        "all_replay_deterministic": True,
        "cases": audit,
    }
    (ROOT / "docs" / "zerobase" / "MIGRATION_APPROVED78_CAPTURE.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
