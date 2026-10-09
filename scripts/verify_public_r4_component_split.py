"""R4 source-grounded component isolation for Chrome vs independent resvg at DPR 1/2.

The only two permitted source components are an already-present frozen PNG facet
and the original SVG path layer. Both extracted from SHA-verified original v34
hybrid SVG; never displayed as reconstructed character output.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from PIL import Image
from verify_public_v34_svgo_chrome import CASES,check_sha,chrome_driver,render_rgba,sha
from verify_public_r2_chrome import render_2x,PATH_RE
from verify_public_r4_cross_engine import compare_rgba,rgba_image,RESVG

def split_source(source):
    matches=list(PATH_RE.finditer(source))
    if not matches or source[matches[-1].end():]!="</svg>":
        raise ValueError("unsupported frozen SVG source path structure")
    prefix=source[:matches[0].start()]
    image=re.search(r'<image [^>]+/>$',prefix)
    if image is None or prefix.count("<image ")!=1:
        raise ValueError("non-canonical source raster")
    if len(matches)!=source.count("<path fill="):
        raise ValueError("unparsed source path")
    return {
        "facet":prefix+"</svg>",
        "paths":prefix[:image.start()]+source[matches[0].start():]
    }

def render_resvg(source_path,folder,name,component,size):
    output=folder/f"{name}_{component}_resvg_{size}.png"
    subprocess.run(["node",str(RESVG),str(source_path),str(output),str(size),component],
                   text=True,capture_output=True,check=True,timeout=120)
    return Image.open(output).convert("RGBA")

def run(v34,out):
    if out.exists():raise FileExistsError("no overwrite: "+str(out))
    for name in CASES:
        check_sha(v34,"v34_evidence_manifest.json",v34/f"{name}_local_safe.svg")
    out.mkdir(parents=True)
    report={"version":"public-r4-component-attribution-v1","cases":[],
            "diagnosticComponentsOnly":True,
            "originalsModified":False,"productionPromoted":False}
    driver=chrome_driver()
    report["chromeVersion"]=driver.capabilities.get("browserVersion")
    try:
        for name in CASES:
            svg_file=v34/f"{name}_local_safe.svg"
            parts=split_source(svg_file.read_text("utf-8"))
            rows={}
            for part in ("facet","paths"):
                chrome340=rgba_image(render_rgba(driver,parts[part]),340)
                chrome680=rgba_image(render_2x(driver,parts[part]),680)
                resvg340=render_resvg(svg_file,out,name,part,340)
                resvg680=render_resvg(svg_file,out,name,part,680)
                comparison340=compare_rgba(chrome340.tobytes(),resvg340.tobytes())
                comparison680=compare_rgba(chrome680.tobytes(),resvg680.tobytes())
                rows[part]={"differentPixels340":comparison340["differentPixels"],
                            "differentPixels680":comparison680["differentPixels"],
                            "alphaDifference680":comparison680["alphaDifferentPixels"],
                            "bbox680":comparison680["boundingBox"],
                            "maxChannelDelta680":comparison680["maxChannelDelta"],
                            "exact340":comparison340["exact"],
                            "exact680":comparison680["exact"]}
                chrome340.save(out/f"{name}_{part}_chrome_340.png")
                chrome680.save(out/f"{name}_{part}_chrome_680.png")
            report["cases"].append({"case":name,"sourceSHA256":sha(svg_file),"components":rows})
            print(name,json.dumps(rows),flush=True)
    finally:
        driver.quit()
    report["allComponentsTested"]=len(report["cases"])==len(CASES)
    report["releasePassed"]=False
    (out/"public_r4_component_attribution.json").write_text(
      json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--v34",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    r=run(args.v34,args.out)
    if not r["allComponentsTested"]:raise SystemExit("R4 component evidence incomplete")
    print("R4_COMPONENT_ATTRIBUTION_COMPLETE / RELEASE_HOLD",flush=True)

if __name__=="__main__":main()
