#!/usr/bin/env python3
"""V20 postprocesses read-only Chrome candidate probes. No thresholds are changed.

Usage:
  python tools/analyze_browser_donor_v20.py --kyoko K_PATH --noel N_PATH
      --ririka R_PATH --out OUT_PATH [--baseline-root PARENT_PATH]
Inputs are directories produced by run_browser_donor_v20_chrome.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median

CASES = ("Kyoko", "Noel", "Ririka")
GEOMETRIC_GATES = ("area", "minSide", "aspect")
CONTACT_GATES = ("sharedEdges", "sharedRatio")
COLOR_GATES = (
    "palette", "protectedArea", "paletteDistance", "paletteError",
    "recolorBudget", "sourceRgbDistance",
)
OTHER_GATES = tuple(key for key in (*COLOR_GATES, *CONTACT_GATES))
AREAS = ((0, 50, "1-50"), (51, 173, "51-173"),
         (174, 350, "174-350"), (351, 1000, "351-1000"),
         (1001, 3000, "1001-3000"), (3001, 1_000_000, ">3000"))
WIDTH_BINS = ((0, 2, "1-2"), (3, 4, "3-4"), (5, 9, "5-9"),
              (10, 19, "10-19"), (20, 99999, "20+"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {key: None for key in ("min", "p10", "p25", "median", "p75", "p90", "max")}
    a = sorted(values)
    def interp(fraction: float) -> float:
        position = (len(a) - 1) * fraction
        lo = int(position)
        hi = min(len(a) - 1, lo + 1)
        return round(a[lo] + (a[hi] - a[lo]) * (position - lo), 4)
    return {"min": a[0], "p10": interp(.10), "p25": interp(.25),
            "median": round(median(a), 4), "p75": interp(.75),
            "p90": interp(.90), "max": a[-1]}


def histogram(values: list[int], bins: tuple) -> dict[str, int]:
    return {
        label: sum(lower <= value <= upper for value in values)
        for lower, upper, label in bins
    }


def independent_scenarios(items: list[dict]) -> dict[str, int]:
    def passes(row: dict, ignored: frozenset) -> bool:
        return all(value for key, value in row["gates"].items()
                   if key not in ignored)
    # Counterfactual candidate counts only, NOT admissible/accepted merges.
    results = {
        "allCurrentGates": sum(passes(r, frozenset()) for r in items),
        "allExceptDonorArea": sum(passes(r, frozenset(("area",))) for r in items),
        "allExceptMinSide": sum(passes(r, frozenset(("minSide",))) for r in items),
        "allExceptAspect": sum(passes(r, frozenset(("aspect",))) for r in items),
        "allExceptThreeGeometryGates": sum(
            passes(r, frozenset(GEOMETRIC_GATES)) for r in items),
        "allExceptColorGates": sum(
            passes(r, frozenset(COLOR_GATES)) for r in items),
        "passContactGates": sum(
            all(r["gates"][g] for g in CONTACT_GATES) for r in items),
        "passIndependentColorGates": sum(
            all(r["gates"][g] for g in COLOR_GATES) for r in items),
    }
    for area_fraction in (.0015, .0030, .0050, .0100, .0200):
        results[f"areaOnlyUpTo{area_fraction:.4f}"] = sum(
            r["donorAreaFraction"] <= area_fraction
            and passes(r, frozenset(("area",))) for r in items)
    # Optimistic geometry-only parameters; still all other guardrails.
    results["geometryRelaxedMinSide3Aspect5Area2pct"] = sum(
        r["donorAreaFraction"] <= .02
        and r["donorMinSide"] >= 3
        and r["donorAspect"] <= 5
        and passes(r, frozenset(GEOMETRIC_GATES)) for r in items)
    return results


def write_histogram_image(output: Path, summaries: dict) -> None:
    """A supplementary PNG, no generative image operations."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    if font_path.exists():
        font = ImageFont.truetype(str(font_path), 19)
        titlefont = ImageFont.truetype(str(font_path), 25)
    else:
        font = ImageFont.load_default()
        titlefont = font
    labels = ("area", "minSide", "aspect", "paletteDistance",
              "sourceRgbDistance", "sharedEdges", "sharedRatio")
    width, height = 1150, 580
    img = Image.new("RGB", (width, height), (250, 250, 250))
    draw = ImageDraw.Draw(img)
    draw.text((30, 22), "v20: independent candidate gate failures (not first-fail counts)",
              fill=(22, 30, 39), font=titlefont)
    shades = ((40, 105, 164), (37, 140, 122), (187, 102, 48))
    max_value = max(1, max(
        summaries[case]["independentGateFailures"][gate]
        for case in CASES for gate in labels
    ))
    left = 225
    right = width - 50
    for j, gate in enumerate(labels):
        y = 95 + j * 60
        draw.text((25, y + 10), gate, fill=(32, 38, 42), font=font)
        for i, name in enumerate(CASES):
            value = summaries[name]["independentGateFailures"][gate]
            x1 = left + int(value / max_value * (right - left))
            y1 = y + i * 15
            draw.rectangle((left, y1, x1, y1 + 10), fill=shades[i])
            draw.text((x1 + 5, y1 - 6), str(value), fill=(25, 34, 42), font=font)
    for i, case in enumerate(CASES):
        draw.rectangle((30 + 255 * i, 535, 48 + 255 * i, 550), fill=shades[i])
        draw.text((58 + 255 * i, 529), case, fill=(25, 34, 42), font=font)
    img.save(output, optimize=True)


def analyze(case_paths: dict[str, Path], out: Path, baseline_root: Path | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    summaries = {}
    all_rows = []
    for name in CASES:
        folder = case_paths[name]
        record = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
        near = record["near"]["metadata"]
        actual = near.get("selectiveMergeCandidateGeometry")
        assert isinstance(actual, list) and actual, f"Missing v20 probe for {name}"
        assert near["selectiveMergeApplied"] == 0, f"Unexpected changed source: {name}"
        assert near["selectiveMergeEvaluated"] == len(actual), name
        assert sum(near["selectiveMergeRejectReasons"].values()) == len(actual), name
        assert record["uiVerification"]["pngPixelAndByteExactToDirectNear"], name
        assert (folder / "near.png").read_bytes() == (folder / "facet.png").read_bytes(), name
        if baseline_root:
            baseline = baseline_root / f"browser-merge-v19-{name}-20261008"
            assert sha256(baseline / "near.png") == sha256(folder / "near.png"), name
        for index, item in enumerate(actual):
            assert len(item["gates"]) == 11, (name, index)
            assert item["donorPixels"] >= 1
            assert item["donorBoxWidth"] >= 1 and item["donorBoxHeight"] >= 1
            assert item["sharedEdges"] >= 1
            assert item["donorPixels"] <= item["donorBoxWidth"] * item["donorBoxHeight"]
            assert item["donorId"] != item["recipientId"]
            gates = item["gates"]
            all_rows.append({"sample": name, "candidateIndex": index,
                             **{key: value for key, value in item.items()
                                if key not in ("gates", "donorBox")},
                             "donorBBox": ",".join(map(str,item["donorBox"])),
                             **{f"pass_{key}": value for key,value in gates.items()}})
        gates = actual[0]["gates"].keys()
        assert all(row["gates"].keys() == actual[0]["gates"].keys() for row in actual)
        gate_failures = {
            key: sum(not candidate["gates"][key] for candidate in actual)
            for key in gates
        }
        area_fail = [v for v in actual if not v["gates"]["area"]]
        summaries[name] = {
            "sourceSHA256": sha256(folder / "source.png"),
            "facetSHA256": sha256(folder / "facet.png"),
            "nearSHA256": sha256(folder / "near.png"),
            "identicalToFacet": True,
            "acceptedMerges": near["selectiveMergeApplied"],
            "neighborPairCount": len(actual),
            "firstFailingReasonCounts": near["selectiveMergeRejectReasons"],
            "independentGateFailures": gate_failures,
            "areaFailAndMinSidePass": sum(not r["gates"]["area"] and r["gates"]["minSide"]
                                         for r in actual),
            "areaFailAndAspectPass": sum(not r["gates"]["area"] and r["gates"]["aspect"]
                                        for r in actual),
            "areaFailButOtherGeometryPass": sum(
                not r["gates"]["area"] and r["gates"]["minSide"]
                and r["gates"]["aspect"] for r in actual),
            "donorPixels": quantiles([r["donorPixels"] for r in actual]),
            "donorMinimumWidth": quantiles([r["donorMinSide"] for r in actual]),
            "donorAspectRatio": quantiles([r["donorAspect"] for r in actual]),
            "sharedContactRatio": quantiles([r["sharedPerimeterFraction"] for r in actual]),
            "sourceRgbDistance": quantiles([r["sourceRgbDistance"] for r in actual]),
            "paletteRgbDistance": quantiles([r["paletteDistance"] for r in actual]),
            "donorAreaHistogram": histogram(
                [r["donorPixels"] for r in actual], AREAS),
            "donorMinSideHistogram": histogram(
                [r["donorMinSide"] for r in actual], WIDTH_BINS),
            "counterfactualCountsNOTApprovedMerges": independent_scenarios(actual),
        }
        print("V20_CASE",name,"pairs",len(actual),
              "firstFailure",near["selectiveMergeRejectReasons"],
              "independentArea/Width/Aspect",
              [gate_failures[k] for k in GEOMETRIC_GATES],
              "counters",summaries[name]["counterfactualCountsNOTApprovedMerges"],
              flush=True)

    with (out / "v20_candidate_rows.csv").open("w",encoding="utf-8-sig",newline="") as file:
        writer=csv.DictWriter(file, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    all_scenario = independent_scenarios([
        item for name in CASES
        for item in json.loads((case_paths[name]/"metrics.json").read_text(encoding="utf-8"))
                       ["near"]["metadata"]["selectiveMergeCandidateGeometry"]
    ])
    result={
        "status":"DIAGNOSTIC_ONLY_NO_PARAMETER_CHANGE",
        "source":"actual Chrome 154 BrowserFallback near with Facet baseline",
        "gateSemantics":"11 independent booleans per actual adjacency; counterfactuals do NOT prove safe merges",
        "mergeMode":"read-only; accepted=0 for three golden sources",
        "totalNeighborPairs":sum(summaries[n]["neighborPairCount"] for n in CASES),
        "totalFirstFailures":{
            reason:sum(summaries[n]["firstFailingReasonCounts"].get(reason,0)
                       for n in CASES)
            for reason in summaries["Kyoko"]["firstFailingReasonCounts"]
        },
        "totalIndependentFailures":{
            gate:sum(summaries[n]["independentGateFailures"][gate] for n in CASES)
            for gate in summaries["Kyoko"]["independentGateFailures"]
        },
        "totalCounterfactualCountsNOTApprovedMerges":all_scenario,
        "samples":summaries,
    }
    (out/"v20_distribution_metrics.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    header=[
        "# v20 BrowserFallback donor geometry distribution",
        "", "Research diagnostics, not production approval. Three original 340×340 golden inputs.",
        "Every actual adjacent pair is counted once with its smaller region as donor.",
        "No model changes, no threshold relaxation, no merges accepted. PNGs remain byte-identical to Facet v15.",
        "", "## Gate breakdown",
        "",
        "| Character | pairs | first-fail area/shape | independent area fail | min-width fail | aspect fail | contact ratio fail | median donor pixels | median min width |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in CASES:
        s=summaries[name];g=s["independentGateFailures"]
        header.append(f"| {name} | {s['neighborPairCount']} | {s['firstFailingReasonCounts']['donorAreaOrAspect']} | {g['area']} | {g['minSide']} | {g['aspect']} | {g['sharedRatio']} | {s['donorPixels']['median']} | {s['donorMinimumWidth']['median']} |")
    header.extend([
        "", "## Isolated-counterfactual candidate counts",
        "Counts are qualifying PAIRS under hypothetical filters, not accepted merges, fidelity proofs or expected region reduction.",
        "",
        "| Diagnostic scenario | qualifying pairs across all three |",
        "| --- | ---: |",
    ])
    for scenario,count in all_scenario.items():
        header.append(f"| `{scenario}` | {count} |")
    header.extend([
        "", "## Interpretation",
        "- The prior first-fail category `donorAreaOrAspect` hides three independent constraints. Their overlap is measured above.",
        "- The label `maxSmallFraction=0.0015` allows at most about 173 pixels in a 340×340 work raster; broad colored regions can be far larger.",
        "- Candidate probes do not reassign any pixel, palette, boundary or contour. Production Facet, v17, v18 and v19 are unchanged.",
        "- Loosening donor area, min-width, or aspect filters alone is **not a proven safe integration**: all palette/contact and final raster checks still apply.",
        "- Follow-up v21 must test specific ranked candidates with one-merge transactions, exact rendered-PNG rollback, and protected thin-feature ROI constraints.",
        "- Do not force a 40→30 cut, recreate missing facial features, or deploy research artifacts without a demonstrated visual gain.",
        "",
        "## Files",
        "`v20_distribution_metrics.json`, `v20_candidate_rows.csv`, `v20_distribution_chart.png`, this report and raw source/Facet/near Chrome evidence.",
    ])
    (out/"v20_distribution_report.md").write_text("\n".join(header)+"\n",encoding="utf-8")
    write_histogram_image(out/"v20_distribution_chart.png",summaries)
    print("V20_AGGREGATE",json.dumps(result["totalCounterfactualCountsNOTApprovedMerges"]),flush=True)
    return result


def main():
    p=argparse.ArgumentParser()
    for case in CASES:
        p.add_argument("--"+case.lower(),type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--baseline-root",type=Path)
    a=p.parse_args()
    analyze({case:getattr(a,case.lower()) for case in CASES},a.out,a.baseline_root)


if __name__=="__main__":
    main()
