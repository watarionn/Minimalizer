from __future__ import annotations
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

OBSERVATION_SCHEMA = "1"

@dataclass(frozen=True)
class DiffMinObservation:
    run_id: str
    candidate_id: str
    effective_mode: str
    apply_candidate: bool
    rollback_reason: str
    silhouette_iou: float
    dino_delta: float | None
    kill_switch: bool = False
    schema_version: str = OBSERVATION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != OBSERVATION_SCHEMA:
            raise ValueError("unsupported DiffMin observation schema")
        if not self.run_id or not self.candidate_id:
            raise ValueError("run_id and candidate_id are required")
        if not 0 <= self.silhouette_iou <= 1:
            raise ValueError("silhouette_iou must be within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def observations_from_release_audit(payload: dict[str, Any], *, run_id: str) -> tuple[DiffMinObservation, ...]:
    mode = payload["effective_mode"]
    killed = bool(payload["kill_switch"])
    out = []
    for item in payload["audit"]["decisions"]:
        artifact = item["artifact"]
        decision = item["decision"]
        baseline = artifact.get("baseline_dino_score")
        candidate = artifact.get("candidate_dino_score")
        delta = None if baseline is None or candidate is None else candidate - baseline
        out.append(DiffMinObservation(
            run_id=run_id,
            candidate_id=artifact["candidate_id"],
            effective_mode=mode,
            apply_candidate=bool(decision["apply_candidate"]),
            rollback_reason=decision["reason"],
            silhouette_iou=float(artifact["silhouette_iou"]),
            dino_delta=delta,
            kill_switch=killed,
        ))
    return tuple(out)

def summarize_observations(items: tuple[DiffMinObservation, ...]) -> dict[str, Any]:
    reasons = Counter(x.rollback_reason for x in items if not x.apply_candidate)
    adopted = sum(x.apply_candidate for x in items)
    deltas = [x.dino_delta for x in items if x.dino_delta is not None]
    return {
        "schema_version": OBSERVATION_SCHEMA,
        "runs": len({x.run_id for x in items}),
        "candidates": len(items),
        "adopted": adopted,
        "rolled_back": len(items) - adopted,
        "adoption_rate": adopted / len(items) if items else 0.0,
        "kill_switch_records": sum(x.kill_switch for x in items),
        "rollback_reasons": dict(sorted(reasons.items())),
        "min_silhouette_iou": min((x.silhouette_iou for x in items), default=None),
        "mean_dino_delta": sum(deltas) / len(deltas) if deltas else None,
    }

def write_observation_log(path: str | Path, items: tuple[DiffMinObservation, ...]) -> None:
    Path(path).write_text("".join(json.dumps(x.to_dict(), sort_keys=True, separators=(",", ":")) + "\n" for x in items), encoding="utf-8")
