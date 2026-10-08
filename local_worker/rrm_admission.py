"""Opt-in local Minimalizer CPU-job admission through Rinka Resource Manager.

On Windows, guarded admissions are enabled for newly started workers.
The existing running worker must never be restarted during active requests.
Set MINIMALIZER_RRM_MODE=off only for explicit rollback.
Only the compute section holds the slot, not the always-on web server.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
import os
from pathlib import Path
import sys


class RRMAdmissionDenied(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Local resource manager: {reason}")


def _guard_factory():
    root = Path(os.environ.get("MINIMALIZER_RRM_ROOT", r"C:\Work\Projects\RinkaLocalOperator"))
    if not root.is_dir() or not (root / "resource_request_guard.py").is_file():
        raise RRMAdmissionDenied("rrm_runtime_missing")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    try:
        from resource_request_guard import ResourceUnavailable, hold_heavy_slot
        return ResourceUnavailable, hold_heavy_slot
    except (ImportError, OSError) as exc:
        raise RRMAdmissionDenied("rrm_import_failed") from exc


@contextmanager
def compute_slot(route: str):
    mode = os.environ.get("MINIMALIZER_RRM_MODE", "enforce" if os.name == "nt" else "off").strip().lower()
    if mode == "off":
        yield
        return
    if mode != "enforce":
        raise RRMAdmissionDenied("invalid_mode")
    unavailable, hold = _guard_factory()
    with ExitStack() as stack:
        try:
            stack.enter_context(
                hold("minimalizer", "local-worker:" + route, kind="cpu")
            )
        except unavailable as exc:
            raise RRMAdmissionDenied(exc.reason) from exc
        except (OSError, ValueError, RuntimeError) as exc:
            raise RRMAdmissionDenied("rrm_state_unavailable") from exc
        yield
