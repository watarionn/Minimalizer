"""R5 genuine Public route browser canary: OFF, ON, missing observer, missing WASM.

Runs built static production-style Public route locally in real Chrome. SHA-verified
archived v32 test images are used solely as deterministic *input fixtures*, NOT
as a visual-quality Golden for this conversion. Production unchanged.
"""
from __future__ import annotations
import argparse
import base64
import functools
import hashlib
import http.server
import json
import socketserver
import threading
from pathlib import Path
from verify_public_v34_svgo_chrome import CASES,check_sha,chrome_driver,sha
from scripts import build_shin_static as build_static

JS_RUN=r"""
const done=arguments[arguments.length-1],input=arguments[0];
(async()=>{try{
if(!window.MinimalizerComputeRoute?.minimalize)
 throw Error("real Public route not loaded");
const decoded=atob(input);
const bytes=new Uint8Array(decoded.length);
for(let i=0;i<decoded.length;i++)bytes[i]=decoded.charCodeAt(i);
const file=new File([bytes],"r5_source_fixture.png",{type:"image/png"});
const result=await window.MinimalizerComputeRoute.minimalize(file);
const copy=await result.response.arrayBuffer();
const png=new Uint8Array(copy);
let packed="";
for(let i=0;i<png.length;i+=16384)
 packed+=String.fromCharCode(...png.slice(i,i+16384));
done({ok:true,shaStatus:window.MinimalizerPublicR5ShadowLast??null,
      png:btoa(packed),type:result.response.headers.get("Content-Type"),
      compute:result.response.headers.get("X-Minimalizer-Compute"),
      quality:result.qualityTier});
}catch(error){done({ok:false,error:String(error),stack:String(error?.stack??"")});}})();
"""
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,format,*args):
        pass
class ThreadServer(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
    daemon_threads=True

def browser_run(url:str,source:bytes,flags:str,block:tuple[str,...]=()) -> dict:
    driver=chrome_driver()
    try:
        driver.set_script_timeout(240)
        if block:
            driver.execute_cdp_cmd("Network.enable",{})
            driver.execute_cdp_cmd("Network.setBlockedURLs",{"urls":list(block)})
            driver.execute_cdp_cmd("Network.setCacheDisabled",{"cacheDisabled":True})
        driver.get(url+"?browserFallbackQuality=lite"+flags)
        event=driver.execute_async_script(JS_RUN,base64.b64encode(source).decode("ascii"))
        if not event.get("ok"):raise RuntimeError("Public actual browser failed: "+str(event))
        png=base64.b64decode(event["png"],validate=True)
        if png[:8]!=b"\x89PNG\r\n\x1a\n":
            raise ValueError("browser returned non-PNG")
        return {"png":png,"sha256":hashlib.sha256(png).hexdigest(),
                "bytes":len(png),"shadow":event.get("shaStatus"),
                "contentType":event.get("type"),
                "compute":event.get("compute"),
                "qualityTier":event.get("quality"),
                "chromeVersion":driver.capabilities.get("browserVersion","unknown")}
    finally:
        driver.quit()

def execute(v32:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R5 evidence target exists")
    for name in CASES:
        check_sha(v32,"v32_evidence_manifest.json",v32/f"{name}_connected_fine.png")
    out.mkdir(parents=True)
    dist=build_static.build()
    server=ThreadServer(("127.0.0.1",0),functools.partial(QuietHandler,directory=str(dist)))
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    url=f"http://127.0.0.1:{server.server_address[1]}/"
    rows=[]
    try:
        for name in CASES:
            source=(v32/f"{name}_connected_fine.png").read_bytes()
            off=browser_run(url,source,"")
            on=browser_run(url,source,"&publicR5Shadow=1")
            expected=off["sha256"]
            if off["shadow"] is not None:raise AssertionError("OFF unexpectedly activated observer")
            diag=on["shadow"]
            if not diag or diag.get("status")!="ok" or diag.get("sha256")!=on["sha256"]:
                raise AssertionError("enabled R5 shadow did not independently hash unchanged PNG")
            if diag.get("applied") is not False or diag.get("productionPromoted") is not False:
                raise AssertionError("shadow claimed production output")
            unchanged=off["png"]==on["png"]
            row={"case":name,"fixtureInputSHA256":sha(v32/f"{name}_connected_fine.png"),
                 "offSHA256":expected,"onSHA256":on["sha256"],
                 "offBytes":off["bytes"],"onBytes":on["bytes"],
                 "offAndOnByteExact":unchanged,
                 "onDiagnosticStatus":diag.get("status"),
                 "onDiagnosticSHA256":diag.get("sha256"),
                 "chromeVersion":off["chromeVersion"]}
            (out/f"{name}_r5_output_off.png").write_bytes(off["png"])
            (out/f"{name}_r5_output_on.png").write_bytes(on["png"])
            rows.append(row)
            print(name,"OFF_ON_BYTE_EXACT",unchanged,"shadow",diag.get("status"),flush=True)
        # Fresh uncached browser denies the shadow module AND resvg WASM;
        # normal Public conversion must survive with identical PNG.
        source=(v32/f"{CASES[0]}_connected_fine.png").read_bytes()
        missing=browser_run(url,source,"&publicR5Shadow=1",
                            block=("*public-r5-shadow-gate.mjs*","*resvg-wasm*"))
        failed_mode_safe=(missing["sha256"]==rows[0]["offSHA256"] and
                          missing["shadow"] and
                          missing["shadow"]["status"]=="unavailable")
        (out/"Kyoko_r5_missing_observer_output.png").write_bytes(missing["png"])
        report={"version":"r5-public-route-shadow-canary-v1","cases":rows,
                "allOffOnByteExact":all(r["offAndOnByteExact"] for r in rows),
                "missingObserverWasmFallbackByteExact":failed_mode_safe,
                "missingObserverStatus":missing["shadow"]["status"] if missing["shadow"] else None,
                "realChrome":True,"staticPublicRouteTested":True,
                "fixtureIsFrozenMinimalizedPNGNotOriginalPhoto":True,
                "deviceIphoneSafariReviewed":False,
                "semanticSourceOwnersReviewed":False,
                "stage8OriginalBudgetPass":False,
                "humanGoldenApproved":False,
                "resvgCrossEngineDpr2Pass":False,
                "productionPromoted":False,"localMinimalizerTouched":False}
        report["researchPass"]=report["allOffOnByteExact"] and failed_mode_safe
        (out/"public_r5_browser_canary.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return report
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--v32",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=execute(a.v32,a.out)
    if not result["researchPass"]:raise SystemExit("R5 FAIL-CLOSED: route output changed")
    print("R5_REAL_CHROME_SHADOW_ON_OFF_FALLBACK_PASS / RELEASE_HOLD",flush=True)
if __name__=="__main__":main()
