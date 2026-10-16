"""Replay pinned signed H06/H08 AnimeSeg observations as generic-clothes negatives.

Reads *private* signed JSON/SVG + class-map ZIP; emits source-free aggregate only.
Neither model inference nor saved masks are sent to production. H04 is not run
because its corresponding original class-map bytes are not in this input ZIP.
"""
from __future__ import annotations
import hashlib,io,json,sys,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_reviewed_annotations import inspect,NAMES,SVG,PINS
from local_l02_outerwear_observer_gate import ObserverSpec,source_only_candidate,known_only_evaluation

WEIGHTS_SHA='f6764a379496712a92d1a85f852a81155cd79132a3e050b77c972be7e1cec394'
CASE_ORDER=('H06','H08')

def replay(signed_human_dir, source_class_zip):
    z=zipfile.ZipFile(source_class_zip)
    recorded=json.loads(z.read('PRIVATE_FILE_SHA256_MANIFEST.json'))
    metrics={'schema':'minimalizer/local-l02/independent-generic-clothes-negative-control/v1',
             'model_id':'suzukimain/AnimeSeg-Mask2Former-v3-Run121',
             'model_weights_sha256':WEIGHTS_SHA,
             'input_semantic_scope':'GENERIC_CLOTHES_NOT_OUTERWEAR',
             'source_pixel_generation':False,'manual_labels_never_used_in_prediction':True,
             'cases':{},'not_run':{'H04':'H04 class-map not contained in this signed offline384 ZIP'},
             'L02':'HOLD','Golden':'HOLD','production':'NO_GO'}
    for c in CASE_ORDER:
        _, src, alpha, labels, top = inspect(Path(signed_human_dir)/NAMES[c],c,
            Path(signed_human_dir)/SVG[c])
        fn=f'{c}_ANIMESEG_384_CLASSIDS_PRIVATE.png'
        data=z.read(fn)
        if hashlib.sha256(data).hexdigest()!=recorded[fn]:
            raise ValueError('MODEL_OBSERVATION_BYTES_SHA_MISMATCH '+c)
        classes=np.asarray(Image.open(io.BytesIO(data)))
        if classes.dtype != np.uint8 or classes.shape!=alpha.shape:
            raise ValueError('INVALID_CLASS_GEOMETRY '+c)
        seen=set(np.unique(classes).tolist())
        names={int(i):('clothes' if int(i)==10 else 'class_'+str(i)) for i in seen}
        spec=ObserverSpec('AnimeSeg-v3/Run121',WEIGHTS_SHA,PINS[c],hashlib.sha256(classes.tobytes()).hexdigest(),names)
        candidate,decision=source_only_candidate(alpha,classes,spec)
        if decision['status']!='ABSTAIN_NO_OUTERWEAR_CLASS' or np.any(candidate):
            raise AssertionError('GENERIC_CLOTHES_FALSELY_PROMOTED')
        pos=labels['outerwear']
        neg=np.logical_or.reduce([labels[k] for k in labels if k!='outerwear'])
        raw=(classes==10)&alpha
        raw_evaluation=known_only_evaluation(alpha,pos,neg,raw)
        metrics['cases'][c]={'signed_source_sha256':PINS[c],
             'class_map_png_sha256':recorded[fn],
             'classid_10_source_only_diagnostic':raw_evaluation,
             'strict_observer_admission':decision}
    return metrics

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('usage: run_local_l02_animeseg_taxonomy_control.py PRIVATE_JSON_DIR PRIVATE_CLASS_ZIP SOURCE_FREE_OUTPUT_JSON')
    report=replay(sys.argv[1],sys.argv[2]);Path(sys.argv[3]).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
