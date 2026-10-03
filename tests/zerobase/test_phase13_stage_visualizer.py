from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from minimalizer_zerobase.evaluation.debug_board import (
    STAGE_VISUALS,
    build_stage_index,
    collect_debug_stages,
    render_debug_board,
    write_phase13_artifacts,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_case(tmp_path: Path) -> tuple[Path, Path]:
    case = tmp_path / "case"
    case.mkdir()
    source = tmp_path / "source.png"
    Image.new("RGB", (32, 32), (210, 205, 200)).save(source)
    source_sha = _sha(source)

    for index, spec in enumerate(STAGE_VISUALS[1:], start=1):
        assert spec.phase is not None and spec.relative_path is not None
        phase_dir = case / f"phase_{spec.phase:02d}"
        phase_dir.mkdir()
        visual = phase_dir / spec.relative_path
        Image.new(
            "RGB",
            (32, 32),
            (20 + index * 8, 40 + index * 5, 60 + index * 3),
        ).save(visual)
        stage = {
            "phase": spec.phase,
            "source": {
                "path": source.name,
                "sha256": source_sha,
                "width": 32,
                "height": 32,
            },
            "coordinate_space": {
                "pixel_width": 32,
                "pixel_height": 32,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "metrics": {"pass": True},
            "outputs": {spec.relative_path: _sha(visual)},
        }
        (phase_dir / "stage.json").write_text(
            json.dumps(stage),
            encoding="utf-8",
        )
    return case, source


def test_phase13_collects_fixed_mandatory_stage_order_and_hashes(tmp_path: Path) -> None:
    case, source = _make_case(tmp_path)

    stages = collect_debug_stages(case, source)

    assert [item.stage_id for item in stages] == [
        "input",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
    ]
    assert all(item.machine_pass is not False for item in stages)
    assert all(len(item.sha256) == 64 for item in stages)


def test_phase13_board_and_stage_index_record_human_first_bad_rule(tmp_path: Path) -> None:
    case, source = _make_case(tmp_path)
    stages = collect_debug_stages(case, source)

    board = render_debug_board("case", stages, cell_size=64, columns=4)
    index = build_stage_index(
        "case",
        stages,
        review_status="fail",
        first_bad_stage_id="06",
        review_note="binding is the first visually broken stage",
    )

    assert board.size == (336, 410)
    assert index["human_review"]["first_bad_stage_id"] == "06"
    assert index["first_machine_bad_stage_id"] is None


def test_phase13_writes_full_stage_contract(tmp_path: Path) -> None:
    case, source = _make_case(tmp_path)
    out = case / "phase_13"

    stage = write_phase13_artifacts(
        source,
        case,
        out,
        review_status="pass",
        review_note="all mandatory stages visually readable",
        cell_size=64,
        columns=4,
    )

    assert stage["metrics"]["pass"] is True
    assert stage["metrics"]["mandatory_stage_count"] == 11
    assert stage["metrics"]["human_review_status"] == "pass"
    for name in (
        "13_debug_board.png",
        "13_stage_index.json",
        "preview.png",
        "metrics.json",
        "stage.json",
    ):
        assert (out / name).is_file()
    assert stage["outputs"]["13_debug_board.png"] == _sha(out / "13_debug_board.png")


def test_phase13_rejects_missing_or_tampered_mandatory_visual(tmp_path: Path) -> None:
    case, source = _make_case(tmp_path)
    target = case / "phase_07" / "07_mass_blocks.png"
    target.write_bytes(b"tampered")

    try:
        collect_debug_stages(case, source)
    except ValueError as exc:
        assert "SHA mismatch" in str(exc)
    else:
        raise AssertionError("expected Phase 13 to reject a tampered mandatory visual")


def test_phase13_treats_legacy_missing_pass_flag_as_unknown_not_failure(
    tmp_path: Path,
) -> None:
    case, source = _make_case(tmp_path)
    stage_path = case / "phase_03" / "stage.json"
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    stage["metrics"].pop("pass")
    stage_path.write_text(json.dumps(stage), encoding="utf-8")

    stages = collect_debug_stages(case, source)
    phase03 = next(item for item in stages if item.stage_id == "03")
    index = build_stage_index("case", stages)

    assert phase03.machine_pass is None
    assert index["first_machine_bad_stage_id"] is None
