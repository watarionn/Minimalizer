from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class StageVisualSpec:
    stage_id: str
    label: str
    phase: int | None
    relative_path: str | None


@dataclass(frozen=True)
class DebugStage:
    stage_id: str
    label: str
    phase: int | None
    path: Path
    sha256: str
    machine_pass: bool | None


STAGE_VISUALS: tuple[StageVisualSpec, ...] = (
    StageVisualSpec("input", "INPUT", None, None),
    StageVisualSpec("03", "SUBJECT", 3, "03_subject_overlay.png"),
    StageVisualSpec("04", "PARTS", 4, "04_part_overlay.png"),
    StageVisualSpec("05", "GRAPH", 5, "05_structure_graph_overlay.png"),
    StageVisualSpec("06", "BINDING", 6, "06_region_binding.png"),
    StageVisualSpec("07", "MASSES", 7, "07_mass_blocks.png"),
    StageVisualSpec("08", "PRUNE", 8, "08_pruned_masses.png"),
    StageVisualSpec("09", "PALETTE", 9, "09_palette_preview.png"),
    StageVisualSpec("10", "PRIMITIVES", 10, "10_selected_primitives.png"),
    StageVisualSpec("11", "COMPOSED", 11, "11_composed_minimal.png"),
    StageVisualSpec("12", "FINAL", 12, "12_final.png"),
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def collect_debug_stages(
    case_dir: str | Path,
    source_path: str | Path,
) -> tuple[DebugStage, ...]:
    case_dir = Path(case_dir)
    source_path = Path(source_path)
    if not source_path.is_file():
        raise ValueError(f"Phase 13 source image is missing: {source_path}")
    source_sha = _sha256_file(source_path)

    collected: list[DebugStage] = [
        DebugStage("input", "INPUT", None, source_path, source_sha, None)
    ]
    for spec in STAGE_VISUALS[1:]:
        assert spec.phase is not None and spec.relative_path is not None
        phase_dir = case_dir / f"phase_{spec.phase:02d}"
        stage_path = phase_dir / "stage.json"
        visual_path = phase_dir / spec.relative_path
        if not stage_path.is_file():
            raise ValueError(
                f"Phase 13 mandatory stage contract is missing: phase {spec.phase:02d}"
            )
        if not visual_path.is_file():
            raise ValueError(
                f"Phase 13 mandatory visual is missing: {visual_path.name}"
            )
        stage = _load_json(stage_path)
        stage_source = stage.get("source")
        if not isinstance(stage_source, dict) or stage_source.get("sha256") != source_sha:
            raise ValueError(
                f"Phase 13 source SHA drift at phase {spec.phase:02d}"
            )
        outputs = stage.get("outputs")
        if not isinstance(outputs, dict):
            raise ValueError(
                f"Phase 13 outputs contract is missing at phase {spec.phase:02d}"
            )
        expected_sha = outputs.get(spec.relative_path)
        actual_sha = _sha256_file(visual_path)
        if expected_sha != actual_sha:
            raise ValueError(
                f"Phase 13 mandatory visual SHA mismatch: {spec.relative_path}"
            )
        pass_value = stage.get("metrics", {}).get("pass")
        machine_pass = (
            bool(pass_value) if isinstance(pass_value, bool) else None
        )
        collected.append(
            DebugStage(
                stage_id=spec.stage_id,
                label=spec.label,
                phase=spec.phase,
                path=visual_path,
                sha256=actual_sha,
                machine_pass=machine_pass,
            )
        )
    return tuple(collected)


def build_stage_index(
    case_id: str,
    stages: tuple[DebugStage, ...],
    *,
    review_status: str = "pending",
    first_bad_stage_id: str | None = None,
    review_note: str = "",
) -> dict[str, Any]:
    if review_status not in {"pending", "pass", "fail"}:
        raise ValueError("Phase 13 review status must be pending/pass/fail")
    stage_ids = {item.stage_id for item in stages}
    if first_bad_stage_id is not None and first_bad_stage_id not in stage_ids:
        raise ValueError("Phase 13 first bad stage is not present on the board")
    if review_status == "pass" and first_bad_stage_id is not None:
        raise ValueError("passing Phase 13 human review cannot name a bad stage")
    if review_status == "fail" and first_bad_stage_id is None:
        raise ValueError("failing Phase 13 human review requires first_bad_stage_id")

    first_machine_bad = next(
        (
            item.stage_id
            for item in stages
            if item.machine_pass is False
        ),
        None,
    )
    return {
        "schema_version": "1.0",
        "phase": 13,
        "case_id": case_id,
        "stage_order": [item.stage_id for item in stages],
        "stages": [
            {
                "stage_id": item.stage_id,
                "label": item.label,
                "phase": item.phase,
                "artifact_name": item.path.name,
                "sha256": item.sha256,
                "mandatory": True,
                "machine_pass": item.machine_pass,
            }
            for item in stages
        ],
        "first_machine_bad_stage_id": first_machine_bad,
        "human_review": {
            "status": review_status,
            "first_bad_stage_id": first_bad_stage_id,
            "note": review_note,
        },
        "first_bad_stage_rule": (
            "Human review identifies the earliest visually broken stage. "
            "Later-stage correction must not hide that root cause."
        ),
    }


def render_debug_board(
    case_id: str,
    stages: tuple[DebugStage, ...],
    *,
    cell_size: int = 300,
    columns: int = 4,
) -> Image.Image:
    if cell_size < 64 or columns < 1:
        raise ValueError("invalid Phase 13 board layout")
    rows = (len(stages) + columns - 1) // columns
    title_h = 44
    label_h = 38
    pad = 10
    cell_w = cell_size + pad * 2
    cell_h = cell_size + label_h + pad * 2
    canvas = Image.new(
        "RGB",
        (cell_w * columns, title_h + cell_h * rows),
        (235, 235, 235),
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text(
        (12, 14),
        f"Phase 13 Debug Board | {case_id}",
        fill=(20, 20, 20),
        font=font,
    )

    for index, item in enumerate(stages):
        row, col = divmod(index, columns)
        x0 = col * cell_w
        y0 = title_h + row * cell_h
        draw.rectangle(
            (x0 + 4, y0 + 4, x0 + cell_w - 4, y0 + cell_h - 4),
            fill=(248, 248, 248),
            outline=(150, 150, 150),
        )
        with Image.open(item.path) as raw:
            image = raw.convert("RGB")
            image.thumbnail((cell_size, cell_size), Image.Resampling.LANCZOS)
            px = x0 + pad + (cell_size - image.width) // 2
            py = y0 + pad + (cell_size - image.height) // 2
            canvas.paste(image, (px, py))
        if item.stage_id == "input":
            status = "SOURCE"
        elif item.machine_pass is None:
            status = "UNKNOWN"
        else:
            status = "PASS" if item.machine_pass else "FAIL"
        label = f"{item.stage_id} {item.label} | {status}"
        draw.text(
            (x0 + pad, y0 + pad + cell_size + 10),
            label,
            fill=(20, 20, 20),
            font=font,
        )
    return canvas


def write_phase13_artifacts(
    source_path: str | Path,
    case_dir: str | Path,
    output_dir: str | Path,
    *,
    review_status: str = "pending",
    first_bad_stage_id: str | None = None,
    review_note: str = "",
    cell_size: int = 300,
    columns: int = 4,
) -> dict[str, Any]:
    source_path = Path(source_path)
    case_dir = Path(case_dir)
    output_dir = Path(output_dir)
    stages = collect_debug_stages(case_dir, source_path)
    index = build_stage_index(
        case_dir.name,
        stages,
        review_status=review_status,
        first_bad_stage_id=first_bad_stage_id,
        review_note=review_note,
    )
    board = render_debug_board(
        case_dir.name,
        stages,
        cell_size=cell_size,
        columns=columns,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    board_path = output_dir / "13_debug_board.png"
    index_path = output_dir / "13_stage_index.json"
    preview_path = output_dir / "preview.png"
    metrics_path = output_dir / "metrics.json"
    stage_path = output_dir / "stage.json"

    board.save(board_path, format="PNG")
    board.save(preview_path, format="PNG")
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    upstream_all_pass = all(
        item.machine_pass is not False for item in stages
    )
    metrics = {
        "pass": True,
        "mandatory_stage_count": len(stages),
        "mandatory_stage_present_count": len(stages),
        "upstream_all_machine_pass": upstream_all_pass,
        "first_machine_bad_stage_id": index["first_machine_bad_stage_id"],
        "human_review_status": review_status,
        "human_first_bad_stage_id": first_bad_stage_id,
        "board_columns": columns,
        "board_cell_size": cell_size,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    phase12_stage = _load_json(case_dir / "phase_12" / "stage.json")
    source_contract = phase12_stage.get("source")
    coordinate_space = phase12_stage.get("coordinate_space")
    if not isinstance(source_contract, dict) or not isinstance(coordinate_space, dict):
        raise ValueError("Phase 13 requires Phase 12 source/coordinate contracts")

    config = {
        "stage_order": [item.stage_id for item in stages],
        "cell_size": cell_size,
        "columns": columns,
        "human_review_status": review_status,
        "first_bad_stage_rule": "first-visual-break",
    }
    inputs: dict[str, dict[str, str]] = {
        "source": {
            "path": source_path.name,
            "sha256": stages[0].sha256,
        }
    }
    for item in stages[1:]:
        assert item.phase is not None
        phase_dir = case_dir / f"phase_{item.phase:02d}"
        inputs[f"phase{item.phase:02d}"] = {
            item.path.name: item.sha256,
            "stage.json": _sha256_file(phase_dir / "stage.json"),
        }
    outputs = {
        path.name: _sha256_file(path)
        for path in (board_path, index_path, preview_path, metrics_path)
    }
    stage = {
        "phase": 13,
        "stage": "stage_visualizer_debug_board",
        "producer": "minimalizer-zerobase2-phase13",
        "producer_version": "0.1",
        "source": source_contract,
        "inputs": inputs,
        "config": config,
        "config_sha256": _canonical_json_sha256(config),
        "coordinate_space": coordinate_space,
        "determinism_policy": "fixed-stage-order-fixed-grid-fixed-resampling",
        "diagnostic_policy": {
            "first_bad_stage_rule": True,
            "no_later_stage_masking": True,
            "human_visual_review_recorded": True,
        },
        "provenance_policy": {
            "generation": "forbidden",
            "inpainting": "forbidden",
            "hidden_completion": "forbidden",
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
