"""Real Chrome smoke for the isolated Local 5-Engine Lab, no live service mutation.

An ephemeral 127.0.0.1 server serves ONLY the checked-out Local PWA and
existing /static assets; a throwaway Chrome profile exercises real VTracer WASM
and pinned ImageTracerJS on a synthetic image. Never sends owner images.
"""
from __future__ import annotations

import json
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "resvg_chrome_cdp.mjs"

PROBE = r"""
<script>
window.addEventListener("load", async () => {
  const out = document.createElement("pre");
  out.id = "five-engine-smoke-result";
  document.body.append(out);
  const pause = ms => new Promise(done => setTimeout(done, ms));
  try {
    const input = document.querySelector("#image-file");
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#e3e8ee"; ctx.fillRect(0,0,64,64);
    ctx.fillStyle = "#183e65"; ctx.fillRect(7,4,46,53);
    ctx.fillStyle = "#e16c28"; ctx.fillRect(22,14,25,32);
    const blob = await new Promise(resolve => c.toBlob(resolve, "image/png"));
    if(!blob) throw new Error("no test PNG");
    const files = new DataTransfer();
    files.items.add(new File([blob], "synthetic-local.png", {type:"image/png"}));
    input.files = files.files;
    input.dispatchEvent(new Event("change", {bubbles:true}));
    for(let i=0;i<120 && document.querySelector("#run-local").disabled;i++) await pause(100);
    if(document.querySelector("#run-local").disabled) throw new Error("source load failed");
    document.querySelector("#run-local").click();
    for(let i=0;i<500;i++) {
      if(!document.querySelector("#run-local").disabled) break;
      await pause(100);
    }
    const v = document.querySelector('[data-slot="vtracer"] img');
    const j = document.querySelector('[data-slot="imagetracer"] img');
    const status = document.querySelector("#run-status").textContent;
    const res = {vtracer:!!v,imagetracer:!!j,
      status,options:document.querySelector("#select-candidate").options.length,
      source:document.querySelector("#source-status").textContent};
    out.textContent = "VTRACER_ROUTE_RESULT=" + JSON.stringify(res);
  }catch(e){
    out.textContent = "VTRACER_ROUTE_FAILURE=" + String(e);
  }
});
</script>
"""

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_args): pass

    def translate_path(self, path):
        req = urlsplit(path).path
        if req.startswith("/local-static/"):
            base = (ROOT / "local_worker/frontend").resolve()
            rel = req[len("/local-static/"):]
        elif req.startswith("/static/"):
            base = (ROOT / "web/static").resolve()
            rel = req[len("/static/"):]
        elif req == "/manifest.webmanifest":
            return str(ROOT / "local_worker/frontend/manifest.webmanifest")
        else:
            return str(ROOT / "not-found")
        target = (base / rel).resolve()
        return str(target) if target.is_relative_to(base) else str(ROOT / "not-found")

    def do_GET(self):
        if urlsplit(self.path).path == "/local-static/five-engine-lab.html":
            html = (ROOT / "local_worker/frontend/five-engine-lab.html").read_text(encoding="utf-8")
            assert "</body>" in html
            payload = html.replace("</body>", PROBE + "</body>").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
        else: super().do_GET()

def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/local-static/five-engine-lab.html"
        proc = subprocess.run(["node", str(DRIVER), url, "#five-engine-smoke-result"],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=100)
        if proc.returncode:
            raise RuntimeError((proc.stdout + proc.stderr)[-1800:])
        marker = "VTRACER_ROUTE_RESULT="
        if marker not in proc.stdout:
            raise RuntimeError("Browser smoke did not report result: " + proc.stdout[-1200:])
        value = json.loads(proc.stdout.split(marker,1)[1].strip().splitlines()[0])
        print(json.dumps(value,ensure_ascii=False))
        assert value["vtracer"] and value["imagetracer"], "One or both actual browser engines failed"
        assert value["options"] >= 3, "Two candidates were not registered"
        print("LOCAL_FIVE_ENGINE_CHROME_PASS")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

if __name__ == "__main__":
    main()
