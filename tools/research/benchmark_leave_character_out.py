"""Research-only leave-one-character-out outerwear benchmark.
Human annotations are used ONLY to construct train split labels and evaluate
held-out character, never as a feature at test time. No release authorization.
"""
from __future__ import annotations
import sys,json,hashlib
from pathlib import Path
import numpy as np,cv2
from sklearn.ensemble import HistGradientBoostingClassifier
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_reviewed_annotations import inspect,PINS,NAMES,SVG
from local_l02_manual_supervised_shadow import source_features,MODEL_PARAMETERS

SEED=20261016
SIZE=900

def prepare(base:Path,case:str,kind:str):
    score,raw,alpha,labels,top=inspect(base/NAMES[case],case,base/SVG[case] if case in SVG else None)
    h,w=alpha.shape
    fraction=min(1.0,SIZE/max(h,w))
    wh=(max(1,round(w*fraction)),max(1,round(h*fraction)))
    if (w,h)!=wh:
        source=cv2.resize(raw,wh,interpolation=cv2.INTER_AREA)
        # Resize alpha independently nearest to faithfully preserve original source support.
        source[:,:,3]=cv2.resize(raw[:,:,3],wh,interpolation=cv2.INTER_NEAREST)
        aa=source[:,:,3]>0
        pos=cv2.resize(labels['outerwear'].astype('uint8'),wh,interpolation=cv2.INTER_NEAREST)>0
        marked=cv2.resize(top.astype('uint8'),wh,interpolation=cv2.INTER_NEAREST)>0
        explicitneg=(cv2.resize((labels['underlayer']|labels['arm_skin']|labels['face_skin']|labels['neck_skin']|labels['lower_body']|labels['hair']|labels['accessory']).astype('uint8'),wh,interpolation=cv2.INTER_NEAREST)>0)
    else:
        source=raw.copy();aa=alpha.copy();pos=labels['outerwear'].copy();marked=top.copy();explicitneg=marked&~pos
    pos &=aa;marked &=aa;explicitneg&=aa&~pos
    known=pos|explicitneg
    features=source_features(source).astype('float32')
    return {'case':case,'source':source,'features':features,'alpha':aa,'positive':pos,
     'known':known,'negative':explicitneg,'marked':marked,'size':wh,'original_wh':[w,h], 'known_negative_count':int(explicitneg.sum())}

def sample_train(cases,limit=15000,negative_method='all_alpha'):
    rng=np.random.default_rng(SEED)
    Xs=[];ys=[];case_counts={}
    for t in cases:
        pos=np.flatnonzero(t['positive'].ravel());
        if negative_method=='known':neg=np.flatnonzero(t['negative'].ravel());
        else:neg=np.flatnonzero((t['alpha']&~t['positive']).ravel())
        if len(pos)<100 or len(neg)<100:raise ValueError('Insufficient class support')
        pi=rng.choice(pos,min(limit,len(pos)),replace=False)
        ni=rng.choice(neg,min(limit,len(neg)),replace=False)
        sel=np.r_[pi,ni]
        Xs.append(t['features'].reshape(-1,18)[sel]);ys.append(np.r_[np.ones(len(pi),np.uint8),np.zeros(len(ni),np.uint8)])
        case_counts[t['case']]={'positive_training_px':len(pi),'negative_training_px':len(ni)}
    return np.concatenate(Xs),np.concatenate(ys),case_counts

def predict(test,model):
    indices=np.flatnonzero(test['alpha'].ravel())
    x=test['features'].reshape(-1,18)
    out=np.zeros(test['alpha'].size,bool)
    for i in range(0,len(indices),20000):
        ids=indices[i:i+20000]
        out[ids]=model.predict_proba(x[ids])[:,1]>=.5
    return out.reshape(test['alpha'].shape)

def score(test,pred):
    y=test['positive'];neg=test['negative'];known=test['known']
    tp=int((y&pred).sum());fn=int((y&~pred).sum());fp=int((neg&pred).sum());
    assert not np.any(pred&~test['alpha'])
    # unknown underlays are not counted as negatives in label-restricted IoU
    restricted=tp/max(1,tp+fn+fp)
    rawfp=int((pred&test['alpha']&~known).sum())
    return {'labelled_only_iou':round(restricted,6),'labelled_only_precision':round(tp/max(1,tp+fp),6),
      'positive_recall':round(tp/max(1,tp+fn),6),'known_negative_fp_rate':round(fp/max(1,int(neg.sum())),6),
      'unknown_predicted_px':rawfp,'unknown_fraction_predicted':round(rawfp/max(1,int((test['alpha']&~known).sum())),6),
      'all_alpha_treat_unlabelled_negative_iou_DIAGNOSTIC_ONLY':round(tp/max(1,tp+fn+fp+rawfp),6),
      'tp':tp,'fn':fn,'fp_known_negative':fp,'pred_total_px':int(pred.sum()),'annotated_jacket_px':int(y.sum())}

def run(data_dir,output_dir):
    data_dir=Path(data_dir);output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    data={case:prepare(data_dir,case,'outerwear') for case in PINS}
    results={'schema':'minimalizer/l02/independent_manual_character_holdout/v1','evaluation_date':'2026-10-16','image_long_side_for_diagnostic':SIZE,
      'precommitted_training_samples_per_class_per_image':15000,'prediction_threshold':0.5,'one_character_per_fold':True,
      'inference_uses_manual_pixels_or_mask':False,'unlabelled_regions_are_not_verified_negative':True,
      'source_sha256s':PINS, 'folds':{},'quality_release':'HOLD','production_release':'NO_GO',
      'model':{'type':'HistGradientBoostingClassifier','params':MODEL_PARAMETERS},'training_negative_assumption':'unannotated opaque pixels used only for sampling presumed negatives'}
    for case,test in data.items():
        train_cases=[v for key,v in data.items() if key!=case]
        X,y,n=sample_train(train_cases)
        model=HistGradientBoostingClassifier(**MODEL_PARAMETERS)
        model.fit(X,y)
        p=predict(test,model)
        stats=score(test,p)
        results['folds'][case]={'held_out':case,'train_cases':[v['case'] for v in train_cases],'training':n,'test':stats,
          'test_original_wh':test['original_wh'],'test_eval_wh':list(test['size']),'test_known_negative_px':test['known_negative_count']}
        np.savez_compressed(output_dir/f'{case}_UNSEEN_OUTERWEAR_PRED_PRIVATE.npz',prediction=p.astype('uint8'),manual_jacket=test['positive'].astype('uint8'),
          known_negative=test['negative'].astype('uint8'),unknown=(test['alpha']&~test['known']).astype('uint8'))
        print('LOCO',case,stats,flush=True)
    (output_dir/'L02_LEAVE_ONE_CHARACTER_OUT_PRIVATE.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    return results
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
