"""BrowserFallback v26: real Chrome foreground-gated lost-boundary audit, no render changes."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import threading
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def translate_path(self,path):
        if path.split("?")[0] in ("/","/index.html"):
            return str(Path(self.directory)/"static"/"index.html")
        return super().translate_path(path)

def digest(buf:bytes)->str:
    return hashlib.sha256(buf).hexdigest()

def run(root:Path,case:str,reference_zip:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(reference_zip) as ref:
        source_bytes=ref.read(case+"/source.png")
        frozen=ref.read(case+"/facet.png")
    (out/"source.png").write_bytes(source_bytes)
    handler=partial(Handler,directory=str(root/"web"))
    server=ThreadingHTTPServer(("127.0.0.1",0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    opts=webdriver.ChromeOptions()
    for flag in ("--headless=new","--no-sandbox","--disable-gpu",
        "--disable-extensions","--disable-dev-shm-usage",
        "--window-size=900,900","--user-data-dir="+str(out/"chrome-profile")):
        opts.add_argument(flag)
    driver=None
    try:
        driver=webdriver.Chrome(options=opts)
        driver.set_script_timeout(180)
        driver.get(f"http://127.0.0.1:{server.server_port}/index.html?browserFallback=force&browserFallbackQuality=facet")
        WebDriverWait(driver,60).until(lambda d:d.execute_script(
            "return !!(window.MinimalizerBrowserFallback&&window.MinimalizerBrowserSubject&&window.MinimalizerStructuralEvidenceV26)"))
        info=driver.execute_script("""return {
          profile:browserFallbackQualityProfile(),forced:browserFallbackForced(),
          observer:window.MinimalizerStructuralEvidenceV26.VERSION
        }""")
        assert info=={"profile":"facet","forced":True,
          "observer":"browser-structural-evidence-v26"},info
        print("V26_REAL_CHROME",driver.capabilities.get("browserVersion"),
          case,info,flush=True)
        result=driver.execute_async_script(r"""
const b64=arguments[0],theCase=arguments[1],done=arguments[arguments.length-1];
(async()=>{
 const binary=Uint8Array.from(atob(b64),x=>x.charCodeAt(0));
 const file=new File([binary],theCase+".png",{type:"image/png"});
 const src=await createImageBitmap(file);
 function rgba(img){
   const c=document.createElement("canvas");c.width=img.width;c.height=img.height;
   const ctx=c.getContext("2d",{willReadFrequently:true});
   ctx.drawImage(img,0,0);return ctx.getImageData(0,0,img.width,img.height).data;
 }
 const input=rgba(src);
 state.file=file;
 const response=await requestBrowserFallback();
 const outputBlob=await response.blob();
 const output=await createImageBitmap(outputBlob);
 if(output.width!==src.width||output.height!==src.height)throw Error("dimension mismatch");
 const rendered=rgba(output);
 // Reuse the existing browser foreground model; this is evidence, NOT part labels.
 const subject=await window.MinimalizerBrowserSubject.predict(file,{
   targetWidth:src.width,targetHeight:src.height
 });
 const report=window.MinimalizerStructuralEvidenceV26.observe(
   input,rendered,src.width,src.height,subject);
 const overlayCanvas=document.createElement("canvas");
 overlayCanvas.width=src.width;overlayCanvas.height=src.height;
 const ov=overlayCanvas.getContext("2d");
 ov.drawImage(src,0,0);
 const data=ov.getImageData(0,0,src.width,src.height);
 for(const i of report.overlayPixels){
   data.data[4*i]=255;data.data[4*i+1]=0;
   data.data[4*i+2]=220;data.data[4*i+3]=255;
 }
 ov.putImageData(data,0,0);
 const maskCanvas=document.createElement("canvas");
 maskCanvas.width=src.width;maskCanvas.height=src.height;
 const mx=maskCanvas.getContext("2d");
 const mask=mx.createImageData(src.width,src.height);
 for(let i=0;i<src.width*src.height;i++){
   const v=Math.max(0,Math.min(255,Math.round(subject.probability[i]*255)));
   mask.data[4*i]=mask.data[4*i+1]=mask.data[4*i+2]=v;
   mask.data[4*i+3]=255;
 }
 mx.putImageData(mask,0,0);
 const bytes=await outputBlob.arrayBuffer();
 const view=new Uint8Array(bytes);
 let str="";
 for(let i=0;i<view.length;i+=16384)
   str+=String.fromCharCode(...view.subarray(i,i+16384));
 done({ok:true,facetBase64:btoa(str),
   previewBase64:overlayCanvas.toDataURL("image/png").split(",")[1],
   maskBase64:maskCanvas.toDataURL("image/png").split(",")[1],
   profileHeader:response.headers.get("X-Minimalizer-Browser-Quality-Profile"),
   subjectProvider:subject.provider,subjectModel:subject.model,
   report});
})().catch(error=>done({ok:false,error:String(error),stack:String(error.stack)}));
""",base64.b64encode(source_bytes).decode("ascii"),case)
        if not result.get("ok"):
            raise RuntimeError("v26 real Chrome observer failed: "+str(result))
        rendered=base64.b64decode(result["facetBase64"])
        assert rendered==frozen,(case,"frozen Facet mismatch")
        assert result["profileHeader"]=="facet",result["profileHeader"]
        assert result["subjectProvider"]=="browser-u2netp"
        report=result["report"]
        assert report["provenance"]["partAuthority"] is False
        assert report["provenance"]["visibleOutputAuthority"] is False
        assert report["summary"]["knownArmSegments"]==0
        assert report["summary"]["knownGarmentSegments"]==0
        assert report["summary"]["unboundSegments"]==report["summary"]["retainedSegmentCount"]
        assert report["status"] in ("evidence_only_unbound","no_supported_lost_boundaries")
        (out/"facet.png").write_bytes(rendered)
        (out/"preview.png").write_bytes(base64.b64decode(result["previewBase64"]))
        (out/"subject_probability.png").write_bytes(base64.b64decode(result["maskBase64"]))
        # Report is deterministic source-observed data, no model-produced identities.
        (out/"metrics.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        stage={"stage":"browser-structural-evidence-v26",
          "case":case,"decision":"EVIDENCE_ONLY_NOT_SEMANTIC",
          "sourceSHA256":digest(source_bytes),"facetSHA256":digest(rendered),
          "sourceDimensions":[report["width"],report["height"]],
          "model":"browser-u2netp","modelAuthority":False,
          "semanticPartAuthority":False,
          "partsAvailable":False,"unknownIsAllowed":True,
          "visibleOutputUnmodified":True,
          "evidenceStatus":report["status"],
          "previewSHA256":digest((out/"preview.png").read_bytes()),
          "probabilitySHA256":digest((out/"subject_probability.png").read_bytes()),
          "metricsSHA256":digest((out/"metrics.json").read_bytes())}
        (out/"stage.json").write_text(json.dumps(stage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("V26_SOURCE_EVIDENCE",case,"subjectPixels",
          report["summary"]["eligibleSubjectPixels"],"lostPixels",
          report["summary"]["rawLostBoundaryPixels"],"segments",
          report["summary"]["retainedSegmentCount"],"unknown",
          report["summary"]["unboundSegments"],
          "frozen_facet_sha",stage["facetSHA256"],flush=True)
        return stage
    finally:
        if driver:driver.quit()
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--reference-zip",type=Path,required=True)
    parser.add_argument("--case",required=True,choices=("Kyoko","Noel","Ririka"))
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    run(a.root.resolve(),a.case,a.reference_zip,a.out)
