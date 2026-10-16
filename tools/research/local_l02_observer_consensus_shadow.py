"""Local L02 source-only independent outerwear observer agreement.

Two independently pretrained pinned model predictions are reconciled ONLY as a
shadow. Human labels are post-inference evaluation, never consensus input.
Unknown pixels must stay unknown. No Phase4 owner or production modifications.
"""
from __future__ import annotations
import base64,hashlib,io,json,zipfile
from pathlib import Path
from collections.abc import Mapping
import numpy as np
from PIL import Image

CASES={
 "H04":("H04_original_signed_trace (1).json","7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3",
 "97716eb50004a153c0fe6934a3f010fcd09c2b27a6b9bd0a1dc4c21c37d766ed",
 "f4c3ea5e73984366f23c29b9e1fb72f8388dd0de53c7a41d43cd2688a10a70ed"),
 "H06":("H06_trace.json","c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8",
 "413735e90ff42381798948163c9c0966473ec616ea035684a8dc1f10962283ad",
 "2627c7dcb3eaec5a54660d52b503da292b8e6a7b9b51a1d828a270fa1d60ac03"),
 "H08":("H08_trace.json","759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e",
 "2ab16a864b23a9a178faf219512e4a7dbb255a659ddb57785c16292b3d008d6d",
 "d07aba41d11ec8a3c5506d14574132b42779d61a0d6a13bb1cd8b5d06628c25b")}
LABELS=("outerwear","underlayer","arm_skin","neck_skin","lower_body","face_skin","hair","accessory")
class ResearchHold(ValueError): pass

def sha(b:bytes)->str:
 return hashlib.sha256(b).hexdigest()

def assert_binary(x,name,shape=None):
 if not isinstance(x,np.ndarray) or x.dtype!=np.dtype(bool) or x.ndim!=2 or (shape is not None and x.shape!=shape):
  raise ResearchHold("INVALID_BINARY_MASK_"+name)
 return x

def decompose(alpha,segformer,deepfashion):
 assert_binary(alpha,"alpha")
 for name,mask in (("segformer",segformer),("deepfashion",deepfashion)):
  assert_binary(mask,name,alpha.shape)
  if np.any(mask&~alpha):raise ResearchHold("OBSERVATION_OUTSIDE_SOURCE_"+name)
 shared=segformer&deepfashion
 seg_only=segformer&~deepfashion
 deep_only=deepfashion&~segformer
 neither=alpha&~(segformer|deepfashion)
 if np.any(shared&seg_only) or np.any(shared&deep_only) or np.any(seg_only&deep_only):
  raise ResearchHold("NONEXCLUSIVE_DIAGNOSTIC_PARTITION")
 if not np.array_equal(shared|seg_only|deep_only|neither,alpha):
  raise ResearchHold("DIAGNOSTIC_PARTITION_INCOMPLETE")
 return {"shared":shared,"segformer_only":seg_only,"deepfashion_only":deep_only,"neither":neither}

def known_only(alpha,pred,positive,negative):
 for name,mask in (("pred",pred),("positive",positive),("negative",negative)):
  assert_binary(mask,name,alpha.shape)
 if np.any((pred|positive|negative)&~alpha):raise ResearchHold("OUTSIDE_SIGNED_SOURCE")
 if np.any(positive&negative):raise ResearchHold("CONTRADICTORY_HUMAN_CATEGORIES")
 tp=int((pred&positive).sum());fp=int((pred&negative).sum());fn=int((~pred&positive).sum())
 unknown=alpha&~(positive|negative)
 return {"labelled_only_iou":round(tp/max(1,tp+fp+fn),6),
         "positive_recall":round(tp/max(1,tp+fn),6),
         "known_negative_fp_rate":round(fp/max(1,int(negative.sum())),6),
         "unknown_predicted_px":int((pred&unknown).sum()),
         "prediction_source_px":int(pred.sum()),
         "tp":tp,"fp_known":fp,"fn":fn}

def diagnose(alpha,segformer,deepfashion,*,positive,negative,hair,arms):
 """Human labels used strictly for post-inference error attribution."""
 part=decompose(alpha,segformer,deepfashion)
 for name,mask in (("positive",positive),("negative",negative),("hair",hair),("arms",arms)):
  assert_binary(mask,name,alpha.shape)
  if np.any(mask&~alpha):raise ResearchHold("DIAGNOSTIC_LABEL_OUTSIDE_SOURCE")
 if np.any(positive&negative):raise ResearchHold("HUMAN_CONFLICT")
 union=segformer|deepfashion
 summary={}
 for name,mask in part.items():
  entry={"source_px":int(mask.sum()),
         "labelled_positive_px":int((mask&positive).sum()),
         "labelled_negative_px":int((mask&negative).sum()),
         "human_hair_px":int((mask&hair).sum()),
         "human_arm_px":int((mask&arms).sum()),
         "unlabelled_source_px":int((mask&alpha&~(positive|negative)).sum())}
  if name!="neither":
   entry.update(known_only(alpha,mask,positive,negative))
  summary[name]=entry
 decision="ABSTAIN_EMPTY_INDEPENDENT_AGREEMENT" if not part["shared"].any() else "SHADOW_AGREEMENT_NOT_OWNER_AUTHORITY"
 return {"decision":decision,"fully_source_bound":True,
         "shared_source_px":int(part["shared"].sum()),
         "disagreement_source_px":int((part["segformer_only"]|part["deepfashion_only"]).sum()),
         "union_source_px":int(union.sum()),
         "agreement_fraction_of_union":round(float(part["shared"].sum()/max(1,union.sum())),6),
         "known_positive_source_px":int(positive.sum()),
         "known_negative_source_px":int(negative.sum()),
         "unknown_source_px":int((alpha&~(positive|negative)).sum()),
         "regions":summary,"owner_promotion_authorized":False}

def load_pred(z:zipfile.ZipFile,path:str,expected_digest:str,alpha:np.ndarray):
 b=z.read(path)
 with np.load(io.BytesIO(b),allow_pickle=False) as raw:
  if set(raw.files)!={"prediction"}:raise ResearchHold("PREDICTION_SCHEMA_MISMATCH")
  u=raw["prediction"]
 if u.shape!=alpha.shape or u.dtype!=np.uint8 or not np.isin(u,(0,1)).all():
  raise ResearchHold("PREDICTION_NOT_BINARY_SOURCE_FRAME")
 mask=u.astype(bool)
 if sha(mask.tobytes())!=expected_digest:raise ResearchHold("MODEL_PREDICTION_SHA_MISMATCH")
 if np.any(mask&~alpha):raise ResearchHold("PREDICTION_OUTSIDE_ALPHA")
 return mask

def load_signed(archive:zipfile.ZipFile,case:str):
 filename,pin,*_=CASES[case]
 manifest=json.loads(archive.read("MANIFEST_SHA256.json"))
 key="signed_human_review/"+filename
 b=archive.read(key)
 if sha(b)!=manifest[key]:raise ResearchHold("HUMAN_REFERENCE_SHA_MISMATCH")
 obj=json.loads(b)
 source=base64.b64decode(obj["image"]["dataURL"].split(",",1)[1],validate=True)
 if sha(source)!=pin:raise ResearchHold("SIGNED_SOURCE_SHA_MISMATCH")
 rgba=np.asarray(Image.open(io.BytesIO(source)).convert("RGBA"),dtype=np.uint8)
 if obj["canvas"]!={"width":rgba.shape[1],"height":rgba.shape[0]}:raise ResearchHold("SIGNED_CANVAS_MISMATCH")
 return rgba

def run(review_archive:Path,segformer_archive:Path,deepfashion_archive:Path,private_output:Path):
 if private_output.exists():raise ResearchHold("REFUSE_OVERWRITE_EXISTING_PRIVATE_EVIDENCE")
 result={"schema":"minimalizer/local-l02/independent-observer-uncertainty/v1",
    "sources":list(CASES),"segformer_model":"sayeed99/segformer-b2-fashion",
    "deepfashion_model":"HasanKabir23/Yolov26s-DeepFashion2",
    "consensus_is_not_semantic_truth":True,
    "independent_observers_evaluated_without_human_labels_at_inference":True,
    "model_licence_resolution":"USER_REPORTS_RESOLVED_2026-10-16_SCOPE_NOT_VERIFIED_HERE",
    "pixels_generated":0,"signed_owner_modified":False,
    "L02":"HOLD","L03":"BLOCKED_ON_L02_SEMANTIC_AND_VISUAL_QUALITY",
    "Golden":"HOLD","production":"NO_GO","cases":{}}
 arrays={}
 with zipfile.ZipFile(review_archive) as reviews,zipfile.ZipFile(segformer_archive) as seg,zipfile.ZipFile(deepfashion_archive) as deep:
  manifest=json.loads(reviews.read("MANIFEST_SHA256.json"))
  for case in CASES:
   rgba=load_signed(reviews,case)
   alpha=rgba[:,:,3]>0
   fn,srcsha,segsha,deepsha=CASES[case]
   s=load_pred(seg,case+"_SOURCE_BOUND_PRIVATE.npz",segsha,alpha)
   d=load_pred(deep,case+"_DEEPFASHION2_OUTERWEAR_PRIVATE.npz",deepsha,alpha)
   maskname=f"reviews/{case}_HUMAN_VISIBLE_MASKS_PRIVATE.npz"
   raw=reviews.read(maskname)
   if sha(raw)!=manifest[maskname]:raise ResearchHold("LABEL_MASK_SHA_MISMATCH")
   with np.load(io.BytesIO(raw),allow_pickle=False) as masks:
    if not np.array_equal(masks["opaque"]>0,alpha):raise ResearchHold("LABEL_ALPHA_MISMATCH")
    positive=masks["outerwear"]>0
    neg=np.logical_or.reduce([masks[k]>0 for k in LABELS if k!="outerwear"])
    hair=masks["hair"]>0
    arms=masks["arm_skin"]>0
   stats=diagnose(alpha,s,d,positive=positive,negative=neg,hair=hair,arms=arms)
   result["cases"][case]={"signed_source_sha256":srcsha,
      "segformer_prediction_sha256":segsha,"deepfashion_prediction_sha256":deepsha,**stats}
   fields=decompose(alpha,s,d)
   arrays[case]={k:v.astype(np.uint8) for k,v in fields.items() if k!="neither"}
 output_json=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
 private_output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(private_output,"w",compression=zipfile.ZIP_DEFLATED) as out:
  out.writestr("SOURCEFREE_DIAGNOSTIC.json",output_json)
  for case,fields in arrays.items():
   b=io.BytesIO();np.savez_compressed(b,**fields)
   out.writestr(case+"_OBSERVER_AGREEMENT_PRIVATE.npz",b.getvalue())
 return result

if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser()
 for key in ("reviewed_zip","segformer_zip","deepfashion_zip","output_private_zip"):p.add_argument(key,type=Path)
 v=p.parse_args()
 print(json.dumps(run(v.reviewed_zip,v.segformer_zip,v.deepfashion_zip,v.output_private_zip),ensure_ascii=False,indent=2))
