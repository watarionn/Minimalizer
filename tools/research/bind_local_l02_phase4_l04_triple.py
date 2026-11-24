"""Bind the existing independent Phase4 result, its Phase5 replay and L04 triple.

The command reads source-bound metadata and artifact bytes only to calculate
SHA-256. It does not inspect review images or alter candidate pixels. A PASS
produces a candidate handoff receipt; Golden and production remain closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from .audit_local_l04_candidate_triple import audit_candidate_triple
    from .verify_local_l02_phase4_receipt import verify_phase4_receipt
except ImportError:  # pragma: no cover - direct CLI execution
    from audit_local_l04_candidate_triple import audit_candidate_triple  # type: ignore
    from verify_local_l02_phase4_receipt import verify_phase4_receipt  # type: ignore


CASES = ("H04", "H06", "H08")
FROZEN_H08_OWNER_SHA256 = "43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52"
AUTHORITY_TRUE_FIELDS = (
    "owner_promotion_authorized",
    "authority_receipt_verified",
    "bound_to_case",
    "bound_to_source_sha",
    "bound_to_prediction_sha",
    "bound_to_observer_sha",
    "owner_promotion_explicitly_approved",
    "unknown_not_promoted",
    "human_labels_not_used_for_inference",
    "production_not_authorized",
)


class CandidateBindingHold(ValueError):
    """Raised when the existing Phase4, Phase5 and L04 artifacts diverge."""


def _json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise CandidateBindingHold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise CandidateBindingHold(reason)


def _verify_h08_authority(path: Path, source_sha: str, candidate_sha: str) -> str:
    authority = _json(path)
    _require(authority.get("schema") == "minimalizer/local-l02/h08-owner-authority/v1", "H08_AUTHORITY_SCHEMA")
    _require(authority.get("case") == "H08", "H08_AUTHORITY_CASE")
    _require(authority.get("frozen_owner_sha256") == FROZEN_H08_OWNER_SHA256, "H08_FROZEN_OWNER_SHA_MISMATCH")
    _require(authority.get("source_sha256") == source_sha, "H08_AUTHORITY_SOURCE_SHA_MISMATCH")
    _require(authority.get("prediction_sha256") == candidate_sha, "H08_AUTHORITY_CANDIDATE_SHA_MISMATCH")
    _require(all(authority.get(field) is True for field in AUTHORITY_TRUE_FIELDS), "H08_AUTHORITY_BOOLEAN_GATE")
    _require(authority.get("golden") == "HOLD" and authority.get("production") == "NO_GO", "H08_AUTHORITY_RELEASE_GATE")
    return _sha(path)


def bind_candidate_triple(
    *,
    phase4_receipt: Path,
    freeze_receipt: Path,
    triple_root: Path,
    phase5_root: Path,
    h08_authority_receipt: Path,
) -> dict[str, Any]:
    review_raw = _json(phase4_receipt)
    freeze_raw = _json(freeze_receipt)
    phase4 = verify_phase4_receipt(review_raw, freeze_raw)
    triple_root = triple_root.resolve()
    phase5_root = phase5_root.resolve()
    triple_audit = audit_candidate_triple(triple_root)
    _require(triple_audit.get("numerical_handoff_eligible") is True, "L04_TRIPLE_AUDIT_HOLD")

    triple_receipt_path = triple_root / "L04_CANDIDATE_TRIPLE_RECEIPT.json"
    triple_receipt = _json(triple_receipt_path)
    receipt_cases = triple_receipt.get("cases")
    _require(isinstance(receipt_cases, list), "L04_TRIPLE_CASES_MISSING")
    indexed_receipt = {
        item.get("case"): item
        for item in receipt_cases
        if isinstance(item, Mapping) and isinstance(item.get("case"), str)
    }
    _require(set(indexed_receipt) == set(CASES), "L04_TRIPLE_CASE_SET_MISMATCH")

    cases: dict[str, dict[str, str]] = {}
    for case in CASES:
        try:
            verified = phase4["cases"][case]
            item = indexed_receipt[case]
        except (KeyError, TypeError) as exc:
            raise CandidateBindingHold(f"CASE_BINDING_MISSING:{case}") from exc
        manifest = _json(triple_root / case / "TRIPLE_MANIFEST.json")
        stage8 = _json(triple_root / case / "stage8_source_ring.json")
        p4_stage_path = phase5_root / case / "phase_04" / "stage.json"
        p5_stage_path = phase5_root / case / "phase_05" / "stage.json"
        graph_path = phase5_root / case / "phase_05" / "05_structure_graph.json"
        _require(p4_stage_path.is_file() and p5_stage_path.is_file() and graph_path.is_file(), f"PHASE5_REPLAY_FILES_MISSING:{case}")
        p4_stage = _json(p4_stage_path)
        p5_stage = _json(p5_stage_path)
        p4_stage_sha = _sha(p4_stage_path)
        p5_stage_sha = _sha(p5_stage_path)
        graph_sha = _sha(graph_path)
        source_sha = str(verified.get("source_sha256", ""))
        candidate_sha = str(verified.get("candidate_sha256", ""))

        checks = (
            (manifest.get("source", {}).get("sha256") == source_sha, "SOURCE_SHA_DIFFERS_FROM_PHASE4"),
            (item.get("source_sha256") == source_sha, "TRIPLE_RECEIPT_SOURCE_SHA_MISMATCH"),
            (stage8.get("signed_source_sha256") == source_sha, "STAGE8_SOURCE_SHA_MISMATCH"),
            (p4_stage.get("source", {}).get("sha256") == source_sha, "PHASE4_STAGE_SOURCE_SHA_MISMATCH"),
            (manifest.get("candidate_sha256") == candidate_sha, "TRIPLE_CANDIDATE_DIFFERS_FROM_PHASE4"),
            (stage8.get("candidate_sha256") == candidate_sha, "STAGE8_CANDIDATE_DIFFERS_FROM_PHASE4"),
            (p4_stage.get("l02_candidate", {}).get("candidate_sha256") == candidate_sha, "PHASE4_STAGE_CANDIDATE_MISMATCH"),
            (item.get("candidate_sha256") == candidate_sha, "TRIPLE_RECEIPT_CANDIDATE_MISMATCH"),
            (stage8.get("phase4_stage_json_sha256") == p4_stage_sha, "STAGE8_PHASE4_STAGE_SHA_MISMATCH"),
            (p5_stage.get("source", {}).get("sha256") == source_sha, "PHASE5_SOURCE_SHA_MISMATCH"),
            (p5_stage.get("inputs", {}).get("phase4", {}).get("stage.json") == p4_stage_sha, "PHASE5_PHASE4_INPUT_SHA_MISMATCH"),
            (stage8.get("phase5_stage_json_sha256") == p5_stage_sha, "STAGE8_PHASE5_STAGE_SHA_MISMATCH"),
            (manifest.get("phase5_stage_json_sha256") == p5_stage_sha, "TRIPLE_PHASE5_STAGE_SHA_MISMATCH"),
            (p5_stage.get("outputs", {}).get("05_structure_graph.json") == graph_sha, "PHASE5_GRAPH_SHA_MISMATCH"),
            (p5_stage.get("metrics", {}).get("pass") is True, "PHASE5_REPLAY_NOT_PASS"),
        )
        for ok, reason in checks:
            _require(ok, f"{case}:{reason}")
        triple_audit_case = triple_audit.get("cases", {}).get(case, {})
        cases[case] = {
            "source_sha256": source_sha,
            "candidate_sha256": candidate_sha,
            "stage8_json_sha256": str(triple_audit_case.get("stage8_json_sha256", "")),
            "expanded_svg_sha256": str(triple_audit_case.get("expanded_svg_sha256", "")),
            "phase4_stage_json_sha256": p4_stage_sha,
            "phase5_stage_json_sha256": p5_stage_sha,
            "phase5_structure_graph_sha256": graph_sha,
        }

    h08_authority_sha = _verify_h08_authority(
        h08_authority_receipt,
        cases["H08"]["source_sha256"],
        cases["H08"]["candidate_sha256"],
    )
    return {
        "schema": "minimalizer/local-l02/l04-candidate-binding/v1",
        "phase4": "PASS",
        "phase5_replay": "PASS",
        "l04_candidate_triple": "PASS",
        "candidate_status": "READY_FOR_OWNER_REVIEW",
        "golden": "HOLD",
        "production": "NO_GO",
        "release_authorized": False,
        "phase4_review_receipt_sha256": _sha(phase4_receipt),
        "phase4_freeze_receipt_sha256": _sha(freeze_receipt),
        "h08_owner_authority_receipt_sha256": h08_authority_sha,
        "l04_candidate_triple_receipt_sha256": _sha(triple_receipt_path),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="既存Phase4/5とL04三点セットの候補SHAを結合する")
    parser.add_argument("--phase4-receipt", type=Path, required=True)
    parser.add_argument("--freeze-receipt", type=Path, required=True)
    parser.add_argument("--triple-root", type=Path, required=True)
    parser.add_argument("--phase5-root", type=Path, required=True)
    parser.add_argument("--h08-authority-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = bind_candidate_triple(
            phase4_receipt=args.phase4_receipt,
            freeze_receipt=args.freeze_receipt,
            triple_root=args.triple_root,
            phase5_root=args.phase5_root,
            h08_authority_receipt=args.h08_authority_receipt,
        )
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "phase4": result["phase4"], "phase5_replay": result["phase5_replay"], "candidate_status": result["candidate_status"], "production": result["production"]}, ensure_ascii=False))
        return 0
    except (OSError, KeyError, TypeError, json.JSONDecodeError, ValueError, CandidateBindingHold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
