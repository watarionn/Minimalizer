from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts
from minimalizer_zerobase.production.profile import (
    CURRENT_PROFILE,
    REVIEWED_SA10_PROFILE,
    SUPPORTED_SEMANTIC_PROFILES,
)


def _case_id(path: Path) -> str:
    return (
        path.stem.replace("_list_thumb", "")
        .replace("(4)", "")
        .strip("_-")
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class ShadowStageResult:
    phase: int
    command: tuple[str, ...]
    elapsed_ms: float
    stage_path: str
    stage_sha256: str
    provenance_artifact_count: int | None


def _run(command: list[str], *, semantic_profile: str) -> float:
    started = perf_counter()
    environment = os.environ.copy()
    environment["MINIMALIZER_SEMANTIC_PROFILE"] = semantic_profile
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    elapsed = (perf_counter() - started) * 1000.0
    if completed.returncode != 0:
        raise RuntimeError(
            "ZeroBase2 shadow stage failed"
            f" (exit={completed.returncode}): "
            + " ".join(command)
            + "\nSTDOUT:\n"
            + completed.stdout[-4000:]
            + "\nSTDERR:\n"
            + completed.stderr[-4000:]
        )
    return elapsed


def run_zerobase2_shadow_pipeline(
    source_path: str | Path,
    output_root: str | Path,
    *,
    semantic_profile: str = CURRENT_PROFILE,
) -> dict[str, Any]:
    source = Path(source_path).resolve()
    output_root = Path(output_root).resolve()
    if semantic_profile not in SUPPORTED_SEMANTIC_PROFILES:
        raise ValueError(f"unsupported Minimalizer semantic profile: {semantic_profile}")
    if not source.is_file():
        raise ValueError(f"ZeroBase2 shadow source is missing: {source}")
    output_root.mkdir(parents=True, exist_ok=True)
    case_dir = output_root / _case_id(source)
    python = sys.executable

    stage_commands: list[tuple[int, list[str]]] = [
        (
            3,
            [
                python,
                str(ROOT / "scripts" / "zerobase2_phase3_subject.py"),
                str(source),
                "--output-root",
                str(output_root),
            ],
        ),
        (
            4,
            [
                python,
                str(ROOT / "scripts" / "zerobase2_phase4_parts.py"),
                str(source),
                "--output-root",
                str(output_root),
            ],
        ),
        (
            5,
            [
                python,
                str(ROOT / "scripts" / "zerobase2_phase5_structure.py"),
                str(source),
                "--output-root",
                str(output_root),
            ],
        ),
        (
            6,
            [
                python,
                str(ROOT / "scripts" / "zerobase2_phase6_binding.py"),
                str(source),
                "--output-root",
                str(output_root),
            ],
        ),
    ]
    for phase in range(7, 13):
        stage_commands.append(
            (
                phase,
                [
                    python,
                    str(ROOT / "tools" / f"run_zerobase_phase{phase}.py"),
                    "--case-dir",
                    str(case_dir),
                    "--source",
                    str(source),
                ],
            )
        )

    started = perf_counter()
    stage_results: list[ShadowStageResult] = []
    for phase, command in stage_commands:
        elapsed_ms = _run(command, semantic_profile=semantic_profile)
        stage_path = case_dir / f"phase_{phase:02d}" / "stage.json"
        if not stage_path.is_file():
            raise RuntimeError(
                f"ZeroBase2 shadow Phase {phase} produced no stage.json"
            )
        artifact_count: int | None = None
        if phase >= 6:
            bridge = bridge_stage_contracts(
                case_dir,
                source,
                max_phase=phase,
            )
            if not bridge.gate_result.passed:
                raise RuntimeError(
                    f"ZeroBase2 shadow Phase {phase} provenance Gate failed"
                )
            artifact_count = len(bridge.artifacts)
        stage_results.append(
            ShadowStageResult(
                phase=phase,
                command=tuple(command),
                elapsed_ms=elapsed_ms,
                stage_path=str(stage_path),
                stage_sha256=_sha256(stage_path),
                provenance_artifact_count=artifact_count,
            )
        )

    final_path = case_dir / "phase_12" / "12_final.png"
    phase12_path = case_dir / "phase_12" / "12_simplification.json"
    if not final_path.is_file() or not phase12_path.is_file():
        raise RuntimeError("ZeroBase2 shadow Phase 12 final output is missing")
    payload = json.loads(phase12_path.read_text(encoding="utf-8"))
    selected_name = payload.get("selected_name")
    candidate = next(
        (
            item
            for item in payload.get("candidates", [])
            if isinstance(item, dict) and item.get("name") == selected_name
        ),
        None,
    )
    if candidate is None or not bool(candidate.get("metrics", {}).get("pass")):
        raise RuntimeError("ZeroBase2 shadow Phase 12 selected candidate failed")

    elapsed_ms = (perf_counter() - started) * 1000.0
    return {
        "schema_version": "1.0",
        "mode": "zerobase2-shadow",
        "semantic_profile": semantic_profile,
        "source": {
            "path": source.name,
            "sha256": _sha256(source),
        },
        "case_id": case_dir.name,
        "case_dir": str(case_dir),
        "final_path": str(final_path),
        "final_sha256": _sha256(final_path),
        "selected_profile": selected_name,
        "phase12_metrics": candidate["metrics"],
        "elapsed_ms": elapsed_ms,
        "stages": [
            {
                "phase": item.phase,
                "elapsed_ms": item.elapsed_ms,
                "stage_path": item.stage_path,
                "stage_sha256": item.stage_sha256,
                "provenance_artifact_count": item.provenance_artifact_count,
            }
            for item in stage_results
        ],
        "failure_policy": (
            "No V2/browser fallback is permitted in ZeroBase2 shadow mode. "
            "Any stage or provenance failure aborts the run."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 3-12 as a strict shadow pipeline."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "artifacts" / "phase15_shadow",
    )
    parser.add_argument(
        "--profile",
        choices=SUPPORTED_SEMANTIC_PROFILES,
        default=CURRENT_PROFILE,
    )
    parser.add_argument("--summary", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_zerobase2_shadow_pipeline(
        args.source,
        args.output_root,
        semantic_profile=args.profile,
    )
    if args.summary is not None:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "mode": summary["mode"],
                "semantic_profile": summary["semantic_profile"],
                "case_id": summary["case_id"],
                "final_sha256": summary["final_sha256"],
                "selected_profile": summary["selected_profile"],
                "primitive_count": summary["phase12_metrics"][
                    "primitive_count"
                ],
                "silhouette_iou": summary["phase12_metrics"][
                    "silhouette_iou"
                ],
                "elapsed_ms": summary["elapsed_ms"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
