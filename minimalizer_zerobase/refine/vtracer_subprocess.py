"""Fail-closed, subprocess-isolated VTracer adapter (SA10.26)."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import cv2
import numpy as np

TIMEOUT_SECONDS = 15
LICENSE_BOUNDARY = "MIT OR Apache-2.0"


def _noop(reason: str, **extra: Any) -> dict[str, Any]:
    return {"status": "fallback_noop", "backend": "vtracer", "isolated": True,
            "visible_output_changed": False, "candidate_authority": False,
            "license_boundary": LICENSE_BOUNDARY, "reason": reason, **extra}


def run_vtracer_isolated(mask: np.ndarray, *, python_executable: str | None = None,
                         timeout: int = TIMEOUT_SECONDS,
                         settings: dict[str, Any] | None = None) -> dict[str, Any]:
    """Vectorize one authorized binary mask; never lets native VTracer escape."""
    source = np.asarray(mask, dtype=np.uint8)
    if source.ndim != 2:
        return _noop("invalid_mask")
    source = np.where(source > 0, 255, 0).astype(np.uint8)
    source_sha = hashlib.sha256(source.tobytes()).hexdigest()
    settings = dict(settings or {})
    worker = Path(__file__).parents[2] / "tools" / "vtracer_isolated_worker.py"
    python = python_executable or sys.executable
    with tempfile.TemporaryDirectory(prefix="minimalizer-vtracer-") as tmp:
        png = Path(tmp) / "mask.png"
        svg = Path(tmp) / "candidate.svg"
        if not cv2.imwrite(str(png), source):
            return _noop("png_write_failed", source_mask_sha256=source_sha)
        command = [python, str(worker), str(png), str(svg), "--settings", json.dumps(settings)]
        try:
            completed = subprocess.run(command, capture_output=True, text=True,
                                       timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            return _noop("timeout", timeout_seconds=timeout, source_mask_sha256=source_sha,
                         exit_code=None, stderr=str(exc))
        except (OSError, subprocess.SubprocessError) as exc:
            return _noop("worker_launch_failed", source_mask_sha256=source_sha,
                         exit_code=None, stderr=str(exc))
        if completed.returncode != 0 or not svg.is_file():
            return _noop("nonzero" if completed.returncode else "missing_svg",
                         source_mask_sha256=source_sha, exit_code=completed.returncode,
                         stderr=completed.stderr[-2000:])
        svg_bytes = svg.read_bytes()
        return {"status": "no-op", "candidate_status": "candidate", "backend": "vtracer", "isolated": True,
                "visible_output_changed": False, "candidate_authority": False,
                "license_boundary": LICENSE_BOUNDARY, "exit_code": 0,
                "source_mask_sha256": source_sha,
                "svg_sha256": hashlib.sha256(svg_bytes).hexdigest(),
                "svg": svg_bytes.decode("utf-8"), "settings": settings}
