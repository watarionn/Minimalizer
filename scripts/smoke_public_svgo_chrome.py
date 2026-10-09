"""Real built MinimalizerPublic Chrome SVGO flag parity smoke (no deployment).

Requires locally installed Chrome, Python standard library only. Uses an isolated
temporary build, private source-fixture canvas, no original user images.
"""
from __future__ import annotations

import functools
import html
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import build_shin_static as builder

CHROME = Path(os.environ.get(
    "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
))
INLINE = r"""
<script>
window.addEventListener("load", async () => {
 const output = document.createElement("pre");
 output.id = "svgo-smoke-result";
 document.body.appendChild(output);
 try {
  // Only in an isolated copy of the built Public page.
  window.MinimalizerBrowserSubject = null;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 64;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle="#e8e4df"; ctx.fillRect(0,0,64,64);
  ctx.fillStyle="#203355"; ctx.fillRect(7,4,47,55);
  ctx.fillStyle="#c82266"; ctx.fillRect(14,9,9,39);
  ctx.fillStyle="#f7b020"; ctx.fillRect(22,35,31,10);
  const blob = await new Promise(r => canvas.toBlob(r,"image/png"));
  const file = new File([blob],"svgo-smoke.png",{type:"image/png"});
  const {response} = await window.MinimalizerComputeRoute.minimalize(file);
  const bytes = await response.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256",bytes);
  const sha = [...new Uint8Array(digest)]
    .map(x=>x.toString(16).padStart(2,"0")).join("");
  output.textContent="SVGO_ROUTE_RESULT="+JSON.stringify({
   http: response.status, sha, bytes: bytes.byteLength,
   shapes: response.headers.get("X-Minimalizer-Shape-Count"),
   audit: response.headers.get("X-Minimalizer-Public-SVGO-Audit"),
   exact: response.headers.get("X-Minimalizer-Public-SVGO-Exact"),
   saved: response.headers.get("X-Minimalizer-Public-SVGO-Saved-Bytes"),
   polygon: response.headers.get("X-Minimalizer-Public-Polygon-Audit")
  });
 } catch(e) { output.textContent="SVGO_ROUTE_FAILURE="+String(e); }
});
</script>
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def run_chrome(url: str, profile: Path) -> dict:
    command = [
        str(CHROME), "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-extensions", "--no-first-run",
        "--disable-background-networking",
        "--user-data-dir=" + str(profile),
        "--virtual-time-budget=30000", "--dump-dom", url,
    ]
    # Chrome --dump-dom uses virtual time and may finish before an async
    # canvas-to-PNG promise settles on cold profile start. Retry ONLY the
    # disposable browser smoke, never alter output acceptance criteria.
    for attempt in range(4):
        process = subprocess.run(command, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=90)
        if process.returncode:
            raise RuntimeError("Chrome failed: " + process.stderr[-400:])
        match = re.search(
            r'<pre id="svgo-smoke-result">SVGO_ROUTE_RESULT=(.*?)</pre>',
            process.stdout, flags=re.DOTALL)
        if match:
            if attempt:
                print(f"Chrome smoke cold-start retry: {attempt}")
            return json.loads(html.unescape(match.group(1)))
    raise AssertionError("Chrome smoke did not finish after 4 tries: " +
                         process.stdout[-800:])


def main() -> None:
    if not CHROME.is_file():
        raise RuntimeError("Chrome not installed: set CHROME_PATH")
    with tempfile.TemporaryDirectory(prefix="minimalizer-svgo-chrome-") as temp:
        root = Path(temp)
        old_destination = builder.DESTINATION
        try:
            builder.DESTINATION = root / "public"
            out = builder.build()
        finally:
            builder.DESTINATION = old_destination
        page = out / "index.html"
        content = page.read_text(encoding="utf-8")
        assert "</body>" in content
        page.write_text(content.replace("</body>", INLINE + "</body>"),
                        encoding="utf-8")
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            functools.partial(QuietHandler, directory=str(root)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}/public/index.html"
            off = run_chrome(base, root / "chrome-off")
            on = run_chrome(base + "?publicSvgoResearch=1", root / "chrome-on")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        assert off["http"] == on["http"] == 200
        assert off["audit"] == "disabled"
        assert on["audit"] in {"ok", "truncated"}
        assert on["exact"] == "1"
        assert int(on["saved"]) > 0
        assert off["sha"] == on["sha"] and off["bytes"] == on["bytes"]
        assert off["shapes"] == on["shapes"]
        assert off["polygon"] == on["polygon"] == "ok"
        print("Chrome Public route ON/OFF PASS")
        print(json.dumps({"off": off, "on": on}, ensure_ascii=False))


if __name__ == "__main__":
    main()
