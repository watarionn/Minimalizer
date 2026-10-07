from __future__ import annotations

import argparse, hashlib, json, shutil
from pathlib import Path
import cv2
import numpy as np

from minimalizer_zerobase.image_io import read_cv_image
from minimalizer_zerobase.simplification import StyleSimplificationPolicy, simplify_composed_scene, write_phase12_artifacts
from minimalizer_zerobase.simplification.animeseg_source_constraints import build_source_constraints_from_files
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
    source_mask=cv2.imread(str(a.phase4.parent/"phase_03/03_subject_mask.png"),0)>0
    def gates(result):
        rgb=cv2.cvtColor(cv2.imread(str(a.output/"baseline/12_final.png" if result is results["baseline"] else a.output/"animeseg_opt_in/12_final.png")),cv2.COLOR_BGR2RGB)
        bg=np.median(np.r_[rgb[:4,:4].reshape(-1,3),rgb[-4:,-4:].reshape(-1,3)],axis=0); cand=np.any(np.abs(rgb.astype(np.int16)-bg.astype(np.int16))>3,axis=2)
        shape=evaluate_source_shape_evidence(source_mask,cand); hard=evaluate_structural_hard_evidence(source_masks=masks,candidate_masks={k:cand&v for k,v in masks.items()}); anatomy=evaluate_source_silhouette_anatomy(source_mask,cand,fragmentation_penalty=0.0,anatomy_evidence={"required_parts":["head","torso","left_arm","right_arm","face"],"retained_parts":[k for k,v in masks.items() if v.any()],"shape_matching":shape.get("match_shapes_i1"),"perceptual":"observer-only"})
        return {"source_silhouette":shape,"topology":hard.to_dict(),"anatomy":anatomy,"primitive_count":len(result.selected.primitives),"face_detail_count":sum("animeseg-" in str(p.get("source_guided_kind")) and p.get("composition_part")=="face" for p in result.selected.primitives),"pass":bool(anatomy.get("gate")=="PASS" and hard.anatomy_pass and hard.topology_pass)}
    metrics={"schema":"sa10.30-real-gc001-v1","source_sha256":sha(a.source),"phase11_stage_sha256":sha(a.phase11/"stage.json"),"animeseg_sha256":sha(a.animeseg),"phase11_selected_primitive_count":results["baseline"].validation["phase11_primitive_count"],"baseline":gates(results["baseline"]),"candidate":gates(results["animeseg_opt_in"]),"output_sha256":{"baseline_png":sha(a.output/"baseline/12_final.png"),"candidate_png":sha(a.output/"animeseg_opt_in/12_final.png")},"decision":{"candidate_output_changed":sha(a.output/"baseline/12_final.png")!=sha(a.output/"animeseg_opt_in/12_final.png"),"production_promotion":False,"status":"HOLD_NO_OUTPUT_DELTA"}}
    (a.output/"metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(metrics["decision"],ensure_ascii=False)); return 0
if __name__=="__main__": main()
