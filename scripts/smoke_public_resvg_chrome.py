"""Real Chrome Public route resvg-wasm ON/OFF SHA parity, disposable static build."""
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
window.addEventListener("load", async () => {
 const result=document.createElement("pre");result.id="resvg-route-result";
 document.body.appendChild(result);
 try {
  window.MinimalizerBrowserSubject=null; // isolated smoke ONLY
  const canvas=document.createElement("canvas");
  canvas.width=canvas.height=64;
  const ctx=canvas.getContext("2d");
  ctx.fillStyle="#e8e4df";ctx.fillRect(0,0,64,64);
  ctx.fillStyle="#203355";ctx.fillRect(7,4,47,55);
  ctx.fillStyle="#c82266";ctx.fillRect(14,9,9,39);
  ctx.fillStyle="#f7b020";ctx.fillRect(22,35,31,10);
  const blob=await new Promise(r=>canvas.toBlob(r,"image/png"));
  const {response}=await window.MinimalizerComputeRoute.minimalize(
    new File([blob],"smoke.png",{type:"image/png"}));
  const bytes=await response.arrayBuffer();
  const hash=await crypto.subtle.digest("SHA-256",bytes);
  const sha=[...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,"0")).join("");
  result.textContent="RESVG_ROUTE_RESULT="+JSON.stringify({
   status:response.status,sha,bytes:bytes.byteLength,
   shapes:response.headers.get("X-Minimalizer-Shape-Count"),
   audit:response.headers.get("X-Minimalizer-Public-RESVG-Audit"),
   changed:response.headers.get("X-Minimalizer-Public-RESVG-Different-Pixels"),
   exact:response.headers.get("X-Minimalizer-Public-RESVG-Exact"),
   polygon:response.headers.get("X-Minimalizer-Public-Polygon-Audit")
  });
 }catch(e){result.textContent="RESVG_ROUTE_FAILURE="+String(e);}
});
</script>
"""
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_args):pass

def chrome(url):
    proc=subprocess.run(["node",str(DRIVER),url,"#resvg-route-result"],
                        cwd=ROOT,capture_output=True,text=True,timeout=90)
    if proc.returncode:
        raise RuntimeError(proc.stdout[-1000:]+proc.stderr[-1000:])
    match=re.search(r"RESVG_ROUTE_RESULT=(\{[^\r\n]*\})",proc.stdout)
    if not match:raise AssertionError("Missing smoke data: "+proc.stdout[-600:])
    return json.loads(match.group(1))

def main():
    with tempfile.TemporaryDirectory(prefix="minimalizer-resvg-public-") as td:
        root=Path(td)
        previous=builder.DESTINATION
        try:
            builder.DESTINATION=root/"public"
            out=builder.build()
        finally:
            builder.DESTINATION=previous
        page=out/"index.html"
        body=page.read_text(encoding="utf-8")
        assert "</body>" in body
        page.write_text(body.replace("</body>",INLINE+"</body>"),encoding="utf-8")
        server=ThreadingHTTPServer(("127.0.0.1",0),
          functools.partial(Quiet,directory=str(root)))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            url=f"http://127.0.0.1:{server.server_port}/public/index.html"
            off=chrome(url)
            on=chrome(url+"?publicResvgResearch=1")
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)
        assert off["status"]==on["status"]==200
        assert off["shapes"]==on["shapes"] and int(on["shapes"])>0
        assert off["sha"]==on["sha"] and off["bytes"]==on["bytes"]
        assert off["audit"]=="disabled"
        assert on["audit"] in ("ok","truncated")
        assert int(on["changed"])>=0
        assert off["polygon"]==on["polygon"]=="ok"
        print("Chrome Public resvg ON/OFF PASS")
        print(json.dumps({"off":off,"on":on},ensure_ascii=False))

if __name__=="__main__":main()
