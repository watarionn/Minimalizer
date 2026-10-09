"""v33 actual Chrome 155 vector SVG raster audit, source fidelity and rollback.

Uses offline localhost/data SVG rendering; no AI inference and no production routing.
Each path is truly vector geometry, while the unchanged Facet background is
embedded as a separate raster in the self-contained SVG.
"""
from __future__ import annotations
import argparse,base64,hashlib,importlib.util,json,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

ROOT=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\ConnectedSourcePlanesV32_20261009")
CASES=("Kyoko","Noel","Ririka")
EPSILON=1.1

def load(path):
    spec=importlib.util.spec_from_file_location("v33_vector",path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def browser():
    options=webdriver.ChromeOptions()
    for flag in ("--headless=new","--no-sandbox","--disable-gpu",
                 "--disable-extensions","--disable-dev-shm-usage",
                 "--window-size=900,900"):
        options.add_argument(flag)
    b=webdriver.Chrome(options=options)
    b.set_script_timeout(90)
    b.get("data:text/html,<html><body>v33 source SVG audit</body></html>")
    return b

def render(driver,svg_path:Path,destination:Path):
    svg=svg_path.read_text(encoding="utf-8")
    answer=driver.execute_async_script(r"""
const svg=arguments[0], done=arguments[arguments.length-1];
const blob=new Blob([svg],{type:"image/svg+xml"});
const url=URL.createObjectURL(blob);
const img=new Image();
img.onload=()=>{
 try{
 const canvas=document.createElement("canvas");
 canvas.width=340;canvas.height=340;
 const context=canvas.getContext("2d",{willReadFrequently:true});
 context.clearRect(0,0,340,340);
 context.drawImage(img,0,0,340,340);
 const rgba=context.getImageData(0,0,340,340);
 if(rgba.data.length!==340*340*4)throw Error("invalid SVG render dimensions");
 const img64=canvas.toDataURL("image/png").split(",")[1];
 done({ok:true,data:img64,dimensions:[canvas.width,canvas.height]});
 }catch(e){done({ok:false,error:String(e)})}
 finally{URL.revokeObjectURL(url);}
};
img.onerror=()=>{URL.revokeObjectURL(url);done({ok:false,error:"browser SVG image onerror"})};
img.src=url;
""",svg)
    if not answer.get("ok"):raise RuntimeError(str(answer))
    destination.write_bytes(base64.b64decode(answer["data"]))
    im=np.asarray(Image.open(destination).convert("RGBA"),dtype=np.uint8)
    if im.shape!=(340,340,4):raise RuntimeError("invalid SVG screenshot")
    return im

def sha(path:Path):return hashlib.sha256(path.read_bytes()).hexdigest()

def assess(mod,name,candidate,target,base,source,seg):
    allowed,protected=mod.class_mask_and_protections(name,source,seg,base)
    delta=np.any(candidate!=base,axis=2)
    mismatch=np.any(candidate!=target,axis=2)
    target_changed=np.any(target!=base,axis=2)
    changes_out=int((delta&~allowed).sum())
    mismatches_out=int((mismatch&~allowed).sum())
    alpha=int(np.count_nonzero(candidate[:,:,3]!=base[:,:,3]))
    protected_changed=int((np.any(candidate!=base,axis=2)&protected).sum())
    protected_mass={}
    for rgb in mod.RGBS[name]:
        old=int(np.all(base[:,:,:3]==rgb,axis=2).sum())
        new=int(np.all(candidate[:,:,:3]==rgb,axis=2).sum())
        protected_mass[str(rgb)]=[old,new]
    real_colors={tuple(c) for c in source[:,:,:3][allowed]}
    unsupported_colors={
        tuple(c) for c in np.unique(candidate[:,:,:3][delta].reshape(-1,3),axis=0)
        if tuple(c) not in real_colors
    }
    # Pixel-accurate *reference* parity is strict; smoothed candidate must
    # pass every semantic, external RGB and protected-color policy independently.
    mask_rmse=float(np.abs(candidate[:,:,:3][allowed].astype(np.int16)-
        target[:,:,:3][allowed].astype(np.int16)).mean())
    return {"deltaPixels":int(delta.sum()),"pixelsDifferentFromV32":int(mismatch.sum()),
        "differentOutsideAllowed":mismatches_out,"changesOutsideAllowed":changes_out,
        "alphaChanges":alpha,"protectedPixelChanges":protected_changed,
        "protectedColorMass":protected_mass,
        "newRasterRGBCount":len(unsupported_colors),
        "meanRGBDifferenceFromV32InsideMask":round(mask_rmse,5),
        "referenceChangedPixels":int(target_changed.sum()),
        "sourcePaletteOnly":len(unsupported_colors)==0,
        "safe":changes_out==0 and alpha==0 and protected_changed==0 and
        not unsupported_colors and all(old==new for old,new in protected_mass.values())}

def run(repo:Path,out:Path):
    if out.exists():raise FileExistsError("v33 stage already exists; no overwrite")
    out.mkdir(parents=True)
    mod=load(repo/"tools/vectorize_browser_planes_v33.py")
    rows=[]
    montage=Image.new("RGB",(5*340+72,len(CASES)*389+16),(246,246,246))
    draw=ImageDraw.Draw(montage)
    b=browser()
    try:
      ver=b.capabilities.get("browserVersion")
      for j,name in enumerate(CASES):
        source=mod.rgba(ROOT/(name+"_source.png"))
        base=mod.rgba(ROOT/(name+"_facet.png"))
        mask=mod.rgba(ROOT/(name+"_anime_seg_mask.png"))
        ref=mod.rgba(ROOT/(name+"_connected_fine.png"))
        visuals=[Image.fromarray(source).convert("RGB"),
                 Image.fromarray(base).convert("RGB"),
                 Image.fromarray(ref).convert("RGB")]
        record={"case":name,"browserVersion":ver,"targetSHA":sha(ROOT/(name+"_connected_fine.png")),
                "sourceSHA":sha(ROOT/(name+"_source.png")),"variants":{}}
        for variant,epsilon in (("exact",0.0),("simplified",EPSILON)):
            svg=out/(name+"_"+variant+".svg")
            created=mod.vectorize(name,"connected_fine",epsilon,svg)
            raster=out/(name+"_"+variant+"_chrome.png")
            im=render(b,svg,raster)
            score=assess(mod,name,im,ref,base,source,mask)
            if variant=="exact":
                if score["pixelsDifferentFromV32"]!=0 or not score["safe"]:
                    raise AssertionError(f"{name}: exact vector SVG raster fails parity {score}")
            score.update(created)
            score["svgFile"]=svg.name;score["svgRaster"]=raster.name
            score["chromeRasterSHA256"]=sha(raster)
            record["variants"][variant]=score
            visuals.append(Image.fromarray(im).convert("RGB"))
            print("V33_CHROME",name,variant,"paths",score["pathCount"],
                "verts",score["svgVertices"],"mismatch",score["pixelsDifferentFromV32"],
                "outside",score["changesOutsideAllowed"],
                "newRGB",score["newRasterRGBCount"],
                "safe",score["safe"],flush=True)
        simplified=record["variants"]["simplified"]
        # Never mark a candidate safe just because it looks nice. Publish
        # only exact vector representation until topology/semantic gate passes.
        simplified["productionReady"]=False
        simplified["candidateAcceptance"]="RESEARCH_ONLY" if simplified["safe"] else "REJECT_UNSAFE"
        record["decision"]="SVG_EXACT_PARITY_PASS_SIMPLIFICATION_ON_HOLD"
        rows.append(record)
        for col,(img,label) in enumerate(zip(visuals,
            ("Original","Frozen Facet","v32 plane raster","v33 SVG exact","v33 SVG simplified"))):
            x=12+col*352;y=10+j*389
            draw.text((x,y),name+" "+label,fill=(35,40,45))
            montage.paste(img,(x,y+26))
    finally:
      b.quit()
    montage.save(out/"v33_svg_browser_comparison.png",optimize=True)
    metrics={"status":"SOURCE_OWNED_SVG_VECTOR_RESEARCH_COMPLETE_PRODUCTION_HOLD",
      "cases":rows,"browserNativeSVGRenderer":True,
      "nonGenerative":True,"partSemanticAuthority":False,
      "publicMainModified":False,"localWorkerModified":False,
      "SVGBackgroundRasterFacetEmbedded":True,
      "holds":["No browser inference model","No trusted left/right arm ownership",
               "No shared-edge Bezier parity proof","No production promotion"]}
    (out/"v33_metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("V33_FINISH",len(rows),"cases",flush=True)
    return metrics

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.repo,args.out)
