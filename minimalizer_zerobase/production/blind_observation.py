from __future__ import annotations

from typing import Any, Iterable, Mapping


class BlindObservationBindingError(RuntimeError):
    pass


def bind_blind_observations(
    manifest: Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    features = {row["id"]: row for row in manifest.get("features", [])}
    by_label: dict[str, list[Mapping[str, Any]]] = {}
    unlabeled = 0
    for row in observations:
        label = row.get("semantic_label")
        if not label:
            unlabeled += 1
            continue
        by_label.setdefault(str(label), []).append(row)

    evidence: dict[str, dict[str, Any]] = {}
    masks: dict[str, dict[str, Any]] = {}
    unresolved: list[str] = []

    for feature_id, feature in sorted(features.items()):
        role = feature["semantic_role"]
        matches = by_label.get(role, [])
        if len(matches) != 1:
            evidence[feature_id] = {
                "state": "unknown",
                "source": "blind_observer_binding",
            }
            unresolved.append(feature_id)
            continue
        obs = matches[0]
        bbox = obs.get("geometry", {}).get("bbox")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            evidence[feature_id] = {
                "state": "unknown",
                "source": "blind_observer_binding",
            }
            unresolved.append(feature_id)
            continue
        evidence[feature_id] = {
            "state": "present",
            "source": "blind_observer_binding",
            "confidence": obs.get("confidence"),
        }
        descriptor = obs.get("geometry", {}).get("mask_descriptor")
        contour = obs.get("geometry", {}).get("contour_envelope")
        masks[feature_id] = {
            "authorized": True,
            "bbox": [float(v) for v in bbox],
            "mask_descriptor": descriptor,
            "contour_envelope": contour,
            "source_evidence_id": obs.get("evidence_id"),
            "semantic_role": role,
        }

    return {
        "schema_version": "1.0",
        "case_id": manifest.get("case_id"),
        "feature_evidence": evidence,
        "authorized_masks": masks,
        "unresolved_features": unresolved,
        "unlabeled_observation_count": unlabeled,
        "manual_semantic_labels_used": False,
        "golden_used": False,
    }
