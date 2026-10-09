"""Real Chrome Public VTracer WASM audit ON/OFF using isolated built page."""
from __future__ import annotations
import functools
import json
import re
import subprocess
import tempfile
import threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import build_shin_static as builder

ROOT=Path(__file__).resolve().parents[1]
DRIVER=ROOT/"scripts/resvg_chrome_cdp.mjs"
INLINE=r"""
<script>
window.addEventListener("load",async()=>{
 const pre=document.createElement("pre");
 pre.id="vtracer-route-result";document.body.appendChild(pre);
 try{
  window.MinimalizerBrowserSubject=null; // isolated smoke only
  const canvas=document.createElement("canvas");
  canvas.width=canvas.height=64;
  const ctx=canvas.getContext("2d");
  ctx.fillStyle="#e8e4df";ctx.fillRect(0,0,64,64);
  ctx.fillStyle="#203355";ctx.fillRect(7,4,47,55);
  ctx.fillStyle="#c82266";ctx.fillRect(14,9,9,39);
  ctx.fillStyle="#f7b020";ctx.fillRect(22,35,31,10);
  const image=await new Promise(r=>canvas.toBlob(r,"image/png"));
  const {response}=await window.MinimalizerComputeRoute.minimalize(
    new File([image],"sample.png",{type:"image/png"}));
  const raw=await response.arrayBuffer();
  const hash=await crypto.subtle.digest("SHA-256",raw);
  const sha=[...new Uint8Array(hash)]
    .map(x=>x.toString(16).padStart(2,"0")).join("");
  pre.textContent="VTRACER_ROUTE_RESULT="+JSON.stringify({
    http:response.status,sha,bytes:raw.byteLength,
    shapes:response.headers.get("X-Minimalizer-Shape-Count"),
    audit:response.headers.get("X-Minimalizer-Public-VTracer-Audit"),
    exact:response.headers.get("X-Minimalizer-Public-VTracer-Exact"),
    changed:response.headers.get("X-Minimalizer-Public-VTracer-Changed-Pixels"),
    polygon:response.headers.get("X-Minimalizer-Public-Polygon-Audit")
  });
 }catch(e){pre.textContent="VTRACER_ROUTE_FAILURE="+String(e);}
});
</script>
"""
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_args):pass

def chrome(url):
    proc=subprocess.run(["node",str(DRIVER),url,"#vtracer-route-result"],
      cwd=ROOT,capture_output=True,text=True,timeout=100)
    if proc.returncode:
        raise RuntimeError(proc.stdout[-900:]+proc.stderr[-900:])
    match=re.search(r"VTRACER_ROUTE_RESULT=(\{[^\r\n]*\})",proc.stdout)
    if not match:raise AssertionError("Missing Chrome data: "+proc.stdout[-600:])
    return json.loads(match.group(1))

def main():
    with tempfile.TemporaryDirectory(prefix="minimalizer-vtracer-public-") as td:
        root=Path(td)
        orig=builder.DESTINATION
        try:
            builder.DESTINATION=root/"public"
            out=builder.build()
        finally:
            builder.DESTINATION=orig
        page=out/"index.html"
        code=page.read_text(encoding="utf-8")
        assert "</body>" in code
        page.write_text(code.replace("</body>",INLINE+"</body>"),encoding="utf-8")
        server=ThreadingHTTPServer(("127.0.0.1",0),
            functools.partial(Quiet,directory=str(root)))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            url=f"http://127.0.0.1:{server.server_port}/public/index.html"
            off=chrome(url)
            on=chrome(url+"?publicVTracerResearch=1")
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)
        assert off["http"]==on["http"]==200
        assert off["sha"]==on["sha"] and off["bytes"]==on["bytes"]
        assert off["shapes"]==on["shapes"] and int(on["shapes"])>0
        assert off["audit"]=="disabled"
        assert on["audit"] in ("exact","pixel-mismatch")
        assert int(on["changed"])>=0
        assert off["polygon"]==on["polygon"]=="ok"
        print("Chrome Public VTracer route ON/OFF PASS")
        print(json.dumps({"off":off,"on":on},ensure_ascii=False))
if __name__=="__main__":main()
