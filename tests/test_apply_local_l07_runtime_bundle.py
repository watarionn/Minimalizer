import subprocess
from pathlib import Path
import shutil

import pytest

from tools.research.apply_local_l07_runtime_bundle import apply_bundle
from tools.research.prepare_local_l07_runtime_bundle import FILES, prepare


ROOT = Path(__file__).parents[1]


def _git_target(source: Path, target: Path) -> str:
    for relative in FILES:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    subprocess.run(["git", "-C", str(target), "init", "-b", "main"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(target), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(target), "config", "user.name", "Minimalizer Test"], check=True)
    subprocess.run(["git", "-C", str(target), "add", "."], check=True)
    subprocess.run(["git", "-C", str(target), "commit", "-m", "fixture"], check=True, capture_output=True)
    return subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_apply_requires_owner_approval(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    prepare(ROOT, bundle)
    worker = _git_target(ROOT, target)

    with pytest.raises(ValueError, match="OWNER_APPROVAL_REQUIRED"):
        apply_bundle(
            bundle,
            target,
            tmp_path / "backup",
            owner_approved=False,
            allow_nonproduction_target=True,
            expected_worker=worker,
        )


def test_apply_is_bounded_and_leaves_restart_readback_pending(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    backup = tmp_path / "backup"
    prepare(ROOT, bundle)
    worker = _git_target(ROOT, target)
    dist_sentinel = target / "dist" / "keep.txt"
    dist_sentinel.parent.mkdir()
    dist_sentinel.write_text("must remain", encoding="utf-8")

    result = apply_bundle(
        bundle,
        target,
        backup,
        owner_approved=True,
        allow_nonproduction_target=True,
        expected_worker=worker,
    )

    assert result["status"] == "APPLIED_PENDING_OWNER_RESTART_READBACK"
    assert result["runtime_mutation"] is True
    assert result["restart_performed"] is False
    assert result["readback_performed"] is False
    assert result["dist_touched"] is False
    assert dist_sentinel.read_text(encoding="utf-8") == "must remain"
    assert (backup / "runtime-apply-manifest.json").is_file()
    for relative in FILES:
        assert (backup / relative).is_file()
        assert (target / relative).read_bytes() == (bundle / relative).read_bytes()


def test_apply_rejects_nonproduction_target_without_test_escape(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    prepare(ROOT, bundle)
    worker = _git_target(ROOT, target)

    with pytest.raises(ValueError, match="PRODUCTION_TARGET_MISMATCH"):
        apply_bundle(
            bundle,
            target,
            tmp_path / "backup",
            owner_approved=True,
            expected_worker=worker,
        )
