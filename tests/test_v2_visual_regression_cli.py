from pathlib import Path

import pytest

from minimalize_engine.v2.regression import VISUAL_REGRESSION_CORPUS_V1
from tools.run_v2_visual_regression import canonical_corpus_paths


def _populate(root: Path) -> tuple[Path, Path]:
    inputs = root / "input"
    references = root / "approved"
    inputs.mkdir()
    references.mkdir()
    for index, name in enumerate(VISUAL_REGRESSION_CORPUS_V1, start=1):
        (inputs / f"{name}_list_thumb.png").touch()
        (references / f"{index:02d}_{name}_APPROVED_GEOMETRIC_REFERENCE.png").touch()
    return inputs, references


def test_canonical_corpus_paths_resolve_all_18(tmp_path: Path):
    inputs, references = _populate(tmp_path)
    cases, refs = canonical_corpus_paths(inputs, references)
    assert tuple(cases) == VISUAL_REGRESSION_CORPUS_V1
    assert tuple(refs) == VISUAL_REGRESSION_CORPUS_V1
    assert len(cases) == len(refs) == 18


def test_canonical_corpus_paths_reject_missing_file(tmp_path: Path):
    inputs, references = _populate(tmp_path)
    missing = inputs / f"{VISUAL_REGRESSION_CORPUS_V1[4]}_list_thumb.png"
    missing.unlink()
    with pytest.raises(FileNotFoundError, match="missing corpus source"):
        canonical_corpus_paths(inputs, references)


def test_reference_directory_is_optional(tmp_path: Path):
    inputs, _ = _populate(tmp_path)
    cases, refs = canonical_corpus_paths(inputs)
    assert len(cases) == 18
    assert refs == {}


def test_validate_corpus_images_rejects_html_disguised_as_png(tmp_path: Path):
    from tools.run_v2_visual_regression import validate_corpus_images

    fake = tmp_path / "fake.png"
    fake.write_text("<!doctype html><html></html>", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid corpus reference image"):
        validate_corpus_images({}, {"Kikirara-Vivi": fake})
