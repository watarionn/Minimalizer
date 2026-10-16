"""MinimalizerLocal L02: pinned SegFormer fashion, NONCOMMERCIAL RESEARCH ONLY.

Only local signed-source RGBA enters inference. Human masks are read afterwards
for evaluation. No private pixels, vertices, weights or output NPZ in GitHub.
Requires existing torch/transformers; no runtime install or network download.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, zipfile
from pathlib import Path
import numpy as np
from PIL import Image

MODEL_REPO = "sayeed99/segformer-b2-fashion"
REVISION = "e82089f3b76fdc5522727f6e793ff3d470c15e74"
WEIGHTS_SHA = "47313d9daf8f759b803b0bf449a4719bcd5b5a46eacad343e99e9660f8cedec1"
MODEL_CONFIG_SHA = "44b342a5e9301a1716dac8a56537e82acfdae8f0597069b0414b7704e39b8705"
PROCESSOR_CONFIG_SHA = "6073ac6a37530ed2a19443d6a748f5579887b3ae48f6730073954b0b38cf3fd6"
CLASSES = {5: "jacket", 10: "coat"}
SOURCE_PINS = {
 "H04": ("H04_original_signed_trace (1).json","7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3"),
 "H06": ("H06_trace.json","c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8"),
 "H08": ("H08_trace.json","759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e"),
}
NEGATIVE_KEYS = ("underlayer","arm_skin","neck_skin","lower_body","face_skin","hair","accessory")
class AuthorityHold(ValueError): pass

def sha(blob): return hashlib.sha256(blob).hexdigest()

def validate_model_dir(model_dir:Path):
    required=("config.json","preprocessor_config.json","model.safetensors")
    if any(not (model_dir/name).is_file() for name in required):
        raise AuthorityHold("PINNED_MODEL_FILES_MISSING")
    if sha((model_dir/"model.safetensors").read_bytes())!=WEIGHTS_SHA:
        raise AuthorityHold("MODEL_WEIGHTS_SHA_MISMATCH")
    if sha((model_dir/"config.json").read_bytes())!=MODEL_CONFIG_SHA:
        raise AuthorityHold("MODEL_CONFIG_SHA_MISMATCH")
    if sha((model_dir/"preprocessor_config.json").read_bytes())!=PROCESSOR_CONFIG_SHA:
        raise AuthorityHold("PROCESSOR_CONFIG_SHA_MISMATCH")
    cfg=json.loads((model_dir/"config.json").read_text(encoding="utf-8"))
    labels=cfg["id2label"]
    if any(labels.get(str(k),"").lower()!=v for k,v in CLASSES.items()):
        raise AuthorityHold("OUTERWEAR_TAXONOMY_MISMATCH")
    return PROCESSOR_CONFIG_SHA

def signed_sample(archive:zipfile.ZipFile, case:str):
    name,pin=SOURCE_PINS[case]
    manifest=json.loads(archive.read("MANIFEST_SHA256.json"))
    f="signed_human_review/"+name
    data=archive.read(f)
    if sha(data)!=manifest[f]:raise AuthorityHold("SIGNATURE_REFERENCE_MISMATCH")
    doc=json.loads(data)
    raw=base64.b64decode(doc["image"]["dataURL"].split(",",1)[1],validate=True)
    if sha(raw)!=pin:raise AuthorityHold("SIGNATURE_SOURCE_MISMATCH")
    rgba=np.asarray(Image.open(io.BytesIO(raw)).convert("RGBA"),np.uint8)
    h,w=rgba.shape[:2]
    if doc["canvas"]!={"width":w,"height":h}:raise AuthorityHold("SIGNED_CANVAS_MISMATCH")
    return rgba

def to_model_rgb(rgba:np.ndarray):
    """Only source RGBA, never reviewed polygons, influences model input."""
    if rgba.dtype!=np.uint8 or rgba.ndim!=3 or rgba.shape[2]!=4:
        raise AuthorityHold("INVALID_RGBA")
    alpha=rgba[:,:,3:4].astype(np.float32)/255.
    return np.rint(rgba[:,:,:3].astype(np.float32)*alpha+(1-alpha)*255).astype(np.uint8)

def source_only_prediction(rgba,model,processor):
    import torch
    h,w=rgba.shape[:2]
    image=Image.fromarray(to_model_rgb(rgba),"RGB")
    inputs=processor(images=image,return_tensors="pt")
    with torch.inference_mode():
        logits=model(**inputs).logits
        up=torch.nn.functional.interpolate(logits.float(),size=(h,w),
                                            mode="bilinear",align_corners=False)
        labels=up.argmax(dim=1)[0].cpu().numpy()
    pred=np.isin(labels,list(CLASSES)) & (rgba[:,:,3]>0)
    if np.any(pred & (rgba[:,:,3]==0)):raise AuthorityHold("SOURCE_PIXEL_GENERATION")
    return pred

def known_only_score(alpha,positive,negative,pred):
    if any(x.shape!=alpha.shape or x.dtype!=np.dtype(bool)
           for x in (alpha,positive,negative,pred)):
        raise AuthorityHold("MASK_GEOMETRY_MISMATCH")
    if np.any(positive&negative):raise AuthorityHold("OVERLAPPING_HUMAN_LABELS")
    if np.any((positive|negative|pred)&~alpha):raise AuthorityHold("OUTSIDE_SIGNED_ALPHA")
    tp=int((pred&positive).sum());fp=int((pred&negative).sum())
    fn=int((~pred&positive).sum())
    unknown=alpha&~(positive|negative)
    return {"labelled_iou":round(tp/max(1,tp+fp+fn),6),
            "positive_recall":round(tp/max(1,tp+fn),6),
            "known_negative_fp_rate":round(fp/max(1,int(negative.sum())),6),
            "known_positive_px":int(positive.sum()),
            "known_negative_px":int(negative.sum()),
            "unknown_predicted_px":int((pred&unknown).sum()),
            "unknown_source_px":int(unknown.sum()),
            "candidate_source_px":int(pred.sum()),
            "tp":tp,"fp_known":fp,"fn":fn,
            "prediction_sha256":sha(pred.tobytes())}

def evaluate_review(archive,case,alpha,pred):
    manifest=json.loads(archive.read("MANIFEST_SHA256.json"))
    path=f"reviews/{case}_HUMAN_VISIBLE_MASKS_PRIVATE.npz"
    blob=archive.read(path)
    if sha(blob)!=manifest[path]:raise AuthorityHold("HUMAN_MASK_SHA_MISMATCH")
    with np.load(io.BytesIO(blob)) as m:
        if not np.array_equal(m["opaque"]>0,alpha):
            raise AuthorityHold("SIGNED_SOURCE_MASK_MISMATCH")
        positive=m["outerwear"]>0
        negative=np.logical_or.reduce([m[k]>0 for k in NEGATIVE_KEYS])
    return known_only_score(alpha,positive,negative,pred)

def run(model_dir:Path,private_inputs:Path,private_output:Path,*,research_only=False):
    if research_only is not True:raise AuthorityHold("NONCOMMERCIAL_RESEARCH_ONLY")
    processor_sha=validate_model_dir(model_dir)
    import torch
    from transformers import SegformerForSemanticSegmentation,SegformerImageProcessor
    torch.set_num_threads(2)
    processor=SegformerImageProcessor.from_pretrained(str(model_dir),local_files_only=True)
    model=SegformerForSemanticSegmentation.from_pretrained(str(model_dir),local_files_only=True).cpu().eval()
    scores={};predictions={}
    with zipfile.ZipFile(private_inputs) as archive:
        for case,(name,pin) in SOURCE_PINS.items():
            rgba=signed_sample(archive,case)
            pred=source_only_prediction(rgba,model,processor)
            scores[case]={"signed_source_sha256":pin,**evaluate_review(
                archive,case,rgba[:,:,3]>0,pred)}
            predictions[case]=pred.astype(np.uint8)
    report={"schema":"minimalizer/local-l02/segformer-b2-fashion/noncommercial-shadow/v1",
       "model":MODEL_REPO,"pinned_revision":REVISION,
       "weights_sha256":WEIGHTS_SHA,"processor_config_sha256":processor_sha,
       "license":"NVIDIA SegFormer research/evaluation noncommercial; NOT authorized for production",
       "research_only":True,"inference_human_masks":False,"unknown_used_as_negative":False,
       "new_visible_source_pixels":0,"owner_promotion_authorized":False,
       "L02":"HOLD","Golden":"HOLD","production":"NO_GO","cases":scores}
    payload=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
    private_output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(private_output,"w",zipfile.ZIP_DEFLATED) as out:
        out.writestr("SOURCEFREE_METRICS.json",payload)
        for case,array in predictions.items():
            buf=io.BytesIO();np.savez_compressed(buf,prediction=array)
            out.writestr(case+"_SOURCE_BOUND_PRIVATE.npz",buf.getvalue())
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("pinned_model_directory",type=Path)
    p.add_argument("private_signed_review_zip",type=Path)
    p.add_argument("private_evidence_zip",type=Path)
    p.add_argument("--research-only",action="store_true",required=True)
    a=p.parse_args()
    print(json.dumps(run(a.pinned_model_directory,a.private_signed_review_zip,
                         a.private_evidence_zip,research_only=a.research_only),
                     ensure_ascii=False,indent=2))
