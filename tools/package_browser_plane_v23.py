#!/usr/bin/env python3
"""Preserve validated v23 golden image artifacts under the canonical short Drive path."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

REPORT_FILES = ("v23_metrics.json", "v23_metrics.csv", "v23_report.md",
                "v23_three_source_comparison.png", "v23_raw_images_metrics.zip")
SCRIPT_FILES = ("run_browser_plane_v23_chrome.py", "analyze_browser_plane_v23.py",
                "package_browser_plane_v23.py")
TEST_FILE = "test_browser_plane_v23.py"
MANIFEST = "v23_evidence_manifest.json"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--drive",type=Path,required=True)
    args=parser.parse_args()
    if not args.drive.is_dir():
        raise FileNotFoundError("Canonical drive folder not mounted: "+str(args.drive))
    files=[args.report/f for f in REPORT_FILES]
    files.extend(args.repo/"tools"/f for f in SCRIPT_FILES)
    files.append(args.repo/"tests"/TEST_FILE)
    for f in files:
        if not f.is_file():
            raise FileNotFoundError(str(f))
    data=json.loads((args.report/"v23_metrics.json").read_text(encoding="utf-8"))
    assert data["status"]=="V23_MAJOR_PLANE_EXPERIMENT_NOT_PRODUCTION"
    assert len(data["cases"])==3
    metadata={
        "status":"RESEARCH_COMPLETE_PRODUCTION_HOLD",
        "source":"watarionn/Minimalizer research/browser-major-plane-v23-20261009",
        "goldenCases":["Kyoko","Noel","Ririka"],
        "files":{f.name:{"sha256":digest(f),"bytes":f.stat().st_size} for f in files},
    }
    manifest=args.report/MANIFEST
    manifest.write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    files.append(manifest)
    for file in files:
        target=args.drive/file.name
        if target.is_file() and digest(target)!=digest(file):
            raise FileExistsError("Conflicting canonical artifact: "+str(target))
        if not target.is_file():
            shutil.copy2(file,target)
        if digest(file)!=digest(target):
            raise IOError("SHA256 mismatch: "+str(target))
    print("V23_SHA256_VERIFIED",len(files),
          "total_bytes",sum(file.stat().st_size for file in files),flush=True)
    print("V23_FILES",",".join(file.name for file in files),flush=True)

if __name__=="__main__":
    main()
