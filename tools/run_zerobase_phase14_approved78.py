from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.evaluation import (
    Approved78CalibrationHarness,
    CalibrationCase,
    MigrationGate,
    load_approved78_binding,
)
from minimalizer_zerobase.geometry import PrimitiveCandidate
from minimalizer_zerobase.scene.models import (
    Region,
    Relation,
    Scene,
    Subject,
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _scene_from_payload(payload: dict[str, Any]) -> Scene:
    coordinate = payload["coordinate_space"]
    coordinate_space = CoordinateSpace(
        width=int(coordinate["width"]),
        height=int(coordinate["height"]),
        unit=str(coordinate.get("unit", "pixel")),
        origin=str(coordinate.get("origin", "top_left")),
    )
    regions = tuple(
        Region(
            region_id=str(item["region_id"]),
            semantic_role=str(item["semantic_role"]),
            evidence_ids=tuple(str(x) for x in item.get("evidence_ids", ())),
            importance=float(item.get("importance", 0.0)),
            confidence=float(item.get("confidence", 0.0)),
            geometry=dict(item.get("geometry", {})),
        )
        for item in payload.get("regions", ())
    )
    subjects = tuple(
        Subject(
            subject_id=str(item["subject_id"]),
            semantic_class=str(item["semantic_class"]),
            region_ids=tuple(str(x) for x in item.get("region_ids", ())),
            importance=float(item.get("importance", 0.0)),
            confidence=float(item.get("confidence", 0.0)),
        )
        for item in payload.get("subjects", ())
    )
    relations = tuple(
        Relation(
            source_id=str(item["source_id"]),
            target_id=str(item["target_id"]),
            kind=str(item["kind"]),
            confidence=(
                None
                if item.get("confidence") is None
                else float(item["confidence"])
            ),
        )
        for item in payload.get("relations", ())
    )
    return Scene(
        coordinate_space=coordinate_space,
        producer=str(payload.get("producer", "saved-artifact")),
        producer_version=str(payload.get("producer_version", "1.0")),
        subjects=subjects,
        regions=regions,
        relations=relations,
        palette=tuple(str(x) for x in payload.get("palette", ())),
        provenance=dict(payload.get("provenance", {})),
        schema_version=str(payload.get("schema_version", "1.0")),
    )


def _candidate_from_payload(payload: dict[str, Any]) -> PrimitiveCandidate:
    return PrimitiveCandidate(
        candidate_id=str(payload["candidate_id"]),
        primitive_type=str(payload["primitive_type"]),
        source_region_id=str(payload["source_region_id"]),
        parameters=dict(payload.get("parameters", {})),
        metrics={
            str(key): float(value)
            for key, value in payload.get("metrics", {}).items()
        },
        semantic_constraints=tuple(
            str(x) for x in payload.get("semantic_constraints", ())
        ),
        schema_version=str(payload.get("schema_version", "1.0")),
    )


def _load_cases(
    repo_root: Path,
    manifest_path: Path,
) -> tuple[tuple[CalibrationCase, ...], dict[str, Any]]:
    binding = load_approved78_binding(manifest_path)
    cases: list[CalibrationCase] = []
    evidence: list[dict[str, Any]] = []
    for reference in binding.references:
        scene_path = repo_root / reference.scene_artifact
        candidate_path = repo_root / reference.candidate_artifact
        if not scene_path.is_file():
            raise ValueError(
                f"Approved-78 scene artifact missing: {scene_path}"
            )
        if not candidate_path.is_file():
            raise ValueError(
                f"Approved-78 candidate artifact missing: {candidate_path}"
            )
        scene_payload = _load_json(scene_path)
        candidates_payload = _load_json(candidate_path)
        if not isinstance(scene_payload, dict):
            raise ValueError(
                f"Approved-78 Scene must be an object: {scene_path}"
            )
        if not isinstance(candidates_payload, list):
            raise ValueError(
                f"Approved-78 candidates must be a list: {candidate_path}"
            )
        scene = _scene_from_payload(scene_payload)
        candidates = tuple(
            _candidate_from_payload(item)
            for item in candidates_payload
            if isinstance(item, dict)
        )
        if not candidates:
            raise ValueError(
                f"Approved-78 candidate artifact is empty: {candidate_path}"
            )
        cases.append(CalibrationCase(reference, scene, candidates))
        evidence.append(
            {
                "index": reference.index,
                "name": reference.name,
                "scene_artifact": reference.scene_artifact,
                "scene_sha256": _sha256_file(scene_path),
                "candidate_artifact": reference.candidate_artifact,
                "candidate_sha256": _sha256_file(candidate_path),
                "candidate_count": len(candidates),
                "region_count": len(scene.regions),
            }
        )
    return tuple(cases), {
        "corpus_id": binding.corpus_id,
        "revision": binding.revision,
        "case_count": len(cases),
        "cases": evidence,
    }


def run_formal_gate(
    *,
    repo_root: Path,
    manifest_path: Path,
    capture_path: Path,
    comparison_path: Path,
) -> dict[str, Any]:
    binding = load_approved78_binding(manifest_path)
    cases, artifact_evidence = _load_cases(repo_root, manifest_path)

    harness = Approved78CalibrationHarness(binding)
    calibration = harness.evaluate(cases)
    calibration_dict = asdict(calibration)

    semantic_role_counts: dict[str, int] = {}
    for case in cases:
        for region in case.scene.regions:
            semantic_role_counts[region.semantic_role] = (
                semantic_role_counts.get(region.semantic_role, 0) + 1
            )
    semantic_role_limited = set(semantic_role_counts) == {"foreground"}
    calibration_diagnostic = {
        "metrics": calibration_dict,
        "target_profile": None,
        "gating": False,
        "reason": (
            "Phase 10 calibration contract prohibits hidden or guessed "
            "CalibrationTargets. Saved Approved-78 Scene artifacts expose "
            "only the foreground semantic role, so angularity/semantic-cost "
            "targets are reported diagnostically and are not reinterpreted "
            "as a formal migration Gate."
        ),
        "semantic_role_counts": semantic_role_counts,
        "foreground_only_saved_scene_artifacts": semantic_role_limited,
    }

    capture = _load_json(capture_path)
    comparison = _load_json(comparison_path)
    migration = MigrationGate().evaluate(capture, comparison)
    migration_dict = migration.to_dict()

    replay_complete = bool(
        len(cases) == 78
        and calibration.case_count == 78
        and int(artifact_evidence["case_count"]) == 78
    )
    pass_value = bool(replay_complete and migration.switch_authorized)
    return {
        "schema_version": "1.0",
        "phase": 14,
        "gate": "Approved-78-formal",
        "pass": pass_value,
        "binding": {
            "corpus_id": binding.corpus_id,
            "revision": binding.revision,
            "reference_count": len(binding.references),
        },
        "artifact_evidence": artifact_evidence,
        "replay_complete": replay_complete,
        "calibration_diagnostic": calibration_diagnostic,
        "migration_gate": migration_dict,
        "migration_gate_pass": bool(migration.switch_authorized),
        "capture_path": str(capture_path.relative_to(repo_root)),
        "comparison_path": str(comparison_path.relative_to(repo_root)),
        "manifest_path": str(manifest_path.relative_to(repo_root)),
        "formal_gate_contract": (
            "Approved-78 formal Gate is MigrationGate over the complete "
            "78-case SHA-bound deterministic replay evidence. The calibration "
            "harness remains an independent diagnostic unless an explicit "
            "canonical CalibrationTargets profile is supplied."
        ),
        "failure_policy": (
            "The Gate fails if any of the 78 saved cases is absent or if "
            "MigrationGate reports source/reference SHA, determinism, "
            "silhouette non-regression, or foreground-ratio non-regression "
            "failure."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Phase 14 Approved-78 formal calibration Gate."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/zerobase/approved78_manifest.json"),
    )
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("docs/zerobase/MIGRATION_APPROVED78_CAPTURE.json"),
    )
    parser.add_argument(
        "--comparison",
        type=Path,
        default=Path(
            "docs/zerobase/MIGRATION_APPROVED78_COMPARISON.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/phase14_approved78/14_approved78_formal_gate.json"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()

    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else repo_root / path

    result = run_formal_gate(
        repo_root=repo_root,
        manifest_path=resolve(args.manifest),
        capture_path=resolve(args.capture),
        comparison_path=resolve(args.comparison),
    )
    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = {
        "pass": result["pass"],
        "reference_count": result["binding"]["reference_count"],
        "replay_complete": result["replay_complete"],
        "calibration_metrics": result["calibration_diagnostic"]["metrics"],
        "calibration_gating": result["calibration_diagnostic"]["gating"],
        "semantic_role_counts": result["calibration_diagnostic"][
            "semantic_role_counts"
        ],
        "migration_gate_pass": result["migration_gate_pass"],
        "migration_reasons": result["migration_gate"]["reasons"],
        "output": str(output),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
