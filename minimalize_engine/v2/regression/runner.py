from __future__ import annotations

import hashlib
import json
import platform as platform_module
import subprocess
import sys
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Mapping

import cv2
import numpy as np

from minimalize_engine.v2.characteristic import annotate_initial_regions
from minimalize_engine.v2.contour.validation import loops_have_self_intersection
from minimalize_engine.v2.region_merge.graph import build_region_graph, edge_key
from minimalize_engine.v2.pipeline import (
    MinimalizerV2Result,
    PipelineConfig,
    _minimalize_v2_impl,
)
from minimalize_engine.v2.region_merge.cut import validate_cut_family
from minimalize_engine.v2.regression.compare import algorithm_digest
from minimalize_engine.v2.regression.debug import write_debug_artifacts
from minimalize_engine.v2.regression.metrics import compute_regression_metrics
from minimalize_engine.v2.regression.types import (
    InvariantCheck,
    RegressionCaseResult,
    RegressionConfig,
    RegressionManifest,
)


VISUAL_REGRESSION_CORPUS_V1 = (
    "Kikirara-Vivi", "Isaki-Riona", "Koganei-Niko", "Vestia-Zeta",
    "Todoroki-Hajime", "Shishiro-Botan", "Shiori-Novella",
    "Natsuiro-Matsuri", "Otonose-Kanade", "Mori-Calliope",
    "Momosuzu-Nene", "Koseki-Bijou", "Kobo-Kanaeru", "Houshou-Marine",
    "Hakos-Baelz", "Gigi-Murin", "Aki-Rosenthal", "Raora-Panthera",
)
SMOKE_CORPUS_V1 = ("Kikirara-Vivi", "Otonose-Kanade", "Hakos-Baelz")
KNOWN_ISSUE_CASES = (
    "face_right_gouge",
    "thin_rectangle_noise",
    "characteristic_accent_loss",
    "hair_skin_color_collapse",
    "subject_background_leakage",
)


def load_rgb_file(path: str | Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"failed to decode image: {path}")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        bgra = image.astype(np.float32)
        alpha = bgra[:, :, 3:4] / 255.0
        bgr = bgra[:, :, :3] * alpha + 255.0 * (1.0 - alpha)
        image = cv2.cvtColor(np.rint(bgr).astype(np.uint8), cv2.COLOR_BGR2RGB)
    else:
        image = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB)
    return image.astype(np.uint8, copy=False)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
def _jsonable_config(config: PipelineConfig) -> dict[str, object]:
    return asdict(config)


def config_hash(config: PipelineConfig) -> str:
    payload = json.dumps(
        _jsonable_config(config),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def resolve_code_revision(repo_root: str | Path | None = None) -> str:
    cwd = None if repo_root is None else str(repo_root)
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def build_manifest(
    source_rgb: np.ndarray,
    *,
    preset: str,
    pipeline_config: PipelineConfig,
    reference_rgb: np.ndarray | None,
    code_revision: str,
) -> RegressionManifest:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_hash = _sha256_bytes(np.ascontiguousarray(source_rgb).tobytes())
    reference_hash = None
    if reference_rgb is not None:
        reference_hash = _sha256_bytes(np.ascontiguousarray(reference_rgb).tobytes())
    run_id = f"{timestamp.replace(':', '').replace('+00:00', 'Z')}-{preset}-{source_hash[:10]}"
    return RegressionManifest(
        run_id=run_id,
        timestamp_utc=timestamp,
        code_revision=code_revision,
        config_hash=config_hash(pipeline_config),
        python_version=platform_module.python_version(),
        opencv_version=cv2.__version__,
        platform=platform_module.platform(),
        preset=preset,
        phase_configs=_jsonable_config(pipeline_config),
        source_hash=source_hash,
        reference_hash=reference_hash,
    )
def _check(name: str, condition: bool, detail: str = "") -> InvariantCheck:
    return InvariantCheck(name=name, passed=bool(condition), detail=detail)


def _analysis_stats_match(result: MinimalizerV2Result) -> bool:
    labels = result.region_merge.initial_labels.ravel()
    lab = result.bundle.analysis_lab.reshape(-1, 3).astype(np.float64)
    count = result.region_merge.initial_region_count
    counts = np.bincount(labels, minlength=count)
    sums = np.vstack(
        [np.bincount(labels, weights=lab[:, channel], minlength=count) for channel in range(3)]
    ).T
    if np.any(counts <= 0):
        return False
    for region_id in range(count):
        stats = result.region_merge.tree.nodes[region_id].stats
        if stats.pixel_count != int(counts[region_id]):
            return False
        if not np.allclose(stats.sum_lab, sums[region_id], rtol=1e-7, atol=1e-4):
            return False
    return True


def _rebuild_initial_graph(result: MinimalizerV2Result, config: PipelineConfig):
    annotations = annotate_initial_regions(
        result.bundle, result.region_merge.initial_labels,
        characteristic=result.characteristic,
    )
    return build_region_graph(
        result.bundle, result.region_merge.initial_labels,
        annotations=annotations, gradient_bins=config.region_merge.gradient_bins,
    )


def _shared_boundaries_consistent(result: MinimalizerV2Result, preset: str) -> bool:
    graph = result.presets[preset].contour.boundary_graph
    for chain_id, chain in graph.chains.items():
        if len(chain.regions) != 2:
            continue
        refs = []
        for region_id in chain.regions:
            matched = [
                ref for ref in graph.region_chains[region_id]
                if ref.chain_id == chain_id
            ]
            if len(matched) != 1:
                return False
            refs.append(matched[0])
        if refs[0].reversed == refs[1].reversed:
            return False
    return True


def _palette_samples_are_observed(result: MinimalizerV2Result, preset: str) -> bool:
    palette = result.presets[preset].palette
    height, width = result.bundle.analysis_rgb.shape[:2]
    for entry in palette.entries.values():
        x, y = entry.source_xy
        if not (0 <= x < width and 0 <= y < height):
            return False
        rgb = tuple(int(value) for value in result.bundle.analysis_rgb[y, x])
        if rgb != entry.rgb:
            return False
        if not np.allclose(entry.lab, result.bundle.analysis_lab[y, x], atol=1e-6):
            return False
    return True
def validate_invariants(
    result: MinimalizerV2Result,
    *,
    preset: str,
    config: PipelineConfig,
) -> tuple[InvariantCheck, ...]:
    pipeline = result.presets[preset]
    tree = result.region_merge.tree
    internal_ids = tuple(tree.merge_sequence)
    checks: list[InvariantCheck] = []
    initial_graph = _rebuild_initial_graph(result, config)
    adjacency_symmetric = all(
        region_id in initial_graph.adjacency.get(neighbor_id, set())
        for region_id, neighbors in initial_graph.adjacency.items()
        for neighbor_id in neighbors
    )
    canonical_edges = all(
        key == edge_key(edge.a, edge.b)
        for key, edge in initial_graph.edges.items()
    )
    no_self_edges = all(edge.a != edge.b for edge in initial_graph.edges.values())
    checks.append(_check(
        "initial_labels_immutable_contract",
        result.region_merge.initial_labels.dtype == np.int32
        and not result.region_merge.initial_labels.flags.writeable,
    ))
    checks.append(_check("region_adjacency_symmetric", adjacency_symmetric))
    checks.append(_check("edge_keys_canonical", canonical_edges))
    checks.append(_check("region_graph_has_no_self_edges", no_self_edges))
    checks.append(_check(
        "region_ids_never_reused",
        len(internal_ids) == len(set(internal_ids))
        and not (set(internal_ids) & set(tree.leaf_ids)),
    ))
    checks.append(_check(
        "region_stats_finite",
        all(
            node.stats.pixel_count > 0
            and np.all(np.isfinite(node.stats.sum_lab))
            and np.all(np.isfinite(node.stats.sum_sq_lab))
            for node in tree.nodes.values()
        ),
    ))
    checks.append(_check("region_colors_from_analysis_lab", _analysis_stats_match(result)))
    checks.append(_check(
        "structural_lab_not_used_as_final_color",
        _palette_samples_are_observed(result, preset),
    ))
    checks.append(_check(
        "shared_contour_boundaries_agree",
        _shared_boundaries_consistent(result, preset),
    ))
    checks.append(_check(
        "contours_have_no_self_intersection",
        all(
            not loops_have_self_intersection(contour.loops)
            for contour in pipeline.contour.contours.values()
        ),
    ))
    selected_count = len(pipeline.selection.region_ids)
    checks.append(_check(
        "contour_preserves_region_count",
        len(pipeline.contour.contours) == selected_count,
    ))
    checks.append(_check(
        "primitive_fitting_preserves_region_count",
        len(pipeline.primitives.primitives) == selected_count,
    ))
    worst_critical = max(
        (
            item.selected.metrics.critical_neighbor_leakage
            for item in pipeline.primitives.primitives.values()
        ),
        default=0.0,
    )
    checks.append(_check(
        "critical_neighbor_leakage_guard",
        worst_critical <= config.primitive.critical_neighbor_leakage_limit + 1e-12,
        f"worst={worst_critical:.6f}",
    ))
    checks.append(_check(
        "palette_uses_observed_analysis_colors",
        _palette_samples_are_observed(result, preset),
    ))
    checks.append(_check(
        "every_region_has_palette_assignment",
        set(pipeline.palette.region_to_palette) == set(pipeline.selection.region_ids),
    ))
    checks.append(_check(
        "detail_budget_has_no_core_coverage_holes",
        all(
            not (
                pipeline.detail_budget.actions[region_id] == "HIDE_OVERLAY"
                and not info.overlay
            )
            for region_id, info in pipeline.detail_budget.shape_info.items()
        ),
    ))
    try:
        validate_cut_family(result.region_merge, result.cut_family)
        nested = True
    except ValueError:
        nested = False
    checks.append(_check("preset_hierarchy_nested", nested))
    scene_ids = {shape.region_id for shape in pipeline.scene.shapes}
    checks.append(_check(
        "scene_covers_all_core_regions",
        scene_ids == set(pipeline.selection.region_ids),
    ))
    if result.characteristic is not None:
        expected = {
            anchor.id for anchor in result.characteristic.anchors
            if anchor.confidence >= config.palette.anchor_confidence_threshold
        }
        retained = {
            anchor_id
            for entry in pipeline.palette.entries.values()
            for anchor_id in entry.anchor_ids
        }
        checks.append(_check(
            "high_confidence_characteristic_anchors_retained",
            expected <= retained,
            f"missing={sorted(expected - retained)}",
        ))
    return tuple(checks)
def _write_run_records(
    output_dir: Path,
    manifest: RegressionManifest,
    metrics,
    invariants: tuple[InvariantCheck, ...],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "run_manifest.json"
    metrics_path = output_dir / "metrics.json"
    invariants_path = output_dir / "invariants.json"
    manifest_payload = {
        "run_id": manifest.run_id,
        "timestamp_utc": manifest.timestamp_utc,
        "code_revision": manifest.code_revision,
        "config_hash": manifest.config_hash,
        "python_version": manifest.python_version,
        "opencv_version": manifest.opencv_version,
        "platform": manifest.platform,
        "preset": manifest.preset,
        "phase_configs": dict(manifest.phase_configs),
        "source_hash": manifest.source_hash,
        "reference_hash": manifest.reference_hash,
    }
    metrics_payload = {}
    for item in fields(metrics):
        value = getattr(metrics, item.name)
        metrics_payload[item.name] = (
            dict(value) if item.name == "phase_timings" else value
        )
    invariants_payload = [
        {"name": item.name, "passed": item.passed, "detail": item.detail}
        for item in invariants
    ]
    for path, payload in (
        (manifest_path, manifest_payload),
        (metrics_path, metrics_payload),
        (invariants_path, invariants_payload),
    ):
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return {
        "manifest": str(manifest_path),
        "metrics": str(metrics_path),
        "invariants": str(invariants_path),
    }
def run_regression_case(
    source_rgb: np.ndarray,
    *,
    pipeline_config: PipelineConfig | None = None,
    regression_config: RegressionConfig | None = None,
    output_dir: str | Path | None = None,
    reference_rgb: np.ndarray | None = None,
    code_revision: str | None = None,
) -> RegressionCaseResult:
    pconfig = pipeline_config or PipelineConfig()
    rconfig = regression_config or RegressionConfig()
    timings: dict[str, float] = {}

    def observer(name: str, elapsed: float) -> None:
        timings[name] = timings.get(name, 0.0) + float(elapsed)

    started = perf_counter()
    result = _minimalize_v2_impl(
        source_rgb,
        presets=(rconfig.main_preset,),
        config=pconfig,
        characteristic=None,
        observer=observer,
    )
    runtime = perf_counter() - started
    digest_before = algorithm_digest(result, rconfig.main_preset)
    metrics = compute_regression_metrics(
        result,
        preset=rconfig.main_preset,
        pipeline_config=pconfig,
        regression_config=rconfig,
        phase_timings=timings,
        runtime_seconds=runtime,
    )
    invariants = list(validate_invariants(
        result, preset=rconfig.main_preset, config=pconfig
    ))
    revision = code_revision or resolve_code_revision()
    manifest = build_manifest(
        np.asarray(source_rgb, dtype=np.uint8),
        preset=rconfig.main_preset,
        pipeline_config=pconfig,
        reference_rgb=reference_rgb,
        code_revision=revision,
    )
    artifacts: dict[str, str] = {}
    out = None if output_dir is None else Path(output_dir)
    if out is not None:
        artifacts.update(
            write_debug_artifacts(
                result,
                rconfig.main_preset,
                out,
                level=rconfig.artifact_level,
                reference_rgb=reference_rgb,
            )
        )
    digest_after = algorithm_digest(result, rconfig.main_preset)
    invariants.append(_check(
        "debug_observation_does_not_change_output",
        digest_before == digest_after,
    ))
    if out is not None:
        artifacts.update(_write_run_records(out, manifest, metrics, tuple(invariants)))
    return RegressionCaseResult(
        manifest=manifest,
        metrics=metrics,
        invariants=tuple(invariants),
        algorithm_digest=digest_after,
        debug_artifacts=artifacts,
    )


def check_debug_observational(
    source_rgb: np.ndarray,
    *,
    pipeline_config: PipelineConfig | None = None,
    preset: str = "minimal",
    output_dir: str | Path | None = None,
) -> bool:
    config = pipeline_config or PipelineConfig()
    baseline = _minimalize_v2_impl(
        source_rgb, presets=(preset,), config=config, characteristic=None, observer=None
    )
    observed = _minimalize_v2_impl(
        source_rgb, presets=(preset,), config=config, characteristic=None, observer=None
    )
    if output_dir is not None:
        write_debug_artifacts(observed, preset, output_dir, level="standard")
    return algorithm_digest(baseline, preset) == algorithm_digest(observed, preset)


def check_determinism(
    source_rgb: np.ndarray,
    *,
    pipeline_config: PipelineConfig | None = None,
    preset: str = "minimal",
) -> bool:
    config = pipeline_config or PipelineConfig()
    first = _minimalize_v2_impl(
        source_rgb,
        presets=(preset,),
        config=config,
        characteristic=None,
        observer=None,
    )
    second = _minimalize_v2_impl(
        source_rgb,
        presets=(preset,),
        config=config,
        characteristic=None,
        observer=None,
    )
    return algorithm_digest(first, preset) == algorithm_digest(second, preset)


def validate_visual_regression_corpus(cases: Mapping[str, str | Path]) -> None:
    provided = set(cases)
    expected = set(VISUAL_REGRESSION_CORPUS_V1)
    missing = sorted(expected - provided)
    extra = sorted(provided - expected)
    if missing or extra:
        raise ValueError(f"visual regression corpus mismatch: missing={missing}, extra={extra}")


def run_visual_regression_corpus(
    cases: Mapping[str, str | Path],
    **kwargs,
) -> dict[str, RegressionCaseResult]:
    validate_visual_regression_corpus(cases)
    return run_regression_files(cases, **kwargs)


def run_regression_files(
    cases: Mapping[str, str | Path],
    *,
    pipeline_config: PipelineConfig | None = None,
    regression_config: RegressionConfig | None = None,
    output_root: str | Path | None = None,
    reference_paths: Mapping[str, str | Path] | None = None,
    code_revision: str | None = None,
) -> dict[str, RegressionCaseResult]:
    results: dict[str, RegressionCaseResult] = {}
    references = dict(reference_paths or {})
    root = None if output_root is None else Path(output_root)
    for name in sorted(cases):
        source = load_rgb_file(cases[name])
        reference = None
        if name in references:
            reference = load_rgb_file(references[name])
        case_dir = None if root is None else root / name
        results[name] = run_regression_case(
            source,
            pipeline_config=pipeline_config,
            regression_config=regression_config,
            output_dir=case_dir,
            reference_rgb=reference,
            code_revision=code_revision,
        )
    return results
