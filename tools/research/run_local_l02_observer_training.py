"""Run a private separate-character observer training job and freeze its checkpoint.

This command consumes only a metadata catalog and a private SDK/trainer.  It
creates a temporary training feed containing train/validation samples only;
H04/H06/H08 holdout rows and their annotation URIs are deliberately omitted
from the trainer process.  The resulting spec and weights are immediately
checked by the fixed-checkpoint intake audit.  No source image, annotation,
mask, or NPZ is opened by this module.
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
from typing import Any, Mapping

from tools.research.audit_local_l02_observer_intake import (
    audit_checkpoint_input,
    audit_training_input,
)


SCHEMA = "minimalizer/local-l02/observer-training/v1"
TRAINING_FEED_SCHEMA = "minimalizer/local-l02/observer-training-input/v1"
HOLDOUT_CASES = ("H04", "H06", "H08")


class ObserverTrainingHold(ValueError):
    """Raised when a private training run cannot be admitted or frozen."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise ObserverTrainingHold(f"FILE_READ_FAILED:{path.name}") from exc


def _load_object(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ObserverTrainingHold(f"CATALOG_READ_FAILED:{path.name}") from exc
    if not isinstance(value, Mapping):
        raise ObserverTrainingHold("CATALOG_ROOT_NOT_OBJECT")
    return value


def _write_training_feed(catalog: Path, destination: Path) -> str:
    raw = _load_object(catalog)
    samples = raw.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ObserverTrainingHold("CATALOG_SAMPLES_MISSING")
    feed_samples: list[Mapping[str, Any]] = []
    for sample in samples:
        if not isinstance(sample, Mapping):
            raise ObserverTrainingHold("CATALOG_SAMPLE_INVALID")
        case_id = sample.get("case_id")
        split = sample.get("split")
        if case_id in HOLDOUT_CASES or split == "holdout":
            continue
        if split not in {"train", "validation"}:
            raise ObserverTrainingHold("NON_HOLDOUT_SAMPLE_SPLIT_INVALID")
        feed_samples.append(sample)
    if not feed_samples:
        raise ObserverTrainingHold("TRAINING_FEED_EMPTY")
    if any(sample.get("case_id") in HOLDOUT_CASES for sample in feed_samples):
        raise ObserverTrainingHold("HOLDOUT_LEAK_IN_TRAINING_FEED")
    feed = {
        "schema": TRAINING_FEED_SCHEMA,
        "source_artifacts_private": True,
        "human_labels_used_for_inference": False,
        "holdout_cases_excluded": list(HOLDOUT_CASES),
        "samples": feed_samples,
    }
    encoded = (json.dumps(feed, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    destination.write_bytes(encoded)
    return _sha256_bytes(encoded)


def _run_trainer(
    *,
    trainer: Path,
    trainer_kind: str,
    sdk_root: Path,
    training_feed: Path,
    spec_output: Path,
    weights_output: Path,
    timeout_seconds: int,
) -> None:
    if trainer_kind not in {"python", "executable"}:
        raise ObserverTrainingHold("INVALID_TRAINER_KIND")
    command = ([sys.executable, str(trainer)] if trainer_kind == "python" else [str(trainer)]) + [
        "--sdk-root",
        str(sdk_root),
        "--training-input",
        str(training_feed),
        "--output-spec",
        str(spec_output),
        "--output-weights",
        str(weights_output),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ObserverTrainingHold("TRAINER_EXECUTION_FAILED") from exc
    if completed.returncode != 0:
        raise ObserverTrainingHold(f"TRAINER_FAILED:{completed.returncode}")
    if not spec_output.is_file() or not weights_output.is_file():
        raise ObserverTrainingHold("TRAINER_OUTPUT_MISSING")


def run_training(
    *,
    sdk_root: Path,
    catalog: Path,
    trainer: Path,
    output_dir: Path,
    receipt: Path,
    trainer_kind: str = "python",
    timeout_seconds: int = 7200,
) -> dict[str, object]:
    """Train on non-holdout characters and freeze an intake-admissible checkpoint."""
    intake = audit_training_input(sdk_root, catalog)
    if intake.get("status") != "TRAINING_INPUT_PASS_RESEARCH_ONLY":
        raise ObserverTrainingHold("TRAINING_INPUT_HOLD")
    if not trainer.is_file():
        raise ObserverTrainingHold("TRAINER_MISSING")
    if receipt.exists():
        raise ObserverTrainingHold("REFUSE_OVERWRITE_RECEIPT")
    output_dir.mkdir(parents=True, exist_ok=True)
    final_spec = output_dir / "observer_spec.json"
    final_weights = output_dir / "observer_weights.bin"
    if final_spec.exists() or final_weights.exists():
        raise ObserverTrainingHold("REFUSE_OVERWRITE_CHECKPOINT")

    catalog_sha256 = _sha256_file(catalog)
    trainer_sha256 = _sha256_file(trainer)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="minimalizer-l02-training-", dir=output_dir.parent) as temp:
        temp_dir = Path(temp)
        feed = temp_dir / "training-input.json"
        feed_sha256 = _write_training_feed(catalog, feed)
        temp_spec = temp_dir / "observer_spec.json"
        temp_weights = temp_dir / "observer_weights.bin"
        _run_trainer(
            trainer=trainer,
            trainer_kind=trainer_kind,
            sdk_root=sdk_root,
            training_feed=feed,
            spec_output=temp_spec,
            weights_output=temp_weights,
            timeout_seconds=timeout_seconds,
        )
        checkpoint = audit_checkpoint_input(temp_spec, temp_weights)
        if checkpoint.get("formal_probe_allowed") is not True:
            raise ObserverTrainingHold("CHECKPOINT_CAPABILITY_HOLD")
        shutil.copyfile(temp_spec, final_spec)
        shutil.copyfile(temp_weights, final_weights)

    result: dict[str, object] = {
        "schema": SCHEMA,
        "status": "TRAINING_CHECKPOINT_FROZEN_RESEARCH_ONLY",
        "catalog_sha256": catalog_sha256,
        "training_feed_sha256": feed_sha256,
        "trainer_sha256": trainer_sha256,
        "observer_id": checkpoint["observer_id"],
        "revision": checkpoint["revision"],
        "weights_sha256": checkpoint["weights_sha256"],
        "output_contract": checkpoint["output_contract"],
        "same_config_cases": list(HOLDOUT_CASES),
        "holdout_excluded_from_trainer_feed": list(HOLDOUT_CASES),
        "human_labels_used_for_holdout_inference": False,
        "phase4": "HOLD",
        "phase5": "NO_GO",
        "golden": "HOLD",
        "production": "NO_GO",
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Run a private L02 observer training job")
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--trainer", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--trainer-kind", choices=("python", "executable"), default="python")
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = run_training(
            sdk_root=args.sdk_root,
            catalog=args.catalog,
            trainer=args.trainer,
            output_dir=args.output_dir,
            receipt=args.receipt,
            trainer_kind=args.trainer_kind,
            timeout_seconds=args.timeout_seconds,
        )
    except (OSError, ObserverTrainingHold) as exc:
        print(json.dumps({"status": "TRAINING_HOLD", "failure": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
