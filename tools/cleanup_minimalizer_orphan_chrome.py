"""On-demand, fail-closed cleanup of abandoned Minimalizer E2E Chrome only.

Default is AUDIT: no process or file is touched. Explicit --apply is
allowed ONLY for a Chrome WebDriver orphan using a tagged temporary profile
created by minimalizer_browser_profile_lifecycle.create_browser_profile.
Active parents, recently started browsers, untagged profiles, user Chrome,
Local Worker, Ollama, Qwen, Docker, and Tailscale are never candidates.

Not a resident monitor. No third-party dependencies, no generic cache purge.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import ntpath
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

if __package__:
    from .minimalizer_browser_profile_lifecycle import (
        default_profile_root, read_owned_profile, cleanup_browser_profile,
    )
else:
    from minimalizer_browser_profile_lifecycle import (
        default_profile_root, read_owned_profile, cleanup_browser_profile,
    )


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    ppid: int
    name: str
    command: str
    started_unix: float
    rss_bytes: int = 0


_PROFILE_RE = re.compile(r'--user-data-dir=(?:"([^"]+)"|(\S+))', re.I)


def chrome_profile_argument(command: str) -> str | None:
    match = _PROFILE_RE.search(command or "")
    return (match.group(1) or match.group(2)).rstrip('"') if match else None


def _same_windows_path(a: str, b: str) -> bool:
    return ntpath.normcase(ntpath.normpath(a)) == ntpath.normcase(ntpath.normpath(b))


def plan_orphans(
    processes: list[ProcessInfo],
    *,
    temp_root: Path,
    now_unix: float,
    minimum_age_seconds: int = 3600,
) -> list[dict]:
    """Return executable cleanup plans only for positively identified orphans.

    The parent and original profile-creator PID must BOTH have exited.
    The entire descendant tree must consist of Chrome with the same profile.
    If another process refers to the profile, fail closed.
    """
    if minimum_age_seconds < 1800:
        raise ValueError("minimum orphan age must be at least 30 minutes")
    pidmap = {p.pid: p for p in processes}
    if len(pidmap) != len(processes):
        raise ValueError("ambiguous OS process snapshot")
    results = []
    for p in processes:
        if (
            p.name.lower() != "chrome.exe"
            or not (p.command and "--headless" in p.command.lower())
            or "--test-type=webdriver" not in p.command.lower()
            or "--type=" in p.command.lower()
            or p.ppid in pidmap
            or now_unix - p.started_unix < minimum_age_seconds
        ):
            continue
        profile_arg = chrome_profile_argument(p.command)
        if not profile_arg:
            continue
        profile = temp_root / ntpath.basename(ntpath.normpath(profile_arg))
        if not _same_windows_path(str(profile), profile_arg):
            continue
        marker = read_owned_profile(profile, root=temp_root)
        if not marker:
            continue
        if marker["creator_pid"] in pidmap:
            continue
        if now_unix - marker["created_unix"] < minimum_age_seconds:
            continue
        group = {p.pid}
        while True:
            grow = {q.pid for q in processes if q.ppid in group}
            if grow.issubset(group):
                break
            group |= grow
        members = [pidmap[pid] for pid in group]
        if any(
            x.name.lower() != "chrome.exe"
            or not _same_windows_path(
                chrome_profile_argument(x.command) or "", profile_arg
            )
            for x in members
        ):
            continue
        # An independent process using the profile is absolute no-go.
        if any(
            x.pid not in group
            and _same_windows_path(
                chrome_profile_argument(x.command) or "", profile_arg
            )
            for x in processes
        ):
            continue
        results.append({
            "root_pid": p.pid,
            "root_started_unix": p.started_unix,
            "process_pids": sorted(group),
            "process_count": len(members),
            "estimated_working_set_mib": round(
                sum(max(0, x.rss_bytes) for x in members) / 1048576, 2
            ),
            "profile": str(profile),
            "source": "tagged_MinimalizerE2E_orphaned_headless_webdriver",
            "creator_pid_gone": True,
            "chromedriver_parent_gone": True,
        })
    return results


def snapshot_windows_processes() -> list[ProcessInfo]:
    if os.name != "nt":
        raise RuntimeError("live process introspection supports Windows only")
    cmd = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$records = @(
 Get-CimInstance Win32_Process | ForEach-Object {
  $created = 0
  if ($_.CreationDate) { $created = ([DateTimeOffset]$_.CreationDate).ToUnixTimeSeconds() }
  [pscustomobject]@{
   pid=[int]$_.ProcessId; ppid=[int]$_.ParentProcessId
   name=[string]$_.Name
   command= if ($_.Name -eq 'chrome.exe') {[string]$_.CommandLine} else {''}
   started_unix=[double]$created
   rss_bytes=[long]$_.WorkingSetSize
  }
 }
)
ConvertTo-Json -InputObject $records -Compress -Depth 3
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=45,
        check=True,
    )
    raw = json.loads(result.stdout.lstrip("\ufeff").strip())
    if not isinstance(raw, list):
        raise RuntimeError("malformed Windows process inventory")
    return [ProcessInfo(**record) for record in raw]


def apply_one(
    item: dict, *, temp_root: Path, minimum_age_seconds: int,
) -> dict:
    """Reread OS state immediately before acting to catch PID reuse."""
    fresh = snapshot_windows_processes()
    verified = plan_orphans(
        fresh, temp_root=temp_root, now_unix=time.time(),
        minimum_age_seconds=minimum_age_seconds,
    )
    match = next((
        x for x in verified
        if x["root_pid"] == item["root_pid"]
        and x["root_started_unix"] == item["root_started_unix"]
        and x["process_pids"] == item["process_pids"]
        and x["profile"] == item["profile"]
    ), None)
    if match is None:
        return {"root_pid": item["root_pid"], "status": "SKIPPED_CHANGED"}
    pids = match["process_pids"]
    # Children first; no /T recursive kill, and only the verified exact PIDs.
    for pid in reversed(pids):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    time.sleep(0.5)
    still_alive = {p.pid for p in snapshot_windows_processes()}
    if set(pids) & still_alive:
        return {"root_pid": item["root_pid"], "status": "PARTIAL_PROFILE_PRESERVED"}
    removed = cleanup_browser_profile(
        Path(match["profile"]), root=temp_root
    )
    return {
        "root_pid": item["root_pid"],
        "status": "CLOSED_AND_PROFILE_CLEARED" if removed
                  else "CLOSED_PROFILE_PRESERVED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Explicitly close tagged orphaned test Chrome only.")
    parser.add_argument("--minimum-age-minutes", type=int, default=60)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    if args.minimum_age_minutes < 30:
        parser.error("minimum age must not be less than 30 minutes")
    root = default_profile_root()
    processes = snapshot_windows_processes()
    results = plan_orphans(
        processes, temp_root=root, now_unix=time.time(),
        minimum_age_seconds=args.minimum_age_minutes * 60,
    )
    operations = []
    if args.apply:
        for candidate in results:
            operations.append(apply_one(
                candidate, temp_root=root,
                minimum_age_seconds=args.minimum_age_minutes * 60,
            ))
    report = {
        "schema": "minimalizer-on-demand-browser-residue-guard-v1",
        "mode": "EXPLICIT_APPLY" if args.apply else "AUDIT_ONLY",
        "persistently_running_watcher_installed": False,
        "other_project_processes_targeted": False,
        "local_worker_and_tailscale_targeted": False,
        "minimum_age_minutes": args.minimum_age_minutes,
        "profiles_root": str(root),
        "orphan_candidate_count": len(results),
        "orphan_candidates": results,
        "operations": operations,
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
