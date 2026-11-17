"""Fail-closed, source-free intake audit for the L02 observer.

The audit has two mutually exclusive intake routes:

* ``checkpoint`` verifies a fixed observer specification and the SHA of its
  private weight file.
* ``training`` verifies the private Live2D SDK layout and imports a metadata-
  only, six-capability catalog.

Neither route opens images, masks, NPZ files, reviews, or H04/H06/H08 data.
Passing this audit only admits a research probe.  It never authorizes Phase4,
Phase5, owner receipt creation, or production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

# Support both ``python -m`` from the repository root and direct CLI
# invocation through ``python tools/research/<script>.py``.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.research.import_live2d_training_catalog import (
    import_training_manifest,
)
from tools.research.local_l02_observer_capability_gate import (
    ObserverCapabilityHold,
    ObserverCapabilitySpec,
    assess_observer_capability,
)
from tools.research.local_l02_observer_training_manifest import TrainingManifestHold


CHECKPOINT_SCHEMA = "minimalizer/l02/observer_checkpoint/v1"
CASES = ("H04", "H06", "H08")
SDK_FILES = {
    "core_header": Path("Core/include/Live2DCubismCore.h"),
    "windows_x64_core_library": Path("Core/lib/windows/x86_64/Live2DCubismCore.lib"),
}
SDK_DIRECTORIES = {"samples_common": Path("Samples/Common")}


class ObserverIntakeHold(ValueError):
    """Raised when an observer intake cannot be admitted."""


def _json_object(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ObserverIntakeHold(f"JSON_READ_FAILED:{path.name}") from exc
    if not isinstance(value, Mapping):
        raise ObserverIntakeHold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ObserverIntakeHold(f"FILE_READ_FAILED:{path.name}") from exc
    return digest.hexdigest()


def _text(value: Any, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise ObserverIntakeHold(f"INVALID_{field.upper()}")
    return value


def _bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise ObserverIntakeHold(f"INVALID_{field.upper()}")
    return value


def audit_checkpoint_input(spec_path: str | Path, weights_path: str | Path) -> dict[str, object]:
    """Validate a fixed source-only checkpoint without running inference."""
    spec_file = Path(spec_path)
    weight_file = Path(weights_path)
    spec = _json_object(spec_file)
    if spec.get("schema") != CHECKPOINT_SCHEMA:
        raise ObserverIntakeHold("INVALID_CHECKPOINT_SCHEMA")
    if not weight_file.is_file():
        raise ObserverIntakeHold("CHECKPOINT_WEIGHTS_MISSING")

    contract = spec.get("output_contract")
    if not isinstance(contract, list) or any(type(value) is not str for value in contract):
        raise ObserverIntakeHold("INVALID_OUTPUT_CONTRACT")
    if spec.get("source_only") is not True:
        raise ObserverIntakeHold("NON_SOURCE_ONLY_CHECKPOINT")
    if spec.get("human_labels_used_for_inference") is not False:
        raise ObserverIntakeHold("HUMAN_LABELS_IN_INFERENCE_INPUT")
    if spec.get("unknown_policy") != "separate_from_negative":
        raise ObserverIntakeHold("UNKNOWN_NOT_SEPARATE_FROM_NEGATIVE")
    same_config_cases = spec.get("same_config_cases")
    if same_config_cases != list(CASES):
        raise ObserverIntakeHold("THREE_CASE_SAME_CONFIG_NOT_DECLARED")

    expected_sha = _text(spec.get("weights_sha256"), "weights_sha256")
    actual_sha = _sha256(weight_file)
    if actual_sha != expected_sha:
        raise ObserverIntakeHold("CHECKPOINT_WEIGHTS_SHA_MISMATCH")
    capability = assess_observer_capability(
        ObserverCapabilitySpec(
            observer_id=_text(spec.get("observer_id"), "observer_id"),
            revision=_text(spec.get("revision"), "revision"),
            weights_sha256=actual_sha,
            output_contract=tuple(contract),
            source_only=True,
        )
    )
    return {
        "schema": "minimalizer/l02/observer_intake_audit/v1",
        "route": "checkpoint",
        "status": capability["status"],
        "observer_id": capability["observer_id"],
        "revision": capability["revision"],
        "weights_sha256": actual_sha,
        "output_contract": capability["observed_capabilities"],
        "missing_capabilities": capability["missing_capabilities"],
        "same_config_cases": CASES,
        "human_labels_used_for_inference": False,
        "formal_probe_allowed": capability["formal_probe_allowed"],
        "reason": capability["reason"],
        "phase4_or_production_authority": False,
    }


def audit_training_input(sdk_root: str | Path, catalog_path: str | Path) -> dict[str, object]:
    """Validate SDK presence and catalog metadata without opening data assets."""
    root = Path(sdk_root)
    catalog = Path(catalog_path)
    failures: list[str] = []
    sdk_report: dict[str, object] = {}
    for name, relative in SDK_FILES.items():
        path = root / relative
        if not path.is_file():
            failures.append(f"SDK_FILE_MISSING:{relative.as_posix()}")
            continue
        sdk_report[name] = {
            "relative_path": relative.as_posix(),
            "sha256": _sha256(path),
        }
    for name, relative in SDK_DIRECTORIES.items():
        path = root / relative
        if not path.is_dir():
            failures.append(f"SDK_DIRECTORY_MISSING:{relative.as_posix()}")
        else:
            sdk_report[name] = {"relative_path": relative.as_posix(), "present": True}

    catalog_report: dict[str, object] | None = None
    if not catalog.is_file():
        failures.append("TRAINING_CATALOG_MISSING")
    else:
        try:
            _manifest, catalog_report = import_training_manifest(catalog)
        except (OSError, TrainingManifestHold, ValueError) as exc:
            failures.append(f"TRAINING_CATALOG_HOLD:{exc}")

    return {
        "schema": "minimalizer/l02/observer_intake_audit/v1",
        "route": "training",
        "status": "TRAINING_INPUT_PASS_RESEARCH_ONLY" if not failures else "TRAINING_INPUT_HOLD",
        "failures": tuple(failures),
        "sdk": sdk_report,
        "catalog": catalog_report or {},
        "h04_h06_h08_opened": False,
        "phase4_or_production_authority": False,
    }


def _write_result(result: Mapping[str, object], output: Path | None) -> None:
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if output is not None:
        output.write_text(encoded, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def _cli() -> int:
    parser = argparse.ArgumentParser(description="L02 observer intake audit")
    subparsers = parser.add_subparsers(dest="route", required=True)

    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--spec", type=Path, required=True)
    checkpoint.add_argument("--weights", type=Path, required=True)
    checkpoint.add_argument("--output", type=Path)

    training = subparsers.add_parser("training")
    training.add_argument("--sdk-root", type=Path, required=True)
    training.add_argument("--catalog", type=Path, required=True)
    training.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        if args.route == "checkpoint":
            result = audit_checkpoint_input(args.spec, args.weights)
        else:
            result = audit_training_input(args.sdk_root, args.catalog)
    except (ObserverIntakeHold, ObserverCapabilityHold) as exc:
        result = {
            "schema": "minimalizer/l02/observer_intake_audit/v1",
            "route": args.route,
            "status": "INTAKE_HOLD",
            "failures": (str(exc),),
            "phase4_or_production_authority": False,
        }
    _write_result(result, args.output)
    return 0 if str(result["status"]).endswith("PASS_RESEARCH_ONLY") else 2


if __name__ == "__main__":
    raise SystemExit(_cli())
