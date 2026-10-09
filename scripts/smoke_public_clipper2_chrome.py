"""Real Chrome MinimalizerPublic Clipper2-WASM ON/OFF isolated conversion parity."""
from __future__ import annotations
import functools
import json
import re
from pathlib import Path
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import build_shin_static as builder

ROOT=Path(__file__).resolve().parents[1]
DRIVER=ROOT/"scripts/resvg_chrome_cdp.mjs"
INLINE=r"""
<script>
window.addEventListener("load",async()=>{
 const result=document.createElement("pre");
 result.id="clipper2-route-result"; document.body.appendChild(result);
 try {
  window.MinimalizerBrowserSubject=null; // disposable smoke copy ONLY
  const canvas=document.createElement("canvas");
  canvas.width=canvas.height=64;
  const ctx=canvas.getContext("2d");
  ctx.fillStyle="#e8e4df";ctx.fillRect(0,0,64,64);
  ctx.fillStyle="#203355";ctx.fillRect(7,4,47,55);
  ctx.fillStyle="#c82266";ctx.fillRect(14,9,9,39);
  ctx.fillStyle="#f7b020";ctx.fillRect(22,35,31,10);
  const blob=await new Promise(r=>canvas.toBlob(r,"image/png"));
  const file=new File([blob],"clipper2-smoke.png",{type:"image/png"});
  const {response}=await window.MinimalizerComputeRoute.minimalize(file);
  const bytes=await response.arrayBuffer();
  const dig=await crypto.subtle.digest("SHA-256",bytes);
  const sha=[...new Uint8Array(dig)].map(x=>x.toString(16).padStart(2,"0")).join("");
  result.textContent="CLIPPER2_ROUTE_RESULT="+JSON.stringify({
    http:response.status,sha,bytes:bytes.byteLength,
    shapes:response.headers.get("X-Minimalizer-Shape-Count"),
    audit:response.headers.get("X-Minimalizer-Public-Clipper2-Audit"),
    exact:response.headers.get("X-Minimalizer-Public-Clipper2-Exact-Shapes"),
    rejected:response.headers.get("X-Minimalizer-Public-Clipper2-Rejected-Shapes"),
    diff:response.headers.get("X-Minimalizer-Public-Clipper2-Different-Pixels"),
    polygon:response.headers.get("X-Minimalizer-Public-Polygon-Audit")
  });
 } catch(e) {
  result.textContent="CLIPPER2_ROUTE_FAILURE="+String(e);
 }
});
</script>
"""
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*_args):pass

def chrome(url):
    p=subprocess.run(["node",str(DRIVER),url,"#clipper2-route-result"],
      cwd=ROOT,capture_output=True,text=True,timeout=100)
    if p.returncode:
        raise RuntimeError(p.stdout[-1000:]+p.stderr[-1000:])
    match=re.search(r"CLIPPER2_ROUTE_RESULT=(\{[^\r\n]*\})",p.stdout)
    if not match:raise AssertionError("Missing Chrome payload: "+p.stdout[-500:])
    return json.loads(match.group(1))

def main():
    with tempfile.TemporaryDirectory(prefix="minimalizer-clipper2-public-") as tmp:
        root=Path(tmp)
        previous=builder.DESTINATION
        try:
            builder.DESTINATION=root/"public"
            out=builder.build()
        finally:
            builder.DESTINATION=previous
        page=out/"index.html"
        source=page.read_text(encoding="utf-8")
        assert "</body>" in source
        page.write_text(source.replace("</body>",INLINE+"</body>"),encoding="utf-8")
        server=ThreadingHTTPServer(("127.0.0.1",0),
            functools.partial(QuietHandler,directory=str(root)))
        t=threading.Thread(target=server.serve_forever,daemon=True)
        t.start()
        try:
            url=f"http://127.0.0.1:{server.server_port}/public/index.html"
            off=chrome(url)
            on=chrome(url+"?publicClipper2Research=1")
        finally:
            server.shutdown();server.server_close();t.join(timeout=3)
        assert off["http"]==on["http"]==200
        assert off["sha"]==on["sha"] and off["bytes"]==on["bytes"]
        assert off["shapes"]==on["shapes"] and int(on["shapes"])>0
        assert off["audit"]=="disabled"
        assert on["audit"] in ("ok","truncated")
        assert int(on["exact"])+int(on["rejected"])>0
        assert off["polygon"]==on["polygon"]=="ok"
        print("Chrome Public Clipper2 route ON/OFF PASS")
        print(json.dumps({"off":off,"on":on},ensure_ascii=False))

if __name__=="__main__":main()
