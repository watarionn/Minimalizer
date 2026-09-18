from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from minimalize_engine.v2 import PerformanceBudget, PerformanceMeasurement, evaluate_performance_budget
from web.service import build_config, minimalize_path, minimalize_v2_path

CASES = (
    "Kikirara-Vivi_list_thumb.png",
    "Otonose-Kanade_list_thumb.png",
    "Todoroki-Hajime_list_thumb.png",
    "Raora-Panthera_list_thumb.png",
    "Hakos-Baelz_list_thumb.png",
)


def _time_call(fn) -> float:
    gc.collect()
    started = perf_counter()
    fn()
    return perf_counter() - started

def run_single_batch(input_dir: Path) -> dict[str, object]:
    budget = PerformanceBudget()
    config = build_config(4, analysis_max_side_cap=budget.max_analysis_side)
    rows: list[dict[str, object]] = []
    for name in CASES:
        path = input_dir / name
        legacy_times: list[float] = []
        v2_times: list[float] = []
        for _ in range(budget.repeats):
            legacy_times.append(_time_call(lambda: minimalize_path(path, config, "png")))
            v2_times.append(_time_call(lambda: minimalize_v2_path(
                path, preset="minimal", include_facets=True,
                analysis_max_side_cap=budget.max_analysis_side,
            )))
        legacy_mean = mean(legacy_times)
        v2_mean = mean(v2_times)
        rows.append({
            "case": name,
            "legacy_seconds": legacy_mean,
            "v2_seconds": v2_mean,
            "ratio": v2_mean / legacy_mean,
            "legacy_repeats": legacy_times,
            "v2_repeats": v2_times,
        })

    legacy_mean = mean(float(row["legacy_seconds"]) for row in rows)
    v2_mean = mean(float(row["v2_seconds"]) for row in rows)
    ratios = [float(row["ratio"]) for row in rows]
    measurement = PerformanceMeasurement(
        mean_legacy_seconds=legacy_mean,
        mean_v2_seconds=v2_mean,
        max_case_v2_seconds=max(float(row["v2_seconds"]) for row in rows),
        mean_case_ratio=mean(ratios),
        max_case_ratio=max(ratios),
        case_count=len(rows),
        repeats=budget.repeats,
        analysis_max_side=budget.max_analysis_side,
        web_workers=budget.web_workers,
        max_concurrent_jobs=budget.max_concurrent_jobs,
    )
    evaluation = evaluate_performance_budget(measurement)
    return {
        "cases": rows,
        "evaluation": evaluation.to_dict(),
    }


def run_benchmark(input_dir: Path) -> dict[str, object]:
    budget = PerformanceBudget()
    batches = [run_single_batch(input_dir) for _ in range(budget.confirmation_batches)]
    evaluations = [batch["evaluation"] for batch in batches]
    measurements = [item["measurement"] for item in evaluations]
    return {
        "schema_version": "minimalizer-v2-performance-budget-confirmation-v1",
        "budget": budget.to_dict(),
        "benchmark_contract": {
            "legacy": "web.service.minimalize_path PNG, level=4, analysis cap=400",
            "v2": "web.service.minimalize_v2_path minimal + facets, analysis cap=400",
            "cases": list(CASES),
            "repeats_per_batch": budget.repeats,
            "confirmation_batches": budget.confirmation_batches,
            "execution": "sequential same-process, gc before each timed call",
        },
        "resource_envelope": {
            "max_analysis_side": budget.max_analysis_side,
            "web_workers": budget.web_workers,
            "max_concurrent_jobs": budget.max_concurrent_jobs,
            "requires_resource_increase": False,
        },
        "batches": batches,
        "all_batches_passed": all(bool(item["passed"]) for item in evaluations),
        "worst_observed": {
            "mean_v2_seconds": max(float(m["mean_v2_seconds"]) for m in measurements),
            "max_case_v2_seconds": max(float(m["max_case_v2_seconds"]) for m in measurements),
            "mean_case_ratio": max(float(m["mean_case_ratio"]) for m in measurements),
            "max_case_ratio": max(float(m["max_case_ratio"]) for m in measurements),
        },
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the fixed V2 default-migration performance budget.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run_benchmark(args.input_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output.resolve())
    print(json.dumps({
        "all_batches_passed": payload["all_batches_passed"],
        "worst_observed": payload["worst_observed"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
