"""R9 isolated static release switching, browser cache hazard, and rollback research.

Real existing Public static builder + live loopback Chrome. No remote deployment,
no live routing, no product files written and NO Safari/device signoff.
"""
from __future__ import annotations
import argparse
import functools
import hashlib
import http.server
import importlib.util
import json
import shutil
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlsplit

from verify_public_v34_svgo_chrome import chrome_driver

ROOT=Path(__file__).resolve().parents[1]
PUBLIC_STATIC=ROOT/"web"/"static"
VERSION="public-r9-disposable-browser-cache-cutover-v1"
ROUTES=(
    "/index.html",
    "/static/app.js?v=20261008-local-public",
    "/static/styles.css",
    "/static/vendor/resvg-wasm/index_bg.wasm",
)
MARKERS={
    "index.html":b"\n<!-- R9 disposable staged release only -->\n",
    "static/app.js":b"\n/* R9 disposable staged release only */\n",
    "static/styles.css":b"\n/* R9 disposable staged release only */\n",
}
BROWSER_SAMPLE=r"""
const done=arguments[arguments.length-1];
const urls=arguments[0],mode=arguments[1],stamp=arguments[2];
(async()=>{try{
const rows=[];
for(const entry of urls){
 const url=stamp ? entry+(entry.includes('?')?'&':'?')+'r9verify='+stamp : entry;
 const res=await fetch(url,{cache:mode});
 if(!res.ok)throw Error('HTTP '+res.status+' '+url);
 const bytes=await res.arrayBuffer();
 const digest=await crypto.subtle.digest('SHA-256',bytes);
 const hex=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
 rows.push({route:entry,sha256:hex,bytes:bytes.byteLength,cache:mode});
}
const controllers=await navigator.serviceWorker?.getRegistrations?.() ?? [];
done({ok:true,rows,serviceWorkerRegistrations:controllers.length,
     userAgent:navigator.userAgent,devicePixelRatio:devicePixelRatio});
}catch(e){done({ok:false,error:String(e)});}})();
"""

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_no_go(r6:Path,r8:Path)->dict:
    a=json.loads(r6.read_text(encoding="utf-8"))
    b=json.loads(r8.read_text(encoding="utf-8"))
    if not (a.get("version")=="public-r6-conservative-release-admission-v1" and
            a.get("status")=="NO_GO" and a.get("releaseAuthorized") is False and
            a.get("blockedGateCount")==8):
        raise ValueError("R9 requires genuine R6 NO_GO evidence")
    if not (b.get("version")=="public-r8-static-vendor-redistribution-inventory-v1" and
            b.get("status")=="INVENTORY_PASS_LEGAL_HOLD" and
            b.get("releaseAuthorized") is False and
            b.get("fullVendorFileCount")==40 and
            b.get("loopbackStaticRollbackDryRun",{}).get("loopbackRollbackByteExact") is True):
        raise ValueError("R9 requires unsigned R8 measured inventory evidence")
    return {"r6SHA256":sha(r6),"r8SHA256":sha(r8)}

def snapshot(folder:Path)->dict:
    return {p.relative_to(folder).as_posix():sha(p)
            for p in sorted(folder.rglob("*")) if p.is_file()}

def staged_releases(built:Path,base:Path,canary:Path,recovered:Path):
    # Exact static build preserved; changes exist ONLY in temp canary directory.
    for target in (base,canary,recovered):shutil.copytree(built,target)
    for rel,marker in MARKERS.items():
        p=canary/rel
        original=p.read_bytes()
        p.write_bytes(original+marker)
    base_sha=snapshot(base);canary_sha=snapshot(canary)
    if set(base_sha)!=set(canary_sha):raise ValueError("unexpected staged asset addition")
    differences={k for k in base_sha if base_sha[k]!=canary_sha[k]}
    if differences!=set(MARKERS):
        raise ValueError("canary did not change exactly three known assets")
    if snapshot(recovered)!=base_sha:
        raise ValueError("full tree restoration is not byte-exact")
    return base_sha,canary_sha

class RouteHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,directory=None,**kw):
        super().__init__(*a,directory=str(a[2].current_root),**kw)
    def log_message(self,*args):pass
    def do_GET(self):
        self.directory=str(self.server.current_root)
        super().do_GET()
    def end_headers(self):
        route=urlsplit(self.path).path
        # Explicitly model a legal but unsafe production cache policy, not
        # assert Shin's actual unknown provider headers or HTTP CDN behavior.
        if route in ("/","/index.html"):
            self.send_header("Cache-Control","no-store")
        else:
            self.send_header("Cache-Control","public, max-age=3600")
        self.send_header("X-R9-Simulation","disposable-loopback")
        super().end_headers()

def browser_rows(driver,urls,mode="default",stamp=""):
    result=driver.execute_async_script(BROWSER_SAMPLE,list(urls),mode,stamp)
    if not result.get("ok"):raise RuntimeError("R9 Chrome fetch failed: "+str(result))
    return result

def compare_rows(rows:dict,tree:dict):
    if len(rows["rows"])!=len(ROUTES):raise ValueError("incomplete cache review")
    mismatches=[]
    for entry in rows["rows"]:
        key=urlsplit(entry["route"]).path.lstrip("/")
        expected=tree[key]
        if entry["sha256"]!=expected:
            mismatches.append(entry["route"])
    return mismatches

def run(r6:Path,r8:Path,out:Path):
    if out.exists():raise FileExistsError("R9 evidence destination exists")
    evidence=verify_no_go(r6,r8)
    module=ROOT/"scripts"/"build_shin_static.py"
    spec=importlib.util.spec_from_file_location("r9_public_static_builder",module)
    builder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    if builder.SOURCE.resolve()!=PUBLIC_STATIC.resolve():
        raise ValueError("unexpected changed static builder source")
    with tempfile.TemporaryDirectory(prefix="r9_disposable_public_") as t:
        root=Path(t)
        builder.DESTINATION=root/"actual-static-builder"
        built=builder.build()
        base,canary,recovered=(root/p for p in ("baseline","canary","recovered"))
        baseline_sha,canary_sha=staged_releases(built,base,canary,recovered)
        server=http.server.ThreadingHTTPServer(("127.0.0.1",0),
                                                RouteHandler)
        server.current_root=base
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        browser=chrome_driver()
        results={}
        addr=f"http://127.0.0.1:{server.server_port}/"
        try:
            browser.set_script_timeout(120)
            browser.get(addr+"?r9=baseline")
            baseline=browser_rows(browser,ROUTES,"reload")
            if compare_rows(baseline,baseline_sha):
                raise ValueError("Chrome baseline differs from built static files")
            # Browser cache warm from baseline, do not disable Chrome cache.
            server.current_root=canary
            browser.get(addr+"?r9=canary")
            stale=browser_rows(browser,ROUTES,"default")
            forced=browser_rows(browser,ROUTES,"reload")
            if compare_rows(forced,canary_sha):
                raise ValueError("Chrome forced fresh request is not canary")
            canary_stale=compare_rows(stale,canary_sha)
            stamped_canary=browser_rows(browser,ROUTES,"default",
                                        "canary-"+canary_sha["static/app.js"][:16])
            if compare_rows(stamped_canary,canary_sha):
                raise ValueError("unique canary URLs still served stale content")
            server.current_root=recovered
            browser.get(addr+"?r9=recovered")
            rollback_default=browser_rows(browser,ROUTES,"default")
            rollback_force=browser_rows(browser,ROUTES,"reload")
            if compare_rows(rollback_force,baseline_sha):
                raise ValueError("Chrome forced recovery differs from original")
            stamp="rollback-"+baseline_sha["static/app.js"][:16]
            rollback_stamped=browser_rows(browser,ROUTES,"default",stamp)
            if compare_rows(rollback_stamped,baseline_sha):
                raise ValueError("new rollback build fingerprint did not restore bytes")
            restored_stale=compare_rows(rollback_default,baseline_sha)
            if not all(len(record["rows"])==4 for record in
                       (baseline,stale,forced,stamped_canary,rollback_default,
                        rollback_force,rollback_stamped)):
                raise ValueError("missing Chrome network sample")
            if any(item["serviceWorkerRegistrations"] for item in
                   (baseline,forced,rollback_force)):
                raise ValueError("unexpected registered Public service worker")
            results={
                "ChromeVersion":browser.capabilities.get("browserVersion"),
                "ChromeDevicePixelRatio":baseline["devicePixelRatio"],
                "baselineByteExact":True,
                "canaryFreshByteExact":True,
                "recoveryFreshByteExact":True,
                "canaryBuildFingerprintByteExact":True,
                "recoveryBuildFingerprintByteExact":True,
                "canaryDefaultCacheMismatches":canary_stale,
                "recoveryDefaultCacheMismatches":restored_stale,
                "testedStaticRoutes":list(ROUTES),
                "serviceWorkerRegistrationsDetected":0,
                "stagingOnly":True,"productionCacheHeadersVerified":False,
                "browserChromeOnly":True,"iphoneSafariDeviceVerified":False,
            }
        finally:
            browser.quit()
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
    report={
        "version":VERSION,**evidence,
        "frozenBaselineIndexSHA256":baseline_sha["index.html"],
        "frozenBaselineAppSHA256":baseline_sha["static/app.js"],
        "frozenBaselineStylesSHA256":baseline_sha["static/styles.css"],
        "frozenBaselineResvgWasmSHA256":baseline_sha["static/vendor/resvg-wasm/index_bg.wasm"],
        "baselineFullFileCount":len(baseline_sha),
        "disposableTreeRestoredByteExact":True,
        "chromeLoopback":results,
        "noServiceWorkerFoundInCurrentStaticSource":True,
        "currentStylesheetUrlBuildFingerprinted":False,
        "currentAppJsUrlFingerprintChangesEachBuild":False,
        "hypotheticalCachingRule":"static max-age=3600 / HTML no-store (NOT actual provider headers)",
        "deploymentProviderLiveCacheVerified":False,
        "fullProductionRollbackSigned":False,"iphoneSafariDprSigned":False,
        "humanGoldenSigned":False,"stage8OriginalBudgetSigned":False,
        "semanticOwnerSigned":False,"resvgMplLegalSigned":False,
        "releaseAuthorized":False,"mergeOrDeployPerformed":False,
        "status":"CACHE_SIMULATION_VERIFIED_PRODUCTION_NO_GO",
    }
    out.mkdir(parents=True)
    (out/"public_r9_cache_rollback.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--r6",required=True,type=Path)
    p.add_argument("--r8",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    data=run(a.r6,a.r8,a.out)
    print("R9_CHROME_STATIC_CACHE_SIM_PASS",data["baselineFullFileCount"],
          "files; canary stale",
          len(data["chromeLoopback"]["canaryDefaultCacheMismatches"]),
          "rollback stale",
          len(data["chromeLoopback"]["recoveryDefaultCacheMismatches"]),
          "PRODUCTION_NO_GO",flush=True)

if __name__=="__main__":main()
