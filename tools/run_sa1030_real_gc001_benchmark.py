from __future__ import annotations

import argparse, hashlib, json, shutil
from pathlib import Path
import cv2
import numpy as np

from minimalizer_zerobase.image_io import read_cv_image
from minimalizer_zerobase.simplification import StyleSimplificationPolicy, simplify_composed_scene, write_phase12_artifacts
from minimalizer_zerobase.simplification.animeseg_source_constraints import build_source_constraints_from_files, source_bound_detail_groups
from minimalizer_zerobase.evaluation.source_shape_evidence import evaluate_source_shape_evidence
from minimalizer_zerobase.evaluation.source_silhouette_anatomy_gate import evaluate_source_silhouette_anatomy
from minimalizer_zerobase.evaluation.structural_hard_evidence import evaluate_structural_hard_evidence

def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def svg(result, path: Path):
    c = result.selected.primitives
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{result.width}" height="{result.height}" viewBox="0 0 {result.width} {result.height}">']
    for p in c:
        q=p["parameters"]; color="#%02x%02x%02x"%tuple(p["palette_color_rgb"]); pts=q.get("components")
        if pts:
            for comp in pts: lines.append(f'<polygon fill="{color}" points="{" ".join(f"{x},{y}" for x,y in comp)}"/>')
    lines.append('</svg>\n'); path.write_text("\n".join(lines), encoding="utf-8")

def detail_overlay(constraints, source_rgba, path: Path, svg_path: Path):
    """Persist source-clipped AnimeSeg detail evidence for review only."""
    h, w = source_rgba.shape[:2]
    canvas = cv2.cvtColor(source_rgba[..., :3], cv2.COLOR_RGB2BGR).copy()
    rows = []
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    for group in source_bound_detail_groups(dict(constraints), source_rgba):
        mask = group["mask"].astype(np.uint8)
        color = tuple(int(v) for v in group["color"])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(canvas, contours, -1, color[::-1], 2)
        polygon_count = 0
        for contour in contours:
            points = cv2.approxPolyDP(contour, 0.0, True)[:, 0, :]
            if len(points) < 3:
                continue
            polygon_count += 1
            pairs = " ".join(f"{int(x)},{int(y)}" for x, y in points)
            lines.append(f'<polygon fill="#{color[0]:02x}{color[1]:02x}{color[2]:02x}" points="{pairs}"/>')
        rows.append({"source_guided_kind": group["source_guided_kind"], "material_owner": group["part"], "pixel_count": int(mask.sum()), "polygon_count": polygon_count, "source_rgb_median": list(color), "alpha_clipped": True, "authority": False})
    lines.append('</svg>\n')
    cv2.imwrite(str(path), canvas)
    svg_path.write_text("\n".join(lines), encoding="utf-8")
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source",type=Path,required=True); ap.add_argument("--phase11",type=Path,required=True); ap.add_argument("--phase4",type=Path,required=True); ap.add_argument("--animeseg",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    raw=read_cv_image(a.source,cv2.IMREAD_UNCHANGED); rgba=cv2.cvtColor(raw,cv2.COLOR_BGRA2RGBA)
    masks={p.stem:cv2.imread(str(p),0)>0 for p in (a.phase4/"part_masks").glob("*.png")}
    payload=json.loads((a.phase11/"11_composition.json").read_text(encoding="utf-8")); cons=build_source_constraints_from_files(a.source,a.animeseg)
    a.output.mkdir(parents=True,exist_ok=True); results={}
    for name, policy, constraints in (("baseline",StyleSimplificationPolicy(),None),("animeseg_opt_in",StyleSimplificationPolicy(animeseg_source_detail_geometry=True),cons)):
        out=a.output/name; out.mkdir(exist_ok=True)
        result=simplify_composed_scene(payload,policy=policy,source_rgba=rgba,source_part_masks=masks,animeseg_source_constraints=constraints)
        write_phase12_artifacts(a.source,a.phase11,result,out,config=policy.to_dict(),phase11_stage=json.loads((a.phase11/"stage.json").read_text()),phase4_dir=a.phase4,phase4_stage=json.loads((a.phase4/"stage.json").read_text()))
        svg(result,out/(name+".svg")); results[name]=result
        if constraints is not None:
            detail_rows = detail_overlay(constraints, rgba, out/"post_repair_detail_overlay.png", out/"post_repair_detail_overlay.svg")
            (out/"post_repair_detail_metrics.json").write_text(json.dumps({"schema":"sa10.31-post-repair-detail-v1","groups":detail_rows,"primitive_budget":{"max_detail_polygons":32,"used":sum(r["polygon_count"] for r in detail_rows)},"authority":False,"rollback_on_hard_gate_fail":True},ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    source_mask=cv2.imread(str(a.phase4.parent/"phase_03/03_subject_mask.png"),0)>0
    def gates(result):
        rgb=cv2.cvtColor(cv2.imread(str(a.output/"baseline/12_final.png" if result is results["baseline"] else a.output/"animeseg_opt_in/12_final.png")),cv2.COLOR_BGR2RGB)
        bg=np.median(np.r_[rgb[:4,:4].reshape(-1,3),rgb[-4:,-4:].reshape(-1,3)],axis=0); cand=np.any(np.abs(rgb.astype(np.int16)-bg.astype(np.int16))>3,axis=2)
        shape=evaluate_source_shape_evidence(source_mask,cand); hard=evaluate_structural_hard_evidence(source_masks=masks,candidate_masks={k:cand&v for k,v in masks.items()}); anatomy=evaluate_source_silhouette_anatomy(source_mask,cand,fragmentation_penalty=0.0,anatomy_evidence={"required_parts":["head","torso","left_arm","right_arm","face"],"retained_parts":[k for k,v in masks.items() if v.any()],"shape_matching":shape.get("match_shapes_i1"),"perceptual":"observer-only"})
        return {"source_silhouette":shape,"topology":hard.to_dict(),"anatomy":anatomy,"primitive_count":len(result.selected.primitives),"face_detail_count":sum("animeseg-" in str(p.get("source_guided_kind")) and p.get("composition_part")=="face" for p in result.selected.primitives),"pass":bool(anatomy.get("gate")=="PASS" and hard.anatomy_pass and hard.topology_pass)}
    baseline_gate = gates(results["baseline"]); candidate_gate = gates(results["animeseg_opt_in"])
    detail_metrics = json.loads((a.output/"animeseg_opt_in/post_repair_detail_metrics.json").read_text(encoding="utf-8"))
    hard_gate_pass = bool(candidate_gate["pass"])
    metrics={"schema":"sa10.31-real-gc001-v1","source_sha256":sha(a.source),"phase11_stage_sha256":sha(a.phase11/"stage.json"),"animeseg_sha256":sha(a.animeseg),"phase11_selected_primitive_count":results["baseline"].validation["phase11_primitive_count"],"baseline":baseline_gate,"candidate":candidate_gate,"post_repair_detail":detail_metrics,"output_sha256":{"baseline_png":sha(a.output/"baseline/12_final.png"),"candidate_png":sha(a.output/"animeseg_opt_in/12_final.png")},"decision":{"candidate_output_changed":sha(a.output/"baseline/12_final.png")!=sha(a.output/"animeseg_opt_in/12_final.png"),"detail_evidence_polygon_count":detail_metrics["primitive_budget"]["used"],"hard_gate_pass":hard_gate_pass,"rollback":not hard_gate_pass,"production_promotion":False,"status":"HOLD_ROLLBACK_HARD_GATE_FAIL" if not hard_gate_pass else "HOLD_NO_OUTPUT_DELTA"}}
    (a.output/"metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(metrics["decision"],ensure_ascii=False)); return 0
if __name__=="__main__": main()
