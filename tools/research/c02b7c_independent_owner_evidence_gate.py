"""C02b7c research gate for source-only independently observed semantic anchors.

This validator CANNOT certify an observer's claimed independence. That requires
external audit. Even agreement only nominates locations for human inspection;
no owner mask, source image, Stage8 scene or production file is ever changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image

CASE_PINS = {
    "GC001": {
        "source": "75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",
        "scene": "7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08",
    },
    "Raden": {
        "source": "d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00",
        "scene": "be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f",
    },
}
OWNERS = frozenset(("right_arm", "left_arm", "hair", "major_clothing"))
CONFIDENCE_MIN = 0.85
ALLOWED_ORIGINS = frozenset(("source_only_semantic_model", "source_only_independent_human"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_string(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def checked_case(case: str, image_path: Path, stage8_path: Path) -> dict:
    if case not in CASE_PINS:
        raise ValueError("UNKNOWN_SIGNED_CASE")
    pins = CASE_PINS[case]
    if sha256(image_path) != pins["source"] or sha256(stage8_path) != pins["scene"]:
        raise ValueError("SIGNED_SOURCE_OR_SCENE_SHA_MISMATCH")
    with Image.open(image_path) as img:
        img.load()
        if img.size != (340, 340):
            raise ValueError("SIGNED_IMAGE_DIMENSIONS_INVALID")
    scene = json.loads(stage8_path.read_text(encoding="utf-8"))
    if (scene.get("original_source_sha256") != pins["source"]
        or scene.get("production_authorized") is not False
        or scene.get("no_new_primitive") is not True
        or scene.get("no_new_material_or_owner") is not True):
        raise ValueError("SIGNED_SCENE_AUTHORITY_MISMATCH")
    return {"case": case, "source_sha256": pins["source"], "stage8_sha256": pins["scene"]}


def _reject_or_validate(record: dict, case: str, expected_source: str) -> tuple:
    required = {"observer_id", "observer_family", "observer_lineage_sha256", "run_sha256",
                "source_sha256", "case", "input_provenance", "origin", "calibrated",
                "owner", "point", "confidence"}
    if not isinstance(record, dict) or set(record) != required:
        raise ValueError("OBSERVER_SCHEMA_FAIL_CLOSED")
    if record["case"] != case or record["source_sha256"] != expected_source:
        raise ValueError("OBSERVER_SOURCE_BINDING_MISMATCH")
    for field in ("observer_lineage_sha256", "run_sha256"):
        if not sha_string(record[field]):
            raise ValueError("OBSERVER_SHA_INVALID")
    for field in ("observer_id", "observer_family"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError("OBSERVER_IDENTITY_INVALID")
    if record["origin"] not in ALLOWED_ORIGINS or record["input_provenance"] != ["original_source_only"]:
        raise ValueError("OBSERVER_INDEPENDENCE_CLAIM_INVALID")
    if record["calibrated"] is not True or record["owner"] not in OWNERS:
        raise ValueError("OBSERVER_UNCALIBRATED_OR_UNKNOWN_OWNER")
    pt = record["point"]
    if not isinstance(pt, list) or len(pt) != 2 or any(type(v) is not int or v < 0 or v >= 340 for v in pt):
        raise ValueError("OBSERVER_POINT_INVALID")
    confidence = record["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("OBSERVER_CONFIDENCE_INVALID")
    return ((pt[0], pt[1]), record["owner"], record["observer_id"],
            record["observer_family"], record["observer_lineage_sha256"], float(confidence))


def inspect(case: str, original_source_sha: str, observations: list[dict]) -> dict:
    """Aggregate externally obtained labels, never infer labels from Stage8 or masks.

    Matching confidence is a *self-attested* claim; review-only cannot promote.
    Return only coordinate-free counts so this result can be checked into GitHub.
    """
    if case not in CASE_PINS or original_source_sha != CASE_PINS[case]["source"]:
        raise ValueError("OBSERVER_TARGET_CASE_SHA_MISMATCH")
    if not isinstance(observations, list):
        raise ValueError("OBSERVATIONS_MUST_BE_LIST")
    locations = defaultdict(list)
    used_runs = set()
    for r in observations:
        loc, owner, observer, family, lineage, conf = _reject_or_validate(r, case, original_source_sha)
        key = (observer, r["run_sha256"], loc)
        if key in used_runs:
            raise ValueError("DUPLICATE_OBSERVER_LOCATION")
        used_runs.add(key)
        locations[loc].append((owner, observer, family, lineage, conf))
    disputed, sparse, uncalibrated, agreement = 0, 0, 0, 0
    for entries in locations.values():
        names = {v[0] for v in entries}
        if len(names) > 1:
            disputed += 1
            continue
        strong = [v for v in entries if v[4] >= CONFIDENCE_MIN]
        if len(strong) < 2:
            uncalibrated += 1
            continue
        # Two claimed independent method families AND disjoint model lineages.
        if (len({v[1] for v in strong}) < 2 or len({v[2] for v in strong}) < 2
            or len({v[3] for v in strong}) < 2):
            sparse += 1
            continue
        agreement += 1
    outcome = ("REVIEW_ONLY_UNVERIFIED_INDEPENDENCE" if agreement else
               "ABSTAIN_NO_INDEPENDENT_ANCHORS")
    return {
        "case": case, "source_sha256": original_source_sha,
        "observer_claims": len(observations), "observed_locations": len(locations),
        "review_only_agreement_locations": agreement,
        "conflicting_locations": disputed, "insufficient_independence_locations": sparse,
        "low_confidence_locations": uncalibrated, "outcome": outcome,
        "confidence_is_self_attested": True,
        "independence_cryptographically_verified": False,
        "owner_ground_truth_verified": False,
        "owner_mask_modifications": 0, "candidate": "NONE",
        "human_golden": "PENDING", "stage8_original_budget": "HOLD",
        "release_authorized": False, "production_changed": False,
    }


def run_private(cases: dict[str, tuple[Path, Path]], submissions: dict | None = None) -> dict:
    if set(cases) != set(CASE_PINS):
        raise ValueError("BOTH_SIGNED_CASES_REQUIRED")
    if submissions is not None and set(submissions) != set(CASE_PINS):
        raise ValueError("BOTH_OBSERVER_CASES_REQUIRED")
    results = []
    for case in CASE_PINS:
        info = checked_case(case, *cases[case])
        results.append(inspect(case, info["source_sha256"], (submissions or {}).get(case, [])))
    return {"schema": "sa1060m_c02b7c_independent_semantic_anchor_gate_v1",
            "cases": results, "semantic_model_executed": False,
            "source_only_observation_policy": True, "observer_review_gate_complete": True,
            "independent_semantic_observations_available": bool(submissions and any(submissions.values())),
            "release_authorized": False, "deployment_verified": False,
            "C02": "IN_PROGRESS", "C03": "HOLD", "C04": "HOLD", "C05_C08": "BLOCKED"}


def main() -> None:
    p = argparse.ArgumentParser()
    for k in ("gc_source", "gc_scene", "raden_source", "raden_scene", "output", "observations"):
        p.add_argument("--" + k.replace('_', '-'), type=Path, required=k != "observations")
    a = p.parse_args()
    inputs = {"GC001": (a.gc_source, a.gc_scene), "Raden": (a.raden_source, a.raden_scene)}
    dest = a.output.resolve()
    if dest.exists() or dest in [v.resolve() for pair in inputs.values() for v in pair] or (a.observations and dest == a.observations.resolve()):
        raise ValueError("OUTPUT_OVERWRITE_FORBIDDEN")
    obs = None if a.observations is None else json.loads(a.observations.read_text(encoding="utf-8"))
    result = run_private(inputs, obs)
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outcomes": {c["case"]: c["outcome"] for c in result["cases"]}, "release_authorized": False}))


if __name__ == "__main__":
    main()
