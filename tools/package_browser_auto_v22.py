#!/usr/bin/env python3
"""Copy checked Auto research artifacts to the existing Drive folder."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ARTIFACTS=("v22_metrics.json","v22_metrics.csv","v22_report.md",
           "v22_three_golden_comparison.png","v22_raw_images_and_metrics.zip")
SCRIPTS=("run_browser_auto_v22_chrome.py","analyze_browser_auto_v22.py",
         "package_browser_auto_v22.py","test_browser_auto_gated_v22.py")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--drive",type=Path,required=True)
    a=p.parse_args()
    if not a.drive.is_dir():
        raise FileNotFoundError(str(a.drive))
    paths=[a.report/f for f in ARTIFACTS]
    paths += [a.repo/"tools"/f for f in SCRIPTS[:3]]
    paths += [a.repo/"tests"/SCRIPTS[3]]
    assert all(x.is_file() for x in paths)
    report=json.loads((a.report/"v22_metrics.json").read_text(encoding="utf-8"))
    assert len(report["cases"])==3 and report["notProductionReady"]
    metadata={"status":"PRODUCTION_HOLD",
              "files":{x.name:{"sha256":sha(x),"bytes":x.stat().st_size} for x in paths}}
    manifest=a.report/"v22_evidence_manifest.json"
    manifest.write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    paths.append(manifest)
    for src in paths:
        dest=a.drive/src.name
        if dest.exists() and sha(dest)!=sha(src):
            raise FileExistsError(str(dest))
        if not dest.exists():
            shutil.copy2(src,dest)
        assert sha(src)==sha(dest),dest
    print("V22_DRIVE_SHA256_VERIFIED",len(paths),flush=True)

if __name__=="__main__":
    main()
