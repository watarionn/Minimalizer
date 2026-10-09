"""v27 Chrome 154 research: SHA-pinned multiclass and pose source-only evidence.
No Local Worker, generated image, or visible Minimalizer changes.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,threading,zipfile,time
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def translate_path(self,path):
        if path.split("?")[0] in ("/","/index.html"):
            return str(Path(self.directory)/"static"/"index.html")
        return super().translate_path(path)

def digest(x):return hashlib.sha256(x).hexdigest()

def compare(root:Path,archive:Path,case:str,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        source=z.read(case+"/source.png")
        facet=z.read(case+"/facet.png")
    (out/"source.png").write_bytes(source)
    handler=partial(Handler,directory=str(root/"web"))
    server=ThreadingHTTPServer(("127.0.0.1",0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    options=webdriver.ChromeOptions()
    for flag in ("--headless=new","--no-sandbox","--disable-gpu",
        "--disable-extensions","--disable-dev-shm-usage",
        "--window-size=900,900","--user-data-dir="+str(out/"chrome-profile")):
        options.add_argument(flag)
    driver=None
    try:
        driver=webdriver.Chrome(options=options)
        driver.set_script_timeout(360)
        driver.get(f"http://127.0.0.1:{server.server_port}/index.html?browserFallback=force&browserFallbackQuality=facet")
        WebDriverWait(driver,60).until(lambda d:d.execute_script("""
return !!(window.MinimalizerBrowserSubject&&window.MinimalizerBrowserFallback
  &&window.MinimalizerStructuralEvidenceV26&&window.MinimalizerBrowserPartEvidenceV27)
"""))
        browser=driver.capabilities.get("browserVersion")
        print("V27_BROWSER",browser,case,flush=True)
        started=time.monotonic()
        output=driver.execute_async_script(r"""
const b64=arguments[0],name=arguments[1],done=arguments[arguments.length-1];
(async()=>{
 const raw=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
 const file=new File([raw],name+".png",{type:"image/png"});
 const original=await createImageBitmap(file);
 const w=original.width,h=original.height;
 const canvas=document.createElement("canvas");canvas.width=w;canvas.height=h;
 const ctx=canvas.getContext("2d",{willReadFrequently:true});
 ctx.drawImage(original,0,0);
 const sourcePixels=ctx.getImageData(0,0,w,h).data;
 state.file=file;
 const facetResponse=await requestBrowserFallback();
 const facetBlob=await facetResponse.blob();
 const resultImg=await createImageBitmap(facetBlob);
 if(resultImg.width!==w||resultImg.height!==h)throw Error("facet dimension mismatch");
 ctx.clearRect(0,0,w,h);ctx.drawImage(resultImg,0,0);
 const facetPixels=ctx.getImageData(0,0,w,h).data;
 const fg=await window.MinimalizerBrowserSubject.predict(file,{targetWidth:w,targetHeight:h});
 const edges=window.MinimalizerStructuralEvidenceV26.observe(sourcePixels,facetPixels,w,h,fg);
 const evidence=await window.MinimalizerBrowserPartEvidenceV27.observe(original,fg,edges,w,h);
 // Render artifact ONLY, never a Minimalizer visible result:
 const maskCanvas=document.createElement("canvas");
 maskCanvas.width=w;maskCanvas.height=h;
 const mc=maskCanvas.getContext("2d");
 const mask=mc.createImageData(w,h);
 const palette=[[0,0,0],[244,165,43],[240,189,156],[244,214,170],
   [30,187,125],[112,119,138]];
 for(let i=0;i<w*h;i++){
    let k=evidence.categoryMap[i],color=palette[k]||[0,0,0];
    for(let c=0;c<3;c++)mask.data[4*i+c]=color[c];
    mask.data[4*i+3]=255;
 }
 mc.putImageData(mask,0,0);
 // Arm corridor is an *observed pose cue*, yellow/cyan lines ONLY when
 // source foreground and verified model class corroborate it.
 const overlay=document.createElement("canvas");overlay.width=w;overlay.height=h;
 const ov=overlay.getContext("2d",{willReadFrequently:true});
 ov.drawImage(original,0,0);
 const overlayData=ov.getImageData(0,0,w,h);
 const edgePixels=new Set(edges.overlayPixels);
 for(const i of edgePixels){
   const cue=evidence.armCueMap[i];
   const k=evidence.categoryMap[i];
   const rgb=cue===1?[250,204,28]:cue===2?[30,217,228]:cue===3?[241,74,214]:
     k===4?[20,236,122]:null;
   if(!rgb)continue;
   for(let c=0;c<3;c++)overlayData.data[4*i+c]=rgb[c];
   overlayData.data[4*i+3]=255;
 }
 ov.putImageData(overlayData,0,0);
 function imageBase64(c){return c.toDataURL("image/png").split(",")[1]}
 const bytes=new Uint8Array(await facetBlob.arrayBuffer());
 let s="";
 for(let i=0;i<bytes.length;i+=16384)
  s+=String.fromCharCode(...bytes.subarray(i,i+16384));
 const report={version:evidence.version,decision:evidence.decision,
   provenance:evidence.provenance,summary:evidence.summary,
   failures:evidence.failures,segments:evidence.segments,
   v26:{summary:edges.summary,status:edges.status,provenance:edges.provenance}};
 done({ok:true,facetBase64:btoa(s),
   classMaskBase64:imageBase64(maskCanvas),
   overlayBase64:imageBase64(overlay),
   report,profile:facetResponse.headers.get("X-Minimalizer-Browser-Quality-Profile")});
})().catch(e=>done({ok:false,error:String(e),stack:String(e.stack)}));
""",base64.b64encode(source).decode("ascii"),case)
        if not output.get("ok"):
            raise RuntimeError("V27 browser error "+str(output)[:1200])
        assert output["profile"]=="facet"
        real=base64.b64decode(output["facetBase64"])
        assert real==facet,"V27 changed original frozen Facet"
        report=output["report"]
        assert report["version"]=="browser-part-evidence-v27"
        assert report["decision"]=="research_part_observations_only"
        assert report["provenance"]["visibleOutputAuthority"] is False
        assert report["provenance"]["partOwnershipAuthority"] is False
        assert report["summary"]["unbound"]==report["summary"]["sourceEdges"]
        assert all(s["semanticPart"]=="unbound" for s in report["segments"])
        (out/"facet.png").write_bytes(real)
        (out/"part_classes.png").write_bytes(base64.b64decode(output["classMaskBase64"]))
        (out/"preview.png").write_bytes(base64.b64decode(output["overlayBase64"]))
        (out/"metrics.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        stage={"stage":"browser-part-evidence-v27",
          "source_sha256":digest(source),"facet_sha256":digest(facet),
          "part_model_sha256":report["provenance"]["multiclassSHA"],
          "pose_model_sha256":report["provenance"]["poseSHA"],
          "source_dimensions":[340,340],"source_case":case,"browser":browser,
          "visible_output_changed":False,"semantic_part_authority":False,
          "part_mask_preview_sha256":digest((out/"part_classes.png").read_bytes()),
          "preview_sha256":digest((out/"preview.png").read_bytes()),
          "metrics_sha256":digest((out/"metrics.json").read_bytes())}
        (out/"stage.json").write_text(json.dumps(stage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("V27_CASE",case,"time",round(time.monotonic()-started,2),
          "classes",report["summary"]["multiclassStatus"],
          "pose",report["summary"]["poseStatus"],
          "clothes",report["summary"]["garmentCueSegments"],
          "left",report["summary"]["leftArmCueSegments"],
          "right",report["summary"]["rightArmCueSegments"],
          "failure",report["failures"],flush=True)
        return stage
    finally:
        if driver:driver.quit()
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--reference-zip",type=Path,required=True)
    p.add_argument("--case",choices=["Kyoko","Noel","Ririka"],required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    compare(x.root.resolve(),x.reference_zip.resolve(),x.case,x.out.resolve())
