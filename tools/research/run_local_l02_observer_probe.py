"""Run and freeze a source-only six-capability observer probe.

The checkpoint intake audit only checks metadata and weights.  This runner is
the next concrete step: it executes one fixed adapter against H04/H06/H08,
never accepts review masks or owner arrays as inputs, validates the complete
evidence contract, and writes private NPZ outputs plus a source-free receipt.
The receipt is research-only; it cannot authorize Phase4, Phase5, Golden, or
production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping

import numpy as np
from PIL import Image

from tools.research.audit_local_l02_observer_intake import audit_checkpoint_input
from tools.research.local_l02_observer_evidence_contract import (
    ObserverEvidenceHold,
    PairwiseRelationObservation,
    RoleObservation,
    ScalarObservation,
    assess_observer_evidence,
)
from tools.research.verify_local_l02_phase4_receipt import (
    CASES,
    SOURCE_SHA256,
)


SCHEMA = "minimalizer/local-l02/observer-probe/v1"
ROLE_KEYS = {
    "outerwear": ("outerwear_mask", "outerwear_unknown"),
    "underlayer": ("underlayer_mask", "underlayer_unknown"),
    "sleeve": ("sleeve_mask", "sleeve_unknown"),
    "arm": ("arm_mask", "arm_unknown"),
}
RELATION_KEYS = (
    ("outerwear", "underlayer", "occlusion_outerwear_underlayer"),
    ("sleeve", "arm", "occlusion_sleeve_arm"),
    ("garment", "body", "occlusion_garment_body"),
)
OUTPUT_KEYS = frozenset(
    {
        *(key for pair in ROLE_KEYS.values() for key in pair),
        *(key for _, _, key in RELATION_KEYS),
        "instance_grouping",
    }
)


class ObserverProbeHold(ValueError):
    """Raised when a probe cannot be frozen safely."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise ObserverProbeHold(f"FILE_READ_FAILED:{path.name}") from exc


def _sha256_array(value: np.ndarray) -> str:
    return _sha256_bytes(np.ascontiguousarray(value).tobytes(order="C"))


def _load_signed_alpha(case: str, path: Path) -> tuple[np.ndarray, str]:
    expected = SOURCE_SHA256[case]
    raw = path.read_bytes()
    actual = _sha256_bytes(raw)
    if actual != expected:
        raise ObserverProbeHold(f"SIGNED_SOURCE_SHA_MISMATCH:{case}")
    try:
        with Image.open(path) as image:
            rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    except (OSError, ValueError) as exc:
        raise ObserverProbeHold(f"SOURCE_DECODE_FAILED:{case}") from exc
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ObserverProbeHold(f"SOURCE_RGBA_INVALID:{case}")
    return rgba[:, :, 3] > 0, actual


def _load_output_bundle(
    *, case: str, output: Path, source_alpha: np.ndarray, observer_id: str
) -> dict[str, str | tuple[str, ...] | tuple[int, int]]:
    try:
        with np.load(output, allow_pickle=False) as raw:
            if frozenset(raw.files) != OUTPUT_KEYS:
                raise ObserverProbeHold(f"OUTPUT_KEYS_MISMATCH:{case}")
            arrays = {key: raw[key] for key in raw.files}
    except ObserverProbeHold:
        raise
    except (OSError, ValueError, KeyError) as exc:
        raise ObserverProbeHold(f"OUTPUT_READ_FAILED:{case}") from exc

    role_observations = tuple(
        RoleObservation(
            role,
            arrays[mask_key],
            _sha256_array(arrays[mask_key]),
            observer_id,
            arrays[unknown_key],
        )
        for role, (mask_key, unknown_key) in ROLE_KEYS.items()
    )
    relations = tuple(
        PairwiseRelationObservation(
            role_a,
            role_b,
            arrays[key],
            _sha256_array(arrays[key]),
            observer_id,
        )
        for role_a, role_b, key in RELATION_KEYS
    )
    grouping = ScalarObservation(
        "instance_grouping",
        arrays["instance_grouping"],
        _sha256_array(arrays["instance_grouping"]),
        observer_id,
    )
    try:
        assessment = assess_observer_evidence(
            source_alpha=source_alpha,
            role_observations=role_observations,
            occlusion_relation=relations,
            instance_grouping=grouping,
        )
    except ObserverEvidenceHold as exc:
        raise ObserverProbeHold(f"EVIDENCE_CONTRACT_HOLD:{case}:{exc}") from exc
    if assessment.status != "CAPABILITY_PASS_RESEARCH_ONLY":
        raise ObserverProbeHold(f"EVIDENCE_CONTRACT_HOLD:{case}")
    return {
        "shape": tuple(int(value) for value in source_alpha.shape),
        "array_sha256": tuple(
            f"{key}={_sha256_array(arrays[key])}" for key in sorted(OUTPUT_KEYS)
        ),
        "observed_capabilities": assessment.observed_capabilities,
    }


def _config_digest(
    *, observer_id: str, revision: str, weights_sha256: str, adapter_sha256: str
) -> str:
    payload = {
        "adapter_sha256": adapter_sha256,
        "adapter_protocol": "minimalizer-local-l02-observer-adapter/v1",
        "observer_id": observer_id,
        "revision": revision,
        "weights_sha256": weights_sha256,
        "same_config_cases": list(CASES),
    }
    return _sha256_bytes(
        (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    )


def run_probe(
    *,
    spec: Path,
    weights: Path,
    adapter: Path,
    sources: Mapping[str, Path],
    output_dir: Path,
    receipt: Path,
    adapter_kind: str = "python",
    timeout_seconds: int = 1800,
) -> dict[str, object]:
    """Run the fixed adapter on all three signed sources and freeze results."""
    intake = audit_checkpoint_input(spec, weights)
    if intake.get("formal_probe_allowed") is not True:
        raise ObserverProbeHold("CHECKPOINT_CAPABILITY_HOLD")
    if adapter_kind not in {"python", "executable"}:
        raise ObserverProbeHold("INVALID_ADAPTER_KIND")
    if not adapter.is_file():
        raise ObserverProbeHold("ADAPTER_MISSING")
    if tuple(sources) != CASES:
        raise ObserverProbeHold("THREE_CASE_SOURCE_SET_INVALID")
    if receipt.exists():
        raise ObserverProbeHold("REFUSE_OVERWRITE_RECEIPT")
    output_dir.mkdir(parents=True, exist_ok=True)
    final_outputs = {case: output_dir / f"{case}_observer_output.npz" for case in CASES}
    if any(path.exists() for path in final_outputs.values()):
        raise ObserverProbeHold("REFUSE_OVERWRITE_PRIVATE_OUTPUT")

    adapter_sha256 = _sha256_file(adapter)
    observer_id = str(intake["observer_id"])
    revision = str(intake["revision"])
    weights_sha256 = str(intake["weights_sha256"])
    config_digest = _config_digest(
        observer_id=observer_id,
        revision=revision,
        weights_sha256=weights_sha256,
        adapter_sha256=adapter_sha256,
    )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="minimalizer-l02-probe-", dir=output_dir.parent) as temp:
        temp_dir = Path(temp)
        cases: dict[str, object] = {}
        for case in CASES:
            source = Path(sources[case])
            alpha, source_sha256 = _load_signed_alpha(case, source)
            temp_output = temp_dir / f"{case}.npz"
            common = [
                "--source",
                str(source),
                "--spec",
                str(spec),
                "--weights",
                str(weights),
                "--output",
                str(temp_output),
                "--case",
                case,
            ]
            command = ([sys.executable, str(adapter)] if adapter_kind == "python" else [str(adapter)]) + common
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ObserverProbeHold(f"ADAPTER_EXECUTION_FAILED:{case}") from exc
            if completed.returncode != 0:
                raise ObserverProbeHold(f"ADAPTER_FAILED:{case}:{completed.returncode}")
            if not temp_output.is_file():
                raise ObserverProbeHold(f"ADAPTER_OUTPUT_MISSING:{case}")
            bundle = _load_output_bundle(
                case=case,
                output=temp_output,
                source_alpha=alpha,
                observer_id=observer_id,
            )
            cases[case] = {
                "source_sha256": source_sha256,
                "source_shape": bundle["shape"],
                "output_npz_sha256": _sha256_file(temp_output),
                "array_sha256": bundle["array_sha256"],
                "observed_capabilities": bundle["observed_capabilities"],
                "inference_config_sha256": config_digest,
            }
        for case in CASES:
            shutil.copyfile(temp_dir / f"{case}.npz", final_outputs[case])

    result: dict[str, object] = {
        "schema": SCHEMA,
        "status": "PROBE_FROZEN_RESEARCH_ONLY",
        "observer_id": observer_id,
        "revision": revision,
        "weights_sha256": weights_sha256,
        "adapter_sha256": adapter_sha256,
        "inference_config_sha256": config_digest,
        "same_config_cases": list(CASES),
        "human_labels_used_for_inference": False,
        "owner_arrays_used_for_inference": False,
        "unknown_policy": "separate_from_negative",
        "cases": cases,
        "phase4": "HOLD",
        "phase5": "NO_GO",
        "golden": "HOLD",
        "production": "NO_GO",
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Run a fixed source-only L02 observer probe")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--h04", type=Path, required=True)
    parser.add_argument("--h06", type=Path, required=True)
    parser.add_argument("--h08", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--adapter-kind", choices=("python", "executable"), default="python")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    try:
        result = run_probe(
            spec=args.spec,
            weights=args.weights,
            adapter=args.adapter,
            sources={"H04": args.h04, "H06": args.h06, "H08": args.h08},
            output_dir=args.output_dir,
            receipt=args.receipt,
            adapter_kind=args.adapter_kind,
            timeout_seconds=args.timeout_seconds,
        )
    except (OSError, ObserverProbeHold) as exc:
        print(json.dumps({"status": "PROBE_HOLD", "failure": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
