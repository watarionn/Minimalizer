"""Disposable, explicitly owned Chrome profiles for Minimalizer benchmark scripts.

The profile contains Chrome cache, not experiment evidence. Evidence must go
to the separate benchmark output directory. When a benchmark exits normally,
the cache is deleted; if Python/Chrome crashes, the owner tag lets the
on-demand orphan scanner identify it without touching other apps' Chrome.
"""
from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
import time
import uuid

PROFILE_SCHEMA = "minimalizer-owned-ephemeral-chrome-v1"
PROFILE_SENTINEL = ".minimalizer-profile-owner.json"


def default_profile_root() -> Path:
    return Path(tempfile.gettempdir()) / "MinimalizerE2E"


def _within_owned_root(path: Path, root: Path) -> bool:
    try:
        actual = path.resolve()
        ancestor = root.resolve()
        return actual.parent == ancestor and actual.name.startswith("run-")
    except (OSError, ValueError):
        return False


def create_browser_profile(*, root: Path | None = None) -> Path:
    owned_root = (root or default_profile_root()).resolve()
    owned_root.mkdir(parents=True, exist_ok=True)
    profile = owned_root / ("run-" + uuid.uuid4().hex)
    # mkdir without exist_ok, fail on collisions rather than reuse user data.
    profile.mkdir()
    metadata = {
        "schema": PROFILE_SCHEMA,
        "owner": "Minimalizer",
        "run_id": profile.name,
        "creator_pid": os.getpid(),
        "created_unix": time.time(),
        "evidence_stored_in_profile": False,
        "may_be_deleted_after_chrome_quits": True,
    }
    (profile / PROFILE_SENTINEL).write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return profile


def read_owned_profile(profile: Path, *, root: Path | None = None) -> dict | None:
    owned_root = root or default_profile_root()
    if not _within_owned_root(profile, owned_root):
        return None
    manifest = profile / PROFILE_SENTINEL
    if not manifest.is_file() or manifest.is_symlink():
        return None
    try:
        record = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (
        not isinstance(record, dict)
        or record.get("schema") != PROFILE_SCHEMA
        or record.get("owner") != "Minimalizer"
        or record.get("run_id") != profile.name
        or record.get("evidence_stored_in_profile") is not False
        or record.get("may_be_deleted_after_chrome_quits") is not True
        or not isinstance(record.get("creator_pid"), int)
        or not isinstance(record.get("created_unix"), (int, float))
    ):
        return None
    return record


def cleanup_browser_profile(profile: Path, *, root: Path | None = None) -> bool:
    """Never remove an unmarked directory or another project's Chrome data."""
    record = read_owned_profile(profile, root=root)
    if record is None:
        return False
    try:
        shutil.rmtree(profile)
        return True
    except OSError as exc:
        # On Windows, an escaped Chrome child can lock one cache file.
        # rmtree may already have deleted the owner sentinel before
        # encountering that lock. Restore it for the later orphan audit.
        try:
            if profile.is_dir():
                (profile / PROFILE_SENTINEL).write_text(
                    json.dumps(record, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8",
                )
        except OSError:
            pass
        # Do not hide the actual benchmark result or exception.
        print(
            f"Minimalizer browser cache cleanup postponed: {type(exc).__name__}",
            file=sys.stderr,
        )
        return False
