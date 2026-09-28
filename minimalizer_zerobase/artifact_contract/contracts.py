from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from minimalizer_zerobase import SCHEMA_VERSION
from minimalizer_zerobase.core.serialization import CanonicalModel

_SHA256_HEX_LENGTH = 64


def _validate_sha256(name: str, value: str) -> None:
    if len(value) != _SHA256_HEX_LENGTH:
        raise ValueError(f"{name} must be a 64-character SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc


class ArtifactOrigin(str, Enum):
    SOURCE_PIXEL = "source_pixel"
    ANALYTICAL = "analytical"
    GEOMETRIC_DERIVATION = "geometric_derivation"
    SEMANTIC_METADATA = "semantic_metadata"
    SYNTHESIZED = "synthesized"
    UNKNOWN = "unknown"


class PartState(str, Enum):
    PRESENT = "present"
    ABSENT_BY_DESIGN = "absent_by_design"
    NOT_VISIBLE_IN_SOURCE = "not_visible_in_source"
    NOT_DETECTED = "not_detected"
    AMBIGUOUS = "ambiguous"
    QA_DROPPED = "qa_dropped"


@dataclass(frozen=True)
class ArtifactParentRef(CanonicalModel):
    artifact_id: str
    sha256: str

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id is required")
        _validate_sha256("parent sha256", self.sha256)


@dataclass(frozen=True)
class ArtifactRecord(CanonicalModel):
    artifact_id: str
    artifact_type: str
    stage: str
    sha256: str
    origin: ArtifactOrigin
    parents: tuple[ArtifactParentRef, ...] = ()
    visible: bool = False
    source_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id is required")
        if not self.artifact_type:
            raise ValueError("artifact_type is required")
        if not self.stage:
            raise ValueError("stage is required")
        _validate_sha256("artifact sha256", self.sha256)
        if not isinstance(self.origin, ArtifactOrigin):
            raise ValueError("origin must be an ArtifactOrigin")
        parent_ids = tuple(parent.artifact_id for parent in self.parents)
        if len(parent_ids) != len(set(parent_ids)):
            raise ValueError("artifact parents must be unique")
        if self.artifact_id in parent_ids:
            raise ValueError("artifact cannot be its own parent")


@dataclass(frozen=True)
class SemanticPartState(CanonicalModel):
    part_id: str
    state: PartState
    artifact_ids: tuple[str, ...] = ()
    confidence: float | None = None
    reason: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.part_id:
            raise ValueError("part_id is required")
        if not isinstance(self.state, PartState):
            raise ValueError("state must be a PartState")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("part confidence must be within [0, 1]")
        if self.state == PartState.PRESENT and not self.artifact_ids:
            raise ValueError("present part state requires at least one artifact")
        artifact_free_states = {
            PartState.ABSENT_BY_DESIGN,
            PartState.NOT_VISIBLE_IN_SOURCE,
            PartState.NOT_DETECTED,
        }
        if self.state in artifact_free_states and self.artifact_ids:
            raise ValueError("absence state must not claim materialized artifacts")


@dataclass(frozen=True)
class RunPolicy(CanonicalModel):
    visible_artifact_policy: str = "observed-only"
    allow_generative_pixels: bool = False
    allow_inpainting: bool = False
    allow_img2img: bool = False
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.visible_artifact_policy != "observed-only":
            raise ValueError("unsupported visible_artifact_policy")


@dataclass(frozen=True)
class RunManifest(CanonicalModel):
    run_id: str
    source_path: str
    source_sha256: str
    source_width: int
    source_height: int
    pipeline_name: str
    pipeline_version: str
    config_sha256: str
    policy: RunPolicy = field(default_factory=RunPolicy)
    stage_manifest_refs: tuple[ArtifactParentRef, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id is required")
        if not self.source_path:
            raise ValueError("source_path is required")
        _validate_sha256("source_sha256", self.source_sha256)
        _validate_sha256("config_sha256", self.config_sha256)
        if self.source_width <= 0 or self.source_height <= 0:
            raise ValueError("source dimensions must be positive")
        if not self.pipeline_name or not self.pipeline_version:
            raise ValueError("pipeline name/version are required")
        stage_ids = tuple(ref.artifact_id for ref in self.stage_manifest_refs)
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("stage manifest refs must be unique")


@dataclass(frozen=True)
class ArtifactManifest(CanonicalModel):
    run_id: str
    artifacts: tuple[ArtifactRecord, ...]
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id is required")
        artifact_ids = tuple(record.artifact_id for record in self.artifacts)
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("artifact manifest requires unique artifact ids")
