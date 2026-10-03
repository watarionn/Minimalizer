from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.run_zerobase_phase14_approved18 import run_gate


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_fixture(
    tmp_path: Path,
    *,
    structural_pass: int = 18,
    tamper_approved_index: int | None = None,
) -> tuple[Path, Path, Path, Path]:
    input_dir = tmp_path / "inputs"
    approved_dir = tmp_path / "approved"
    input_dir.mkdir()
    approved_dir.mkdir()

    entries = []
    rows = []
    for index in range(1, 19):
        input_name = f"case-{index:02d}_list_thumb.png"
        approved_name = f"{index:02d}_approved.png"
        input_bytes = f"input-{index}".encode()
        approved_bytes = f"approved-{index}".encode()
        (input_dir / input_name).write_bytes(input_bytes)
        (approved_dir / approved_name).write_bytes(approved_bytes)
        entries.append(
            {
                "order": index,
                "character": f"case-{index:02d}",
                "input_file": input_name,
                "input_sha256": _sha(input_bytes),
                "approved_file": approved_name,
                "approved_sha256": _sha(approved_bytes),
            }
        )
        rows.append(
            {
                "order": index,
                "character": f"case-{index:02d}",
                "input_hash_ok": True,
                "approved_hash_ok": True,
                "structural_gate_pass": index <= structural_pass,
            }
        )

    if tamper_approved_index is not None:
        name = f"{tamper_approved_index:02d}_approved.png"
        (approved_dir / name).write_bytes(b"tampered")

    manifest = {"schema_version": 1, "entries": entries}
    evaluation = {
        "summary": {
            "count": 18,
            "structural_gate_pass": structural_pass,
            "mean_shape_count": 18.333333,
        },
        "rows": rows,
    }
    manifest_path = tmp_path / "manifest.json"
    evaluation_path = tmp_path / "evaluation.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    evaluation_path.write_text(json.dumps(evaluation), encoding="utf-8")
    return manifest_path, input_dir, approved_dir, evaluation_path


def test_phase14_approved18_gate_passes_exact_fixed_set(tmp_path: Path) -> None:
    manifest, inputs, approved, evaluation = _write_fixture(tmp_path)

    result = run_gate(
        manifest_path=manifest,
        input_dir=inputs,
        approved_dir=approved,
        evaluation_path=evaluation,
    )

    assert result["pass"] is True
    assert result["input_sha_pass_count"] == 18
    assert result["approved_sha_pass_count"] == 18
    assert result["structural_gate_pass_count"] == 18


def test_phase14_approved18_gate_fails_closed_on_structural_miss(
    tmp_path: Path,
) -> None:
    manifest, inputs, approved, evaluation = _write_fixture(
        tmp_path,
        structural_pass=17,
    )

    result = run_gate(
        manifest_path=manifest,
        input_dir=inputs,
        approved_dir=approved,
        evaluation_path=evaluation,
    )

    assert result["pass"] is False
    assert result["structural_gate_pass_count"] == 17


def test_phase14_approved18_gate_fails_closed_on_hash_mismatch(
    tmp_path: Path,
) -> None:
    manifest, inputs, approved, evaluation = _write_fixture(
        tmp_path,
        tamper_approved_index=7,
    )

    result = run_gate(
        manifest_path=manifest,
        input_dir=inputs,
        approved_dir=approved,
        evaluation_path=evaluation,
    )

    assert result["pass"] is False
    assert result["approved_sha_pass_count"] == 17
