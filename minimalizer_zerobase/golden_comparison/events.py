"""Event producer boundary for Golden Comparison.

This module has no network or Event Hub dependency. It only translates an
already-computed Golden Gap result into Rinka Event Envelope v1.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping

def _stable_id(prefix: str, *parts: str) -> str:
    material="\x1f".join(parts).encode("utf-8")
    return prefix+sha256(material).hexdigest()[:32]

def build_golden_evaluated_event(
    report: Mapping[str, Any],
    *,
    previous_report: Mapping[str, Any] | None = None,
    run_id: str,
    occurred_at: str | None = None,
    event_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    hop_count: int = 0,
) -> dict[str, Any]:
    case_id=report.get("case_id")
    if not isinstance(case_id,str) or not case_id:
        raise ValueError("Golden Gap report requires case_id")
    if not isinstance(run_id,str) or not run_id:
        raise ValueError("Golden Gap event requires run_id")
    gate=report.get("gate")
    if gate not in {"PASS","FAIL"}:
        raise ValueError("Golden Gap report requires PASS/FAIL gate")
    score=report.get("diagnostic_mean")
    if not isinstance(score,(int,float)) or isinstance(score,bool):
        raise ValueError("Golden Gap report requires numeric diagnostic_mean")
    previous_score=None
    if previous_report is not None:
        if previous_report.get("case_id")!=case_id:
            raise ValueError("previous report case_id mismatch")
        raw=previous_report.get("diagnostic_mean")
        if not isinstance(raw,(int,float)) or isinstance(raw,bool):
            raise ValueError("previous report requires numeric diagnostic_mean")
        previous_score=float(raw)
    score=float(score)
    delta=None if previous_score is None else score-previous_score
    if delta is None: verdict="evaluated"
    elif delta>0: verdict="improved"
    elif delta<0: verdict="regressed"
    else: verdict="unchanged"
    eid=event_id or _stable_id("evt_","minimalizer.golden.evaluated",run_id,case_id)
    corr=correlation_id or _stable_id("corr_","minimalizer.golden",run_id)
    return {
      "spec_version":"rinka.event/1.0",
      "event_id":eid,
      "event_name":"minimalizer.golden.evaluated",
      "event_version":1,
      "project_id":"minimalizer",
      "origin":"golden-comparison",
      "occurred_at":occurred_at or datetime.now(timezone.utc).isoformat(),
      "correlation_id":corr,
      "causation_id":causation_id,
      "hop_count":hop_count,
      "subject":{"type":"golden_case","id":case_id},
      "payload":{
        "run_id":run_id,
        "golden_id":case_id,
        "score":score,
        "previous_score":previous_score,
        "delta":delta,
        "verdict":verdict,
        "gate":gate,
        "hard_failures":list(report.get("hard_failures",[])),
      },
      "artifacts":[],
      "meta":{"producer":"minimalizer.golden_comparison","environment":"production"},
    }
