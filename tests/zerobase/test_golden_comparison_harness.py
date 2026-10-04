from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from minimalizer_zerobase.golden_comparison.harness import (
    GoldenHarnessError,
    canonical_report_json,
    verify_case,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    payloads = {
        "source": ("source.png", b"source"),
        "golden": ("golden.jpg", b"golden"),
        "current": ("current.png", b"current"),
    }
    assets = {}
    for role, (name, data) in payloads.items():
        (asset_dir / name).write_bytes(data)
        assets[role] = {
            "file_name": name,
            "drive_file_id": f"drive-{role}",
            "sha256": _sha(data),
            "media_type": "image/jpeg" if name.endswith(".jpg") else "image/png",
        }
    manifest = {"schema_version": "1.0", "case_id": "test-case", "assets": assets}
    manifest_path = tmp_path / "case.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, asset_dir


def test_triplet_verification_is_deterministic(tmp_path: Path) -> None:
    manifest, assets = _fixture(tmp_path)
    first = canonical_report_json(verify_case(manifest, assets))
    second = canonical_report_json(verify_case(manifest, assets))
    assert first == second
    assert json.loads(first)["gate"] == "PASS"


def test_triplet_fails_closed_on_asset_replacement(tmp_path: Path) -> None:
    manifest, assets = _fixture(tmp_path)
    (assets / "golden.jpg").write_bytes(b"replacement")
    with pytest.raises(GoldenHarnessError, match="golden"):
        verify_case(manifest, assets)


def test_triplet_fails_closed_on_missing_asset(tmp_path: Path) -> None:
    manifest, assets = _fixture(tmp_path)
    (assets / "current.png").unlink()
    with pytest.raises(GoldenHarnessError, match="missing current asset"):
        verify_case(manifest, assets)


def test_manifest_requires_exact_triplet_roles(tmp_path: Path) -> None:
    manifest, assets = _fixture(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["assets"]["extra"] = payload["assets"]["source"]
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(GoldenHarnessError, match="exactly source/golden/current"):
        verify_case(manifest, assets)
