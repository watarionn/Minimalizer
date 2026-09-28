from __future__ import annotations

import json

import pytest

from minimalizer_zerobase.artifact_contract import (
    ArtifactManifest,
    ArtifactOrigin,
    ArtifactParentRef,
    ArtifactRecord,
    PartState,
    ProvenancePolicyGate,
    RunManifest,
    RunPolicy,
    SemanticPartState,
    write_contract_bundle,
)

SOURCE_SHA = "1" * 64
CONFIG_SHA = "2" * 64
ANALYSIS_SHA = "3" * 64
GEOMETRY_SHA = "4" * 64
OTHER_SHA = "5" * 64


def _manifest(policy: RunPolicy | None = None) -> RunManifest:
    return RunManifest(
        run_id="run-001",
        source_path="source.png",
        source_sha256=SOURCE_SHA,
        source_width=128,
        source_height=96,
        pipeline_name="zerobase2",
        pipeline_version="artifact-contract-foundation-1",
        config_sha256=CONFIG_SHA,
        policy=policy or RunPolicy(),
    )


def _source() -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id="source",
        artifact_type="source-image",
        stage="input",
        sha256=SOURCE_SHA,
        origin=ArtifactOrigin.SOURCE_PIXEL,
    )


def _analysis() -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id="subject-mask",
        artifact_type="analysis-mask",
        stage="phase03",
        sha256=ANALYSIS_SHA,
        origin=ArtifactOrigin.ANALYTICAL,
        parents=(ArtifactParentRef("source", SOURCE_SHA),),
    )


def _visible_geometry() -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id="primitive-001",
        artifact_type="primitive",
        stage="phase10",
        sha256=GEOMETRY_SHA,
        origin=ArtifactOrigin.GEOMETRIC_DERIVATION,
        parents=(
            ArtifactParentRef("source", SOURCE_SHA),
            ArtifactParentRef("subject-mask", ANALYSIS_SHA),
        ),
        visible=True,
    )


def test_contract_models_serialize_enum_values_canonically() -> None:
    payload = _manifest().to_dict()
    assert payload["policy"]["visible_artifact_policy"] == "observed-only"
    assert payload["policy"]["allow_generative_pixels"] is False

    record = _visible_geometry()
    encoded = json.loads(record.to_json())
    assert encoded["origin"] == "geometric_derivation"
    assert encoded["visible"] is True


def test_semantic_part_state_distinguishes_absence_from_present() -> None:
    present = SemanticPartState(
        part_id="face",
        state=PartState.PRESENT,
        artifact_ids=("phase04:part_masks/face.png",),
        confidence=0.95,
    )
    hidden = SemanticPartState(
        part_id="right_arm",
        state=PartState.NOT_VISIBLE_IN_SOURCE,
        reason="fully occluded in observed source",
    )
    dropped = SemanticPartState(
        part_id="face",
        state=PartState.QA_DROPPED,
        artifact_ids=("candidate-face-artifact",),
        reason="failed structural QA",
    )
    assert present.to_dict()["state"] == "present"
    assert hidden.to_dict()["state"] == "not_visible_in_source"
    assert dropped.to_dict()["artifact_ids"] == ["candidate-face-artifact"]

    with pytest.raises(ValueError):
        SemanticPartState(part_id="face", state=PartState.PRESENT)
    with pytest.raises(ValueError):
        SemanticPartState(
            part_id="face",
            state=PartState.NOT_DETECTED,
            artifact_ids=("unexpected-visible-artifact",),
        )


def test_observed_only_gate_accepts_source_derived_visible_artifact() -> None:
    result = ProvenancePolicyGate().evaluate(
        _manifest(),
        (_source(), _analysis(), _visible_geometry()),
    )
    assert result.passed is True
    assert result.violations == ()


@pytest.mark.parametrize(
    "origin",
    (ArtifactOrigin.SYNTHESIZED, ArtifactOrigin.UNKNOWN),
)
def test_observed_only_gate_rejects_forbidden_visible_origin(origin) -> None:
    record = ArtifactRecord(
        artifact_id="bad-visible",
        artifact_type="render-fragment",
        stage="phase10",
        sha256=OTHER_SHA,
        origin=origin,
        parents=(ArtifactParentRef("source", SOURCE_SHA),),
        visible=True,
    )
    result = ProvenancePolicyGate().evaluate(_manifest(), (_source(), record))
    codes = {item.code for item in result.violations}
    assert result.passed is False
    assert "invalid-visible-origin" in codes
    assert "forbidden-visible-lineage" in codes


def test_observed_only_gate_rejects_visible_geometry_without_source_lineage() -> None:
    analysis = ArtifactRecord(
        artifact_id="analysis-only",
        artifact_type="analysis-mask",
        stage="phase03",
        sha256=ANALYSIS_SHA,
        origin=ArtifactOrigin.ANALYTICAL,
    )
    visible = ArtifactRecord(
        artifact_id="derived",
        artifact_type="primitive",
        stage="phase10",
        sha256=GEOMETRY_SHA,
        origin=ArtifactOrigin.GEOMETRIC_DERIVATION,
        parents=(ArtifactParentRef("analysis-only", ANALYSIS_SHA),),
        visible=True,
    )
    result = ProvenancePolicyGate().evaluate(_manifest(), (analysis, visible))
    assert "visible-lineage-lacks-source-pixels" in {
        item.code for item in result.violations
    }


def test_gate_rejects_parent_hash_mismatch_and_missing_parent() -> None:
    mismatched = ArtifactRecord(
        artifact_id="mismatch",
        artifact_type="derived",
        stage="phase06",
        sha256=GEOMETRY_SHA,
        origin=ArtifactOrigin.GEOMETRIC_DERIVATION,
        parents=(ArtifactParentRef("source", OTHER_SHA),),
    )
    missing = ArtifactRecord(
        artifact_id="missing",
        artifact_type="derived",
        stage="phase06",
        sha256=OTHER_SHA,
        origin=ArtifactOrigin.GEOMETRIC_DERIVATION,
        parents=(ArtifactParentRef("does-not-exist", SOURCE_SHA),),
    )
    result = ProvenancePolicyGate().evaluate(
        _manifest(),
        (_source(), mismatched, missing),
    )
    codes = {item.code for item in result.violations}
    assert "parent-hash-mismatch" in codes
    assert "missing-parent-artifact" in codes


def test_gate_rejects_artifact_lineage_cycle() -> None:
    left = ArtifactRecord(
        artifact_id="left",
        artifact_type="metadata",
        stage="test",
        sha256=ANALYSIS_SHA,
        origin=ArtifactOrigin.SEMANTIC_METADATA,
        parents=(ArtifactParentRef("right", OTHER_SHA),),
    )
    right = ArtifactRecord(
        artifact_id="right",
        artifact_type="metadata",
        stage="test",
        sha256=OTHER_SHA,
        origin=ArtifactOrigin.SEMANTIC_METADATA,
        parents=(ArtifactParentRef("left", ANALYSIS_SHA),),
    )
    result = ProvenancePolicyGate().evaluate(_manifest(), (left, right))
    assert "artifact-lineage-cycle" in {
        item.code for item in result.violations
    }


def test_gate_rejects_run_policy_that_allows_generated_pixels() -> None:
    policy = RunPolicy(allow_generative_pixels=True)
    result = ProvenancePolicyGate().evaluate(_manifest(policy), (_source(),))
    assert result.passed is False
    assert "run-policy-allows-generated-visible-content" in {
        item.code for item in result.violations
    }


def test_artifact_manifest_requires_unique_ids() -> None:
    source = _source()
    with pytest.raises(ValueError):
        ArtifactManifest(run_id="run-001", artifacts=(source, source))


def test_contract_bundle_persistence_is_deterministic(tmp_path) -> None:
    artifacts = (_visible_geometry(), _source(), _analysis())
    first = write_contract_bundle(tmp_path, _manifest(), artifacts)
    run_bytes_first = (tmp_path / "run.json").read_bytes()
    artifact_bytes_first = (tmp_path / "artifacts.json").read_bytes()

    second = write_contract_bundle(tmp_path, _manifest(), artifacts)
    assert (tmp_path / "run.json").read_bytes() == run_bytes_first
    assert (tmp_path / "artifacts.json").read_bytes() == artifact_bytes_first
    assert first.run_manifest_sha256 == second.run_manifest_sha256
    assert first.artifact_manifest_sha256 == second.artifact_manifest_sha256

    payload = json.loads(artifact_bytes_first)
    assert [item["artifact_id"] for item in payload["artifacts"]] == [
        "primitive-001",
        "source",
        "subject-mask",
    ]


def test_gate_rejects_forbidden_origin_even_when_not_visible() -> None:
    generated = ArtifactRecord(
        artifact_id="hidden-generated",
        artifact_type="intermediate-image",
        stage="analysis",
        sha256=OTHER_SHA,
        origin=ArtifactOrigin.SYNTHESIZED,
        parents=(ArtifactParentRef("source", SOURCE_SHA),),
        visible=False,
    )
    result = ProvenancePolicyGate().evaluate(_manifest(), (_source(), generated))
    assert result.passed is False
    assert "forbidden-artifact-origin" in {
        item.code for item in result.violations
    }
