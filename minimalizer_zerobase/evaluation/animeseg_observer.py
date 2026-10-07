"""Fail-closed, non-authoritative AnimeSeg observer adapter."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

def observe(source: Path, work_dir: Path, *, python: str | None = None,
            timeout_s: int = 180, filename: str = "models/anime_seg_mask2former_v3.safetensors") -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    mask = work_dir / "animeseg_mask.png"
    req = {"source": str(Path(source).resolve()), "mask_png": str(mask), "filename": filename}
    exe = python or os.environ.get("ANIMESEG_PYTHON", r"C:\Work\Temp\Minimalizer-AnimeSeg\.venv\Scripts\python.exe")
    cmd = [exe, str(Path(__file__).parents[2] / "tools" / "animeseg_isolated_worker.py")]
    try:
        p = subprocess.run(cmd, input=json.dumps(req) + "\n", text=True, capture_output=True,
                           timeout=timeout_s, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status":"observer_unavailable", "reason":type(exc).__name__,
                "authority":False, "production_authority":False}
    try:
        result = json.loads(p.stdout.splitlines()[-1])
    except (ValueError, IndexError):
        result = {"status":"observer_unavailable", "reason":"invalid_worker_output", "authority":False}
    if p.returncode != 0 or result.get("status") != "ok":
        result["status"] = "observer_unavailable"
        result["authority"] = False
    result["worker_returncode"] = p.returncode
    result["stderr_present"] = bool(p.stderr.strip())
    result["production_authority"] = False
    return result
