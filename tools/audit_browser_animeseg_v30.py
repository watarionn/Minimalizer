"""V30 source-bound AnimeSeg v3 masks, frozen v29 sparse probes, no render changes."""
from pathlib import Path
import json, hashlib, zipfile, csv
from PIL import Image,ImageDraw
ROOT=Path(r"C:\Temp\minimalizer-v30-evidence")
V27=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\PartEvidenceV27_20261009\v27_stages_metrics.zip")
V29=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\AnimeCorpusSafetyV29_20261009\v29_sparse_anchor_results.csv")
OUT=ROOT/"audit";OUT.mkdir(exist_ok=True)
palette={(0,0,0):"background",(255,220,180):"skin",(100,150,255):"face",(255,0,0):"hair_main",(0,255,255):"left_eye",(255,255,0):"right_eye",(150,255,0):"left_eyebrow",(0,255,100):"right_eyebrow",(255,140,0):"nose",(255,0,150):"mouth",(180,0,255):"clothes",(128,128,0):"accessory"}
sha=lambda b:hashlib.sha256(b).hexdigest()
with V29.open(encoding="utf-8-sig",newline="") as f:anchors=list(csv.DictReader(f))
gallery=Image.new("RGB",(340*4+50,340*2+90),(244,244,244)); draw=ImageDraw.Draw(gallery)
result={"status":"ANIMESEG_CPU_EXECUTION_PASS_SEMANTIC_VISUAL_HOLD","semanticAuthority":False,"browserModelReady":False,"renderedOutputModified":False,"cases":{}}
with zipfile.ZipFile(V27) as z:
 for row,n in enumerate(("Noel","Ririka")):
  folder=ROOT/n
  src=(folder/"source.png").read_bytes(); mask=(folder/"animeseg_mask.png").read_bytes()
  assert src==z.read(n+"/source.png")
  facet=z.read(n+"/facet.png");(folder/"facet.png").write_bytes(facet)
  a=Image.open(folder/"source.png").convert("RGBA")
  b=Image.open(folder/"animeseg_mask.png").convert("RGB")
  f=Image.open(folder/"facet.png").convert("RGB")
  assert a.size==b.size==f.size==(340,340)
  pix=list(b.getdata()); assert set(pix)<=set(palette)
  matches=[]; counts={"matched":0,"abstained":0,"misclassified":0}
  for item in anchors:
   if item["case"]!=n:continue
   x,y=int(item["x"]),int(item["y"])
   observed=palette[b.getpixel((x,y))]
   desired="hair_main" if item["visibleReference"]=="hair" else "clothes"
   status="matched" if observed==desired else "abstained" if observed=="background" else "misclassified"
   counts[status]+=1
   matches.append({"id":item["id"],"x":x,"y":y,"expected":desired,"observed":observed,"status":status})
  assert len(matches)==10
  annotated=b.copy();ad=ImageDraw.Draw(annotated)
  for p in matches:ad.ellipse((p["x"]-4,p["y"]-4,p["x"]+4,p["y"]+4),outline=(255,255,255),width=2)
  for col,(im,label) in enumerate(((a.convert("RGB"),"Original"),(f,"Facet unchanged"),(b,"AnimeSeg mask"),(annotated,"10 sparse probes"))):
   xx=10+col*350;yy=10+row*385
   gallery.paste(im,(xx,yy+28));draw.text((xx,yy),n+" "+label,fill=(0,0,0))
  obj=json.loads((folder/"worker_stdout.txt").read_text(encoding="utf-8"))
  assert obj["status"]=="ok" and obj["authority"] is False and obj["mask_sha256"]==sha(mask)
  result["cases"][n]={"sourceSHA256":sha(src),"facetSHA256":sha(facet),"maskSHA256":sha(mask),"counts":obj["pixel_counts"],"unknownPixels":obj["unknown_pixel_count"],"sparseProbeCounts":counts,"sparseProbes":matches,"workerExitCode":0}
  (folder/"stage.json").write_text(json.dumps(result["cases"][n],indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
  print("V30_ANALYSIS",n,counts,"mask",sha(mask),flush=True)
gallery.save(OUT/"v30_noel_ririka_original_facet_animeseg.png",optimize=True)
(OUT/"v30_metrics.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
with (OUT/"v30_sparse_animeseg.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["case","id","x","y","expected","observed","status"]);w.writeheader()
 for name,case in result["cases"].items():
  for p in case["sparseProbes"]:w.writerow({"case":name,**p})
print("V30_AUDIT_PASS",len(result["cases"]),"cases",flush=True)
