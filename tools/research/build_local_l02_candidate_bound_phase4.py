"""Build a candidate-bound Phase 4 part bundle from private research inputs.

This is a source-free-code entry point: source pixels, candidate arrays and
generated masks stay outside Git.  It deliberately does not use review labels.
The candidate is treated as positive garment evidence, not as permission to
replace an existing semantic owner. Protected and already-known semantic
parts are never overwritten; only candidate pixels in unknown space can be
promoted when their 8-connected component touches a clothing context.
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


def _write_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path)


def build_case_bundle(
    *,
    case: str,
    source_path: Path,
    base_dir: Path,
    candidate_path: Path,
    output_root: Path,
    expected_source_sha: str,
    expected_candidate_sha: str,
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

    phase4_dir = output_root / case / "phase_04"
    mask_dir = phase4_dir / "part_masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        _write_mask(mask_dir / f"{part}.png", result[part])
    metrics = {
        "schema": "minimalizer/local-l02/candidate-bound-phase4-metrics/v1",
        "case": case,
        "phase": 4,
        "integration_policy": "candidate-positive-garment-preserve-known-v2",
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
            "integration_policy": "candidate-positive-garment-preserve-known-v2",
            "candidate_labels_used_in_inference": False,
            "review_labels_used_in_inference": False,
            "unknown_policy": "unconnected-candidate-pixels-become-unknown",
            "protected_parts": list(PROTECTED_PARTS),
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
        stages.append(build_case_bundle(
            case=case,
            source_path=_source_path(source_root, case),
            base_dir=base_root / case / "phase_04",
            candidate_path=_candidate_path(candidate_root, case),
            output_root=output_root,
            expected_source_sha=str(item["source_sha256"]),
            expected_candidate_sha=str(item["candidate_sha256"]),
        ))
    return stages


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        stages = build_bundle(_json(args.receipt), args.source_root, args.base_root, args.candidate_root, args.output_root)
        print(json.dumps({"cases": len(stages), "status": "CANDIDATE_BOUND_PHASE4_BUILT"}, ensure_ascii=False))
        return 0
    except (OSError, KeyError, json.JSONDecodeError, CandidateBoundPhase4Hold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
