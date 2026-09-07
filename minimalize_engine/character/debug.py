from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np

from .models import CharacterStructure
from .part_types import CharacterPartType


_LABEL_COLORS = {
    CharacterPartType.HEAD: (255, 80, 80),
    CharacterPartType.FACE: (255, 170, 120),
    CharacterPartType.HAIR: (180, 90, 255),
    CharacterPartType.TORSO: (80, 220, 120),
    CharacterPartType.LEFT_ARM: (60, 200, 240),
    CharacterPartType.RIGHT_ARM: (40, 150, 230),
    CharacterPartType.LEFT_LEG: (255, 210, 60),
    CharacterPartType.RIGHT_LEG: (230, 170, 40),
    CharacterPartType.OUTFIT: (180, 180, 180),
    CharacterPartType.PROP: (255, 70, 170),
}


def render_character_debug_overlay(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
) -> np.ndarray:
    out = image_rgb.copy()
    for part in structure.parts:
        if part.part_type == CharacterPartType.SUBJECT:
            continue
        color = _LABEL_COLORS.get(part.part_type, (255, 255, 255))
        x, y, w, h = part.bbox
        cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), color, 1)
        label = f"{part.part_type}:{part.confidence:.2f}"
        cv2.putText(
            out,
            label,
            (x, max(10, y - 3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.34,
            color,
            1,
            cv2.LINE_AA,
        )

    fv = structure.metadata.get("face_validation") or {}
    if fv:
        bbox = fv.get("candidate_bbox") or fv.get("expected_bbox")
        if bbox:
            x, y, w, h = [int(round(v)) for v in bbox]
            color = (90, 220, 90) if fv.get("accepted") else (160, 160, 160)
            cv2.rectangle(out, (x, y), (x + max(1, w) - 1, y + max(1, h) - 1), color, 1)
            label = f"face_gate:{float(fv.get('confidence', 0.0)):.2f}"
            cv2.putText(
                out,
                label,
                (x, min(out.shape[0] - 4, y + max(10, h) + 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.32,
                color,
                1,
                cv2.LINE_AA,
            )

    if structure.pose_graph is not None:
        graph = structure.pose_graph
        by_id = {n.id: n for n in graph.nodes}
        for edge in graph.edges:
            if edge.source_id not in by_id or edge.target_id not in by_id:
                continue
            a = by_id[edge.source_id].position
            b = by_id[edge.target_id].position
            cv2.line(
                out,
                (int(round(a[0])), int(round(a[1]))),
                (int(round(b[0])), int(round(b[1]))),
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
        for node in graph.nodes:
            cv2.circle(
                out,
                (int(round(node.position[0])), int(round(node.position[1]))),
                3,
                (255, 255, 255),
                -1,
            )
    return out


def save_character_debug_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    structure: CharacterStructure,
) -> None:
    out = render_character_debug_overlay(image_rgb, structure)
    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))



def save_character_detail_debug_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
) -> None:
    out = image_rgb.copy()

    face = detail_metadata.get("face", {})
    validation = face.get("validation") or {}
    layout = face.get("layout") or {}
    fb = layout.get("face_bbox")
    if not fb:
        fb = validation.get("candidate_bbox") or validation.get("expected_bbox")
    if fb:
        x, y, w, h = [int(round(v)) for v in fb]
        box_color = (255, 180, 120) if validation.get("accepted", True) else (180, 180, 180)
        cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), box_color, 1)
        if validation:
            label = f"gate {float(validation.get('confidence', 0.0)):.2f}"
            cv2.putText(
                out,
                label,
                (x, min(out.shape[0] - 4, y + h + 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.32,
                box_color,
                1,
                cv2.LINE_AA,
            )
            reasons = validation.get("reasons") or []
            if reasons:
                reason = str(reasons[0])[:54]
                cv2.putText(
                    out,
                    reason,
                    (x, min(out.shape[0] - 4, y + h + 22)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.28,
                    box_color,
                    1,
                    cv2.LINE_AA,
                )

    for key, color in [
        ("left_eye", (70, 255, 120)),
        ("right_eye", (70, 255, 120)),
        ("mouth", (255, 90, 120)),
    ]:
        item = layout.get(key)
        if item:
            x, y = int(round(item[0])), int(round(item[1]))
            cv2.circle(out, (x, y), 3, color, -1)

    hair = detail_metadata.get("hair", {})
    for flow in hair.get("flows", []):
        pts = flow.get("points") or []
        if len(pts) < 2:
            continue
        arr = np.asarray(
            [(int(round(x)), int(round(y))) for x, y in pts],
            dtype=np.int32,
        )
        color = {
            "bangs": (255, 80, 220),
            "side_hair": (180, 80, 255),
            "back_hair": (100, 120, 255),
            "hair_feature": (255, 220, 70),
        }.get(flow.get("flow_type"), (255, 255, 255))

        if len(arr) >= 3 and flow.get("flow_type") == "hair_feature":
            cv2.polylines(out, [arr], True, color, 1, cv2.LINE_AA)
        else:
            cv2.polylines(out, [arr], False, color, 1, cv2.LINE_AA)

    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))


def save_character_outfit_debug_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
) -> None:
    out = image_rgb.copy()
    outfit = detail_metadata.get("outfit", {})
    structure = outfit.get("structure") or {}

    items = [
        ("torso", (80, 230, 120), "torso"),
        ("left_sleeve", (80, 210, 250), "L sleeve"),
        ("right_sleeve", (60, 160, 245), "R sleeve"),
        ("lower", (255, 210, 70), structure.get("lower_type", "lower")),
        ("left_shoe", (180, 120, 255), "L shoe"),
        ("right_shoe", (145, 95, 235), "R shoe"),
    ]

    for key, color, label in items:
        item = structure.get(key)
        if not item:
            continue
        bbox = item.get("bbox")
        if not bbox:
            continue
        x, y, w, h = [int(round(v)) for v in bbox]
        cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), color, 1)
        cv2.putText(
            out,
            label,
            (x, max(10, y - 3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.34,
            color,
            1,
            cv2.LINE_AA,
        )

    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))



def save_character_prop_debug_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
) -> None:
    out = image_rgb.copy()
    props = detail_metadata.get("props", {})
    descriptors = props.get("descriptors") or []

    type_colors = {
        "staff_like": (255, 100, 80),
        "sword_like": (255, 180, 80),
        "microphone_like": (255, 80, 190),
        "headphone_like": (80, 220, 255),
        "hat_like": (190, 110, 255),
        "bag_like": (120, 255, 120),
        "unknown": (230, 230, 230),
    }

    for d in descriptors:
        bbox = d.get("bbox")
        if not bbox:
            continue
        x, y, w, h = [int(round(v)) for v in bbox]
        ptype = d.get("prop_type", "unknown")
        color = type_colors.get(ptype, (230, 230, 230))
        cv2.rectangle(
            out,
            (x, y),
            (x + max(1, w) - 1, y + max(1, h) - 1),
            color,
            1,
        )
        label = f"{ptype}:{float(d.get('confidence', 0)):.2f}"
        cv2.putText(
            out,
            label,
            (x, max(10, y - 3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.32,
            color,
            1,
            cv2.LINE_AA,
        )

        a = d.get("axis_start")
        b = d.get("axis_end")
        if a and b:
            cv2.line(
                out,
                (int(round(a[0])), int(round(a[1]))),
                (int(round(b[0])), int(round(b[1]))),
                color,
                1,
                cv2.LINE_AA,
            )

        md = d.get("metadata") or {}
        for key in ["left_center", "right_center", "head_center"]:
            c = md.get(key)
            if c:
                cv2.circle(
                    out,
                    (int(round(c[0])), int(round(c[1]))),
                    3,
                    color,
                    -1,
                )

    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))



def save_character_body_debug_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
) -> None:
    out = image_rgb.copy()
    body = detail_metadata.get("body", {})
    analysis = body.get("analysis") or {}

    torso = analysis.get("torso_points") or []
    if len(torso) >= 3:
        pts = np.asarray(
            [(int(round(x)), int(round(y))) for x, y in torso],
            dtype=np.int32,
        )
        cv2.polylines(out, [pts], True, (90, 255, 150), 1, cv2.LINE_AA)

    limb_colors = {
        "left_arm": (70, 220, 255),
        "right_arm": (60, 160, 255),
        "left_leg": (255, 220, 70),
        "right_leg": (255, 165, 70),
    }

    for limb in analysis.get("limbs", []):
        ptype = limb.get("part_type", "unknown")
        color = limb_colors.get(ptype, (255, 255, 255))
        prox = limb.get("proximal")
        bend = limb.get("bend")
        distal = limb.get("distal")
        if prox and bend and distal:
            pts = np.asarray(
                [
                    (int(round(prox[0])), int(round(prox[1]))),
                    (int(round(bend[0])), int(round(bend[1]))),
                    (int(round(distal[0])), int(round(distal[1]))),
                ],
                dtype=np.int32,
            )
            cv2.polylines(out, [pts], False, color, 2, cv2.LINE_AA)
            for point in pts:
                cv2.circle(out, tuple(point), 3, color, -1)

        if prox:
            label = (
                f"{ptype} "
                f"{float(limb.get('proximal_width', 0)):.1f}/"
                f"{float(limb.get('distal_width', 0)):.1f}"
            )
            cv2.putText(
                out,
                label,
                (int(round(prox[0])), max(10, int(round(prox[1])) - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.30,
                color,
                1,
                cv2.LINE_AA,
            )

    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))


def render_face_diagnostics_overlay(
    image_rgb: np.ndarray,
    detail_metadata: dict,
    report: dict,
) -> np.ndarray:
    """Render a compact visual dashboard for Phase 10.6 face review."""
    src = image_rgb.copy()
    h, w = src.shape[:2]
    panel_w = max(220, min(310, int(round(w * 0.82))))
    out = np.full((h, w + panel_w, 3), 245, dtype=np.uint8)
    out[:, :w] = src

    face = detail_metadata.get("face", {}) or {}
    layout = face.get("layout", {}) or {}
    bbox = layout.get("face_bbox")
    if bbox:
        x, y, bw, bh = [int(round(v)) for v in bbox]
        status = str(report.get("status", "unavailable"))
        box_color = {
            "healthy": (70, 220, 110),
            "watch": (245, 185, 65),
            "repair": (245, 90, 90),
        }.get(status, (175, 175, 175))
        cv2.rectangle(
            out,
            (x, y),
            (x + max(1, bw) - 1, y + max(1, bh) - 1),
            box_color,
            2,
        )

    selected = set(report.get("selected_features") or [])
    for name, layout_key in (
        ("primary_eye", None),
        ("secondary_eye", None),
        ("mouth", "mouth"),
    ):
        if layout_key == "mouth":
            item = layout.get("mouth")
            if item:
                color = (65, 210, 105) if name in selected else (155, 155, 155)
                cv2.circle(out, (int(round(item[0])), int(round(item[1]))), 4, color, -1)

    primary_side = (
        (face.get("identity_signals") or {}).get("primary_eye_side") or "none"
    )
    eye_items = {
        "left": layout.get("left_eye"),
        "right": layout.get("right_eye"),
    }
    for side, item in eye_items.items():
        if not item:
            continue
        feature = "primary_eye" if side == primary_side else "secondary_eye"
        color = (65, 210, 105) if feature in selected else (155, 155, 155)
        cv2.circle(out, (int(round(item[0])), int(round(item[1]))), 4, color, -1)

    x0 = w + 12
    y0 = 18
    line_h = 17
    font = cv2.FONT_HERSHEY_SIMPLEX

    def line(text: str, *, scale: float = 0.37, thickness: int = 1) -> None:
        nonlocal y0
        safe = str(text)[:52]
        cv2.putText(
            out,
            safe,
            (x0, y0),
            font,
            scale,
            (35, 35, 35),
            thickness,
            cv2.LINE_AA,
        )
        y0 += line_h

    line("Face Diagnostics 10.6", scale=0.45, thickness=1)
    line(f"status: {report.get('status', 'unavailable')}")
    line(f"tier: {report.get('visibility_tier') or '-'}")
    line(f"minimality: {report.get('minimality_level') or '-'}")
    planned = report.get("planned_shape_count")
    actual = report.get("actual_shape_count")
    released = report.get("released_shape_slots")
    line(f"shapes: plan {planned} / actual {actual} / free {released}")
    kept = report.get("selected_features") or []
    line("kept: " + (", ".join(kept) if kept else "legacy / none"), scale=0.32)

    for label, key in (
        ("identity", "identity_score"),
        ("geometry", "face_geometry_score"),
        ("boundary", "face_boundary_score"),
        ("retention", "face_retention_score"),
    ):
        value = report.get(key)
        line(f"{label}: {float(value):.3f}" if value is not None else f"{label}: N/A")

    if report.get("rollback_applied"):
        line(f"rollback: +{report.get('rollback_feature')}", scale=0.34)
    warnings = report.get("warnings") or []
    if warnings:
        line("review:", scale=0.36)
        for warning in warnings[:4]:
            line("- " + str(warning), scale=0.29)
    else:
        line("review: no face-specific warning", scale=0.31)

    return out


def save_face_diagnostics_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
    report: dict,
) -> None:
    out = render_face_diagnostics_overlay(image_rgb, detail_metadata, report)
    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))


def save_character_hand_debug_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
) -> None:
    out = image_rgb.copy()
    analysis = (detail_metadata.get("hands") or {}).get("analysis") or {}
    rendering = (detail_metadata.get("hands") or {}).get("rendering") or {}
    for shape in rendering.get("shapes") or []:
        pts = np.asarray(shape.get("points") or [], dtype=np.float32)
        if len(pts) >= 3:
            pts_i = np.round(pts).astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(out, [pts_i], True, (245, 245, 80), 2, cv2.LINE_AA)
    for hand in analysis.get("hands") or []:
        bbox = hand.get("bbox") or [0, 0, 0, 0]
        x, y, w, h = [int(round(v)) for v in bbox]
        side = hand.get("side", "?")
        intent = hand.get("intent", "unknown")
        confidence = float(hand.get("confidence", 0.0))
        color = (80, 230, 120) if side == "left" else (80, 170, 250)
        if w > 0 and h > 0:
            cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), color, 1)
        center = hand.get("center")
        if center:
            cx, cy = int(round(center[0])), int(round(center[1]))
            cv2.circle(out, (cx, cy), 3, color, -1)
        rendered = (detail_metadata.get("hands") or {}).get("rendering") or {}
        rendered_sides = set(rendered.get("rendered_sides") or [])
        suffix = " shape" if side in rendered_sides else " analysis"
        label = f"{side[0].upper()} hand {intent} {confidence:.2f}{suffix}"
        cv2.putText(
            out,
            label,
            (x, max(10, y - 3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.30,
            color,
            1,
            cv2.LINE_AA,
        )
    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))


def save_character_hand_geometry_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
) -> None:
    out = image_rgb.copy()
    hands_meta = detail_metadata.get("hands") or {}
    report = hands_meta.get("geometry_validation") or {}
    rendering = hands_meta.get("rendering") or {}

    for shape in rendering.get("shapes") or []:
        pts = np.asarray(shape.get("points") or [], dtype=np.float32)
        if len(pts) >= 3:
            pts_i = np.round(pts).astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(out, [pts_i], True, (245, 245, 80), 2, cv2.LINE_AA)

    y = 14
    cv2.putText(out, "Hand Geometry 11.3", (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (245,245,245), 1, cv2.LINE_AA)
    y += 13
    for item in report.get("hands") or []:
        side = item.get("side", "?")
        before = item.get("before_center") or [0, 0]
        after = item.get("after_center") or before
        bx, by = int(round(before[0])), int(round(before[1]))
        ax, ay = int(round(after[0])), int(round(after[1]))
        color = (80, 230, 120) if side == "left" else (80, 170, 250)
        cv2.circle(out, (bx, by), 3, (235, 110, 90), 1)
        cv2.circle(out, (ax, ay), 3, color, -1)
        if item.get("corrected"):
            cv2.arrowedLine(out, (bx, by), (ax, ay), color, 1, cv2.LINE_AA, tipLength=0.25)
        label = (
            f"{side[0].upper()} {item.get('intent','?')} "
            f"conn {float(item.get('connection_score',0)):.2f} "
            f"dir {float(item.get('direction_score',0)):.2f}"
        )
        cv2.putText(out, label, (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.28, color, 1, cv2.LINE_AA)
        y += 11

    score = report.get("score")
    if score is not None:
        cv2.putText(out, f"score {float(score):.3f} corrected {int(report.get('corrected_count',0))}", (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (245,245,245), 1, cv2.LINE_AA)

    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))


def save_character_hand_validation_overlay(
    path: str | Path,
    image_rgb: np.ndarray,
    detail_metadata: dict,
) -> None:
    out = image_rgb.copy()
    hands_meta = detail_metadata.get("hands") or {}
    report = hands_meta.get("candidate_validation") or {}
    analysis = hands_meta.get("analysis") or {}
    by_side = {item.get("side"): item for item in report.get("items") or []}

    for hand in analysis.get("hands") or []:
        bbox = hand.get("bbox") or [0, 0, 0, 0]
        x, y, w, h = [int(round(v)) for v in bbox]
        item = by_side.get(hand.get("side"), {})
        accepted = bool(item.get("accepted", False))
        color = (80, 230, 120) if accepted else (245, 90, 90)
        if w > 0 and h > 0:
            cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), color, 2 if accepted else 1)
        score = float(item.get("score", 0.0))
        label = f"{hand.get('side','?')[0].upper()} {hand.get('intent','?')} {score:.2f} {'KEEP' if accepted else 'DROP'}"
        cv2.putText(out, label, (x, max(10, y - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.28, color, 1, cv2.LINE_AA)

    y = 14
    cv2.putText(out, "Hand Validation 11.4", (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (245,245,245), 1, cv2.LINE_AA)
    y += 13
    cv2.putText(
        out,
        f"keep {int(report.get('accepted_count',0))} drop {int(report.get('rejected_count',0))} score {float(report.get('score',1.0)):.3f}",
        (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (245,245,245), 1, cv2.LINE_AA
    )
    bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
    cv2.imencode(Path(path).suffix or ".png", bgr)[1].tofile(str(path))
