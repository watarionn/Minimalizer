"""R25: signed-original source/owner/renderer error attribution (research only).

Quantifies where the original reference raster already differs from the signed
source photo, separately from where Chrome deviates from the frozen OpenCV
reference, for each of 11 signed Stage8 owner masks and official historical
Phase04 face/arms. Both masks/outputs and source may overlap; metrics are
NOT independent semantic truth, and do not endorse paint or part edits.

Private original PNG / SVG / owner heatmaps are saved ONLY in approved Drive.
Public JSON contains numeric aggregates and pinned SHA but no coordinates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tools/research"))
from verify_public_v34_svgo_chrome import chrome_driver,render_rgba
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from research_public_r12_exact_raster_prune import SOURCE,input_checks
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from sa1060b_first_bad_stage_audit import source_connected_background

VERSION="public-r25-signed-source-stage04-stage8-chrome-11-owner-fidelity-v1"
PRIVATE="SA1041_FullCharacterSVG_20261008"
CASES=("GC001","Raden")
FROZEN={
 "GC001":{
  "svg":"0f10af9aaddad0ee96c7acbafb73361ee0000ee6833b9d581025659895718b34",
  "reference":"b155651a9aac6979472f391564756a3866ab0ed4fe0e955af58a3ab3557d39c9",
  "masks":{"face":"b4812364eaec7da9930a18ae85270d6612555d3fb3d80283efcf69b03aa6a72f",
           "left_arm":"49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f",
           "right_arm":"4900beccaf0ca4a9ca33600339df77976a4500f1db932fcb240a41907b935b91"},
  "chromeWrongPixels":3919,"historicalStage8":{"face":0,"left_arm":5,"right_arm":24},
  "connectedBorder":{"face":0,"left_arm":0,"right_arm":533}
 },
 "Raden":{
  "svg":"ecc48fcf20a85b584a421bbd7f485c40c1c0bab6cd536049a73a61d4d7ac97db",
  "reference":"749fc372e293de4a839b13dc2196d5576e98d2f5c784d73449ca2f96ab074a92",
  "masks":{"face":"a192ef05aa3ae2cc42e249cb311349d82dd5e4115c1aa438c7a3205ba0d4ec2f",
           "left_arm":"6872bd01fb350b5ce2b5ec09b44feaa2c46cc442aa327cccc0e8681db33b404e",
           "right_arm":"79829023fd293e16a619dbc7b84736ca3d2ac172ac442c04d35bc1a3eae13025"},
  "chromeWrongPixels":2681,
  "connectedBorder":{"face":0,"left_arm":7,"right_arm":3},
 }
}

def digest(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def pinned(path:Path,expected:str)->None:
    if not path.is_file() or digest(path)!=expected:
        raise ValueError("R25 frozen source artifact mismatch: "+path.name)

def rgb_image(path:Path,alpha:bool=False)->np.ndarray:
    with Image.open(path) as im:
        arr=np.asarray(im.convert("RGBA" if alpha else "RGB"))
    if arr.shape != ((340,340,4) if alpha else (340,340,3)):
        raise ValueError("R25 signed image geometry mismatch")
    return arr

def mask_image(path:Path)->np.ndarray:
    with Image.open(path) as im: a=np.asarray(im.convert("L"))
    if a.shape!=(340,340) or not np.isin(a,[0,255]).all():
        raise ValueError("R25 original signed mask is not binary")
    return a==255

def error_groups(original:np.ndarray,reference:np.ndarray,chrome:np.ndarray,
                 mask:np.ndarray,border_connected:np.ndarray|None=None)->dict:
    """Compare the *same* fixed ROI; source-vs-reference != Chrome-vs-reference.

    The source/reference metric measures upstream reference model mismatch;
    Chrome/reference measures browser raster mismatch; not owner semantics.
    """
    if (original.shape!=reference.shape or reference.shape!=chrome.shape or
        original.shape!=(340,340,3) or mask.shape!=(340,340) or
        mask.dtype!=np.dtype("bool")):
        raise ValueError("R25 pixel and ROI dimensions must all be signed 340x340")
    if border_connected is not None and (
        border_connected.shape!=mask.shape or border_connected.dtype!=mask.dtype):
        raise ValueError("R25 background observer geometry invalid")
    interior=cv2.erode(mask.astype(np.uint8),np.ones((3,3),np.uint8),iterations=2)!=0
    boundary=mask & ~interior
    errors_source=(original.astype(np.int16)-reference.astype(np.int16))
    errors_chrome=(chrome.astype(np.int16)-reference.astype(np.int16))
    original_ref_difference=np.any(errors_source!=0,axis=2)
    chrome_ref_difference=np.any(errors_chrome!=0,axis=2)
    owner_cells={}
    for label,part in (("all",mask),("interiorEroded2",interior),("boundaryComplement",boundary)):
        n=int(part.sum())
        owner_cells[label]={
         "maskPixels":n,
         "sourceVsFrozenReferenceChangedPixels":int(np.count_nonzero(original_ref_difference&part)),
         "sourceVsFrozenReferenceMAE":round(float(np.abs(errors_source)[part].mean()),6) if n else None,
         "chromeVsFrozenReferenceChangedPixels":int(np.count_nonzero(chrome_ref_difference&part)),
         "chromeVsFrozenReferenceMAE":round(float(np.abs(errors_chrome)[part].mean()),6) if n else None,
         "chromeAndSourceReferenceErrorCoincidentPixels":int(np.count_nonzero(
             original_ref_difference&chrome_ref_difference&part)),
        }
    if owner_cells["interiorEroded2"]["maskPixels"]+owner_cells["boundaryComplement"]["maskPixels"] != owner_cells["all"]["maskPixels"]:
        raise AssertionError("R25 interior/boundary partition invalid")
    return {
      "regions":owner_cells,
      "sourceBorderConnectedExactRGBOverlap":int(np.count_nonzero(mask & border_connected)) if border_connected is not None else None,
      "sourcePhotoSemanticOwnerCertified":False
    }

def render_case(case:str,root:Path,stage8:Path,chrome_driver_instance)->tuple[dict,dict]:
    signed=root/PRIVATE
    case_root=signed/case
    source=signed/"original_inputs"/(case+"_source.png")
    svg=case_root/"full_character_vector.svg"
    reference=case_root/"signed_full_opencv_reference.png"
    expect=FROZEN[case]
    pinned(source,SOURCE[case][0])
    pinned(svg,expect["svg"])
    pinned(reference,expect["reference"])
    pinned(stage8,SCENE_SHA256[case])
    source_rgba=rgb_image(source,True)
    source_rgb=source_rgba[...,:3]
    reference_rgb=rgb_image(reference)
    computed=np.frombuffer(render_rgba(chrome_driver_instance,svg.read_text(encoding="utf-8")),
                           dtype=np.uint8).reshape(340,340,4).copy()
    chrome_rgb=computed[...,:3]
    # Never compare an unknown Alpha/compositing policy as though it's RGB.
    if not np.all(computed[...,3]==255):
        raise ValueError("R25 expected fully opaque frozen SVG")
    wrong=np.any(chrome_rgb!=reference_rgb,axis=2)
    n_wrong=int(wrong.sum())
    if n_wrong!=expect["chromeWrongPixels"]:
        raise ValueError("R25 historical full scene Chrome RGB parity drift")
    stage=json.loads(stage8.read_text(encoding="utf-8"))
    owners,cap,w,h=input_checks(case,stage)
    if w!=340 or h!=340:raise ValueError("R25 signed 340px Stage8 only")
    connected,observation=source_connected_background(source_rgb,source_rgba[...,3])
    owner_results={}
    owner_masks={}
    for p in owners:
        label=p["source_mask_owner"]
        mask=(rasterize_primitive_candidate(p,width=340,height=340)>0)
        owner_results[label]=error_groups(source_rgb,reference_rgb,chrome_rgb,mask,connected)
        owner_results[label]["originalStage8Vertices"]=sum(
            len(r["points"]) for r in p["parameters"]["rings"])
        owner_masks[label]=mask
    historical={}
    signed_masks={}
    for role,expected in expect["masks"].items():
        maskpath=case_root/f"signed_{role}_stage04_mask.png"
        pinned(maskpath,expected)
        sig=mask_image(maskpath)
        signed_masks[role]=sig
        diag=error_groups(source_rgb,reference_rgb,chrome_rgb,sig,connected)
        current=owner_masks[role]
        diag["signedStage04MaskPixels"]=int(sig.sum())
        diag["originalStage8OwnerMaskPixels"]=int(current.sum())
        diag["stage8VsSignedStage04XorPixels"]=int(np.count_nonzero(sig^current))
        diag["stage8MissedSignedPixels"]=int(np.count_nonzero(sig & ~current))
        diag["stage8ExtraUnsignedPixels"]=int(np.count_nonzero(current & ~sig))
        if case=="GC001" and diag["stage8VsSignedStage04XorPixels"]!=expect["historicalStage8"][role]:
            raise ValueError("R25 GC001 signed Stage8 role comparison drift")
        if diag["sourceBorderConnectedExactRGBOverlap"]!=expect["connectedBorder"][role]:
            raise ValueError("R25 original photo source-connected RGB observation drift")
        historical[role]=diag
    metrics={
      "case":case,"originalSourceSHA256":digest(source),
      "signedStage8SceneSHA256":digest(stage8),
      "historicalStage8Cap":cap,"signedStage8OriginalVertices":SOURCE[case][2],
      "frozenFullCharacterSvgSHA256":digest(svg),
      "frozenOpenCvFullReferenceSHA256":digest(reference),
      "replayedChromeFullSceneVsFrozenReferenceDifferentPixels":n_wrong,
      "stage8OwnerCount":len(owner_results),
      "stage8SourceOwnedRegions":owner_results,
      "historicalPhase04SignedRegions":historical,
      "sourceExactBorderRgbObserver":observation,
      "signedStage04RightArmSemanticGroundTruthProven":False,
      "sourceRoiChromaticErrorDoesNotCertifyCorrectPartLabel":True,
      "humanOwnerReviewRequired":True,
      "productionReleaseAuthorized":False,
    }
    private={"case":case,"original":source_rgb,"reference":reference_rgb,
             "chrome":chrome_rgb,"wrong":wrong,"historical":signed_masks,
             "ownerMasks":owner_masks}
    return metrics,private

def comparison_board(data:dict,path:Path)->None:
    orig,ref,chrome=data["original"],data["reference"],data["chrome"]
    error=np.abs(chrome.astype(np.int16)-ref.astype(np.int16)).max(axis=2)
    colors=np.zeros((340,340,3),dtype=np.uint8)
    colors[...,0]=np.minimum(error*3,255).astype(np.uint8)
    colors[...,2]=(data["wrong"]*80).astype(np.uint8)
    face=data["historical"]["face"]
    left=data["historical"]["left_arm"]
    right=data["historical"]["right_arm"]
    signed_masks=np.zeros((340,340,3),dtype=np.uint8)
    signed_masks[...,0]=(right*255).astype(np.uint8)
    signed_masks[...,1]=(left*255).astype(np.uint8)
    signed_masks[...,2]=(face*255).astype(np.uint8)
    panels=[("SIGNED SOURCE RGB",orig),("FROZEN OPENCV REFERENCE",ref),
           ("REAL CHROME REPLAY",chrome),("CHROME VS REFERENCE DIFFERENCE",colors),
           ("SIGNED FACE/LEFT/RIGHT ROI",signed_masks)]
    board=Image.new("RGB",(340*len(panels),380),(248,248,246))
    pen=ImageDraw.Draw(board)
    for i,(label,array) in enumerate(panels):
        board.paste(Image.fromarray(array,"RGB"),(i*340,40))
        pen.text((i*340+5,10),label,fill=(20,20,20))
    board.save(path)

def run(source_root:Path,gc_stage8:Path,raden_stage8:Path,out:Path)->dict:
    source_root=source_root.resolve()
    out=out.resolve()
    if out.exists():raise FileExistsError("R25 cannot overwrite evidence output")
    for source in (source_root,gc_stage8.resolve(),raden_stage8.resolve()):
        if out==source or source in out.parents or out in source.parents:
            raise ValueError("R25 research output inside frozen signed source")
    input_scenes={"GC001":gc_stage8,"Raden":raden_stage8}
    diagnostics=[]
    driver=chrome_driver()
    try:
        version=driver.capabilities.get("browserVersion","unknown")
        for case in CASES:
            info,private=render_case(case,source_root,input_scenes[case],driver)
            diagnostics.append(info)
            out.mkdir(parents=True,exist_ok=True)
            comparison_board(private,out/(case+"_r25_PRIVATE_owner_chrome_error_board.png"))
    finally:driver.quit()
    result={
     "version":VERSION,
     "measuredChromeVersion":version,
     "cases":diagnostics,
     "allOriginalInputsReauthenticated":True,
     "all11SignedStage8OwnerRegionsMeasuredEach":True,
     "signedFaceArmsEachComparedToSourceReferenceAndChrome":True,
     "hardHistoricalStage8CapPassed":False,
     "humanSemanticOwnerSigned":False,
     "sourceConnectedExactRGBIsNotAnatomyOracle":True,
     "noApprovedRepaintOrSourceGeometryChange":True,
     "productionReleaseAuthorized":False,
     "status":"R25_SIGNED_SOURCE_OWNER_ERROR_ATTRIBUTION_COMPLETE_RELEASE_NO_GO"}
    (out/"public_r25_owner_source_rgb_error_attribution.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    for k in ("source-root","gc-stage8","raden-stage8","out"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    r=run(a.source_root,a.gc_stage8,a.raden_stage8,a.out)
    for row in r["cases"]:
        print("R25_SIGNED_SOURCE_OWNER",row["case"],
              "Chrome_vs_reference",row["replayedChromeFullSceneVsFrozenReferenceDifferentPixels"],
              "phase04_signed_right_bg_overlap",
              row["historicalPhase04SignedRegions"]["right_arm"]["sourceBorderConnectedExactRGBOverlap"],
              "NO_GO",flush=True)
if __name__=="__main__":main()
