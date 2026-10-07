from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import cv2

from minimalizer_zerobase.image_io import read_cv_image

from minimalizer_zerobase.core.serialization import CanonicalModel

from .contracts import (
    ArtifactOrigin,
    ArtifactParentRef,
    ArtifactRecord,
    RunManifest,
)
from .persistence import ContractBundleWriteResult, write_contract_bundle
from .policy import ProvenanceGateResult, ProvenancePolicyGate

SUPPORTED_PHASES = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
BRIDGE_VERSION = "stage-contract-bridge-v1"


class StageContractBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class StageContractBridgeResult(CanonicalModel):
    run_manifest: RunManifest
    artifacts: tuple[ArtifactRecord, ...]
    gate_result: ProvenanceGateResult
    bundle: ContractBundleWriteResult
    gate_report_path: str
    gate_report_sha256: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(raw)


def _phase_dir(case_dir: Path, phase: int) -> Path:
    return case_dir / f"phase_{phase:02d}"


def _artifact_id(phase: int, relative_path: str) -> str:
    return f"phase{phase:02d}:{relative_path}"


def _normalize_relative_path(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    drive_like = bool(pure.parts and pure.parts[0].endswith(":"))
    if (
        pure.is_absolute()
        or drive_like
        or ".." in pure.parts
        or "." in pure.parts
    ):
        raise StageContractBridgeError(
            f"unsafe stage artifact path: {relative_path!r}"
        )
    if not pure.parts:
        raise StageContractBridgeError("empty stage artifact path")
    return pure.as_posix()


def _load_stage(case_dir: Path, phase: int) -> tuple[Path, dict[str, Any]]:
    phase_dir = _phase_dir(case_dir, phase)
    stage_path = phase_dir / "stage.json"
    if not stage_path.is_file():
        raise StageContractBridgeError(
            f"missing Phase {phase} stage manifest: {stage_path}"
        )
    try:
        stage = json.loads(stage_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StageContractBridgeError(
            f"cannot read Phase {phase} stage manifest: {stage_path}"
        ) from exc
    if not isinstance(stage, dict):
        raise StageContractBridgeError(
            f"Phase {phase} stage manifest must be a JSON object"
        )
    if stage.get("phase") != phase:
        raise StageContractBridgeError(
            f"Phase {phase} manifest declares phase={stage.get('phase')!r}"
        )
    for required in (
        "stage",
        "producer",
        "producer_version",
        "source",
        "config",
        "config_sha256",
        "outputs",
    ):
        if required not in stage:
            raise StageContractBridgeError(
                f"Phase {phase} manifest missing required field {required!r}"
            )
    if not isinstance(stage["config"], dict):
        raise StageContractBridgeError(
            f"Phase {phase} config must be a JSON object"
        )
    expected_config_sha = _canonical_json_sha256(stage["config"])
    if stage["config_sha256"] != expected_config_sha:
        raise StageContractBridgeError(
            f"Phase {phase} config SHA mismatch"
        )
    if not isinstance(stage["outputs"], dict) or not stage["outputs"]:
        raise StageContractBridgeError(
            f"Phase {phase} outputs must be a non-empty object"
        )
    return phase_dir, stage


def _validate_source_contract(
    stages: dict[int, dict[str, Any]],
    source_path: Path,
) -> dict[str, Any]:
    canonical = stages[3].get("source")
    if not isinstance(canonical, dict):
        raise StageContractBridgeError("Phase 3 source contract is missing")
    required = ("path", "sha256", "width", "height")
    if any(key not in canonical for key in required):
        raise StageContractBridgeError(
            "Phase 3 source contract is incomplete"
        )

    canonical_sha = canonical["sha256"]
    canonical_width = canonical["width"]
    canonical_height = canonical["height"]
    for phase, stage in stages.items():
        source = stage.get("source")
        if not isinstance(source, dict):
            raise StageContractBridgeError(
                f"Phase {phase} source contract is missing"
            )
        if source.get("sha256") != canonical_sha:
            raise StageContractBridgeError(
                f"Phase {phase} source SHA differs from Phase 3"
            )
        if source.get("width") != canonical_width or source.get("height") != canonical_height:
            raise StageContractBridgeError(
                f"Phase {phase} source dimensions differ from Phase 3"
            )

    if not source_path.is_file():
        raise StageContractBridgeError(
            f"source file does not exist: {source_path}"
        )
    actual_sha = _sha256_file(source_path)
    if actual_sha != canonical_sha:
        raise StageContractBridgeError(
            "source file SHA does not match the canonical stage source"
        )
    source_image = read_cv_image(source_path, cv2.IMREAD_UNCHANGED)
    if source_image is None:
        raise StageContractBridgeError(
            "source file cannot be decoded as an image"
        )
    actual_height, actual_width = source_image.shape[:2]
    if (actual_width, actual_height) != (canonical_width, canonical_height):
        raise StageContractBridgeError(
            "source file dimensions do not match the canonical stage source"
        )
    return canonical


def _output_origin(relative_path: str) -> ArtifactOrigin:
    return (
        ArtifactOrigin.SEMANTIC_METADATA
        if relative_path.lower().endswith(".json")
        else ArtifactOrigin.ANALYTICAL
    )


def _output_type(relative_path: str) -> str:
    name = PurePosixPath(relative_path).name.lower()
    if name == "metrics.json":
        return "stage-metrics"
    if name == "preview.png":
        return "stage-preview"
    if "masses" in name and name.endswith(".json"):
        return "semantic-mass-data"
    if "importance" in name and name.endswith(".json"):
        return "importance-omission-data"
    if "importance_heatmap" in name:
        return "importance-heatmap"
    if name == "09_palette.json":
        return "palette-consolidation-data"
    if name == "09_palette_preview.png":
        return "palette-preview"
    if name == "09_palette_strip.png":
        return "palette-strip"
    if name == "10_geometry.json":
        return "part-aware-geometry-data"
    if name == "10_candidate_grid.png":
        return "primitive-candidate-grid"
    if name == "10_selected_primitives.png":
        return "selected-primitive-preview"
    if name == "11_composition.json":
        return "semantic-composition-scene"
    if name == "11_composed_minimal.png":
        return "semantic-composition-preview"
    if name == "11_zorder_overlay.png":
        return "semantic-zorder-overlay"
    if name == "12_simplification.json":
        return "style-simplification-data"
    if name == "12_final.png":
        return "style-simplification-final"
    if name.startswith("12_candidate_") and name.endswith(".png"):
        return "style-simplification-candidate"
    if name == "12_before.png":
        return "style-simplification-before"
    if name == "12_removed_shapes_overlay.png":
        return "style-simplification-diff-overlay"
    if name == "13_debug_board.png":
        return "stage-debug-board"
    if name == "13_stage_index.json":
        return "stage-debug-index"
    if name == "14_case_evaluation.json":
        return "evaluation-redesign-data"
    if name == "14_eval_sheet.png":
        return "evaluation-sheet"
    if name == "14_corpus_summary.json":
        return "evaluation-corpus-summary"
    if "pruned_masses" in name:
        return "pruned-mass-preview"
    if "removed_overlay" in name:
        return "omission-overlay"
    if "mass_labels" in name:
        return "mass-label-map"
    if "mass_blocks" in name:
        return "mass-preview"
    if "mass_silhouette" in name:
        return "mass-silhouette"
    if "mask" in name:
        return "analysis-mask"
    if "overlay" in name:
        return "analysis-overlay"
    if "graph" in name and name.endswith(".json"):
        return "structural-graph"
    if "bindings" in name and name.endswith(".json"):
        return "region-binding-data"
    if "labels" in name:
        return "region-label-map"
    if name.endswith(".json"):
        return "semantic-metadata"
    if name.endswith(".png"):
        return "analysis-image"
    return "stage-output"


def _dedupe_parent_refs(
    refs: list[ArtifactParentRef],
) -> tuple[ArtifactParentRef, ...]:
    by_id: dict[str, ArtifactParentRef] = {}
    for ref in refs:
        previous = by_id.get(ref.artifact_id)
        if previous is not None and previous.sha256 != ref.sha256:
            raise StageContractBridgeError(
                f"conflicting parent hashes for {ref.artifact_id}"
            )
        by_id[ref.artifact_id] = ref
    return tuple(by_id[key] for key in sorted(by_id))


def _resolve_direct_input(
    descriptor: dict[str, Any],
    source_record: ArtifactRecord,
    records: dict[str, ArtifactRecord],
) -> ArtifactParentRef:
    sha256 = descriptor.get("sha256")
    if not isinstance(sha256, str):
        raise StageContractBridgeError(
            "direct stage input descriptor must contain sha256"
        )
    if sha256 == source_record.sha256:
        return ArtifactParentRef(source_record.artifact_id, source_record.sha256)

    candidates = [
        record
        for record in records.values()
        if record.sha256 == sha256
    ]
    if not candidates:
        raise StageContractBridgeError(
            f"direct stage input hash cannot be resolved: {sha256}"
        )

    declared_path = descriptor.get("path")
    if isinstance(declared_path, str):
        declared_name = PurePosixPath(
            declared_path.replace("\\", "/")
        ).name
        path_matches = [
            record
            for record in candidates
            if PurePosixPath(
                str(record.metadata.get("relative_path", ""))
            ).name == declared_name
        ]
        if path_matches:
            candidates = path_matches

    chosen = sorted(candidates, key=lambda record: record.artifact_id)[0]
    return ArtifactParentRef(chosen.artifact_id, chosen.sha256)


def _resolve_stage_inputs(
    phase: int,
    stage: dict[str, Any],
    source_record: ArtifactRecord,
    records: dict[str, ArtifactRecord],
) -> tuple[ArtifactParentRef, ...]:
    if phase == 3:
        return (
            ArtifactParentRef(
                source_record.artifact_id,
                source_record.sha256,
            ),
        )

    raw_inputs = stage.get("inputs")
    if not isinstance(raw_inputs, dict) or not raw_inputs:
        raise StageContractBridgeError(
            f"Phase {phase} must declare upstream inputs"
        )

    refs: list[ArtifactParentRef] = []
    for group_name, group in sorted(raw_inputs.items()):
        if not isinstance(group, dict):
            raise StageContractBridgeError(
                f"Phase {phase} input group {group_name!r} must be an object"
            )

        if group_name.startswith("phase") and group_name[5:].isdigit():
            upstream_phase = int(group_name[5:])
            if upstream_phase >= phase:
                raise StageContractBridgeError(
                    f"Phase {phase} cannot depend on Phase {upstream_phase}"
                )
            for relative_path, expected_sha in sorted(group.items()):
                if not isinstance(expected_sha, str):
                    raise StageContractBridgeError(
                        f"Phase {phase} input hash for {relative_path!r} must be a string"
                    )
                normalized = _normalize_relative_path(relative_path)
                artifact_id = _artifact_id(upstream_phase, normalized)
                record = records.get(artifact_id)
                if record is None:
                    raise StageContractBridgeError(
                        f"Phase {phase} input does not resolve: {artifact_id}"
                    )
                if record.sha256 != expected_sha:
                    raise StageContractBridgeError(
                        f"Phase {phase} input SHA mismatch for {artifact_id}"
                    )
                refs.append(ArtifactParentRef(record.artifact_id, record.sha256))
            continue

        refs.append(
            _resolve_direct_input(group, source_record, records)
        )

    if not refs:
        raise StageContractBridgeError(
            f"Phase {phase} resolved no upstream inputs"
        )
    return _dedupe_parent_refs(refs)


def _verify_and_record_stage(
    phase: int,
    phase_dir: Path,
    stage: dict[str, Any],
    source_record: ArtifactRecord,
    parent_refs: tuple[ArtifactParentRef, ...],
) -> tuple[ArtifactRecord, tuple[ArtifactRecord, ...]]:
    producer = str(stage["producer"])
    producer_version = str(stage["producer_version"])
    config_sha256 = str(stage["config_sha256"])

    output_records: list[ArtifactRecord] = []
    for raw_relative_path, expected_sha in sorted(stage["outputs"].items()):
        if not isinstance(expected_sha, str):
            raise StageContractBridgeError(
                f"Phase {phase} output hash must be a string"
            )
        relative_path = _normalize_relative_path(raw_relative_path)
        artifact_path = phase_dir.joinpath(*PurePosixPath(relative_path).parts)
        if not artifact_path.is_file():
            raise StageContractBridgeError(
                f"Phase {phase} output is missing: {relative_path}"
            )
        actual_sha = _sha256_file(artifact_path)
        if actual_sha != expected_sha:
            raise StageContractBridgeError(
                f"Phase {phase} output SHA mismatch: {relative_path}"
            )
        output_records.append(
            ArtifactRecord(
                artifact_id=_artifact_id(phase, relative_path),
                artifact_type=_output_type(relative_path),
                stage=f"phase{phase:02d}",
                sha256=actual_sha,
                origin=_output_origin(relative_path),
                parents=parent_refs,
                visible=False,
                source_refs=(source_record.artifact_id,),
                metadata={
                    "relative_path": relative_path,
                    "producer": producer,
                    "producer_version": producer_version,
                    "config_sha256": config_sha256,
                    "declared_output": True,
                },
            )
        )

    stage_path = phase_dir / "stage.json"
    stage_record = ArtifactRecord(
        artifact_id=_artifact_id(phase, "stage.json"),
        artifact_type="stage-manifest",
        stage=f"phase{phase:02d}",
        sha256=_sha256_file(stage_path),
        origin=ArtifactOrigin.SEMANTIC_METADATA,
        parents=parent_refs,
        visible=False,
        source_refs=(source_record.artifact_id,),
        metadata={
            "relative_path": "stage.json",
            "stage_name": stage["stage"],
            "producer": producer,
            "producer_version": producer_version,
            "config_sha256": config_sha256,
        },
    )
    return stage_record, tuple(output_records)


def bridge_stage_contracts(
    case_dir: str | Path,
    source_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    max_phase: int = 6,
) -> StageContractBridgeResult:
    case_dir = Path(case_dir)
    source_path = Path(source_path)
    if not case_dir.is_dir():
        raise StageContractBridgeError(
            f"case directory does not exist: {case_dir}"
        )

    if max_phase not in SUPPORTED_PHASES or max_phase < 6:
        raise StageContractBridgeError(
            f"unsupported max_phase={max_phase}; expected a supported phase from 6 through 14"
        )
    selected_phases = tuple(
        phase for phase in SUPPORTED_PHASES if phase <= max_phase
    )
    loaded: dict[int, tuple[Path, dict[str, Any]]] = {
        phase: _load_stage(case_dir, phase)
        for phase in selected_phases
    }
    stages = {phase: stage for phase, (_, stage) in loaded.items()}
    source_contract = _validate_source_contract(stages, source_path)

    source_record = ArtifactRecord(
        artifact_id="source",
        artifact_type="source-image",
        stage="input",
        sha256=source_contract["sha256"],
        origin=ArtifactOrigin.SOURCE_PIXEL,
        visible=False,
        source_refs=("source",),
        metadata={
            "declared_path": source_contract["path"],
            "verification": "sha256+dimensions",
            "width": source_contract["width"],
            "height": source_contract["height"],
        },
    )

    records: dict[str, ArtifactRecord] = {
        source_record.artifact_id: source_record
    }
    stage_records: list[ArtifactRecord] = []
    phase_config_shas: dict[str, str] = {}

    for phase in selected_phases:
        phase_dir, stage = loaded[phase]
        parent_refs = _resolve_stage_inputs(
            phase,
            stage,
            source_record,
            records,
        )
        stage_record, output_records = _verify_and_record_stage(
            phase,
            phase_dir,
            stage,
            source_record,
            parent_refs,
        )
        for record in (*output_records, stage_record):
            if record.artifact_id in records:
                raise StageContractBridgeError(
                    f"duplicate bridged artifact ID: {record.artifact_id}"
                )
            records[record.artifact_id] = record
        stage_records.append(stage_record)
        phase_config_shas[f"phase{phase:02d}"] = stage["config_sha256"]

    run_manifest = RunManifest(
        run_id=f"{case_dir.name}:phase03-{max_phase:02d}",
        source_path=str(source_contract["path"]),
        source_sha256=source_record.sha256,
        source_width=int(source_contract["width"]),
        source_height=int(source_contract["height"]),
        pipeline_name="minimalizer-zerobase2",
        pipeline_version=BRIDGE_VERSION,
        config_sha256=_canonical_json_sha256(phase_config_shas),
        stage_manifest_refs=tuple(
            ArtifactParentRef(record.artifact_id, record.sha256)
            for record in stage_records
        ),
    )

    artifacts = tuple(records.values())
    gate_result = ProvenancePolicyGate().evaluate(
        run_manifest,
        artifacts,
    )
    if not gate_result.passed:
        details = "; ".join(
            f"{item.code}:{item.artifact_id or '-'}"
            for item in gate_result.violations
        )
        raise StageContractBridgeError(
            f"provenance policy gate failed: {details}"
        )

    target_dir = (
        Path(output_dir)
        if output_dir is not None
        else case_dir / "artifact_contract"
    )
    bundle = write_contract_bundle(
        target_dir,
        run_manifest,
        artifacts,
    )

    gate_path = target_dir / "provenance_gate.json"
    gate_payload = (gate_result.to_json() + "\n").encode("utf-8")
    gate_path.write_bytes(gate_payload)

    return StageContractBridgeResult(
        run_manifest=run_manifest,
        artifacts=tuple(
            sorted(artifacts, key=lambda item: item.artifact_id)
        ),
        gate_result=gate_result,
        bundle=bundle,
        gate_report_path=gate_path.name,
        gate_report_sha256=_sha256_bytes(gate_payload),
    )
