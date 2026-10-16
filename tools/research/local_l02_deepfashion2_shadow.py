"""Standalone DeepFashion2 ONNX source-only research shadow, NEVER production owner.

Separate independent prediction from human-label evaluation. Requires numpy, cv2,
PIL and onnxruntime ONLY when running actual inference. Never downloads weights.
"""
from __future__ import annotations
import argparse,base64,hashlib,io,json,zipfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image

MODEL_SHA='485bc106721febbd82fe24297e12a9fb49a435a552afff1e6b76308716555f76'
SOURCES={
'H04':('H04_original_signed_trace (1).json','7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3'),
'H06':('H06_trace.json','c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8'),
'H08':('H08_trace.json','759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e')}
OUTERWEAR_IDS=(2,3)
CONFIDENCE=0.50

class ResearchHold(ValueError):pass

def preprocess_rgba(src, side=416):
    if src.ndim!=3 or src.shape[-1]!=4 or src.dtype!=np.uint8:
        raise ResearchHold('INVALID_SIGNED_SOURCE')
    h,w=src.shape[:2];s=min(side/w,side/h)
    rw,rh=round(w*s),round(h*s)
    rgb=np.rint(src[:,:,:3].astype('float32')*(src[:,:,3:4]/255.)+255*(1-src[:,:,3:4]/255.)).astype('uint8')
    im=cv2.resize(rgb,(rw,rh),interpolation=cv2.INTER_AREA)
    x,y=(side-rw)//2,(side-rh)//2
    pad=np.full((side,side,3),255,np.uint8);pad[y:y+rh,x:x+rw]=im
    return pad.transpose(2,0,1)[None].astype('float32')/255.,(x,y,rw,rh)

def decode_source_only(rows,proto,meta,alpha,confidence=CONFIDENCE):
    """ONNX output: 300 NMS entries [xyxy,conf,class,32 mask coeffs], 32x104x104 proto."""
    if rows.shape!=(300,38) or proto.shape!=(32,104,104):raise ResearchHold('UNEXPECTED_ONNX_OUTPUT_CONTRACT')
    if not np.isfinite(rows).all() or not np.isfinite(proto).all():raise ResearchHold('NONFINITE_MODEL_OUTPUT')
    if alpha.ndim!=2 or alpha.dtype!=bool:raise ResearchHold('INVALID_ALPHA')
    x,y,rw,rh=meta;h,w=alpha.shape;side=416
    if min(rw,rh)<1 or x<0 or y<0 or x+rw>side or y+rh>side:raise ResearchHold('INVALID_LETTERBOX')
    out=np.zeros(alpha.shape,bool);counts={};invalid=0;nouter=0
    for row in rows:
        if float(row[4])<confidence:continue
        cid=int(round(float(row[5])));counts[str(cid)]=counts.get(str(cid),0)+1
        if cid not in OUTERWEAR_IDS:continue
        nouter+=1
        x1,y1,x2,y2=(float(v) for v in row[:4])
        if x2<=x1 or y2<=y1:invalid+=1;continue
        raw=np.asarray(row[6:38],dtype=np.float32)@proto.reshape(32,-1)
        logits=raw.reshape(104,104)
        prob=1/(1+np.exp(-np.clip(logits,-60,60)))
        mask=cv2.resize(prob,(side,side),interpolation=cv2.INTER_LINEAR)>.5
        yy,xx=np.indices((side,side))
        mask&=(xx>=x1)&(xx<=x2)&(yy>=y1)&(yy<=y2)
        out|=cv2.resize(mask[y:y+rh,x:x+rw].astype('uint8'),(w,h),interpolation=cv2.INTER_NEAREST)>0
    out&=alpha
    return out,{'detected_classes':counts,'outwear_instances':nouter,'invalid_boxes':invalid,
                'candidate_source_px':int(out.sum()),'source_pixels_generated':0,
                'owner_promotion_authorized':False}

def evaluate_review(zip_obj,case,alpha,pred):
    manifest=json.loads(zip_obj.read('MANIFEST_SHA256.json'))
    target=f'reviews/{case}_HUMAN_VISIBLE_MASKS_PRIVATE.npz'
    buf=zip_obj.read(target)
    if hashlib.sha256(buf).hexdigest()!=manifest[target]:raise ResearchHold('SIGNED_REVIEW_NPZ_SHA_MISMATCH')
    with np.load(io.BytesIO(buf)) as masks:
        if not np.array_equal(masks['opaque']>0,alpha):raise ResearchHold('REVIEW_ALPHA_MISMATCH')
        pos=masks['outerwear']>0
        neg=np.logical_or.reduce([masks[k]>0 for k in ('underlayer','arm_skin','neck_skin','lower_body','face_skin','hair','accessory')])
    if np.any(pos&neg):raise ResearchHold('HUMAN_OWNER_OVERLAP')
    tp=int((pred&pos).sum());fp=int((pred&neg).sum());fn=int((~pred&pos).sum())
    unknown=alpha&~(pos|neg)
    return {'known_only_iou':round(tp/max(1,tp+fp+fn),6),
            'positive_recall':round(tp/max(1,tp+fn),6),
            'known_negative_fp_rate':round(fp/max(1,int(neg.sum())),6),
            'unknown_predicted_px':int((pred&unknown).sum()),
            'unknown_source_px':int(unknown.sum()),
            'tp':tp,'fp_known':fp,'fn':fn,
            'prediction_sha256':hashlib.sha256(pred.tobytes()).hexdigest()}

def run(private_archive:Path,onnx_model:Path,private_output_zip:Path):
    if hashlib.sha256(onnx_model.read_bytes()).hexdigest()!=MODEL_SHA:raise ResearchHold('UNVERIFIED_MODEL_WEIGHTS')
    import onnxruntime as ort
    opt=ort.SessionOptions();opt.intra_op_num_threads=2
    sess=ort.InferenceSession(str(onnx_model),sess_options=opt,providers=['CPUExecutionProvider'])
    if (tuple(sess.get_inputs()[0].shape)!=(1,3,416,416) or
        tuple(sess.get_outputs()[0].shape)!=(1,300,38) or
        tuple(sess.get_outputs()[1].shape)!=(1,32,104,104)):
        raise ResearchHold('UNEXPECTED_ONNX_SIGNATURE')
    data={};predictions={}
    with zipfile.ZipFile(private_archive) as z:
        manifest=json.loads(z.read('MANIFEST_SHA256.json'))
        for case,(filename,sha) in SOURCES.items():
            path='signed_human_review/'+filename
            refbytes=z.read(path)
            if hashlib.sha256(refbytes).hexdigest()!=manifest[path]:raise ResearchHold('SIGNED_REVIEW_JSON_SHA_MISMATCH')
            d=json.loads(refbytes)
            src_bytes=base64.b64decode(d['image']['dataURL'].split(',',1)[1],validate=True)
            if hashlib.sha256(src_bytes).hexdigest()!=sha:raise ResearchHold('SIGNED_SOURCE_BYTES_SHA_MISMATCH')
            src=np.asarray(Image.open(io.BytesIO(src_bytes)).convert('RGBA'),np.uint8)
            h,w=src.shape[:2]
            if d['canvas']!={'width':w,'height':h}:raise ResearchHold('SOURCE_CANVAS_MISMATCH')
            tensor,meta=preprocess_rgba(src)
            rows,proto=sess.run(None,{'images':tensor})
            pred,diag=decode_source_only(rows[0],proto[0],meta,src[:,:,3]>0)
            evaluation=evaluate_review(z,case,src[:,:,3]>0,pred)
            data[case]={'signed_source_sha256':sha,'native_wh':[w,h],**diag,**evaluation}
            predictions[case]=pred.astype('uint8')
    report={'schema':'minimalizer/l02/deepfashion2-source-only-shadow/v1',
       'model_repo':'HasanKabir23/Yolov26s-DeepFashion2','model_sha256':MODEL_SHA,
       'fixed_network_input':[416,416],'confidence':CONFIDENCE,
       'outerwear_class_ids':list(OUTERWEAR_IDS),
       'original_source_and_manual_annotations_immutable':True,
       'human_annotation_used_in_inference':False,'owner_promotion_authorized':False,
       'L02_status':'HOLD','Golden_status':'HOLD','production':'NO_GO','cases':data}
    payload=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode('utf8')
    private_output_zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(private_output_zip,'w',compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr('SOURCEFREE_METRICS.json',payload)
        for case,arr in predictions.items():
            f=io.BytesIO();np.savez_compressed(f,prediction=arr)
            output.writestr(f'{case}_DEEPFASHION2_OUTERWEAR_PRIVATE.npz',f.getvalue())
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_signed_review_zip',type=Path)
    p.add_argument('onnx_model_file',type=Path)
    p.add_argument('private_output_zip',type=Path)
    args=p.parse_args()
    result=run(args.private_signed_review_zip,args.onnx_model_file,args.private_output_zip)
    print(json.dumps(result,indent=2,ensure_ascii=False))
