"""v31 non-generative source-backed garment color-plane research.

Only source RGB observed inside AnimeSeg's original garment observation
is quantized into connected grid-aligned planes; this is an independent
diagnostic, not a replacement for the accepted Facet renderer.
"""
from pathlib import Path
import json,hashlib,math,csv
from collections import Counter
from PIL import Image, ImageDraw
ROOT=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\AnimeSegExecutionV30_20261009")
OUT=Path(r"C:\Temp\minimalizer-v31-evidence")
OUT.mkdir(parents=True,exist_ok=False)
LABEL=(180,0,255)
EXPECTED={"Noel":{"source":"f0dceadc5af23eaa914d3fece271186aca428ce176d76bd91c05686b1f44ef26","mask":"859da4900b7d509ad9a87fb9c12573e454b7c42a2dfebbc6da94d053d6e4e7a2"},
"Ririka":{"source":"6da229380c2673611b57bada10b77d03b9b831770070d594137f2062ca302914","mask":"13f64e315ced17dad41e8a1187c4cf5503a884d70af9e7c9de4f0ee6fc070190"}}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[]
gallery=Image.new("RGB",(340*4+50,2*385),(246,246,246))
gd=ImageDraw.Draw(gallery)
for row,name in enumerate(("Noel","Ririka")):
 source=ROOT/(name+"_source.png")
 mask=ROOT/(name+"_animeseg_mask.png")
 facet=ROOT/(name+"_facet.png")
 assert sha(source)==EXPECTED[name]["source"] and sha(mask)==EXPECTED[name]["mask"]
 src=Image.open(source).convert("RGBA")
 sem=Image.open(mask).convert("RGB")
 base=Image.open(facet).convert("RGBA")
 assert src.size==sem.size==base.size==(340,340)
 s=list(src.getdata());m=list(sem.getdata());b=list(base.getdata())
 # White/transparent silhouette is owned by Facet, never reconstructed here.
 target={i for i,p in enumerate(m) if p==LABEL and s[i][3]==255 and b[i][3]!=0}
 # Connected grid tiles: 8x8 source-observed points, robust median RGB
 # No invented palette: select the actual RGB source medoid of each tile.
 tiles=[]; plane=base.copy();px=list(plane.getdata());sampled=0
 for yy in range(0,340,8):
  for xx in range(0,340,8):
   ids=[y*340+x for y in range(yy,min(yy+8,340)) for x in range(xx,min(xx+8,340)) if y*340+x in target]
   if len(ids)<8:continue
   cols=[s[i][:3] for i in ids]
   center=tuple(sorted(c[k] for c in cols)[len(cols)//2] for k in range(3))
   medoid=min(cols,key=lambda c:sum((c[k]-center[k])**2 for k in range(3)))
   for i in ids:
    # Display preview only; use original Facet alpha, do not introduce pixels.
    px[i]=(*medoid,b[i][3])
   sampled+=len(ids)
   tiles.append({"bbox":[xx,yy,min(8,340-xx),min(8,340-yy)],"count":len(ids),"sourceMedoidRGB":list(medoid)})
 plane.putdata(px)
 out=OUT/(name+"_source_garment_planes_diagnostic.png");plane.save(out,optimize=True)
 # Original source-garment RGB vs baseline/quantized diagnostic, SAME observed pixels.
 err0=sum(sum(abs(s[i][k]-b[i][k]) for k in range(3)) for i in target)/(3*max(1,len(target)))
 err1=sum(sum(abs(s[i][k]-px[i][k]) for k in range(3)) for i in target)/(3*max(1,len(target)))
 changed={i for i,(a,c) in enumerate(zip(b,px)) if a!=c}
 assert changed<=target
 assert all(px[i][3]==b[i][3] for i in range(len(px)))
 assert all(px[i]==b[i] for i in range(len(px)) if i not in target)
 rec={"case":name,"sourceSHA":sha(source),"maskSHA":sha(mask),"facetSHA":sha(facet),"garmentObservedPixels":len(target),"sampledPixels":sampled,"tilePlanes":len(tiles),
   "changedPreviewPixels":len(changed),"changedOutsideObservedGarment":len(changed-target),"alphaChangedPixels":0,
   "sourceRGBMAEFacetOnModelGarment":round(err0,5),
   "sourceRGBMAEDiagnosticOnModelGarment":round(err1,5),
   "sourceOnlyRGB":True,"semanticAccuracyVerified":False,"armPartsVerified":False,"productionAuthority":False,
   "diagnosticImageSHA":sha(out),"tiles":tiles}
 records.append(rec)
 for col,(im,label) in enumerate(((src.convert("RGB"),"Original"),(base.convert("RGB"),"Facet baseline"),(sem,"AnimeSeg observation"),(plane.convert("RGB"),"Source tiles ONLY diagnostic"))):
  x=10+col*350;y=row*385+8
  gd.text((x,y),name+" "+label,fill=(20,20,20))
  gallery.paste(im,(x,y+27))
 print("V31_SOURCE_PLANE",name,"planes",len(tiles),"mask_px",len(target),"changed",len(changed),"MAE",round(err0,3),round(err1,3),flush=True)
gallery.save(OUT/"v31_source_planes_comparison.png",optimize=True)
report={"status":"SOURCE_PLANE_DIAGNOSTIC_PASS_RENDER_PROMOTION_HOLD","method":"8x8 fixed source-medoid tiles clipped to observed AnimeSeg clothes and existing Facet alpha","cases":records,
 "claims":["not a browser implementation","not a semantically validated garment/arm mask","no new colors/no image generation","diagnostic only; Facet production unaffected"]}
(OUT/"v31_metrics.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
with (OUT/"v31_metrics.csv").open("w",encoding="utf-8-sig",newline="") as f:
 keys=["case","garmentObservedPixels","sampledPixels","tilePlanes","changedPreviewPixels","changedOutsideObservedGarment","alphaChangedPixels","sourceRGBMAEFacetOnModelGarment","sourceRGBMAEDiagnosticOnModelGarment"]
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows([{k:r[k] for k in keys} for r in records])
assert all(r["changedOutsideObservedGarment"]==r["alphaChangedPixels"]==0 for r in records)
