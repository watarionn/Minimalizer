"""Build a candidate-bound Phase 4 part bundle from private research inputs.

This is a source-free-code entry point: source pixels, candidate arrays and
generated masks stay outside Git.  It deliberately does not use review labels.
The candidate is treated as positive garment evidence, not as permission to
replace an existing semantic owner. Protected and already-known semantic
parts are never overwritten; only candidate pixels in unknown space can be
promoted when their 8-connected component touches a clothing context.

    An optional independently generated outerwear observation can perform a
    separate owner arbitration pass.  That pass removes only existing arm-owner
    pixels that belong to a connected outerwear component which also touches a
    clothing context, while preserving pixels supported by the same independent
    arm observer.  It never promotes unknown pixels and never uses a human mask.
    This is the H06/H08 sleeve-versus-arm correction, not a case-specific
    threshold or a visual-review override.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

import numpy as np
from PIL import Image
from scipy import ndimage

try:
    from .audit_local_l02_phase5_input import CASES, PARTS
except ImportError:  # pragma: no cover - direct CLI execution
    from audit_local_l02_phase5_input import CASES, PARTS  # type: ignore


PROTECTED_PARTS = ("head", "hair", "face", "neck", "accessory_or_held_object")
CLOTHING_CONTEXT_PARTS = ("torso", "lower_body", "major_clothing", "unknown")


class CandidateBoundPhase4Hold(ValueError):
    """Input cannot be converted into a safe candidate-bound bundle."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise CandidateBoundPhase4Hold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _source_path(source_root: Path, case: str) -> Path:
    matches = sorted(source_root.glob(f"{case}.*"))
    if len(matches) != 1:
        raise CandidateBoundPhase4Hold(f"SOURCE_FILE_NOT_UNIQUE:{case}")
    return matches[0]


def _candidate_path(candidate_root: Path, case: str) -> Path:
    matches = sorted(candidate_root.glob(f"{case}*CANDIDATE*.npz"))
    if len(matches) != 1:
        raise CandidateBoundPhase4Hold(f"CANDIDATE_FILE_NOT_UNIQUE:{case}")
    return matches[0]


def _load_source_alpha(path: Path) -> tuple[np.ndarray, tuple[int, int]]:
    with Image.open(path) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    alpha = rgba[:, :, 3] > 0
    return alpha, (int(rgba.shape[1]), int(rgba.shape[0]))


def _load_base_masks(base_dir: Path, source_sha: str) -> tuple[dict[str, np.ndarray], Mapping[str, object]]:
    stage_path = base_dir / "stage.json"
    if not stage_path.is_file():
        raise CandidateBoundPhase4Hold("SOURCE_ONLY_STAGE_MISSING")
    stage = _json(stage_path)
    source = stage.get("source")
    if not isinstance(source, Mapping) or source.get("sha256") != source_sha:
        raise CandidateBoundPhase4Hold("SOURCE_ONLY_SOURCE_SHA_MISMATCH")
    outputs = stage.get("outputs")
    if not isinstance(outputs, Mapping):
        raise CandidateBoundPhase4Hold("SOURCE_ONLY_OUTPUT_MANIFEST_MISSING")
    masks: dict[str, np.ndarray] = {}
    expected_shape: tuple[int, int] | None = None
    for part in PARTS:
        path = base_dir / "part_masks" / f"{part}.png"
        recorded_sha = outputs.get(f"part_masks/{part}.png")
        if not path.is_file() or not isinstance(recorded_sha, str):
            raise CandidateBoundPhase4Hold(f"SOURCE_ONLY_PART_MASK_MISSING:{part}")
        if _sha256_file(path) != recorded_sha:
            raise CandidateBoundPhase4Hold(f"SOURCE_ONLY_PART_MASK_SHA_MISMATCH:{part}")
        with Image.open(path) as image:
            array = np.asarray(image.convert("L"), dtype=np.uint8) > 0
        if expected_shape is None:
            expected_shape = array.shape
        if array.shape != expected_shape:
            raise CandidateBoundPhase4Hold(f"SOURCE_ONLY_PART_MASK_DIMENSION_MISMATCH:{part}")
        masks[part] = array
    return masks, stage


def integrate_candidate_masks(
    base_masks: Mapping[str, np.ndarray],
    candidate_owner: np.ndarray,
    source_alpha: np.ndarray,
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Integrate positive garment evidence without reassigning known owners."""
    if candidate_owner.ndim != 2 or candidate_owner.dtype != np.uint8:
        raise CandidateBoundPhase4Hold("CANDIDATE_ARRAY_TYPE_OR_RANK_INVALID")
    if candidate_owner.shape != source_alpha.shape:
        raise CandidateBoundPhase4Hold("CANDIDATE_SOURCE_DIMENSION_MISMATCH")
    if not np.isin(candidate_owner, (0, 1, 2)).all():
        raise CandidateBoundPhase4Hold("CANDIDATE_OWNER_VALUE_INVALID")
    candidate = candidate_owner > 0
    if np.any(candidate & ~source_alpha):
        raise CandidateBoundPhase4Hold("CANDIDATE_OUTSIDE_SOURCE_ALPHA")

    result = {part: np.asarray(base_masks[part], dtype=bool).copy() for part in PARTS}
    protected = np.zeros_like(candidate)
    for part in PROTECTED_PARTS:
        protected |= result[part]
    known = np.zeros_like(candidate)
    for part in PARTS:
        if part != "unknown":
            known |= result[part]
    context = np.zeros_like(candidate)
    for part in CLOTHING_CONTEXT_PARTS:
        context |= result[part]
    context_touch = ndimage.binary_dilation(
        context, structure=np.ones((3, 3), dtype=bool)
    )

    # The research runners emit a full owner map. Its positive pixels are
    # evidence, not a semantic replacement command. Preserve every known
    # owner and let only unknown-space evidence compete for promotion.
    eligible = candidate & ~protected & ~known
    labels, count = ndimage.label(eligible, structure=np.ones((3, 3), dtype=np.uint8))
    accepted = np.zeros_like(candidate)
    for label in range(1, int(count) + 1):
        component = labels == label
        if np.any(component & context_touch):
            accepted |= component
    rejected = eligible & ~accepted

    result["major_clothing"] |= accepted
    result["unknown"] |= rejected

    stats = {
        "candidate_pixels": int(candidate.sum()),
        "accepted_garment_pixels": int(accepted.sum()),
        "rejected_unknown_pixels": int(rejected.sum()),
        "protected_candidate_pixels": int((candidate & protected).sum()),
        "known_owner_conflict_pixels": int((candidate & ~protected & known).sum()),
        "candidate_components": int(count),
    }
    return result, stats


def arbitrate_outerwear_over_arm_owners(
    masks: Mapping[str, np.ndarray],
    outerwear_observed: np.ndarray,
    source_alpha: np.ndarray,
    arm_observed: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Move only authenticated outerwear-over-arm pixels to clothing.

    The outerwear observation is source-only evidence from an independent
    garment detector.  A connected component must contain both an existing
    arm owner and a non-arm clothing-context pixel before it can remove an
    arm owner.  This prevents isolated arm detections from being relabeled as
    clothing and keeps unknown pixels abstained.
    """
    if (
        type(outerwear_observed) is not np.ndarray
        or outerwear_observed.dtype != np.bool_
        or outerwear_observed.ndim != 2
        or outerwear_observed.shape != source_alpha.shape
    ):
        raise CandidateBoundPhase4Hold("OUTERWEAR_EVIDENCE_TYPE_OR_SHAPE_INVALID")
    if type(source_alpha) is not np.ndarray or source_alpha.dtype != np.bool_:
        raise CandidateBoundPhase4Hold("SOURCE_ALPHA_TYPE_INVALID")
    if np.any(outerwear_observed & ~source_alpha):
        raise CandidateBoundPhase4Hold("OUTERWEAR_EVIDENCE_OUTSIDE_SOURCE_ALPHA")
    if arm_observed is None:
        arm_observed = np.zeros_like(source_alpha)
    if (
        type(arm_observed) is not np.ndarray
        or arm_observed.dtype != np.bool_
        or arm_observed.shape != source_alpha.shape
    ):
        raise CandidateBoundPhase4Hold("ARM_EVIDENCE_TYPE_OR_SHAPE_INVALID")
    if np.any(arm_observed & ~source_alpha):
        raise CandidateBoundPhase4Hold("ARM_EVIDENCE_OUTSIDE_SOURCE_ALPHA")
    result = {part: np.asarray(masks[part], dtype=bool).copy() for part in PARTS}
    arm = result["left_arm"] | result["right_arm"]
    context = (
        result["torso"]
        | result["lower_body"]
        | result["major_clothing"]
    ) & ~arm
    # The old integration passed the complete outerwear detector mask here.
    # That mask includes garment regions but has no authority over exposed arm
    # pixels.  Preserve the independent arm observation before connected
    # component arbitration; otherwise a coat detector can recolor hands and
    # exposed forearms as clothing.
    observed = outerwear_observed & source_alpha & ~arm_observed
    labels, count = ndimage.label(observed, structure=np.ones((3, 3), dtype=np.uint8))
    reassign = np.zeros_like(observed)
    eligible_components = 0
    for label in range(1, int(count) + 1):
        component = labels == label
        component_arm = component & arm & ~arm_observed
        if np.any(component_arm) and np.any(component & context):
            eligible_components += 1
            reassign |= component_arm
    result["left_arm"] &= ~reassign
    result["right_arm"] &= ~reassign
    result["major_clothing"] |= reassign
    return result, {
        "outerwear_observed_pixels": int(observed.sum()),
        "arm_observed_pixels_protected": int(arm_observed.sum()),
        "outerwear_components": int(count),
        "eligible_outerwear_components": eligible_components,
        "arm_owner_pixels_reassigned_to_clothing": int(reassign.sum()),
    }


def integrate_outerwear_owner_evidence(
    masks: Mapping[str, np.ndarray],
    outerwear_owner: np.ndarray,
    source_alpha: np.ndarray,
    arm_observed: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Integrate a source-only outerwear instance map as garment evidence.

    The previous Phase4 path consumed the observer's binary mask only as a
    reason to delete arm owners.  That left the observer-positive garment
    pixels unknown or owned by the old decomposition, so the rendered change
    was mostly a small boundary delta.  Here the observer's complete instance
    support is promoted to ``major_clothing`` after excluding protected parts
    and independently observed arm pixels.  Existing non-protected owners are
    removed only where this authenticated garment evidence wins, and unknown
    remains unknown everywhere else.
    """
    if (
        type(outerwear_owner) is not np.ndarray
        or outerwear_owner.ndim != 2
        or outerwear_owner.dtype.kind not in "iu"
        or outerwear_owner.shape != source_alpha.shape
        or np.any(outerwear_owner < 0)
    ):
        raise CandidateBoundPhase4Hold("OUTERWEAR_OWNER_TYPE_OR_SHAPE_INVALID")
    if type(source_alpha) is not np.ndarray or source_alpha.dtype != np.bool_:
        raise CandidateBoundPhase4Hold("SOURCE_ALPHA_TYPE_INVALID")
    if np.any((outerwear_owner > 0) & ~source_alpha):
        raise CandidateBoundPhase4Hold("OUTERWEAR_OWNER_OUTSIDE_SOURCE_ALPHA")
    if arm_observed is None:
        arm_observed = np.zeros_like(source_alpha)
    if (
        type(arm_observed) is not np.ndarray
        or arm_observed.dtype != np.bool_
        or arm_observed.shape != source_alpha.shape
    ):
        raise CandidateBoundPhase4Hold("ARM_EVIDENCE_TYPE_OR_SHAPE_INVALID")
    if np.any(arm_observed & ~source_alpha):
        raise CandidateBoundPhase4Hold("ARM_EVIDENCE_OUTSIDE_SOURCE_ALPHA")

    result = {part: np.asarray(masks[part], dtype=bool).copy() for part in PARTS}
    protected = np.zeros_like(source_alpha)
    for part in PROTECTED_PARTS:
        protected |= result[part]
    observed = (outerwear_owner > 0) & source_alpha
    promoted = observed & ~protected & ~arm_observed

    removed_by_part: dict[str, int] = {}
    for part in PARTS:
        if part in ("major_clothing", "unknown"):
            continue
        removed = result[part] & promoted
        removed_by_part[part] = int(removed.sum())
        result[part] &= ~promoted
    result["major_clothing"] |= promoted
    result["unknown"] &= ~promoted

    return result, {
        "outerwear_owner_pixels_observed": int(observed.sum()),
        "outerwear_owner_pixels_promoted": int(promoted.sum()),
        "outerwear_owner_pixels_rejected_protected": int((observed & protected).sum()),
        "outerwear_owner_pixels_protected_by_arm_observer": int((observed & arm_observed).sum()),
        "arm_owner_pixels_reassigned_to_clothing": removed_by_part.get("left_arm", 0) + removed_by_part.get("right_arm", 0),
        "outerwear_owner_conflict_pixels_removed": int(sum(removed_by_part.values())),
    }


def _write_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path)


def _load_outerwear_evidence(
    evidence_root: Path, case: str, source_alpha: np.ndarray, source_sha: str
) -> tuple[np.ndarray, np.ndarray, Mapping[str, object]]:
    evidence_path = evidence_root / f"{case}_LAYERED_GARMENT_OWNER_PRIVATE.npz"
    receipt_path = evidence_root / f"{case}_LAYERED_GARMENT_RECEIPT.json"
    if not evidence_path.is_file() or not receipt_path.is_file():
        raise CandidateBoundPhase4Hold(f"OUTERWEAR_EVIDENCE_MISSING:{case}")
    receipt = _json(receipt_path)
    if (
        receipt.get("source_sha256") != source_sha
        or receipt.get("source_only") is not True
        or receipt.get("human_masks_used_in_inference") is not False
        or receipt.get("review_json_used_in_inference") is not False
        or receipt.get("frozen_owner_used_in_inference") is not False
        or receipt.get("unknown_not_treated_as_negative") is not True
    ):
        raise CandidateBoundPhase4Hold(f"OUTERWEAR_EVIDENCE_PROVENANCE_INVALID:{case}")
    with np.load(evidence_path, allow_pickle=False) as archive:
        if "outerwear_observed" not in archive.files or "owner" not in archive.files or "source_alpha" not in archive.files or "arm_mask" not in archive.files:
            raise CandidateBoundPhase4Hold(f"OUTERWEAR_EVIDENCE_SCHEMA_INVALID:{case}")
        outerwear = np.asarray(archive["outerwear_observed"])
        owner = np.asarray(archive["owner"])
        evidence_alpha = np.asarray(archive["source_alpha"])
        arm = np.asarray(archive["arm_mask"])
    if (
        outerwear.dtype != np.uint8
        or owner.dtype.kind not in "iu"
        or evidence_alpha.dtype != np.uint8
        or arm.dtype != np.uint8
        or outerwear.shape != source_alpha.shape
        or owner.shape != source_alpha.shape
        or evidence_alpha.shape != source_alpha.shape
        or arm.shape != source_alpha.shape
        or not np.isin(outerwear, (0, 1)).all()
        or np.any(owner < 0)
        or not np.isin(evidence_alpha, (0, 1)).all()
        or not np.isin(arm, (0, 1)).all()
        or not np.array_equal(evidence_alpha.astype(bool), source_alpha)
    ):
        raise CandidateBoundPhase4Hold(f"OUTERWEAR_EVIDENCE_ARRAY_INVALID:{case}")
    if receipt.get("owner_array_sha256") != _sha256_bytes(owner.tobytes(order="C")):
        raise CandidateBoundPhase4Hold(f"OUTERWEAR_OWNER_SHA_MISMATCH:{case}")
    if receipt.get("arm_mask_sha256") != _sha256_bytes(arm.tobytes(order="C")):
        raise CandidateBoundPhase4Hold(f"ARM_EVIDENCE_SHA_MISMATCH:{case}")
    return owner, arm.astype(bool), {
        "receipt_sha256": _sha256_file(receipt_path),
        "evidence_file_sha256": _sha256_file(evidence_path),
        "evidence_path": evidence_path.name,
        "arm_mask_sha256": str(receipt["arm_mask_sha256"]),
        "owner_array_sha256": str(receipt["owner_array_sha256"]),
    }


def build_case_bundle(
    *,
    case: str,
    source_path: Path,
    base_dir: Path,
    candidate_path: Path,
    output_root: Path,
    expected_source_sha: str,
    expected_candidate_sha: str,
    outerwear_owner: np.ndarray | None = None,
    arm_observed: np.ndarray | None = None,
    outerwear_metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    actual_source_sha = _sha256_file(source_path)
    if actual_source_sha != expected_source_sha:
        raise CandidateBoundPhase4Hold(f"SOURCE_SHA_MISMATCH:{case}")
    source_alpha, (width, height) = _load_source_alpha(source_path)
    base_masks, base_stage = _load_base_masks(base_dir, expected_source_sha)
    with np.load(candidate_path, allow_pickle=False) as archive:
        if archive.files != ["candidate_owner"]:
            raise CandidateBoundPhase4Hold(f"CANDIDATE_SCHEMA_INVALID:{case}")
        candidate = np.asarray(archive["candidate_owner"])
    actual_candidate_sha = _sha256_bytes(candidate.tobytes(order="C"))
    if actual_candidate_sha != expected_candidate_sha:
        raise CandidateBoundPhase4Hold(f"CANDIDATE_SHA_MISMATCH:{case}")
    result, stats = integrate_candidate_masks(base_masks, candidate, source_alpha)
    arbitration_stats: dict[str, int] = {}
    if outerwear_owner is not None:
        result, arbitration_stats = integrate_outerwear_owner_evidence(
            result, outerwear_owner, source_alpha, arm_observed
        )
        stats.update(arbitration_stats)
    integration_policy = (
        "candidate-positive-garment-preserve-known-v5-outerwear-owner-integration"
        if outerwear_owner is not None
        else "candidate-positive-garment-preserve-known-v2"
    )

    phase4_dir = output_root / case / "phase_04"
    mask_dir = phase4_dir / "part_masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        _write_mask(mask_dir / f"{part}.png", result[part])
    metrics = {
        "schema": "minimalizer/local-l02/candidate-bound-phase4-metrics/v1",
        "case": case,
        "phase": 4,
        "integration_policy": integration_policy,
        "source_sha256": expected_source_sha,
        "candidate_sha256": expected_candidate_sha,
        "source_width": width,
        "source_height": height,
        "part_coverage": {part: int(mask.sum()) for part, mask in result.items()},
        **stats,
    }
    metrics_path = phase4_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outputs = {"metrics.json": _sha256_file(metrics_path)}
    outputs.update({f"part_masks/{part}.png": _sha256_file(mask_dir / f"{part}.png") for part in PARTS})
    stage = {
        "schema": "minimalizer/local-l02/candidate-bound-phase4-stage/v1",
        "phase": 4,
        "stage": "semantic_part_decomposition",
        "producer": "minimalizer-l02-candidate-bound-phase4",
        "producer_version": "1.0",
        "config": {
            "integration_policy": integration_policy,
            "candidate_labels_used_in_inference": False,
            "review_labels_used_in_inference": False,
            "unknown_policy": "unconnected-candidate-pixels-become-unknown",
            "protected_parts": list(PROTECTED_PARTS),
            "outerwear_observer_used": outerwear_owner is not None,
            "arm_observer_used_for_owner_arbitration": arm_observed is not None,
            "outerwear_observer_metadata": dict(outerwear_metadata or {}),
        },
        "source": {"path": source_path.name, "sha256": expected_source_sha, "width": width, "height": height},
        "l02_candidate": {
            "candidate_sha256": expected_candidate_sha,
            "candidate_file_sha256": _sha256_file(candidate_path),
            "candidate_key": "candidate_owner",
        },
        "inputs": {
            "source_only_stage_sha256": _sha256_file(base_dir / "stage.json"),
            "candidate_npz_sha256": _sha256_file(candidate_path),
        },
        "outputs": outputs,
        "metrics": metrics,
    }
    (phase4_dir / "stage.json").write_text(json.dumps(stage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stage


def build_bundle(
    receipt: Mapping[str, object], source_root: Path, base_root: Path,
    candidate_root: Path, output_root: Path,
    outerwear_evidence_root: Path | None = None,
) -> list[dict[str, object]]:
    if receipt.get("phase4") != "PASS":
        raise CandidateBoundPhase4Hold("PHASE4_RECEIPT_NOT_PASS")
    cases = receipt.get("cases")
    if not isinstance(cases, Mapping):
        raise CandidateBoundPhase4Hold("PHASE4_CASES_MISSING")
    stages = []
    for case in CASES:
        item = cases.get(case)
        if not isinstance(item, Mapping):
            raise CandidateBoundPhase4Hold(f"PHASE4_CASE_MISSING:{case}")
        source_path = _source_path(source_root, case)
        source_alpha, _ = _load_source_alpha(source_path)
        outerwear_owner = None
        arm_observed = None
        outerwear_metadata: Mapping[str, object] | None = None
        if outerwear_evidence_root is not None:
            outerwear_owner, arm_observed, outerwear_metadata = _load_outerwear_evidence(
                outerwear_evidence_root, case, source_alpha, str(item["source_sha256"])
            )
        stages.append(build_case_bundle(
            case=case,
            source_path=source_path,
            base_dir=base_root / case / "phase_04",
            candidate_path=_candidate_path(candidate_root, case),
            output_root=output_root,
            expected_source_sha=str(item["source_sha256"]),
            expected_candidate_sha=str(item["candidate_sha256"]),
            outerwear_owner=outerwear_owner,
            arm_observed=arm_observed,
            outerwear_metadata=outerwear_metadata,
        ))
    return stages


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--outerwear-evidence-root", type=Path)
    args = parser.parse_args()
    try:
        stages = build_bundle(
            _json(args.receipt), args.source_root, args.base_root, args.candidate_root,
            args.output_root, args.outerwear_evidence_root,
        )
        print(json.dumps({"cases": len(stages), "status": "CANDIDATE_BOUND_PHASE4_BUILT"}, ensure_ascii=False))
        return 0
    except (OSError, KeyError, json.JSONDecodeError, CandidateBoundPhase4Hold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
