from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable, Mapping

from PIL import Image, ImageDraw, ImageFont

from minimalizer_zerobase.analyzers.contracts import Evidence
from minimalizer_zerobase.importance.precedent_diagnostic import (
    PB3ImportanceDiagnosticReport,
)


PB4_DEBUG_BOARD_VERSION = "pb4-v1"


@dataclass(frozen=True)
class PB4ComponentRow:
    component_id: str
    role: str
    support_ratio: float
    evidence_authority_state: str
    semantic_removal_observer: str
    semantic_removal_impact: float | None
    semantic_merge_observer: str
    semantic_merge_impact: float | None
    merge_target_id: str | None
    primitive_advisor_status: str
    primitive_advisor_agreement: bool | None
    recommendation: str
    reasons: tuple[str, ...]
    production_action: str | None
    hard_fail_override_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "role": self.role,
            "support_ratio": round(float(self.support_ratio), 12),
            "evidence_authority_state": self.evidence_authority_state,
            "semantic_removal_observer": self.semantic_removal_observer,
            "semantic_removal_impact": self.semantic_removal_impact,
            "semantic_merge_observer": self.semantic_merge_observer,
            "semantic_merge_impact": self.semantic_merge_impact,
            "merge_target_id": self.merge_target_id,
            "primitive_advisor_status": self.primitive_advisor_status,
            "primitive_advisor_agreement": self.primitive_advisor_agreement,
            "recommendation": self.recommendation,
            "reasons": list(self.reasons),
            "production_action": self.production_action,
            "hard_fail_override_allowed": False,
        }


@dataclass(frozen=True)
class PB4SemanticDebugBoard:
    component_rows: tuple[PB4ComponentRow, ...]
    role_component_counts: Mapping[str, int]
    relation_counts: Mapping[str, int]
    recommendation_counts: Mapping[str, int]
    observer_availability: Mapping[str, int]
    authority_counts: Mapping[str, int]
    advisor_context_count: int
    semantic_context_score: float | None
    semantic_context_status: str
    hard_failures: tuple[str, ...]
    production_policy_changed: bool
    production_output_changed: bool
    adopted_visual_baseline: str | None = None
    version: str = PB4_DEBUG_BOARD_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "component_rows": [row.to_dict() for row in self.component_rows],
            "role_component_counts": dict(sorted(self.role_component_counts.items())),
            "relation_counts": dict(sorted(self.relation_counts.items())),
            "recommendation_counts": dict(sorted(self.recommendation_counts.items())),
            "observer_availability": dict(sorted(self.observer_availability.items())),
            "authority_counts": dict(sorted(self.authority_counts.items())),
            "advisor_context_count": self.advisor_context_count,
            "semantic_context_score": self.semantic_context_score,
            "semantic_context_status": self.semantic_context_status,
            "hard_failures": list(self.hard_failures),
            "hard_failure_count": len(self.hard_failures),
            "hard_failures_visible": True,
            "hard_fail_override_allowed": False,
            "production_policy_changed": self.production_policy_changed,
            "production_output_changed": self.production_output_changed,
            "adopted_visual_baseline": self.adopted_visual_baseline,
        }


def _pb3_payload(
    value: PB3ImportanceDiagnosticReport | Mapping[str, Any],
) -> dict[str, Any]:
    payload = value.to_dict() if isinstance(value, PB3ImportanceDiagnosticReport) else dict(value)
    if payload.get("authoritative") is not False:
        raise ValueError("PB4 requires non-authoritative PB3 diagnostic")
    if payload.get("can_override_hard_fail") is not False:
        raise ValueError("PB4 cannot display PB3 evidence that can override hard fail")
    if payload.get("production_policy_changed") is not False:
        raise ValueError("PB4 requires PB3 production_policy_changed=false")
    if payload.get("production_output_changed") is not False:
        raise ValueError("PB4 requires PB3 production_output_changed=false")
    return payload


def _component_evidence(
    pb2_evidence: Iterable[Evidence],
) -> tuple[tuple[Evidence, ...], tuple[Evidence, ...]]:
    components: list[Evidence] = []
    relations: list[Evidence] = []
    for item in pb2_evidence:
        if item.evidence_type == "region_component":
            components.append(item)
        elif item.evidence_type == "layer_relation":
            relations.append(item)

    components.sort(key=lambda item: item.evidence_id)
    relations.sort(key=lambda item: item.evidence_id)
    if not components:
        raise ValueError("PB4 requires PB2 region_component evidence")

    ids = [item.evidence_id for item in components]
    if len(ids) != len(set(ids)):
        raise ValueError("PB4 component evidence ids must be unique")

    return tuple(components), tuple(relations)


def _authority_state(item: Evidence) -> str:
    authority = item.normalization.get("authority")
    if not isinstance(authority, Mapping):
        raise ValueError(f"{item.evidence_id}: missing authority provenance")
    state = str(authority.get("state", ""))
    if state not in {"observed", "advisor", "promoted"}:
        raise ValueError(f"{item.evidence_id}: unsupported authority state")
    production = authority.get("production_authority")
    if state == "promoted":
        if production is not True:
            raise ValueError(
                f"{item.evidence_id}: promoted authority must declare production_authority=true"
            )
    elif production is not False:
        raise ValueError(
            f"{item.evidence_id}: non-promoted evidence cannot declare production authority"
        )
    return state


def _semantic_context(
    payload: Mapping[str, Any],
) -> tuple[float | None, str]:
    context = payload.get("context_semantic_retention")
    if context is None:
        return None, "UNAVAILABLE"
    if not isinstance(context, Mapping):
        raise ValueError("PB4 semantic context must be an object")
    if context.get("authoritative") is not False:
        raise ValueError("PB4 semantic context must remain non-authoritative")
    if context.get("can_override_hard_fail") is not False:
        raise ValueError("PB4 semantic context cannot override hard fail")
    score = context.get("semantic_retention_score")
    if score is not None:
        score = float(score)
        if not 0.0 <= score <= 1.0:
            raise ValueError("PB4 semantic context score must be within [0, 1]")
    return score, str(context.get("status", "UNKNOWN"))


def build_pb4_semantic_debug_board(
    *,
    pb2_evidence: Iterable[Evidence],
    pb3_report: PB3ImportanceDiagnosticReport | Mapping[str, Any],
    adopted_visual_baseline: str | None = None,
) -> PB4SemanticDebugBoard:
    components, relations = _component_evidence(pb2_evidence)
    pb3 = _pb3_payload(pb3_report)

    pb3_rows = pb3.get("components")
    if not isinstance(pb3_rows, list):
        raise ValueError("PB4 requires PB3 component rows")

    pb3_by_id: dict[str, Mapping[str, Any]] = {}
    for row in pb3_rows:
        if not isinstance(row, Mapping):
            raise ValueError("PB4 PB3 component row must be an object")
        component_id = str(row.get("component_id", ""))
        if not component_id:
            raise ValueError("PB4 PB3 component row requires component_id")
        if component_id in pb3_by_id:
            raise ValueError(f"PB4 duplicate PB3 component: {component_id}")
        pb3_by_id[component_id] = row

    component_ids = {item.evidence_id for item in components}
    pb3_ids = set(pb3_by_id)
    if component_ids != pb3_ids:
        missing = sorted(component_ids - pb3_ids)
        extra = sorted(pb3_ids - component_ids)
        raise ValueError(
            "PB4 PB2/PB3 component mismatch: "
            f"missing={missing} extra={extra}"
        )

    role_counts: dict[str, int] = {}
    recommendation_counts: dict[str, int] = {}
    observer_counts = {
        "removal_available": 0,
        "removal_unavailable": 0,
        "merge_available": 0,
        "merge_unavailable": 0,
    }
    authority_counts = {
        "observed": 0,
        "advisor": 0,
        "promoted": 0,
    }

    for item in components + relations:
        authority_counts[_authority_state(item)] += 1

    rows: list[PB4ComponentRow] = []
    advisor_context_count = 0
    for item in components:
        diagnostic = pb3_by_id[item.evidence_id]
        role = str(item.semantic_label or diagnostic.get("role") or "unknown")
        diag_role = str(diagnostic.get("role", role))
        if diag_role != role:
            raise ValueError(
                f"{item.evidence_id}: PB2/PB3 role mismatch ({role} != {diag_role})"
            )
        support = float(item.geometry.get("support_ratio", -1.0))
        if not 0.0 <= support <= 1.0:
            raise ValueError(f"{item.evidence_id}: invalid support_ratio")

        removal_impact = diagnostic.get("removal_impact")
        merge_impact = diagnostic.get("merge_impact")
        removal_state = "AVAILABLE" if removal_impact is not None else "UNAVAILABLE"
        merge_state = "AVAILABLE" if merge_impact is not None else "UNAVAILABLE"
        observer_counts[
            "removal_available" if removal_impact is not None else "removal_unavailable"
        ] += 1
        observer_counts[
            "merge_available" if merge_impact is not None else "merge_unavailable"
        ] += 1

        advisor_status = str(diagnostic.get("primitive_advisor_status", "UNAVAILABLE"))
        advisor_agreement = diagnostic.get("primitive_advisor_agreement")
        if advisor_status != "UNAVAILABLE" or advisor_agreement is not None:
            advisor_context_count += 1

        recommendation = str(diagnostic.get("recommendation", ""))
        if not recommendation:
            raise ValueError(f"{item.evidence_id}: PB3 recommendation missing")
        recommendation_counts[recommendation] = recommendation_counts.get(
            recommendation, 0
        ) + 1
        role_counts[role] = role_counts.get(role, 0) + 1

        reasons_raw = diagnostic.get("reasons")
        if not isinstance(reasons_raw, list):
            raise ValueError(f"{item.evidence_id}: PB3 reasons must be a list")
        reasons = tuple(str(value) for value in reasons_raw)

        production_action = diagnostic.get("production_action")
        if production_action is not None:
            raise ValueError(
                f"{item.evidence_id}: PB4 cannot accept PB3 production action"
            )

        rows.append(
            PB4ComponentRow(
                component_id=item.evidence_id,
                role=role,
                support_ratio=support,
                evidence_authority_state=_authority_state(item),
                semantic_removal_observer=removal_state,
                semantic_removal_impact=(
                    None if removal_impact is None else float(removal_impact)
                ),
                semantic_merge_observer=merge_state,
                semantic_merge_impact=(
                    None if merge_impact is None else float(merge_impact)
                ),
                merge_target_id=diagnostic.get("merge_target_id"),
                primitive_advisor_status=advisor_status,
                primitive_advisor_agreement=advisor_agreement,
                recommendation=recommendation,
                reasons=reasons,
                production_action=None,
            )
        )

    relation_counts: dict[str, int] = {}
    for item in relations:
        relation = str(item.geometry.get("relation", "UNKNOWN"))
        relation_counts[relation] = relation_counts.get(relation, 0) + 1

    semantic_score, semantic_status = _semantic_context(pb3)
    failures_raw = pb3.get("hard_failures") or []
    if not isinstance(failures_raw, list):
        raise ValueError("PB4 hard_failures must be a list")
    failures = tuple(sorted(str(value) for value in failures_raw))

    return PB4SemanticDebugBoard(
        component_rows=tuple(rows),
        role_component_counts=role_counts,
        relation_counts=relation_counts,
        recommendation_counts=recommendation_counts,
        observer_availability=observer_counts,
        authority_counts=authority_counts,
        advisor_context_count=advisor_context_count,
        semantic_context_score=semantic_score,
        semantic_context_status=semantic_status,
        hard_failures=failures,
        production_policy_changed=False,
        production_output_changed=False,
        adopted_visual_baseline=adopted_visual_baseline,
    )


def canonical_pb4_debug_json(board: PB4SemanticDebugBoard) -> str:
    return (
        json.dumps(
            board.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )


def render_pb4_debug_text(board: PB4SemanticDebugBoard) -> str:
    payload = board.to_dict()
    authority = payload["authority_counts"]
    observers = payload["observer_availability"]
    recommendations = payload["recommendation_counts"]

    lines = [
        "PB4 / SA4 Semantic Debug Board",
        f"version: {board.version}",
        "",
        "AUTHORITY",
        f"  OBSERVED EVIDENCE: {authority.get('observed', 0)}",
        f"  ADVISOR EVIDENCE: {authority.get('advisor', 0)}",
        f"  PROMOTED PRODUCTION AUTHORITY: {authority.get('promoted', 0)}",
        f"  advisor context rows: {board.advisor_context_count}",
        "",
        "GLOBAL",
        f"  semantic context status: {board.semantic_context_status}",
        f"  semantic context score: {board.semantic_context_score}",
        f"  hard failures: {len(board.hard_failures)}",
    ]
    for failure in board.hard_failures:
        lines.append(f"    HARD FAIL: {failure}")
    lines += [
        "  hard-fail override allowed: false",
        f"  production policy changed: {str(board.production_policy_changed).lower()}",
        f"  production output changed: {str(board.production_output_changed).lower()}",
        f"  adopted visual baseline: {board.adopted_visual_baseline}",
        "",
        "OBSERVER AVAILABILITY",
        f"  removal available: {observers.get('removal_available', 0)}",
        f"  removal unavailable: {observers.get('removal_unavailable', 0)}",
        f"  merge available: {observers.get('merge_available', 0)}",
        f"  merge unavailable: {observers.get('merge_unavailable', 0)}",
        "",
        "RECOMMENDATIONS",
    ]
    for key, value in sorted(recommendations.items()):
        lines.append(f"  {key}: {value}")

    lines += ["", "COMPONENTS"]
    for row in board.component_rows:
        removal = (
            "NA"
            if row.semantic_removal_impact is None
            else f"{row.semantic_removal_impact:.6f}"
        )
        merge = (
            "NA"
            if row.semantic_merge_impact is None
            else f"{row.semantic_merge_impact:.6f}"
        )
        reasons = ",".join(row.reasons) or "-"
        lines.append(
            "  "
            + " | ".join(
                (
                    row.component_id,
                    row.role,
                    f"support={row.support_ratio:.6f}",
                    f"authority={row.evidence_authority_state}",
                    f"remove={row.semantic_removal_observer}:{removal}",
                    f"merge={row.semantic_merge_observer}:{merge}",
                    f"advisor={row.primitive_advisor_status}",
                    f"recommendation={row.recommendation}",
                    f"reasons={reasons}",
                    "production_action=null",
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_pb4_debug_image(
    board: PB4SemanticDebugBoard,
    *,
    row_height: int = 17,
    width: int = 1600,
) -> Image.Image:
    if row_height < 12 or width < 900:
        raise ValueError("invalid PB4 board layout")

    font = ImageFont.load_default()
    summary_lines = render_pb4_debug_text(board).splitlines()
    component_start = summary_lines.index("COMPONENTS")
    header_lines = summary_lines[:component_start]
    component_lines = summary_lines[component_start + 1 :]

    height = max(
        240,
        18 + (len(header_lines) + len(component_lines) + 4) * row_height,
    )
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    y = 10
    for line in header_lines:
        if line == "AUTHORITY":
            draw.rectangle((6, y - 2, width - 6, y + row_height - 2), fill=(238, 238, 238))
        elif line == "GLOBAL" or line == "OBSERVER AVAILABILITY" or line == "RECOMMENDATIONS":
            draw.line((6, y - 3, width - 6, y - 3), fill=(180, 180, 180))
        if "HARD FAIL:" in line:
            draw.rectangle((6, y - 2, width - 6, y + row_height - 2), outline=(0, 0, 0))
        draw.text((10, y), line, fill="black", font=font)
        y += row_height

    draw.line((6, y, width - 6, y), fill=(100, 100, 100))
    y += row_height
    columns = (
        "component_id",
        "role",
        "support",
        "authority",
        "remove",
        "merge",
        "advisor",
        "recommendation",
        "reasons",
        "production",
    )
    draw.text((10, y), " | ".join(columns), fill="black", font=font)
    y += row_height

    for row in board.component_rows:
        removal = "NA" if row.semantic_removal_impact is None else f"{row.semantic_removal_impact:.4f}"
        merge = "NA" if row.semantic_merge_impact is None else f"{row.semantic_merge_impact:.4f}"
        reasons = ",".join(row.reasons) or "-"
        text = " | ".join(
            (
                row.component_id,
                row.role,
                f"{row.support_ratio:.5f}",
                row.evidence_authority_state,
                f"{row.semantic_removal_observer}:{removal}",
                f"{row.semantic_merge_observer}:{merge}",
                row.primitive_advisor_status,
                row.recommendation,
                reasons,
                "null",
            )
        )
        draw.text((10, y), text, fill="black", font=font)
        y += row_height

    return image
