"""Apply a prepared Local L07 bundle with owner-only safeguards.

The command intentionally does not restart a worker, change git refs, or
touch ``dist/``.  It backs up only the manifest-listed files it replaces and reports
that a separate owner-approved restart/readback is still required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


SCHEMA = "minimalizer/local-l07/runtime-apply/v1"
MANIFEST_SCHEMA = "minimalizer/local-l07/runtime-staging/v1"
EXPECTED_WORKER = "64cfeb76e5f8ff4e93b6810880c68f1996348ede"
PRODUCTION_TARGET = Path(r"C:\Work\Projects\_runtime\minimalizer-production")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _load_manifest(bundle: Path) -> dict[str, Any]:
    manifest_path = bundle / "runtime-staging-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("STAGING_MANIFEST_MISSING")
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("STAGING_MANIFEST_SCHEMA_INVALID")
    if value.get("status") != "STAGING_READY":
        raise ValueError("STAGING_NOT_READY")
    records = value.get("files")
    if not isinstance(records, list) or len(records) != 5:
        raise ValueError("STAGING_FILE_SET_INVALID")
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError("STAGING_FILE_RECORD_INVALID")
        path = Path(record["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("STAGING_PATH_INVALID")
        source = bundle / path
        if not source.is_file() or _sha256(source) != record.get("sha256"):
            raise ValueError("STAGING_FILE_SHA_MISMATCH:" + record["path"])
    return value


def apply_bundle(
    bundle: Path,
    target: Path,
    backup: Path,
    *,
    owner_approved: bool,
    allow_nonproduction_target: bool = False,
    expected_worker: str = EXPECTED_WORKER,
) -> dict[str, Any]:
    if not owner_approved:
        raise ValueError("OWNER_APPROVAL_REQUIRED")
    bundle = bundle.resolve()
    target = target.resolve()
    backup = backup.resolve()
    if not allow_nonproduction_target and target != PRODUCTION_TARGET.resolve():
        raise ValueError("PRODUCTION_TARGET_MISMATCH")
    manifest = _load_manifest(bundle)
    if not target.is_dir():
        raise ValueError("TARGET_DIRECTORY_MISSING")
    current_worker = _git_head(target)
    if current_worker != expected_worker:
        raise ValueError(f"WORKER_SHA_MISMATCH:{current_worker}")
    records = tuple(manifest["files"])
    destinations: list[tuple[dict[str, str], Path, Path]] = []
    for record in records:
        relative = Path(record["path"])
        destination = target / relative
        if not destination.parent.is_dir():
            raise ValueError("TARGET_PARENT_MISSING:" + record["path"])
        if destination.is_symlink() or (destination.exists() and not destination.is_file()):
            raise ValueError("TARGET_FILE_NOT_REGULAR:" + record["path"])
        destinations.append((record, destination, backup / relative))
    if backup.exists():
        if not backup.is_dir() or any(backup.iterdir()):
            raise ValueError("BACKUP_MUST_BE_NEW_EMPTY_DIRECTORY")
    else:
        backup.mkdir(parents=True)

    applied: list[dict[str, str]] = []
    try:
        for record, destination, backup_path in destinations:
            if destination.is_file():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup_path)
            shutil.copy2(bundle / Path(record["path"]), destination)
            if _sha256(destination) != record["sha256"]:
                raise ValueError("TARGET_SHA_MISMATCH:" + record["path"])
            applied.append({"path": record["path"], "sha256": record["sha256"]})

        result = {
            "schema": SCHEMA,
            "status": "APPLIED_PENDING_OWNER_RESTART_READBACK",
            "owner_approved": True,
            "runtime_mutation": True,
            "worker_before": current_worker,
            "worker_after": _git_head(target),
            "backup_dir": str(backup),
            "dist_touched": False,
            "restart_performed": False,
            "readback_performed": False,
            "files": applied,
        }
        (backup / "runtime-apply-manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return result
    except Exception:
        for _record, destination, backup_path in reversed(destinations):
            if backup_path.is_file():
                shutil.copy2(backup_path, destination)
            elif destination.is_file():
                destination.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--owner-approved", action="store_true")
    args = parser.parse_args()
    try:
        result = apply_bundle(
            args.bundle,
            args.target,
            args.backup,
            owner_approved=args.owner_approved,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({"schema": SCHEMA, "status": "HOLD", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
