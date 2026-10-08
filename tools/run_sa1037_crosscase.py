"""SA10.37 independent image and SVG self-intersection research hard gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCHEMA = "sa10.37-topology-locked-apparel-geometry-v1"


def aggregate_cases(reports: dict[str,dict]) -> dict:
    if len(reports) < 2:
        raise ValueError("two distinct character sources are required")
    sources=set()
    resolved=0
    safely_skipped=0
    failed=[]
    summaries={}
    for name,case in sorted(reports.items()):
        if case.get("schema") != SCHEMA:
            raise ValueError(f"unknown SA10.37 metrics: {name}")
        sha=case.get("case_source_sha256")
        if not isinstance(sha,str) or len(sha)!=64 or sha in sources:
            raise ValueError(f"invalid or duplicate source: {name}")
        sources.add(sha)
        common=(
            case.get("Stage04_source_masks_verified") is True
            and case.get("Stage08_outer_sha_verified") is True
            and case.get("Stage36_material_provenance_verified") is True
            and case.get("Stage36_original_RGB_pixel_replay_equal") is True
            and case.get("face_left_right_arm_rgb_unchanged") is True
            and case.get("pixels_modified_outside_lower_body_owner")==0
            and case.get("existing_outer_primitive_count")==11
            and case.get("apparel_subpaths_before")==case.get("apparel_subpaths_after")
            and case.get("production_promotion_authorized") is False
        )
        if case.get("status")=="RESEARCH_GEOMETRIC_VERTEX_REDUCTION_HOLD":
            resolved+=1
            valid=(
                case.get("all_filled_polygons_simple") is True
                and case.get("candidate_self_intersecting_panels")==[]
                and bool(case.get("baseline_self_intersecting_panels"))
                and case.get("original_total_vertices")==36
                and case.get("candidate_total_vertices",999)<=30
                and case.get("saved_vertices",0)>=6
                and case.get("source_color_nonregression_gate") is True
                and case.get("material_precision_gate") is True
                and case.get("necktie_source_width_protected") is True
                and case.get("original_apparel_color_lab_mse",0)>0
                and case.get("optimized_apparel_color_lab_mse",99999)
                    <=case.get("original_apparel_color_lab_mse",0)*1.02
                and case.get("apparel_subpaths_before")==5
            )
        elif case.get("status")=="NONMATCHING_CASE_NO_OP":
            safely_skipped+=1
            valid=(
                case.get("apparel_subpaths_before")==0
                and case.get("apparel_subpaths_after")==0
                and case.get("saved_vertices")==0
                and case.get("original_total_vertices")==0
                and case.get("candidate_total_vertices")==0
                and case.get("candidate_preview_sha256")==case.get("baseline_source36_preview_sha256")
            )
        else:
            valid=False
        if not (common and valid):
            failed.append(name)
        summaries[name]={
            "gate":"PASS" if common and valid else "FAIL",
            "status":case.get("status"),
            "material_vertices_before_after":[case.get("original_total_vertices"),case.get("candidate_total_vertices")],
            "self_intersection_before_after":[case.get("baseline_self_intersecting_panels",[]),case.get("candidate_self_intersecting_panels",[])],
            "apparel_rgb_mse_improvement":case.get("apparel_lab_mse_improvement_from_stage36"),
        }
    passed=not failed and resolved>=1 and safely_skipped>=1
    return {
        "schema":"sa10.37-multicase-apparel-simplification-v1",
        "source_count":len(sources),
        "corrected_case_count":resolved,
        "unrelated_character_noop_count":safely_skipped,
        "cases":summaries,
        "research_gate":"PASS" if passed else "FAIL",
        "failed_cases":failed,
        "production_promotion_authorized":False,
        "open_release_gates":[
            "OVERALL_OUTER_VERTEX_BUDGET_NOT_MET",
            "BROWSER_SVG_CLIPPING_AND_RASTER_PARITY_NOT_PASSED",
            "HUMAN_VISUAL_APPROVAL_REQUIRED",
        ],
        "status":"RESEARCH_GEOMETRY_CLEANUP_COMPLETE_NO_GO" if passed else "HOLD_INCOMPLETE_EVIDENCE",
    }


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--case",action="append",required=True,help="Case=metrics.json")
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    cases={}
    for spec in args.case:
        if "=" not in spec:
            raise ValueError("use Case=path")
        name,path=spec.split("=",1)
        if not name.strip() or name in cases:
            raise ValueError("duplicate or blank case")
        cases[name]=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    report=aggregate_cases(cases)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if report["research_gate"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
