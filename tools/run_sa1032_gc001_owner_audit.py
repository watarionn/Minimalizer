"""Audit explicit GC001 primitive owners in Phase 11 and selected Phase 12.

Never infer a semantic owner from RGB/material or from __unbound__ geometry.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

REQUIRED = frozenset({"face", "hair", "left_arm", "right_arm"})


def explicit_owner(primitive: dict) -> str | None:
    semantic = primitive.get("semantic_part_id")
    composition = primitive.get("composition_part")
    legacy = primitive.get("owner")
    # An explicitly unbound primitive must not be relabelled as an anatomy part.
    if composition == "__unbound__":
        return None
    return semantic or composition or legacy


def audit_records(records: list[dict]) -> dict:
    if not isinstance(records, list):
        raise ValueError("primitives must be a list")
    counts: Counter[str] = Counter()
    invalid: list[dict] = []
    unbound = 0
    for index, primitive in enumerate(records):
        if not isinstance(primitive, dict):
            invalid.append({"index": index, "reason": "not_object"})
            continue
        semantic = primitive.get("semantic_part_id")
        composition = primitive.get("composition_part")
        legacy = primitive.get("owner")
        if semantic and composition and semantic != composition:
            invalid.append({"index": index, "reason": "conflicting_semantic_owner"})
            continue
        if legacy and semantic and legacy != semantic:
            invalid.append({"index": index, "reason": "conflicting_legacy_owner"})
            continue
        if composition == "__unbound__":
            if semantic or legacy:
                invalid.append({"index": index, "reason": "unbound_has_semantic_owner"})
            else:
                unbound += 1
            continue
        owner = explicit_owner(primitive)
        if not isinstance(owner, str) or not owner.strip():
            invalid.append({"index": index, "reason": "missing_explicit_owner"})
            continue
        counts[owner] += 1
    missing = sorted(REQUIRED.difference(counts))
    return {
        "primitive_count": len(records),
        "explicit_owner_counts": dict(sorted(counts.items())),
        "unbound_primitive_count": unbound,
        "missing_required_owners": missing,
        "invalid_records": invalid,
        "status": "OWNER_AUDIT_PASS" if not missing and not invalid else "HOLD_OWNER_PROVENANCE",
    }


def scene_records(scene: dict, selection: str = "selected") -> list[dict]:
    """Resolve the actual 11-primitive selected Phase 12 candidate by default."""
    if not isinstance(scene, dict):
        raise ValueError("scene must be an object")
    if "candidates" in scene and selection != "phase11":
        name = scene.get("selected_name") if selection == "selected" else selection
        found = [entry for entry in scene["candidates"] if entry.get("name") == name]
        if len(found) != 1:
            raise ValueError(f"candidate not found or duplicated: {name}")
        records = found[0].get("primitives")
    else:
        records = scene.get("primitives_back_to_front")
        if records is None:
            records = scene.get("baseline", {}).get("primitives")
    if not isinstance(records, list):
        raise ValueError("scene has no explicit primitive list")
    return records


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--scene", required=True, type=Path)
    p.add_argument("--selection", default="selected")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    scene = json.loads(args.scene.read_text(encoding="utf-8-sig"))
    records = scene_records(scene, args.selection)
    result = audit_records(records)
    result["selection"] = scene.get("selected_name") if args.selection == "selected" and "candidates" in scene else args.selection
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
