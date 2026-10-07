from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from minimalizer_zerobase.evaluation.adopted_baseline_registry import (
    BaselineAdoptionRecord,
)

SA10_REGRESSION_TRANSACTION_VERSION = "sa10.14-v1"

HARD_GATE_NAMES = (
    "feature_survival",
    "forbidden_face_detail",
    "anatomy",
    "topology",
    "source_authority",
    "phase14_machine",
    "phase14_human_visual",
    "determinism",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha(name: str, value: Any) -> str:
    text = str(value or "")
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")
    return text


def _case_id(name: str, payload: Mapping[str, Any]) -> str:
    value = str(payload.get("case_id") or "")
    if not value:
        raise ValueError(f"{name}: case_id is required")
    return value


def _available_pass(name: str, row: Mapping[str, Any]) -> dict[str, Any]:
    if row.get("status") != "AVAILABLE":
        raise ValueError(f"{name}: hard evidence must be AVAILABLE")
    passed = row.get("passed")
    if not isinstance(passed, bool):
        raise ValueError(f"{name}: passed must be bool")
    return {"name": name, "status": "AVAILABLE", "passed": passed}


@dataclass(frozen=True)
class RegressionTransactionReport:
    artifact_version: str
    transaction_id: str
    case_id: str
    source_sha256: str
    candidate_sha256: str
    hard_evidence: tuple[dict[str, Any], ...]
    adopted_baseline: Mapping[str, Any]
    phase14_evidence: Mapping[str, Any]
    evidence_versions: Mapping[str, Any]
    diagnostics: Mapping[str, Any]
    evidence_links: Mapping[str, bool]
    pass_transaction: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_version": self.artifact_version,
            "transaction_id": self.transaction_id,
            "case_id": self.case_id,
            "source_sha256": self.source_sha256,
            "candidate_sha256": self.candidate_sha256,
            "hard_evidence": [dict(row) for row in self.hard_evidence],
            "adopted_baseline": dict(self.adopted_baseline),
            "phase14_evidence": dict(self.phase14_evidence),
            "evidence_versions": dict(self.evidence_versions),
            "diagnostics": dict(self.diagnostics),
            "evidence_links": dict(self.evidence_links),
            "pass_transaction": self.pass_transaction,
            "boundary": {
                "aggregate_quality_score": False,
                "diagnostics_can_override_hard_fail": False,
                "candidate_self_reference_forbidden": True,
                "adopted_baseline_production_inference_allowed": False,
                "golden_used_for_inference": False,
                "browser_v12_used_for_inference": False,
                "new_quality_thresholds": False,
            },
        }


def build_regression_transaction(
    *,
    transaction_id: str,
    case: Mapping[str, Any],
    adoption_record: Mapping[str, Any],
    actual_source_sha256: str,
    actual_candidate_sha256: str,
    visual_hard_gate: Mapping[str, Any],
    hard_evidence: Mapping[str, Any],
    phase14: Mapping[str, Any],
    semantic_retention: Mapping[str, Any],
    face_raster_guard: Mapping[str, Any],
) -> RegressionTransactionReport:
    tx = str(transaction_id).strip()
    if not tx:
        raise ValueError("transaction_id is required")

    record = BaselineAdoptionRecord.from_mapping(adoption_record)
    case_id = _case_id("case", case)
    for name, payload in (
        ("visual_hard_gate", visual_hard_gate),
        ("hard_evidence", hard_evidence),
        ("phase14", phase14),
        ("semantic_retention", semantic_retention),
        ("face_raster_guard", face_raster_guard),
    ):
        if _case_id(name, payload) != case_id:
            raise ValueError(f"{name}: case_id mismatch")
    if record.case_id != case_id:
        raise ValueError("adoption_record: case_id mismatch")

    source_sha = _sha("actual_source_sha256", actual_source_sha256)
    candidate_sha = _sha("actual_candidate_sha256", actual_candidate_sha256)

    case_source_sha = _sha("case.source.sha256", case.get("source", {}).get("sha256"))
    case_candidate_sha = _sha(
        "case.provenance.production_candidate_sha256",
        case.get("provenance", {}).get("production_candidate_sha256"),
    )

    binding = visual_hard_gate.get("binding", {})
    visual_source_sha = _sha("visual binding source", binding.get("source_sha256"))
    visual_candidate_sha = _sha(
        "visual binding candidate", binding.get("candidate_artifact_sha256")
    )
    visual_baseline_sha = _sha(
        "visual binding baseline", binding.get("baseline_artifact_sha256")
    )

    hard_source_sha = _sha(
        "hard evidence source", hard_evidence.get("source", {}).get("sha256")
    )
    hard_candidate_sha = _sha(
        "hard evidence candidate",
        hard_evidence.get("production_candidate", {}).get("sha256"),
    )
    semantic_source_sha = _sha(
        "semantic source", semantic_retention.get("source", {}).get("sha256")
    )
    semantic_candidate_sha = _sha(
        "semantic candidate", semantic_retention.get("candidate", {}).get("sha256")
    )
    guard_candidate_sha = _sha(
        "face guard candidate", face_raster_guard.get("production_candidate_sha256")
    )
    phase14_source_sha = _sha(
        "phase14 source", phase14.get("source", {}).get("sha256")
    )

    links = {
        "source_matches_adoption": source_sha == record.source_sha256,
        "source_matches_case": source_sha == case_source_sha,
        "source_matches_visual_gate": source_sha == visual_source_sha,
        "source_matches_hard_evidence": source_sha == hard_source_sha,
        "source_matches_phase14": source_sha == phase14_source_sha,
        "source_matches_dino": source_sha == semantic_source_sha,
        "candidate_matches_case": candidate_sha == case_candidate_sha,
        "candidate_matches_visual_gate": candidate_sha == visual_candidate_sha,
        "candidate_matches_hard_evidence": candidate_sha == hard_candidate_sha,
        "candidate_matches_dino": candidate_sha == semantic_candidate_sha,
        "candidate_matches_face_guard": candidate_sha == guard_candidate_sha,
        "baseline_matches_adoption": visual_baseline_sha == record.baseline_artifact_sha256,
        "baseline_binding_passed": binding.get("binding_passed") is True,
        "visual_gate_transaction_matches": binding.get("evaluation_transaction_id") == tx,
        "baseline_separate_transaction": binding.get("same_transaction") is False,
        "baseline_not_production_input": binding.get("production_inference_allowed") is False,
        "candidate_self_reference_forbidden": binding.get("candidate_self_reference_forbidden") is True,
        "face_guard_source_only": face_raster_guard.get("source_only") is True,
        "face_guard_outside_unchanged": (
            face_raster_guard.get("face_raster_guard", {}).get(
                "changed_outside_face_pixels"
            )
            == 0
        ),
        "face_guard_no_generation": (
            face_raster_guard.get("generated_or_inpainted_pixel_count") == 0
        ),
    }

    semantic = semantic_retention.get("semantic_retention", {})
    if semantic.get("authoritative") is not False:
        raise ValueError("DINO semantic evidence must remain non-authoritative")
    if semantic.get("can_override_hard_fail") is not False:
        raise ValueError("DINO semantic evidence cannot override hard failures")
    if semantic_retention.get("hard_gate_override_allowed") is not False:
        raise ValueError("DINO hard-gate override must remain disabled")
    if semantic_retention.get("production_output_changed") is not False:
        raise ValueError("DINO evidence cannot change production output")

    visual_feature = _available_pass(
        "feature_survival", visual_hard_gate.get("feature_survival", {})
    )
    visual_face = _available_pass(
        "forbidden_face_detail",
        visual_hard_gate.get("forbidden_face_detail", {}),
    )
    hard_rows = hard_evidence.get("hard_evidence", {})
    anatomy = _available_pass("anatomy", hard_rows.get("anatomy", {}))
    topology = _available_pass("topology", hard_rows.get("topology", {}))
    source_authority = _available_pass(
        "source_authority", hard_rows.get("source_authority", {})
    )

    phase14_machine = {
        "name": "phase14_machine",
        "status": "AVAILABLE",
        "passed": bool(phase14.get("machine_pass")),
    }
    phase14_human = {
        "name": "phase14_human_visual",
        "status": "AVAILABLE",
        "passed": bool(phase14.get("human_visual_qa", {}).get("passed")),
    }
    determinism = {
        "name": "determinism",
        "status": "AVAILABLE",
        "passed": bool(phase14.get("determinism", {}).get("passed")),
    }

    hard = (
        visual_feature,
        visual_face,
        anatomy,
        topology,
        source_authority,
        phase14_machine,
        phase14_human,
        determinism,
    )

    # Cross-check the case fixture but never let it become authority.
    fixture_hard = case.get("hard_evidence", {})
    for row in hard:
        fixture = fixture_hard.get(row["name"], {})
        if fixture.get("status") != "AVAILABLE" or fixture.get("passed") is not row["passed"]:
            raise ValueError(f"case fixture hard-evidence mismatch: {row['name']}")

    adopted_baseline = {
        "baseline_artifact_id": record.baseline_artifact_id,
        "baseline_artifact_sha256": record.baseline_artifact_sha256,
        "adoption_transaction_id": record.adoption_transaction_id,
        "evaluation_transaction_id": binding.get("evaluation_transaction_id"),
        "binding_passed": binding.get("binding_passed") is True,
        "same_transaction": binding.get("same_transaction") is True,
        "production_inference_allowed": False,
    }
    phase14_evidence = {
        "machine_pass": phase14_machine["passed"],
        "human_visual_pass": phase14_human["passed"],
        "determinism_pass": determinism["passed"],
        "determinism_sha256": _sha(
            "phase14 determinism sha256",
            phase14.get("determinism", {}).get("first_evaluation_sha256"),
        ),
        "phase14_pass": phase14.get("pass") is True,
    }
    evidence_versions = {
        "visual_hard_gate": visual_hard_gate.get("artifact_version"),
        "hard_evidence": hard_evidence.get("artifact_version"),
        "semantic_retention": semantic_retention.get("artifact_version"),
        "face_raster_guard": face_raster_guard.get("artifact_version"),
        "phase14_schema": phase14.get("schema_version"),
    }

    diagnostics = {
        "semantic_retention": {
            "status": semantic.get("status"),
            "value": semantic.get("semantic_retention_score"),
            "authoritative": False,
            "can_override_hard_fail": False,
        },
        "case_diagnostics": dict(case.get("diagnostics", {})),
        "actual_emission_support": dict(hard_evidence.get("actual_emission_support", {})),
    }

    pass_transaction = bool(
        all(links.values())
        and all(row["passed"] for row in hard)
        and phase14.get("pass") is True
    )

    return RegressionTransactionReport(
        artifact_version=SA10_REGRESSION_TRANSACTION_VERSION,
        transaction_id=tx,
        case_id=case_id,
        source_sha256=source_sha,
        candidate_sha256=candidate_sha,
        hard_evidence=hard,
        adopted_baseline=adopted_baseline,
        phase14_evidence=phase14_evidence,
        evidence_versions=evidence_versions,
        diagnostics=diagnostics,
        evidence_links=links,
        pass_transaction=pass_transaction,
    )
