from __future__ import annotations
from dataclasses import dataclass
import json
import os
from pathlib import Path
from .diffmin import DIFFMIN_GUARDED, DIFFMIN_OFF, GuardedDiffMinSwitch
from .diffmin_handoff import DiffMinBundleAudit, audit_handoff_bundle

DIFFMIN_KILL_ENV = "MINIMALIZER_DIFFMIN_KILL"

@dataclass(frozen=True)
class DiffMinReleaseResult:
    effective_mode: str
    kill_switch: bool
    audit: DiffMinBundleAudit
    audit_file: str | None

def kill_switch_active() -> bool:
    return os.getenv(DIFFMIN_KILL_ENV, "").strip().lower() in {"1", "true", "yes", "on"}

def run_release_gate(bundle_root: str | Path, *, requested_mode: str | None = None, audit_dir: str | Path | None = None) -> DiffMinReleaseResult:
    killed = kill_switch_active()
    mode = DIFFMIN_OFF if killed or requested_mode is None or (requested_mode == DIFFMIN_GUARDED and audit_dir is None) else requested_mode
    audit = audit_handoff_bundle(bundle_root, GuardedDiffMinSwitch(mode))
    out = None
    if audit_dir is not None:
        path = Path(audit_dir)
        path.mkdir(parents=True, exist_ok=True)
        out = path / "diffmin_release_audit.json"
        payload = {"schema_version": "1", "effective_mode": mode, "kill_switch": killed, "audit": audit.to_dict()}
        out.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return DiffMinReleaseResult(mode, killed, audit, str(out) if out else None)
