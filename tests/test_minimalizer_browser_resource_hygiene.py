"""Fail-closed tests for Minimalizer's nonresident Chrome cache/runtime hygiene."""
from __future__ import annotations

from pathlib import Path
import json
import os
import time

import pytest

from tools.minimalizer_browser_profile_lifecycle import (
    PROFILE_SENTINEL, PROFILE_SCHEMA,
    cleanup_browser_profile, create_browser_profile, read_owned_profile,
)
from tools.cleanup_minimalizer_orphan_chrome import (
    ProcessInfo, chrome_profile_argument, plan_orphans,
)


def profiles(tmp_path):
    root = tmp_path / "MinimalizerE2E"
    root.mkdir()
    profile = create_browser_profile(root=root)
    return root, profile


def old_tag(root: Path, profile: Path):
    marker_file = profile / PROFILE_SENTINEL
    marker = json.loads(marker_file.read_text(encoding="utf-8"))
    marker["created_unix"] = time.time() - 7200
    marker["creator_pid"] = 90001
    marker_file.write_text(json.dumps(marker), encoding="utf-8")
    return marker


def fake_tree(profile: Path, *, parent_gone=True, browser_old=True):
    now = time.time()
    created = now - 7200 if browser_old else now - 25
    profile_cli = str(profile)
    root = ProcessInfo(
        33001, 29999, "chrome.exe",
        'chrome.exe --headless=new --test-type=webdriver --user-data-dir="' +
        profile_cli + '"',
        created, 63 * 1048576,
    )
    children = [
        ProcessInfo(
            33002, 33001, "chrome.exe",
            'chrome.exe --type=renderer --user-data-dir="' + profile_cli + '"',
            created, 29 * 1048576,
        )
    ]
    if not parent_gone:
        children.append(ProcessInfo(29999, 10, "chromedriver.exe", "", now - 7200))
    return [root] + children


def plan(rows, root):
    return plan_orphans(rows, temp_root=root, now_unix=time.time(), minimum_age_seconds=3600)


def test_ephemeral_owned_profile_deleted_after_normal_run(tmp_path):
    root, profile = profiles(tmp_path)
    assert (profile / PROFILE_SENTINEL).is_file()
    assert read_owned_profile(profile, root=root)["schema"] == PROFILE_SCHEMA
    (profile / "Cache").mkdir()
    (profile / "Cache" / "test.bin").write_bytes(b"not a source image")
    assert cleanup_browser_profile(profile, root=root) is True
    assert not profile.exists()
    assert root.is_dir()


def test_locked_chrome_cache_restores_owner_tag_for_future_orphan_audit(tmp_path, monkeypatch):
    from tools import minimalizer_browser_profile_lifecycle as lifecycle

    root, profile = profiles(tmp_path)

    def simulate_windows_locked_file(path):
        # Windows rmtree can remove the tag before hitting a locked cache.
        (path / PROFILE_SENTINEL).unlink()
        raise PermissionError("chrome still owns cache")

    monkeypatch.setattr(lifecycle.shutil, "rmtree", simulate_windows_locked_file)
    assert cleanup_browser_profile(profile, root=root) is False
    assert read_owned_profile(profile, root=root) is not None


def test_unmarked_or_external_chrome_directory_never_deleted(tmp_path):
    root, profile = profiles(tmp_path)
    unrelated = tmp_path / "SomeOtherProjectChrome"
    unrelated.mkdir()
    (unrelated / "user-bookmarks.txt").write_text("retain", encoding="utf-8")
    assert cleanup_browser_profile(unrelated, root=root) is False
    assert (unrelated / "user-bookmarks.txt").is_file()
    (profile / PROFILE_SENTINEL).unlink()
    assert cleanup_browser_profile(profile, root=root) is False
    assert profile.exists()


def test_only_old_orphaned_tagged_webdriver_tree_selected(tmp_path):
    root, profile = profiles(tmp_path)
    old_tag(root, profile)
    candidates = plan(fake_tree(profile), root)
    assert len(candidates) == 1
    assert candidates[0]["process_pids"] == [33001, 33002]
    assert candidates[0]["estimated_working_set_mib"] == 92
    assert candidates[0]["source"] == "tagged_MinimalizerE2E_orphaned_headless_webdriver"


def test_active_chromedriver_creator_or_recent_test_cannot_be_cleaned(tmp_path):
    root, profile = profiles(tmp_path)
    old_tag(root, profile)
    assert plan(fake_tree(profile, parent_gone=False), root) == []
    assert plan(fake_tree(profile, browser_old=False), root) == []
    rows = fake_tree(profile)
    rows.append(ProcessInfo(90001, 100, "python.exe", "", time.time() - 3600))
    assert plan(rows, root) == []


def test_unmarked_user_chrome_and_false_origin_cannot_be_cleaned(tmp_path):
    root, profile = profiles(tmp_path)
    old_tag(root, profile)
    raw = fake_tree(profile)
    for altered_cmd in (
        'chrome.exe --headless=new --user-data-dir="' + str(profile) + '"',
        'chrome.exe --test-type=webdriver --user-data-dir="' + str(profile) + '"',
        'chrome.exe --headless=new --test-type=webdriver --user-data-dir="' +
        str(tmp_path / "UserChrome") + '"',
        'chrome.exe --headless=new --test-type=webdriver --type=renderer --user-data-dir="' +
        str(profile) + '"',
    ):
        updated = [ProcessInfo(raw[0].pid, raw[0].ppid, raw[0].name,
                               altered_cmd, raw[0].started_unix)] + raw[1:]
        assert plan(updated, root) == []
    assert chrome_profile_argument("chrome.exe --headless") is None


def test_shared_profile_from_separate_browser_is_never_terminated(tmp_path):
    root, profile = profiles(tmp_path)
    old_tag(root, profile)
    rows = fake_tree(profile)
    rows.append(ProcessInfo(
        55555, 12, "chrome.exe",
        'chrome.exe --user-data-dir="' + str(profile) + '"',
        time.time() - 7200,
    ))
    assert plan(rows, root) == []


def test_invalid_sentinel_and_short_age_fail_closed(tmp_path):
    root, profile = profiles(tmp_path)
    # The create time is current, so even an old process is not eligible.
    assert plan(fake_tree(profile), root) == []
    marker = old_tag(root, profile)
    marker["owner"] = "UnrelatedApplication"
    (profile / PROFILE_SENTINEL).write_text(json.dumps(marker), encoding="utf-8")
    assert plan(fake_tree(profile), root) == []


def test_reject_unsafe_too_short_minimum_age(tmp_path):
    root, profile = profiles(tmp_path)
    old_tag(root, profile)
    with pytest.raises(ValueError):
        plan_orphans(fake_tree(profile),temp_root=root,
                     now_unix=time.time(),minimum_age_seconds=20)


def test_delete_only_profile_subdirectory_tagged_to_minimalizer(tmp_path):
    root, profile = profiles(tmp_path)
    neighbor = root / "run-unrelated"
    neighbor.mkdir()
    (neighbor / "value.txt").write_text("do not delete", encoding="utf-8")
    assert cleanup_browser_profile(profile, root=root)
    assert (neighbor / "value.txt").is_file()
