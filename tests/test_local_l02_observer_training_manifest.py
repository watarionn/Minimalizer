import pytest

from tools.research.local_l02_observer_training_manifest import (
    HOLDOUT_CASES,
    REQUIRED_ANNOTATION_ROLES,
    TrainingManifest,
    TrainingManifestHold,
    build_sample,
    validate_training_manifest,
)


SHA = "a" * 64


def _manifest(*, samples):
    return TrainingManifest(
        schema="minimalizer/l02/observer_training_manifest/v1",
        dataset_revision="dataset-r1",
        unknown_policy="separate_from_negative",
        human_labels_used_for_holdout_inference=False,
        samples=tuple(samples),
    )


def _sample(sample_id, character_id, case_id, split):
    return build_sample(
        sample_id=sample_id,
        character_id=character_id,
        case_id=case_id,
        split=split,
        source_sha256=SHA,
        annotation_sha256=SHA,
    )


def _valid_samples():
    return [
        _sample("t1", "char-train", "T1", "train"),
        _sample("v1", "char-validation", "V1", "validation"),
        _sample("h04", "char-h04", "H04", "holdout"),
        _sample("h06", "char-h06", "H06", "holdout"),
        _sample("h08", "char-h08", "H08", "holdout"),
    ]


def test_valid_manifest_freezes_three_holdout_cases():
    result = validate_training_manifest(_manifest(samples=_valid_samples()))
    assert result["status"] == "TRAINING_MANIFEST_PASS"
    assert result["holdout_cases"] == tuple(sorted(HOLDOUT_CASES))
    assert REQUIRED_ANNOTATION_ROLES


@pytest.mark.parametrize("case_id", sorted(HOLDOUT_CASES))
def test_holdout_case_cannot_enter_training_split(case_id):
    samples = _valid_samples()
    samples[0] = _sample("bad", "char-train", case_id, "train")
    with pytest.raises(TrainingManifestHold, match="HOLDOUT_IN_TRAINING_DATA"):
        validate_training_manifest(_manifest(samples=samples))


def test_character_cannot_cross_train_and_validation():
    samples = _valid_samples()
    samples[1] = _sample("v1", "char-train", "V1", "validation")
    with pytest.raises(TrainingManifestHold, match="CHARACTER_LEAK_TRAIN_VALIDATION"):
        validate_training_manifest(_manifest(samples=samples))


def test_character_cannot_cross_training_and_holdout():
    samples = _valid_samples()
    samples[2] = _sample("h04", "char-train", "H04", "holdout")
    with pytest.raises(TrainingManifestHold, match="CHARACTER_LEAK_INTO_HOLDOUT"):
        validate_training_manifest(_manifest(samples=samples))


def test_unknown_role_cannot_be_dropped():
    samples = _valid_samples()
    samples[0] = build_sample(
        sample_id="bad",
        character_id="char-train-2",
        case_id="T2",
        split="train",
        source_sha256=SHA,
        annotation_sha256=SHA,
        annotation_roles=REQUIRED_ANNOTATION_ROLES - {"unknown"},
    )
    with pytest.raises(TrainingManifestHold, match="INCOMPLETE_ANNOTATION_ROLES"):
        validate_training_manifest(_manifest(samples=samples))
