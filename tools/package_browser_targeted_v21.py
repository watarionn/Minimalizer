#!/usr/bin/env python3
"""Preserve v21 research outputs to the exact Drive project folder with SHA256 verification."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

REPORT_FILES=(
    "v21_metrics.json",
    "v21_trial_results.csv",
    "v21_report.md",
    "v21_five_pair_comparison.png",
    "v21_accepted_changes_emphasized.png",
    "v21_repro_inputs_outputs.zip",
)
SOURCE_FILES=(
    "tools/run_browser_targeted_v21_chrome.py",
    "tools/analyze_browser_targeted_v21.py",
    "tools/package_browser_targeted_v21.py",
    "tests/test_browser_targeted_v21.py",
)
MANIFEST="v21_evidence_manifest.json"


def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()


def preserve(report:Path,repo:Path,drive:Path,replace_reviewed:bool=False):
    if not drive.is_dir():
        raise FileNotFoundError(f"Expected previously created canonical Drive folder: {drive}")
    files=[report/name for name in REPORT_FILES]+[repo/name for name in SOURCE_FILES]
    for p in files:
        if not p.is_file():raise FileNotFoundError(str(p))
    meta=json.loads((report/"v21_metrics.json").read_text(encoding="utf-8"))
    assert meta["approvedResearchCount"]==2
    assert meta["rolledBackExplicitPairCount"]==3
    assert meta["missingPairNegativeCount"]==1
    metadata={
        "status":"RESEARCH_PASS_PRODUCTION_HOLD",
        "source":"GitHub research/browser-targeted-v21-20261008",
        "goldenCases":["Kyoko","Noel","Ririka"],
        "productionChanged":False,
        "files":{p.name:{"size":p.stat().st_size,"sha256":sha256(p)} for p in files},
    }
    # A controlled revision is required after review found the Noel staff
    # changed 161 pixels in the provisional positive trial.
    superseded={}
    for source in files:
        target=drive/source.name
        if target.is_file() and sha256(target)!=sha256(source):
            if not replace_reviewed:
                raise FileExistsError(f"Conflicting evidence; explicit review replacement needed: {target}")
            superseded[source.name]={"previousSha256":sha256(target),
                                     "correctedSha256":sha256(source)}
    metadata["supersededProvisionalReview"]={
        "reason":"Protect Noel's thin staff after high-contrast inspection revealed a 161px change in a previously accepted trial",
        "updatedFiles":superseded,
    }
    manifest=report/MANIFEST
    manifest.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    files.append(manifest)
    for source in files:
        target=drive/source.name
        if target.exists():
            if sha256(target)!=sha256(source):
                if not replace_reviewed:
                    raise FileExistsError(f"Conflicting Drive artifact, refusing overwrite: {target}")
                shutil.copy2(source,target)
        else:
            shutil.copy2(source,target)
        if sha256(target)!=sha256(source):
            raise IOError(f"Drive SHA256 mismatch: {target}")
    print("V21_DRIVE_SHA256_VERIFIED",len(files),
          "BYTES",sum(p.stat().st_size for p in files),flush=True)
    print("V21_PRESERVED_FILES",json.dumps([p.name for p in files]),flush=True)


if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--report",type=Path,required=True)
    arg.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    arg.add_argument("--drive",type=Path,required=True)
    arg.add_argument("--replace-reviewed-evidence",action="store_true")
    o=arg.parse_args()
    preserve(o.report,o.repo,o.drive,o.replace_reviewed_evidence)
