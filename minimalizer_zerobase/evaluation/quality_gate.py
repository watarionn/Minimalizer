from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from minimalizer_zerobase.evaluation.calibration import load_approved78_binding

@dataclass(frozen=True)
class GateCheck:
    name: str
    passed: bool
    detail: str
    release_critical: bool = True

@dataclass(frozen=True)
class FinalQualityGateResult:
    checks: tuple[GateCheck, ...]
    foundation_ready: bool
    migration_ready: bool
    approved78_replayable_cases: int

    def to_dict(self) -> dict:
        return {**asdict(self), "checks": [asdict(x) for x in self.checks]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

class FinalQualityGate:
    REQUIRED_STAGES = (
        "01_evidence.json", "02_fused_scene.json", "03_reconstructed_scene.json",
        "04_importance_scene.json", "05_palette_scene.json", "06_candidates.json",
        "07_optimization.json", "08_vector_scene.json", "09_vector_scene.svg",
    )

    def audit_artifact_capture(self, root: str | Path) -> tuple[GateCheck, ...]:
        root = Path(root)
        manifest_path = root / "manifest.json"
        if not manifest_path.is_file():
            return (GateCheck("stage_artifact_integrity", False, "manifest.json missing"),)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stages = tuple(manifest.get("stages", ()))
        missing = tuple(x for x in self.REQUIRED_STAGES if not (root / x).is_file())
        valid = stages == self.REQUIRED_STAGES and not missing
        detail = "complete deterministic stage capture" if valid else f"missing={missing}; manifest_stages={stages}"
        return (GateCheck("stage_artifact_integrity", valid, detail),)

    def audit_approved78(self, repo_root: str | Path, manifest_path: str | Path) -> GateCheck:
        repo_root = Path(repo_root)
        binding = load_approved78_binding(manifest_path)
        count = sum(
            (repo_root / r.scene_artifact).is_file() and (repo_root / r.candidate_artifact).is_file()
            for r in binding.references
        )
        return GateCheck("approved78_replay_evidence", count == 78, f"{count}/78 replayable cases present", False)

    def evaluate(self, *, repo_root: str | Path, artifact_root: str | Path,
                 approved78_manifest: str | Path, production_boundary_clean: bool,
                 renderer_deterministic: bool, replay_deterministic: bool,
                 notices_present: bool) -> FinalQualityGateResult:
        checks = list(self.audit_artifact_capture(artifact_root))
        checks.extend((
            GateCheck("deterministic_replay", replay_deterministic, "saved Evidence replay equality"),
            GateCheck("renderer_determinism", renderer_deterministic, "canonical SVG equality"),
            GateCheck("production_boundary_isolation", production_boundary_clean, "no ZeroBase imports in current production entry points"),
            GateCheck("release_license_notices", notices_present, "ZeroBase third-party code/model notice policy recorded"),
        ))
        approved = self.audit_approved78(repo_root, approved78_manifest)
        checks.append(approved)
        foundation_ready = all(x.passed for x in checks if x.release_critical)
        migration_ready = foundation_ready and approved.passed
        count = int(approved.detail.split("/", 1)[0])
        return FinalQualityGateResult(tuple(checks), foundation_ready, migration_ready, count)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()
