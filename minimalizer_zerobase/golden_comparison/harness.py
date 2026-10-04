from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROLES = ("source", "golden", "current")


class GoldenHarnessError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise GoldenHarnessError("unsupported golden case schema_version")
    if not isinstance(payload.get("case_id"), str) or not payload["case_id"]:
        raise GoldenHarnessError("golden case requires case_id")
    assets = payload.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(ROLES):
        raise GoldenHarnessError("golden case assets must be exactly source/golden/current")
    for role in ROLES:
        asset = assets[role]
        if not isinstance(asset, dict):
            raise GoldenHarnessError(f"{role} asset must be an object")
        for key in ("file_name", "drive_file_id", "sha256", "media_type"):
            if not isinstance(asset.get(key), str) or not asset[key]:
                raise GoldenHarnessError(f"{role}.{key} is required")
        sha = asset["sha256"]
        if len(sha) != 64:
            raise GoldenHarnessError(f"{role}.sha256 must be 64 hex characters")
        try:
            int(sha, 16)
        except ValueError as exc:
            raise GoldenHarnessError(f"{role}.sha256 must be hexadecimal") from exc
    return payload


def build_report(manifest: dict[str, Any], asset_dir: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    all_verified = True
    for role in ROLES:
        expected = manifest["assets"][role]
        path = asset_dir / expected["file_name"]
        if not path.is_file():
            raise GoldenHarnessError(f"missing {role} asset: {path}")
        actual_sha = _sha256(path)
        verified = actual_sha == expected["sha256"]
        all_verified = all_verified and verified
        rows.append(
            {
                "role": role,
                "file_name": expected["file_name"],
                "drive_file_id": expected["drive_file_id"],
                "media_type": expected["media_type"],
                "expected_sha256": expected["sha256"],
                "actual_sha256": actual_sha,
                "verified": verified,
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "schema_version": "1.0",
        "case_id": manifest["case_id"],
        "gate": "PASS" if all_verified else "FAIL",
        "assets": rows,
    }


def verify_case(manifest_path: Path, asset_dir: Path) -> dict[str, Any]:
    report = build_report(_load_manifest(manifest_path), asset_dir)
    if report["gate"] != "PASS":
        failed = [row["role"] for row in report["assets"] if not row["verified"]]
        raise GoldenHarnessError("asset SHA mismatch: " + ", ".join(failed))
    return report


def canonical_report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
