"""R45-R46: read-only visible source-pixel palette measurements.

Never edit a source mask, signed palette or product route. A candidate RGB is
an *existing pixel in the original photo*, not an invented semantic color.
Numerical color fit is NOT a human-approved part label or art-quality gate.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tools/research"))
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from verify_public_r25_source_owner_attribution import pinned,PRIVATE
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from sa1060b_first_bad_stage_audit import source_connected_background

def visible_source_parts(parts):
    seen=np.zeros((340,340),dtype=bool)
    output={}
    for p in reversed(parts):
        raw=rasterize_primitive_candidate(p,width=340,height=340)>0
        visible=raw&~seen
        output[p["source_mask_owner"]]=visible
        seen|=raw
    assert sum(int(m.sum()) for m in output.values())==int(seen.sum())
    return output
def observed_medoid(rgb):
    if rgb.dtype!=np.uint8 or rgb.ndim!=2 or rgb.shape[1]!=3 or not len(rgb):
        raise ValueError("original RGB source pixels required")
    median=np.median(rgb,axis=0)
    idx=int(np.abs(rgb.astype(np.float64)-median).sum(axis=1).argmin())
    return [int(v) for v in rgb[idx]]
def mae(rgb,color):
    if not len(rgb):return None
    return round(float(np.abs(rgb.astype(np.float64)-np.array(color)).mean()),6)
def study(root,scenes,out):
    if out.exists():raise FileExistsError("cannot overwrite signed numerical evidence")
    results=[]
    for case in ("GC001","Raden"):
        photo=root/PRIVATE/"original_inputs"/(case+"_source.png")
        pinned(photo,SOURCE[case][0])
        signed=scenes[case];pinned(signed,SCENE_SHA256[case])
        parts,cap,w,h=input_checks(case,json.loads(signed.read_text("utf8")))
        if len(parts)!=11 or (w,h)!=(340,340):raise ValueError("incomplete source")
        rgba=np.asarray(Image.open(photo).convert("RGBA"))
        bg,observer=source_connected_background(rgba[...,:3],rgba[...,3])
        masks=visible_source_parts(parts)
        case_rows=[]
        for part in parts:
            key=part["source_mask_owner"]
            m=masks[key]
            interior=cv2.erode(m.astype(np.uint8),np.ones((3,3),np.uint8),iterations=2)!=0
            eligible=interior & (rgba[...,3]==255) & ~bg
            rgb=rgba[...,:3][eligible]
            original=part["palette_color_rgb"]
            candidate=observed_medoid(rgb) if len(rgb) else None
            score=mae(rgb,original)
            proposed=mae(rgb,candidate) if candidate else None
            case_rows.append({
               "owner":key,"visiblePixels":int(m.sum()),
               "opaqueVisibleInteriorSourceSamplePixels":int(eligible.sum()),
               "sourceConnectedBackgroundSuppressedPixels":int((interior&bg).sum()),
               "existingPaletteRGB":original,
               "existingSourceInteriorMAE":score,
               "observedSourcePixelCandidateRGB":candidate,
               "candidateSourceInteriorMAE":proposed,
               "measuredMAEGain":round(score-proposed,6) if proposed is not None else None,
               "sourceObservedRGBNotAnatomyProof":True,
               "paletteMutationAuthorized":False})
        results.append({"case":case,"originalStage8Vertices":SOURCE[case][2],
                        "historicCap":cap,"sourceOwnerCount":11,
                        "originalSourceUnmodified":True,"ownerRows":case_rows,
                        "semanticCandidateColorApproved":False})
    out.mkdir(parents=True)
    payload={"version":"public-r45-visible-source-color-observation-v1",
             "cases":results,"originalPhotosOrMasksModified":False,
             "sourcePixelProposalsOnlyFromObservedSource":True,
             "noGenerativeFill":True,"faceMicrofeaturesPainted":False,
             "humanSemanticApprovalSigned":False,
             "productPaletteChanged":False,"productionReleaseAuthorized":False}
    (out/"private_r45_visible_source_palette_observations.json").write_text(
        json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for case in results:
        print("R45",case["case"],"foreground-observed",
            [(r["owner"],r["opaqueVisibleInteriorSourceSamplePixels"],
              r["measuredMAEGain"]) for r in case["ownerRows"]
             if r["owner"] in ("right_arm","left_arm","major_clothing","accessory_or_held_object","unknown")],
            flush=True)
    return payload
def main():
    a=argparse.ArgumentParser()
    for name in ("root","gc","raden","out"):a.add_argument("--"+name,required=True,type=Path)
    args=a.parse_args()
    study(args.root,{"GC001":args.gc,"Raden":args.raden},args.out)
if __name__=="__main__":main()
