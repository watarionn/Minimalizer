"""R44-R45: signed original-photo/owner-mask human review contact sheets.

Draw only historical pixels and contours. No generation, no new owner mask or
semantic certification. Original photo contact sheets PRIVATE Drive only.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from verify_public_r25_source_owner_attribution import FROZEN,PRIVATE,pinned,mask_image

PRIORITY=("right_arm","left_arm","major_clothing","accessory_or_held_object","unknown")
def run(root:Path,scenes:dict[str,Path],out:Path):
    if out.exists():raise FileExistsError("preserve original evidence")
    out.mkdir(parents=True)
    reports=[]
    for case in ("GC001","Raden"):
        source=root/PRIVATE/"original_inputs"/(case+"_source.png")
        pinned(source,SOURCE[case][0])
        frozen=scenes[case];pinned(frozen,SCENE_SHA256[case])
        scene=json.loads(frozen.read_text(encoding="utf8"))
        parts,cap,w,h=input_checks(case,scene)
        assert len(parts)==11 and (w,h)==(340,340)
        rgba=np.asarray(Image.open(source).convert("RGBA"))
        photo=rgba[...,:3]
        owner={p["source_mask_owner"]:p for p in parts}
        visible={}
        later=np.zeros((340,340),dtype=bool)
        for p in reversed(parts):
            mask=rasterize_primitive_candidate(p,width=340,height=340)>0
            visible[p["source_mask_owner"]]=mask&~later
            later|=mask
        board=Image.new("RGB",(340*3,380*len(PRIORITY)),(245,245,245))
        writer=ImageDraw.Draw(board)
        review=[]
        for row,name in enumerate(PRIORITY):
            p=owner[name]
            mask=rasterize_primitive_candidate(p,width=340,height=340)>0
            vis=visible[name]
            color=np.asarray(p["palette_color_rgb"],dtype=np.uint8)
            isolate=np.full((340,340,3),255,dtype=np.uint8)
            isolate[mask]=color
            overlay=photo.copy()
            contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(overlay,contours,-1,(255,0,255),1)
            overlay[vis]=(overlay[vis]*0.75+np.array([255,100,0])*0.25).astype(np.uint8)
            panels=(photo,isolate,overlay)
            titles=("SIGNED PHOTO",f"STAGE8 {name}","SIGNED MASK OVER PHOTO")
            for j,(im,title) in enumerate(zip(panels,titles)):
                at=(340*j,380*row+40)
                board.paste(Image.fromarray(im,"RGB"),at)
                writer.text((340*j+7,380*row+11),title,fill=(20,20,20))
            stage04=None
            if name in ("right_arm","left_arm"):
                src=root/PRIVATE/case/f"signed_{name}_stage04_mask.png"
                pinned(src,FROZEN[case]["masks"][name])
                stage04=mask_image(src)
            review.append({"owner":name,"ownerMaskPixels":int(mask.sum()),
                "visibleUnoccludedMaskPixels":int(vis.sum()),
                "overlaidByLaterOwnerPixels":int((mask&~vis).sum()),
                "stage8VsIndependentSignedStage04MaskXorPixels":
                    int(np.count_nonzero(mask^stage04)) if stage04 is not None else None,
                "sourcePhotoOriginalUntouched":True,
                "manualSourceOwnerSemanticReviewSigned":False})
        target=out/(case+"_r44_PRIVATE_owner_comparison_board.png")
        board.save(target)
        reports.append({"case":case,"sourceSHA256":SOURCE[case][0],
          "sourceStage8SHA256":SCENE_SHA256[case],
          "historicVertexCap":cap,"signedSemanticOwnerApproval":False,
          "boardSha256":hashlib.sha256(target.read_bytes()).hexdigest(),
          "reviewItems":review})
    result={"version":"public-r44-source-owner-review-v1","cases":reports,
      "privateOriginalPhotoContactBoardsNeverPublished":True,
      "originalPhotoAndOwnerMasksModified":False,
      "faceMicrofeaturesGenerated":False,
      "independentHumanReviewSigned":False,
      "productionReleaseAuthorized":False}
    (out/"public_r44_source_owner_review_coordinate_free.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return result
def main():
    a=argparse.ArgumentParser()
    for name in ("root","gc","raden","out"):a.add_argument("--"+name,type=Path,required=True)
    q=a.parse_args()
    run(q.root,{"GC001":q.gc,"Raden":q.raden},q.out)
if __name__=="__main__":main()
