"""L02 research-only source-color sleeve attachment diagnostic.

The only proposal inputs are authenticated original RGBA and independently
predicted SegFormer fashion 47-class semantic IDs. Hand review masks enter a
separate post-prediction evaluator, NEVER the owner proposal. Threshold is a
ONE-TIME EXPLORATORY hypothesis from H04/H06/H08; NO holdout quality authority.
"""
from __future__ import annotations
import base64,hashlib,io,json,zipfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

CASES={
 "H04":("H04_original_signed_trace (1).json","7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3","389d5975cb66cbc7ca64d27bbd6b1950abce40f6399096d651e86996afd8b1b6"),
 "H06":("H06_trace.json","c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8","06e02c257d982a4da45ee8f77da8730d91615502eaa2cc9e438068e69e1e286a"),
 "H08":("H08_trace.json","759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e","d6ff3cee53338711f6dc253dc423d772f52d7cce711d3311a6497002739976f5"),
}
MODEL_WEIGHTS_SHA="47313d9daf8f759b803b0bf449a4719bcd5b5a46eacad343e99e9660f8cedec1"
# OpenCV Lab image-plane Euclidean threshold. Chosen during exploratory probing of
# THIS three-character set, not an independently validated production policy.
EXPLORATORY_CIELAB_DISTANCE=30.
OWNER_IDS=(5,10)
SLEEVE_ID=32
NEGATIVE_CATEGORIES=("underlayer","arm_skin","neck_skin","lower_body","face_skin","hair","accessory")

class ResearchHold(ValueError):pass

def digest(blob:bytes)->str:return hashlib.sha256(blob).hexdigest()

def propose(rgba:np.ndarray, classids:np.ndarray):
    """A source-only observation. No human/manual or Phase4 protected owner input."""
    if rgba.dtype!=np.dtype('uint8') or rgba.ndim!=3 or rgba.shape[2]!=4:
        raise ResearchHold("SOURCE_MUST_BE_RGBA_UINT8")
    alpha=rgba[:,:,3]>0
    if classids.shape!=alpha.shape or classids.dtype!=np.dtype('uint8'):
        raise ResearchHold("INVALID_CLASSIDS")
    if int(classids.max())>=47:raise ResearchHold("UNRECOGNIZED_CLASS_ID")
    base=np.isin(classids,OWNER_IDS)&alpha
    sleeve=(classids==SLEEVE_ID)&alpha
    if not np.any(base):
        return np.zeros_like(alpha),{
            "decision":"ABSTAIN_NO_OUTERWEAR_SEED","owner_promotion_authorized":False,
            "new_source_pixels":0,"candidate_pixels":0,
        }
    n,ids,_,_=cv2.connectedComponentsWithStats(sleeve.astype("uint8"),connectivity=8)
    adjacent=cv2.dilate(base.astype("uint8"),np.ones((3,3),np.uint8),iterations=1)>0
    accepted=[i for i in range(1,n) if np.any(adjacent&(ids==i))]
    touching=sleeve&np.isin(ids,accepted)
    # Color similarity to nearest source jacket/coat evidence. This is not a
    # semantic guarantee; long-distance same-color matches are research only.
    from scipy.ndimage import distance_transform_edt
    lab=cv2.cvtColor(rgba[:,:,:3],cv2.COLOR_RGB2LAB).astype("float32")
    _,nearest=distance_transform_edt(~base,return_indices=True)
    dist=np.sqrt(np.square(lab-lab[nearest[0],nearest[1]]).sum(axis=2))
    recovered=touching&(dist<EXPLORATORY_CIELAB_DISTANCE)
    proposal=base|recovered
    if np.any(proposal&~alpha):raise ResearchHold("GENERATED_PIXEL_OUTSIDE_ALPHA")
    return proposal,{
        "decision":"EXPLORATORY_ONLY_NOT_INDEPENDENTLY_VALIDATED",
        "source_base_pixels":int(base.sum()),
        "source_sleeve_pixels":int(sleeve.sum()),
        "adjacent_sleeve_components":len(accepted),
        "source_connected_sleeve_pixels":int(touching.sum()),
        "source_color_matched_sleeve_pixels":int(recovered.sum()),
        "candidate_pixels":int(proposal.sum()),
        "source_pixels_added_outside_original":0,
        "owner_promotion_authorized":False,
    }

def score(alpha,positive,negative,unknown_label,pred,protected_arm,protected_hair):
    """Manual human masks only AFTER proposal. Unknown MUST stay unknown."""
    for name,mask in (("alpha",alpha),("positive",positive),("negative",negative),
                      ("unknown_label",unknown_label),("pred",pred),
                      ("protected_arm",protected_arm),("protected_hair",protected_hair)):
        if mask.dtype!=np.dtype('bool') or mask.shape!=alpha.shape:raise ResearchHold("INVALID_EVALUATION_MASK_"+name)
    if np.any(positive&negative) or not np.array_equal(unknown_label,alpha&~(positive|negative)):
        raise ResearchHold("UNKNOWN_OR_LABEL_AUTHORITY_CONFLICT")
    if np.any((positive|negative|pred|protected_arm|protected_hair)&~alpha):
        raise ResearchHold("PROPOSAL_OR_LABEL_OUTSIDE_ALPHA")
    tp=int((pred&positive).sum());fp=int((pred&negative).sum());fn=int((~pred&positive).sum())
    return {"known_only_iou":round(tp/max(1,tp+fp+fn),6),
            "known_positive_recall":round(tp/max(1,tp+fn),6),
            "known_negative_fp_rate":round(fp/max(1,int(negative.sum())),6),
            "known_arm_fp_pixels":int((pred&protected_arm).sum()),
            "known_hair_fp_pixels":int((pred&protected_hair).sum()),
            "unknown_predicted_pixels":int((pred&unknown_label).sum()),
            "tp":tp,"fp_known":fp,"fn":fn,
            "source_prediction_sha256":digest(pred.tobytes())}

def run(reviewed_zip:Path,private_classes_zip:Path,private_output_zip:Path):
    if private_output_zip.exists():raise ResearchHold("REFUSE_PRIVATE_EVIDENCE_OVERWRITE")
    report={"schema":"minimalizer/local-l02/connected-source-color-sleeve/v1",
            "weights_sha256":MODEL_WEIGHTS_SHA,
            "class_scope":{"5":"jacket","10":"coat","32":"sleeve_not_guaranteed_outerwear"},
            "analysis_threshold":"EXPLORATORY_LAB_DISTANCE_30_SELECTED_WITH_THIS_EVALUATION_SET",
            "independent_holdout_not_performed":True,
            "manual_labels_used_during_prediction":False,
            "source_pixels_synthesized":0,"owner_authority":False,
            "L02":"HOLD","Golden":"HOLD","production":"NO_GO","cases":{}}
    outputs={}
    with zipfile.ZipFile(reviewed_zip) as z, zipfile.ZipFile(private_classes_zip) as classes:
        manifest=json.loads(z.read("MANIFEST_SHA256.json"))
        for case,(filename,source_pin,class_pin) in CASES.items():
            key="signed_human_review/"+filename
            raw=z.read(key)
            if digest(raw)!=manifest[key]:raise ResearchHold("SIGNED_REVIEW_SHA_MISMATCH")
            doc=json.loads(raw)
            source_bytes=base64.b64decode(doc["image"]["dataURL"].split(",",1)[1],validate=True)
            if digest(source_bytes)!=source_pin:raise ResearchHold("SIGNED_SOURCE_SHA_MISMATCH")
            rgba=np.asarray(Image.open(io.BytesIO(source_bytes)).convert("RGBA"),dtype=np.uint8)
            if doc["canvas"]!={"width":rgba.shape[1],"height":rgba.shape[0]}:
                raise ResearchHold("SIGNED_CANVAS_MISMATCH")
            with np.load(io.BytesIO(classes.read(case+"_SLEEVE_SEMANTIC_PRIVATE.npz")),allow_pickle=False) as archive:
                if "classids" not in archive.files:raise ResearchHold("PINNED_CLASSIDS_MISSING")
                classids=archive["classids"]
            if digest(classids.tobytes())!=class_pin:raise ResearchHold("CLASSIDS_SOURCE_PIN_MISMATCH")
            candidate,provenance=propose(rgba,classids)
            baseline=np.isin(classids,OWNER_IDS)&(rgba[:,:,3]>0)
            human_path="reviews/"+case+"_HUMAN_VISIBLE_MASKS_PRIVATE.npz"
            humanbytes=z.read(human_path)
            if digest(humanbytes)!=manifest[human_path]:raise ResearchHold("HUMAN_LABEL_SHA_MISMATCH")
            with np.load(io.BytesIO(humanbytes),allow_pickle=False) as m:
                alpha=rgba[:,:,3]>0
                if not np.array_equal(m["opaque"]>0,alpha):raise ResearchHold("HUMAN_ALPHA_MISMATCH")
                pos=m["outerwear"]>0
                negative=np.logical_or.reduce([m[k]>0 for k in NEGATIVE_CATEGORIES])
                arm=m["arm_skin"]>0;hair=m["hair"]>0
            unknown=alpha&~(pos|negative)
            report["cases"][case]={"signed_source_sha256":source_pin,
                "classids_prediction_sha256":class_pin,**provenance,
                "original_jacket_coat":score(alpha,pos,negative,unknown,baseline,arm,hair),
                "exploratory_sleeve_attachment":score(alpha,pos,negative,unknown,candidate,arm,hair)}
            outputs[case]=candidate.astype(np.uint8)
    payload=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    private_output_zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(private_output_zip,"w",zipfile.ZIP_DEFLATED) as out:
        out.writestr("SOURCEFREE_METRICS.json",payload)
        for case,prediction in outputs.items():
            f=io.BytesIO();np.savez_compressed(f,prediction=prediction)
            out.writestr(case+"_PRIVATE_PREDICTION.npz",f.getvalue())
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("reviewed_zip",type=Path);p.add_argument("private_classes_zip",type=Path)
    p.add_argument("private_output_zip",type=Path)
    a=p.parse_args()
    print(json.dumps(run(a.reviewed_zip,a.private_classes_zip,a.private_output_zip),indent=2,ensure_ascii=False))
