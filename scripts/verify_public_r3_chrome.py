"""R3 exact directed-lattice co-linear proposals: real Chrome native/2x Golden gate.

Input v34/v32 manifests are verified before output. This is a research-only
negative-outcome recorder; NEVER affects MinimalizerPublic or Local routes.
"""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from PIL import Image
from verify_public_v34_svgo_chrome import (
    CASES, SIZE, check_sha, chrome_driver, render_rgba, mismatched_pixels, sha)
from verify_public_r2_chrome import render_2x

NODE = Path(__file__).with_name("public_r3_exact_collinear.cjs")

def run(v34: Path, v32: Path, out: Path):
    if out.exists():
        raise FileExistsError("non-overwrite research output: "+str(out))
    for name in CASES:
        check_sha(v34,"v34_evidence_manifest.json",v34/f"{name}_local_safe.svg")
        check_sha(v34,"v34_evidence_manifest.json",v34/f"{name}_local_safe_chrome.png")
        check_sha(v32,"v32_evidence_manifest.json",v32/f"{name}_connected_fine.png")
    out.mkdir(parents=True)
    driver=chrome_driver()
    report={"version":"public-r3-exact-lattice-v1",
            "chromeVersion":driver.capabilities.get("browserVersion","unknown"),
            "cases":[],"sourceSemanticOwnershipCertified":False,
            "stage8OriginalVertexBudgetPass":False,
            "humanGoldenSigned":False,
            "localMinimalizerTouched":False,"productionPromoted":False}
    try:
        for name in CASES:
            source=v34/f"{name}_local_safe.svg"
            candidate=out/f"{name}_r3_collinear_proposal.svg"
            metrics=out/f"{name}_r3_exact_lattice_audit.json"
            subprocess.run(["node",str(NODE),str(source),str(candidate),str(metrics)],
                           capture_output=True,text=True,check=True,timeout=120)
            audit=json.loads(metrics.read_text(encoding="utf-8"))
            before=source.read_text(encoding="utf-8")
            after=candidate.read_text(encoding="utf-8")
            original=Image.open(v32/f"{name}_connected_fine.png").convert("RGBA").tobytes()
            archived=Image.open(v34/f"{name}_local_safe_chrome.png").convert("RGBA").tobytes()
            if len(original)!=SIZE[0]*SIZE[1]*4 or len(archived)!=len(original):
                raise RuntimeError("unexpected frozen Golden dimensions")
            raw_rgba=render_rgba(driver,before)
            candidate_rgba=render_rgba(driver,after)
            diff_baseline=mismatched_pixels(raw_rgba,original)
            diff_prior=mismatched_pixels(raw_rgba,archived)
            diff_proposed=mismatched_pixels(candidate_rgba,original)
            diff_2x=mismatched_pixels(render_2x(driver,before),render_2x(driver,after))
            injected=after.replace("</svg>",
                '<rect x="0" y="0" width="340" height="340" fill="#000"/></svg>')
            negative=mismatched_pixels(render_rgba(driver,injected),original)
            exact=(
                diff_baseline==diff_prior==diff_proposed==diff_2x==0 and negative>0 and
                audit["candidateCoverageComplete"] and
                audit["failedEdgeProofGroups"]==0 and audit["failedWholeMaskGroups"]==0 and
                audit["checkedColorGroups"]==audit["sourceColorGroups"])
            row={"case":name,
                 "sourceColorGroups":audit["sourceColorGroups"],
                 "checkedColorGroups":audit["checkedColorGroups"],
                 "sourceVertices":audit["sourceVertices"],
                 "groupsWithStrictCollinearProposals":audit["groupsWithCollinearProposals"],
                 "provenRemovableVertices":audit["mathematicallyProposedVertexSavings"],
                 "edgeProofFailures":audit["failedEdgeProofGroups"],
                 "maskFailures":audit["failedWholeMaskGroups"],
                 "originalVsFrozenV32PixelDiff":diff_baseline,
                 "originalVsArchivedChromePixelDiff":diff_prior,
                 "candidateVsFrozenV32PixelDiff":diff_proposed,
                 "candidateVsOriginalChrome2xPixelDiff":diff_2x,
                 "negativeControlPixelDiff":negative,
                 "candidateUnchangedBytes":sha(source)==sha(candidate),
                 "sourceSHA256":sha(source),"candidateSHA256":sha(candidate),
                 "chromeGatePass":exact,"geometryOutputPromoted":False}
            report["cases"].append(row)
            print(name,json.dumps({k:row[k] for k in (
                "sourceColorGroups","sourceVertices",
                "groupsWithStrictCollinearProposals","provenRemovableVertices",
                "candidateVsFrozenV32PixelDiff",
                "candidateVsOriginalChrome2xPixelDiff","chromeGatePass")}),flush=True)
    finally:
        driver.quit()
    report["allExact"]=(len(report["cases"])==len(CASES) and
                        all(x["chromeGatePass"] for x in report["cases"]))
    report["anyStrictCollinearImprovement"]=any(
        row["provenRemovableVertices"]>0 for row in report["cases"])
    report["productQualityImproved"]=False
    (out/"public_r3_gate.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--v34",required=True,type=Path)
    a.add_argument("--v32",required=True,type=Path)
    a.add_argument("--out",required=True,type=Path)
    args=a.parse_args()
    data=run(args.v34,args.v32,args.out)
    if not data["allExact"]:
        raise SystemExit("R3_HOLD: Chrome parity or full-owner proof failed")
    if not data["anyStrictCollinearImprovement"]:
        print("R3_EXACT_EDGE_PROOF_PASS / ZERO_VERTEX_SAVINGS / QUALITY_HOLD",flush=True)
    else:
        print("R3_EXACT_EDGE_PROOF_PASS / CANDIDATES_RESEARCH_ONLY / QUALITY_HOLD",flush=True)

if __name__=="__main__":main()
