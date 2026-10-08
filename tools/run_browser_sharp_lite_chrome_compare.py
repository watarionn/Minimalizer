"""Independent real-Chrome BrowserFallback Lite / Sharp / Exact image and UI benchmark."""
from __future__ import annotations
import argparse
import base64
import json
import shutil
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

if __package__:
    from .minimalizer_browser_profile_lifecycle import (
        create_browser_profile, cleanup_browser_profile,
    )
else:
    from minimalizer_browser_profile_lifecycle import (
        create_browser_profile, cleanup_browser_profile,
    )

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def translate_path(self, path):
        if path.split('?')[0] in ('/', '/index.html'):
            return str(Path(self.directory) / 'static' / 'index.html')
        return super().translate_path(path)

def compare(root: Path, source: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, output / "source.png")
    handler = partial(QuietHandler, directory=str(root / "web"))
    http = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    profile = create_browser_profile()
    options = webdriver.ChromeOptions()
    for option in ("--headless=new", "--no-sandbox", "--disable-gpu",
                   "--disable-extensions", "--disable-dev-shm-usage",
                   "--window-size=900,900",
                   "--user-data-dir=" + str(profile)):
        options.add_argument(option)
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        driver.get(f"http://127.0.0.1:{http.server_port}/index.html?browserFallback=force&browserFallbackQuality=sharp")
        WebDriverWait(driver, 45).until(
            lambda d: d.execute_script(
                "return !!(window.MinimalizerBrowserFallback && "
                "window.MinimalizerCanonicalContour && "
                "window.MinimalizerOpenCvRaster)"))
        print("Browser runtime loaded; browser =", driver.capabilities.get("browserVersion"), flush=True)
        ui=driver.execute_script("return {profile:browserFallbackQualityProfile(), structural:browserFallbackStructuralMode(), canonical:browserFallbackCanonicalContourLite(), forced:browserFallbackForced()}")
        print("UI_SHARP_ROUTE",ui,flush=True)
        assert ui == {"profile":"sharp","structural":"l0-lite-jacobi","canonical":True,"forced":True},ui
        b64 = base64.b64encode(source.read_bytes()).decode("ascii")
        driver.execute_script("""
const raw=atob(arguments[0]);
const binary=new Uint8Array(raw.length);
for(let i=0;i<raw.length;i++) binary[i]=raw.charCodeAt(i);
window.__geoSourceFile=new File([binary], 'source.png', {type:'image/png'});
window.__geoRuns={};
window.__geoRun=async function(name,opts){
 window.__geoRuns[name]={status:'running'};
 try{
  const result=await window.MinimalizerBrowserFallback.minimalizeFile(window.__geoSourceFile,opts);
  const blob=await result.response.blob();
  const data=await new Promise((resolve,reject)=>{
    const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=()=>reject(r.error);r.readAsDataURL(blob);
  });
  window.__geoRuns[name]={
    status:'ok',headers:Object.fromEntries(result.response.headers.entries()),
    metadata:result.metadata, png:data.substring(data.indexOf(',')+1)
  };
 }catch(e){
  window.__geoRuns[name]={status:'error',error:String(e),stack:String(e.stack)};
 }
};""", b64)
        cases = {
            "lite": {"structuralMode": "l0-lite-jacobi"},
            "sharp": {"structuralMode": "l0-lite-jacobi", "canonicalContourLite": True},
            "exact": {"structuralMode": "spectral-exact"},
        }
        shared = {"analysisMaxSide":400,"workMaxSide":400,"maxShapes":40,"slicIterations":10,"paletteTarget":8}
        all_results = {}
        for name, spec in cases.items():
            print("START", name, flush=True)
            started = time.monotonic()
            driver.execute_script("window.__geoRun(arguments[0],arguments[1])", name, {**shared,**spec})
            WebDriverWait(driver, 180, poll_frequency=1).until(
                lambda d: d.execute_script(
                    "return window.__geoRuns[arguments[0]]?.status !== 'running'",name))
            payload = driver.execute_script(
                "const r=window.__geoRuns[arguments[0]];delete window.__geoRuns[arguments[0]];return r;", name)
            if payload.get("status") != "ok":
                print("ERROR", name, payload, flush=True)
                raise RuntimeError(str(payload))
            (output / f"{name}.png").write_bytes(base64.b64decode(payload.pop("png")))
            payload["wallSeconds"]=round(time.monotonic()-started,2)
            all_results[name]=payload
            metric=payload["metadata"]
            print("DONE",name,"seconds",payload["wallSeconds"],
                  "shapes",metric.get("shapeCount"),"vertices",metric.get("vertexCount"),
                  "contour",metric.get("contourMethod"),
                  "simplifier",metric.get("contourSimplifier"),
                  "subject",metric.get("subjectGuided"),
                  "iou",metric.get("contourMinRegionIoU"),flush=True)
        # Call the real app.js requestBrowserFallback route as the final integration gate.
        # The query parameter on this page forces BrowserFallback and enables Sharp.
        driver.set_script_timeout(120)
        ui = driver.execute_async_script("""
const done=arguments[arguments.length-1];
try {
  state.file=window.__geoSourceFile;
  requestBrowserFallback().then(async(response)=>{
    const headers=Object.fromEntries(response.headers.entries());
    const blob=await response.blob();
    const reader=new FileReader();
    reader.onload=()=>done({status:'ok',headers,png:reader.result.split(',')[1]});
    reader.onerror=()=>done({status:'error',error:'FileReader failed'});
    reader.readAsDataURL(blob);
  }).catch(err=>done({status:'error',error:String(err)}));
} catch(e) { done({status:'error',error:String(e)}); }
""")
        if ui.get("status") != "ok":
            raise RuntimeError("Actual app.js Sharp request failed: " + str(ui))
        ui_png=base64.b64decode(ui.pop("png"))
        ui_exact_match=ui_png == (output / "sharp.png").read_bytes()
        ui_headers=ui["headers"]
        if ui_headers.get("x-minimalizer-browser-quality-profile") != "sharp":
            raise RuntimeError("App route did not select Sharp: " + str(ui_headers))
        if ui_headers.get("x-minimalizer-contour-method") != "canonical-shared-chain":
            raise RuntimeError("App route was not shared-boundary: " + str(ui_headers))
        if ui_headers.get("x-minimalizer-raster-method") != "opencv-fillpoly-2x":
            raise RuntimeError("App route raster mismatch: " + str(ui_headers))
        if not ui_exact_match:
            raise RuntimeError("App route Sharp PNG differs from direct Sharp")
        print("UI_REQUEST_BROWSER_FALLBACK_PASS", ui_exact_match,flush=True)
        all_results["uiVerification"] = {
            "profile": "sharp",
            "forcedBrowserRoute": True,
            "pngPixelAndByteExactToDirectSharp": ui_exact_match,
            "headers": ui_headers,
        }
        with (output / "metrics.json").open("w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print("OUTPUT",output,flush=True)
        return all_results
    finally:
        try:
            if driver is not None:
                driver.quit()
        finally:
            try:
                http.shutdown()
                http.server_close()
            finally:
                cleanup_browser_profile(profile)

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    compare(a.root.resolve(),a.source.resolve(),a.out.resolve())
