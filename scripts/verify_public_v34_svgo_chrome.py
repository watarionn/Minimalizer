"""Chrome Golden gate for a disposable pinned-SVGO v34 research candidate.

Verifies frozen manifests before writing anything. Reads archived v34 hybrid SVG,
v34 Chrome PNG and v32 Golden PNG. Writes only into a fresh --out directory.
No production, Local Worker, or source-owner mutation.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image

CASES = ("Kyoko", "Noel", "Ririka")
SIZE = (340, 340)
NODE = Path(__file__).resolve().parent / "public_v34_svgo_candidate.mjs"
JS = r"""
const svg=arguments[0],done=arguments[arguments.length-1];
const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
const img=new Image();
img.onload=()=>{try{
 const canvas=document.createElement('canvas');canvas.width=340;canvas.height=340;
 const ctx=canvas.getContext('2d',{willReadFrequently:true});
 if(!ctx)throw Error('missing canvas');ctx.drawImage(img,0,0);
 const data=ctx.getImageData(0,0,340,340).data;
 let str='';for(let k=0;k<data.length;k+=16384)
   str+=String.fromCharCode(...data.slice(k,Math.min(k+16384,data.length)));
 done({ok:true,rgba:btoa(str)});
 }catch(err){done({ok:false,error:String(err)});}finally{URL.revokeObjectURL(url);}};
img.onerror=()=>{URL.revokeObjectURL(url);done({ok:false,error:'SVG decode failed'});};
img.src=url;
"""

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_sha(folder: Path, manifest_name: str, path: Path) -> str:
    manifest = json.loads((folder / manifest_name).read_text(encoding="utf-8"))
    expected = {item["name"]: item["sha256"] for item in manifest["files"]}
    if path.name not in expected or sha(path) != expected[path.name]:
        raise ValueError(f"frozen Golden SHA mismatch: {path}")
    return expected[path.name]

def render_rgba(driver, svg: str) -> bytes:
    response = driver.execute_async_script(JS, svg)
    if not response.get("ok"):
        raise RuntimeError(f"Chrome SVG failure: {response}")
    rgba = base64.b64decode(response["rgba"], validate=True)
    if len(rgba) != SIZE[0] * SIZE[1] * 4:
        raise RuntimeError("incorrect Chrome RGBA dimensions")
    return rgba

def mismatched_pixels(a: bytes, b: bytes) -> int:
    if len(a) != len(b) or len(a) % 4:
        raise ValueError("invalid RGBA comparison")
    return sum(a[i:i+4] != b[i:i+4] for i in range(0, len(a), 4))

def chrome_driver():
    from selenium import webdriver
    opts = webdriver.ChromeOptions()
    for arg in ("--headless=new", "--no-sandbox", "--disable-gpu",
                "--disable-extensions", "--window-size=900,900"):
        opts.add_argument(arg)
    driver = webdriver.Chrome(options=opts)
    driver.set_script_timeout(60)
    driver.get("data:text/html,<html><body>MinimalizerPublic independent v34 gate</body></html>")
    return driver

def run(v34: Path, v32: Path, out: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"no overwrite: {out}")
    for case in CASES:
        check_sha(v34, "v34_evidence_manifest.json", v34 / f"{case}_local_safe.svg")
        check_sha(v34, "v34_evidence_manifest.json", v34 / f"{case}_local_safe_chrome.png")
        check_sha(v32, "v32_evidence_manifest.json", v32 / f"{case}_connected_fine.png")
    out.mkdir(parents=True)
    rows = []
    driver = chrome_driver()
    try:
        browser_version = driver.capabilities.get("browserVersion", "unknown")
        for case in CASES:
            source = v34 / f"{case}_local_safe.svg"
            candidate = out / f"{case}_svgo_candidate.svg"
            proc = subprocess.run(["node", str(NODE), str(source), str(candidate)],
                                  text=True, capture_output=True, check=True, timeout=90)
            info = json.loads(proc.stdout)
            frozen = Image.open(v32 / f"{case}_connected_fine.png").convert("RGBA")
            if frozen.size != SIZE:
                raise ValueError("frozen Golden has wrong dimensions")
            baseline = frozen.tobytes()
            original = render_rgba(driver, source.read_text(encoding="utf-8"))
            prior_chrome = Image.open(v34 / f"{case}_local_safe_chrome.png").convert("RGBA").tobytes()
            optimized = render_rgba(driver, candidate.read_text(encoding="utf-8"))
            d_base = mismatched_pixels(original, baseline)
            d_prior = mismatched_pixels(original, prior_chrome)
            d_candidate = mismatched_pixels(optimized, baseline)
            d_original = mismatched_pixels(optimized, original)
            exact = (d_base == d_prior == d_candidate == d_original == 0)
            # Deliberate unsourced painting: negative control MUST be detected.
            bad = candidate.read_text(encoding="utf-8").replace(
                "</svg>", '<rect x="0" y="0" width="340" height="340" fill="#000"/></svg>')
            d_negative = mismatched_pixels(render_rgba(driver, bad), baseline)
            if d_negative == 0:
                raise AssertionError("negative-control injected painting undetected")
            rows.append({"case": case, **info,
                         "originalVsV32DifferentPixels": d_base,
                         "originalVsV34ChromeDifferentPixels": d_prior,
                         "candidateVsV32DifferentPixels": d_candidate,
                         "candidateVsV34DifferentPixels": d_original,
                         "negativeControlDifferentPixels": d_negative,
                         "exactRgbaParity": exact,
                         "losslessBytesSaved": max(0, info["savedBytes"]) if exact else 0,
                         "promoted": False})
            print(f"{case}: exact={exact} bytes={info['originalBytes']} -> {info['candidateBytes']} negative={d_negative}", flush=True)
    finally:
        driver.quit()
    result = {"version": "public-v34-svgo-gate-v1",
              "browser": "Chrome", "chromeVersion": browser_version,
              "cases": rows, "allGoldenExact": len(rows) == len(CASES) and all(x["exactRgbaParity"] for x in rows),
              "negativeControlsPassed": len(rows) == len(CASES) and all(x["negativeControlDifferentPixels"] > 0 for x in rows),
              "productGoldenApproved": False, "semanticSourceOwnershipApproved": False,
              "geometrySmoothed": False, "productionPromoted": False, "localMinimalizerTouched": False}
    (out / "public_v34_svgo_gate.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v34", type=Path, required=True)
    parser.add_argument("--v32", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.v34, args.v32, args.out)
    if not report["allGoldenExact"] or not report["negativeControlsPassed"]:
        raise SystemExit("HOLD: candidate mismatch or negative controls failed")
    print("CHROME_GOLDEN_SERIALIZATION_GATE_PASS / PRODUCT_QUALITY_HOLD", flush=True)

if __name__ == "__main__":
    main()
