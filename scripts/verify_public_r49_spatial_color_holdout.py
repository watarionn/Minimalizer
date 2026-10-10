"""R49: spatial crossvalidation of source-observed owner color proposals.

Readonly signed photo and Stage8 masks. Held-out block samples score RGB color
fit only. They cannot certify owner anatomy, original palette aesthetics,
Golden images, or approve production recoloring.
"""
import argparse,json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tools/research"))
from verify_public_r45_visible_source_palette import visible_source_parts,observed_medoid,mae
from verify_public_r25_source_owner_attribution import PRIVATE,pinned
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from sa1060b_first_bad_stage_audit import source_connected_background

def split_folds(mask,folds=4,block=16):
    if mask.shape!=(340,340) or mask.dtype!=np.dtype("bool"):
        raise ValueError("R49 signed original mask only")
    y,x=np.indices(mask.shape)
    labels=((x//block)+(2*(y//block)))%folds
    return [(mask&(labels==i)) for i in range(folds)]

def source_case(case,root,scene):
    photo=root/PRIVATE/"original_inputs"/(case+"_source.png")
    pinned(photo,SOURCE[case][0]);pinned(scene,SCENE_SHA256[case])
    parts,cap,w,h=input_checks(case,json.loads(scene.read_text(encoding="utf8")))
    if len(parts)!=11 or (w,h)!=(340,340):raise ValueError("R49 source scene incomplete")
    rgba=np.asarray(Image.open(photo).convert("RGBA"))
    border,_=source_connected_background(rgba[...,:3],rgba[...,3])
    masks=visible_source_parts(parts)
    result=[]
    for part in parts:
        name=part["source_mask_owner"]
        visible=masks[name]
        interior=cv2.erode(visible.astype(np.uint8),np.ones((3,3),np.uint8),iterations=2)>0
        eligible=interior&(rgba[...,3]==255)&~border
        if int(eligible.sum())<128:
            result.append({"owner":name,"sourceEligibleSamples":int(eligible.sum()),
                           "foldsTested":0,"holdoutPassCount":0,
                           "researchColorGeneralizationApproved":False,
                           "status":"INSUFFICIENT_SPATIAL_HOLDOUT_DATA"})
            continue
        sub=split_folds(eligible)
        tests=[]
        for idx,held in enumerate(sub):
            other=eligible&~held
            train=rgba[...,:3][other]
            test=rgba[...,:3][held]
            if len(train)<128 or len(test)<32:continue
            medoid=observed_medoid(train)
            baseline=mae(test,part["palette_color_rgb"])
            candidate=mae(test,medoid)
            tests.append({"fold":idx,"heldOutSamples":int(len(test)),
                          "sourceRgbBaselineMAE":baseline,
                          "sourceRgbCandidateMAE":candidate,
                          "heldOutMAEGain":round(baseline-candidate,6),
                          "colorCandidateWasTrulyObservedInTrainingPixels":True})
        passes=sum(x["heldOutMAEGain"]>0 for x in tests)
        # The name "generalizes" refers ONLY to photo-RGB fit, not semantics.
        result.append({"owner":name,"sourceEligibleSamples":int(eligible.sum()),
                       "foldsTested":len(tests),"holdoutPassCount":passes,
                       "holdoutDiagnostics":tests,
                       "researchColorGeneralizationApproved":False,
                       "independentSemanticOwnerApproved":False,
                       "status":"PHOTO_RGB_SPATIAL_CROSSVALIDATION_ONLY"})
    return {"case":case,"originalStage8Vertices":SOURCE[case][2],
            "historicalStage8Cap":cap,"owners":result,
            "paletteModified":False,"sourceHumanSemanticReviewSigned":False}

def run(root,scenes,out):
    if out.exists():raise FileExistsError("R49 preserve signed evidence")
    results=[source_case(c,root,scenes[c]) for c in ("GC001","Raden")]
    payload={"version":"public-r49-spatial-owner-color-holdout-v1",
             "cases":results,"sourceOriginalPhotoAndOwnerMasksUnmodified":True,
             "faceDetailsGenerated":False,"colorPromotionAuthorized":False,
             "originalStage8VertexBudgetApproved":False,
             "humanSemanticOwnerSignoff":False,"productionReleaseAuthorized":False}
    out.mkdir(parents=True)
    (out/"private_r49_spatial_color_holdout.json").write_text(
        json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for case in results:
        print("R49",case["case"],[(x["owner"],x["holdoutPassCount"],x["foldsTested"])
           for x in case["owners"] if x["owner"] in ("hair","right_arm","left_arm","major_clothing","accessory_or_held_object","unknown")],
           "SEMANTIC_HOLD",flush=True)
    return payload
def main():
    a=argparse.ArgumentParser()
    for n in ("root","gc","raden","out"):a.add_argument("--"+n,type=Path,required=True)
    args=a.parse_args()
    run(args.root,{"GC001":args.gc,"Raden":args.raden},args.out)
if __name__=="__main__":main()
