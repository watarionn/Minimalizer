from pathlib import Path

import pytest

from prepare_local_l04_visual_review_kit import prepare


def _source(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    root.mkdir()
    sources = root / "sources"
    sources.mkdir()
    for case in ("H04", "H06", "H08"):
        (sources / f"{case}.png").write_bytes(b"source")
        case_dir = root / case
        case_dir.mkdir()
        (case_dir / "expanded_stage8.svg").write_text("<svg/>", encoding="utf-8")
    (root / "L04_CANDIDATE_TRIPLE_RECEIPT.json").write_text(
        '{"schema":"minimalizer/local-l04/candidate-triple-receipt/v1","cases":[{"case":"H04","source_sha256":"a","stage8_json_sha256":"b","expanded_svg_sha256":"c"},{"case":"H06","source_sha256":"d","stage8_json_sha256":"e","expanded_svg_sha256":"f"},{"case":"H08","source_sha256":"g","stage8_json_sha256":"h","expanded_svg_sha256":"i"}]}',
        encoding="utf-8",
    )
    return root


def test_prepare_creates_human_first_kit_without_receipt(tmp_path: Path) -> None:
    destination = tmp_path / "review"
    result = prepare(_source(tmp_path), destination)
    assert result["status"] == "READY_FOR_INDEPENDENT_VISUAL_REVIEW"
    assert result["receipt_created"] is False
    assert (destination / "README_日本語.md").exists()
    assert (destination / "L04独立視覚Golden確認票.txt").exists()


def test_prepare_rejects_existing_destination(tmp_path: Path) -> None:
    destination = tmp_path / "review"
    destination.mkdir()
    with pytest.raises(FileExistsError):
        prepare(_source(tmp_path), destination)


def test_prepare_rejects_package_without_signed_sources(tmp_path: Path) -> None:
    source = _source(tmp_path)
    for path in (source / "sources").iterdir():
        path.unlink()
    (source / "sources").rmdir()
    with pytest.raises(FileNotFoundError, match="sources"):
        prepare(source, tmp_path / "review")
