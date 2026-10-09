"""v32 non-generative, read-only source-owned connected planes from AnimeSeg masks.

Produces DIAGNOSTIC PNGs only. No browser route, no replacement of accepted Facet.
Source RGB medoids are sampled from their own connected irregular SLIC plane.
Unknown arm/garment semantics remain unbound. Never synthesize or infer pixels.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from skimage.segmentation import slic
from scipy.ndimage import label

CASES={
 "Kyoko":{
  "source":r"C:\Work\Temp\macro-gc001\GC001_source.png",
  "mask":r"C:\Work\Temp\sa1026-animeseg-gc001-v457\animeseg_mask.png",
  "source_sha":"75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",
  "mask_sha":"ea1be2ff34d3bdbef5693ab3dbe1c60363fe6365cb42454829b96994f3520148",
 },
 "Noel":{
  "source":r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\AnimeSegExecutionV30_20261009\Noel_source.png",
  "mask":r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\AnimeSegExecutionV30_20261009\Noel_animeseg_mask.png",
  "source_sha":"f0dceadc5af23eaa914d3fece271186aca428ce176d76bd91c05686b1f44ef26",
  "mask_sha":"859da4900b7d509ad9a87fb9c12573e454b7c42a2dfebbc6da94d053d6e4e7a2",
 },
 "Ririka":{
  "source":r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\AnimeSegExecutionV30_20261009\Ririka_source.png",
  "mask":r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\AnimeSegExecutionV30_20261009\Ririka_animeseg_mask.png",
  "source_sha":"6da229380c2673611b57bada10b77d03b9b831770070d594137f2062ca302914",
  "mask_sha":"13f64e315ced17dad41e8a1187c4cf5503a884d70af9e7c9de4f0ee6fc070190",
 },
}
FROZEN=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\PartEvidenceV27_20261009\v27_stages_metrics.zip")
OUT=Path(__import__("os").environ.get("MINIMALIZER_V32_OUT",r"C:\Temp\minimalizer-v32-evidence"))
CONFIGS=(("connected_coarse",260,2.0),("connected_fine",540,3.0))
GARMENT=np.array((180,0,255),dtype=np.uint8)
PROTECTED_COLORS={"Kyoko":((149,211,27),),"Noel":((68,37,36),),"Ririka":()}
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1048576),b""):h.update(part)
    return h.hexdigest()
def rgba(path):
    return np.asarray(Image.open(path).convert("RGBA"),dtype=np.uint8).copy()
def measure(src,base,candidate,mask):
    return float(np.abs(src[:,:,:3][mask].astype(np.int16)-
      candidate[:,:,:3][mask].astype(np.int16)).mean())
def reconstruct(source,baseline,eligible,nseg,compact,protected_colors=()):
    h,w=eligible.shape
    if not np.any(eligible):
      return baseline.copy(), {"regions":0,"acceptedRegions":0,"rejectedRegions":0,
        "contourVerticesDiagnostic":0,"changedPixels":0,
        "changedOutsideGarment":0,"alphaChanges":0}
    # Source-observed foreground partition; the image is never generated.
    labels=slic(source[:,:,:3],n_segments=nseg,compactness=compact,
       sigma=0.7,mask=eligible,start_label=1,enforce_connectivity=True,
       convert2lab=True,channel_axis=-1)
    labels=np.asarray(labels,dtype=np.int32)
    assert not np.any(labels[~eligible])
    out=baseline.copy()
    total_regions=0
    accepted=0
    rolled_back=0
    vertices=0
    source_color_set={tuple(x) for x in source[:,:,:3][eligible].reshape(-1,3)}
    for lab in np.unique(labels):
      if lab<=0:continue
      belongs=labels==lab
      # A plane is topologically connected; no holes can be relabeled.
      components,count=label(belongs,np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.uint8))
      for c in range(1,count+1):
        mask=components==c
        count_px=int(mask.sum())
        if count_px<7:continue
        total_regions+=1
        cols=source[:,:,:3][mask]
        median=np.median(cols,axis=0)
        squared=np.square(cols.astype(np.float32)-median).sum(axis=1)
        color=cols[int(np.argmin(squared))]
        if tuple(color) in protected_colors:
          rolled_back+=1
          continue
        # The proposed color MUST be a real pixel in this connected part.
        assert tuple(color) in source_color_set
        old=np.abs(baseline[:,:,:3][mask].astype(np.int16)-
                   cols.astype(np.int16)).sum()
        new=np.abs(color.astype(np.int16)-cols.astype(np.int16)).sum()
        if new >= old:
          rolled_back+=1
          continue
        accepted+=1
        out[:,:,:3][mask]=color
        contours,_=cv2.findContours(mask.astype(np.uint8),
          cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        vertices+=sum(len(cv2.approxPolyDP(t,1.2,True)) for t in contours)
    changed=np.any(out!=baseline,axis=2)
    assert not np.any(changed&~eligible)
    assert np.array_equal(out[:,:,3],baseline[:,:,3])
    assert all(tuple(color) in source_color_set
        for color in np.unique(out[:,:,:3][changed].reshape(-1,3),axis=0))
    return out,{"regions":total_regions,"acceptedRegions":accepted,
       "rejectedRegions":rolled_back,"contourVerticesDiagnostic":vertices,
       "changedPixels":int(changed.sum()),
       "changedOutsideGarment":int((changed&~eligible).sum()),
       "alphaChanges":int(np.count_nonzero(out[:,:,3]!=baseline[:,:,3]))}
def run():
    import zipfile
    OUT.mkdir(exist_ok=False)
    montage=Image.new("RGB",(340*5+72,len(CASES)*388+12),(246,246,246))
    draw=ImageDraw.Draw(montage)
    metrics=[]
    with zipfile.ZipFile(FROZEN) as z:
      for idx,(name,item) in enumerate(CASES.items()):
        source_path=Path(item["source"]);mask_path=Path(item["mask"])
        assert sha(source_path)==item["source_sha"],name+" source SHA"
        assert sha(mask_path)==item["mask_sha"],name+" mask SHA"
        source=rgba(source_path)
        garment=np.asarray(Image.open(mask_path).convert("RGB"),dtype=np.uint8)
        from io import BytesIO
        facet_bytes=z.read(name+"/facet.png")
        base=np.asarray(Image.open(BytesIO(facet_bytes)).convert("RGBA"),dtype=np.uint8)
        assert source.shape==base.shape==(340,340,4)
        eligible=np.all(garment==GARMENT,axis=2)&(source[:,:,3]==255)&(base[:,:,3]!=0)
        reserved=np.zeros(eligible.shape,dtype=bool)
        for rgb in PROTECTED_COLORS[name]:
          reserved|=np.all(base[:,:,:3]==rgb,axis=2)
        if name=="Kyoko":reserved[263:290,90:112]=True
        excluded=int(np.count_nonzero(eligible&reserved))
        eligible &= ~reserved
        assert eligible.any()
        visuals=[Image.fromarray(source).convert("RGB"),Image.fromarray(base).convert("RGB")]
        grid_path=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\SourcePlanesV31_20261009")/(name+"_source_garment_planes_diagnostic.png")
        visuals.append(Image.open(grid_path).convert("RGB") if grid_path.exists()
          else Image.fromarray(base).convert("RGB"))
        for key,regions,compact in CONFIGS:
          output,stat=reconstruct(source,base,eligible,regions,compact,protected_colors=PROTECTED_COLORS[name])
          assert np.array_equal(output[reserved],base[reserved])
          for rgb in PROTECTED_COLORS[name]:
            assert np.count_nonzero(np.all(base[:,:,:3]==rgb,axis=2))==np.count_nonzero(np.all(output[:,:,:3]==rgb,axis=2))
          mae_base=measure(source,base,base,eligible)
          mae_new=measure(source,base,output,eligible)
          assert mae_new<=mae_base+1e-5
          out_path=OUT/(name+"_"+key+".png")
          Image.fromarray(output).save(out_path,optimize=True)
          stat.update({"name":name,"variant":key,
            "sourceSHA256":item["source_sha"],"maskSHA256":item["mask_sha"],
            "facetSHA256":hashlib.sha256(facet_bytes).hexdigest(),
            "outputSHA256":sha(out_path),
            "sourceRGBMAEFacet":round(mae_base,5),
            "sourceRGBMAECandidate":round(mae_new,5),
            "eligibleGarmentPixels":int(eligible.sum()),
            "excludedProtectedGarmentPixels":excluded,
            "protectedColorMassExact":True,
            "protectedRegionPixelChanges":0,
            "inputMaskPartAuthority":False,"newColors":False,
            "semanticArmsVerified":False,"productionAuthority":False})
          metrics.append(stat)
          visuals.append(Image.fromarray(output).convert("RGB"))
          print("V32_SOURCE_CONTOUR",name,key,
             "regions",stat["regions"],"accepted",stat["acceptedRegions"],
             "changed",stat["changedPixels"],"MAE",
             stat["sourceRGBMAEFacet"],stat["sourceRGBMAECandidate"],flush=True)
        for col,(img,title) in enumerate(zip(visuals,
             ("Original","Frozen Facet","v31 tiled or Facet","v32 connected coarse","v32 connected fine"))):
          x=12+col*352;y=12+idx*388
          draw.text((x,y),name+" "+title,fill=(25,35,50))
          montage.paste(img,(x,y+27))
    montage.save(OUT/"v32_source_contiguous_comparison.png",optimize=True)
    report={"status":"CONNECTED_SOURCE_PLANES_RESEARCH_COMPLETED_VISUAL_HOLD",
       "cases":metrics,"sourceAndFacetIntact":True,
       "renderAuthority":False,"productionPromoted":False,
       "semanticPartAuthority":False,"generativeImageUse":False,
       "note":"Segmentation planes derive from observed source RGB, but AnimeSeg mask itself is not independently trusted arm/garment truth."}
    (OUT/"v32_metrics.json").write_text(
       json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    columns=["name","variant","regions","acceptedRegions","rejectedRegions",
       "contourVerticesDiagnostic","eligibleGarmentPixels","changedPixels",
       "sourceRGBMAEFacet","sourceRGBMAECandidate","changedOutsideGarment","alphaChanges"]
    with (OUT/"v32_metrics.csv").open("w",encoding="utf-8-sig",newline="") as f:
       writer=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
       writer.writeheader();writer.writerows(metrics)
if __name__=="__main__":run()
