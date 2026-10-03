from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_gate(
    *,
    manifest_path: Path,
    input_dir: Path,
    approved_dir: Path,
    evaluation_path: Path,
) -> dict[str, Any]:
    manifest = _load(manifest_path)
    evaluation = _load(evaluation_path)
    entries = manifest.get("entries", [])
    rows = evaluation.get("rows", [])
    summary = evaluation.get("summary", {})

    if len(entries) != 18:
        raise ValueError("Approved-18 manifest must contain exactly 18 entries")
    if len(rows) != 18:
        raise ValueError("Approved-18 evaluation must contain exactly 18 rows")

    sha_rows: list[dict[str, Any]] = []
    input_sha_pass = 0
    approved_sha_pass = 0
    for entry in entries:
        input_path = input_dir / entry["input_file"]
        approved_path = approved_dir / entry["approved_file"]
        input_ok = input_path.is_file() and _sha(input_path) == entry["input_sha256"]
        approved_ok = (
            approved_path.is_file()
            and _sha(approved_path) == entry["approved_sha256"]
        )
        input_sha_pass += int(input_ok)
        approved_sha_pass += int(approved_ok)
        sha_rows.append(
            {
                "order": entry["order"],
                "character": entry["character"],
                "input_file": entry["input_file"],
                "input_sha256_ok": input_ok,
                "approved_file": entry["approved_file"],
                "approved_sha256_ok": approved_ok,
            }
        )

    structural_pass = int(summary.get("structural_gate_pass", 0))
    row_structural_pass = sum(
        int(bool(row.get("structural_gate_pass"))) for row in rows
    )
    row_input_hash_pass = sum(
        int(bool(row.get("input_hash_ok"))) for row in rows
    )
    row_approved_hash_pass = sum(
        int(bool(row.get("approved_hash_ok"))) for row in rows
    )
    pass_value = bool(
        input_sha_pass == 18
        and approved_sha_pass == 18
        and row_input_hash_pass == 18
        and row_approved_hash_pass == 18
        and structural_pass == 18
        and row_structural_pass == 18
    )
    return {
        "schema_version": "1.0",
        "phase": 14,
        "gate": "Approved-18-regression",
        "pass": pass_value,
        "case_count": 18,
        "input_sha_pass_count": input_sha_pass,
        "approved_sha_pass_count": approved_sha_pass,
        "evaluation_input_sha_pass_count": row_input_hash_pass,
        "evaluation_approved_sha_pass_count": row_approved_hash_pass,
        "structural_gate_pass_count": structural_pass,
        "row_structural_gate_pass_count": row_structural_pass,
        "diagnostics": {
            "mean_shape_count": summary.get("mean_shape_count"),
            "mean_coarse_color_similarity": summary.get(
                "mean_coarse_color_similarity"
            ),
            "mean_edge_iou": summary.get("mean_edge_iou"),
            "mean_edge_density_delta": summary.get(
                "mean_edge_density_delta"
            ),
            "diagnostic_metrics_are_non_gating": True,
        },
        "sha_evidence": sha_rows,
        "failure_policy": (
            "Approved-18 regression requires all 18 input hashes, all 18 "
            "Approved-reference hashes, and all 18 structural gates to pass. "
            "Historical coarse-color/edge metrics remain diagnostic only."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Phase 14 Approved-18 regression Gate."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "tests" / "assets" / "approved18_manifest.json",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=ROOT / "artifacts" / "phase14_approved18_inputs",
    )
    parser.add_argument(
        "--approved-dir",
        type=Path,
        default=ROOT / "artifacts" / "phase14_approved18_references",
    )
    parser.add_argument(
        "--evaluation",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "phase14_approved18_evaluation"
            / "approved18_evaluation.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "phase14_approved18"
            / "14_approved18_regression_gate.json"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_gate(
        manifest_path=args.manifest,
        input_dir=args.input_dir,
        approved_dir=args.approved_dir,
        evaluation_path=args.evaluation,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "pass": result["pass"],
                "case_count": result["case_count"],
                "input_sha_pass_count": result["input_sha_pass_count"],
                "approved_sha_pass_count": result["approved_sha_pass_count"],
                "structural_gate_pass_count": result[
                    "structural_gate_pass_count"
                ],
                "diagnostics": result["diagnostics"],
                "output": str(args.output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
