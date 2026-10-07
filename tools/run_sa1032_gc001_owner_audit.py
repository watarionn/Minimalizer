"""Audit GC001 phase-11/12 ownership without guessing from colors.

No image editing; reject missing or ambiguous primitive owner records.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

OWNERS = {"face", "hair", "left_arm", "right_arm"}


def audit_records(records: list[dict]) -> dict:
    if not isinstance(records, list):
        raise ValueError("primitives must be a list")
    counts = Counter()
    invalid = []
    for i, primitive in enumerate(records):
        if not isinstance(primitive, dict):
            invalid.append({"index": i, "reason": "not_object"})
            continue
        owner = primitive.get("owner")\n        if owner is None:\n            owner = primitive.get("semantic_part_id") or primitive.get("composition_part")
        if not isinstance(owner, str) or not owner.strip():
            invalid.append({"index": i, "reason": "missing_explicit_owner"})
            continue
        counts[owner] += 1
    missing = sorted(OWNERS - counts.keys())
    return {
        "primitive_count": len(records),
        "owners": dict(sorted(counts.items())),
        "missing_required_owners": missing,
        "invalid_records": invalid,
        "status": "OWNER_AUDIT_PASS" if not missing and not invalid else "HOLD_OWNER_PROVENANCE",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--scene", required=True, type=Path)
    p.add_argument("--primitives-key", default="primitives_back_to_front")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    scene = json.loads(args.scene.read_text(encoding="utf-8-sig"))
    if not isinstance(scene, dict) or args.primitives_key not in scene:
        raise ValueError("scene lacks explicitly selected primitive list")
    result = audit_records(scene[args.primitives_key])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
