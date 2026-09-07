from __future__ import annotations
import csv, json
from dataclasses import replace
from pathlib import Path
from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.io.image_exporter import export_png

root=Path(__file__).parents[1]
corpus=root/'tests/assets/corpus'
out=root/'examples/near_background_rc7'
out.mkdir(parents=True,exist_ok=True)
files=sorted(p for p in corpus.iterdir() if p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'})
rows=[]
for p in files:
    base=MinimalizeConfig.from_level(4,analysis_max_side=220,target_max_shapes=36,line_mode='none',enable_auto_retry=False,enable_character_auto_retry=False)
    off=minimalize(p, replace(base, shape_value_near_background_max_color_distance=-1.0))
    on=minimalize(p, base)
    export_png(off,out/f'{p.stem}_off.png')
    export_png(on,out/f'{p.stem}_on.png')
    qo,qn=off.metadata.get('quality',{}),on.metadata.get('quality',{})
    vr=on.metadata.get('global_shape_value',{})
    near=sum(1 for d in vr.get('decisions',[]) if d.get('reason')=='near_background_fragment' and d.get('action')=='remove')
    row={
      'file':p.name,'subject':bool(on.metadata.get('subject_mode')),
      'shapes_off':len(off.shapes),'shapes_on':len(on.shapes),'removed_near_background':near,
      'quality_off':qo.get('score'),'quality_on':qn.get('score'),
      'identity_off':qo.get('identity_score'),'identity_on':qn.get('identity_score'),
      'minimality_off':qo.get('minimality_score'),'minimality_on':qn.get('minimality_score'),
      'silhouette_off':qo.get('silhouette_similarity'),'silhouette_on':qn.get('silhouette_similarity'),
    }
    rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
with (out/'report.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def mean(k):
    vals=[float(r[k]) for r in rows if r[k] is not None]; return sum(vals)/len(vals) if vals else None
summary={
 'images':len(rows),'changed_images':sum(r['removed_near_background']>0 for r in rows),
 'removed_near_background':sum(r['removed_near_background'] for r in rows),
 'mean_shapes_off':mean('shapes_off'),'mean_shapes_on':mean('shapes_on'),
 'mean_quality_off':mean('quality_off'),'mean_quality_on':mean('quality_on'),
 'mean_identity_off':mean('identity_off'),'mean_identity_on':mean('identity_on'),
 'mean_minimality_off':mean('minimality_off'),'mean_minimality_on':mean('minimality_on'),
 'mean_silhouette_off':mean('silhouette_off'),'mean_silhouette_on':mean('silhouette_on'),
}
(out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
