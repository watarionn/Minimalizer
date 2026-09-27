from __future__ import annotations
import json, sys
from pathlib import Path
import cv2, numpy as np
ROOT=Path(__file__).parents[1]; sys.path.insert(0,str(ROOT))
from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.production import ProductionPipeline
from zerobase_migration_audit import CORPUS, metrics, render_zero

def main():
    m=json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
    for threshold in (0.05,0.10,0.25,0.50,0.75):
        vals=[]; counts=[]
        for case in m["cases"][:18]:
            src=cv2.imread(str(CORPUS/"inputs"/case["input_file"]),cv2.IMREAD_UNCHANGED)
            rgba=cv2.cvtColor(src,cv2.COLOR_BGRA2RGBA)
            ref=cv2.cvtColor(cv2.imread(str(CORPUS/"references"/case["approved_file"])),cv2.COLOR_BGR2RGB)
            ev=SLICRegionAdapter(min_foreground_ratio=threshold).analyze(rgba,CoordinateSpace(rgba.shape[1],rgba.shape[0]))
            if not ev: vals.append((0.0,1.0)); counts.append(0); continue
            result=ProductionPipeline().run(ev)
            mm=metrics(render_zero(result.vector_scene.to_dict()),ref)
            vals.append((mm["silhouette_iou"],mm["foreground_ratio_error"])); counts.append(len(result.vector_scene.primitives))
        print(threshold,round(float(np.mean([x[0] for x in vals])),6),round(float(np.mean([x[1] for x in vals])),6),round(float(np.mean(counts)),2),flush=True)
if __name__=="__main__": main()
