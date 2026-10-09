"""Independent v33 real Chrome re-render SHA validation (exact and rejected proposals)."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

def sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda:fp.read(1048576),b""):h.update(block)
    return h.hexdigest()

def verify(repo:Path,original:Path,replay:Path):
    if replay.exists():raise FileExistsError("v33 replay target already exists")
    cmd=[sys.executable,str(repo/"tools/audit_browser_svg_v33_chrome.py"),
         "--repo",str(repo),"--out",str(replay)]
    subprocess.run(cmd,check=True,timeout=300)
    names=sorted(x.name for x in original.iterdir() if x.is_file())
    other=sorted(x.name for x in replay.iterdir() if x.is_file())
    assert names==other,(names,other)
    assert len(names)==14,(len(names),names)
    outputs={}
    for name in names:
        left=original/name;right=replay/name
        assert sha(left)==sha(right),(name,"not deterministic")
        outputs[name]=sha(left)
        print("V33_SVG_REPLAY_SHA_PASS",name,outputs[name],flush=True)
    m=json.loads((original/"v33_metrics.json").read_text(encoding="utf-8"))
    assert len(m["cases"])==3 and m["status"]=="SOURCE_OWNED_SVG_VECTOR_RESEARCH_COMPLETE_PRODUCTION_HOLD"
    assert all(case["variants"]["exact"]["pixelsDifferentFromV32"]==0
         and case["variants"]["exact"]["safe"] is True
         and case["variants"]["simplified"]["safe"] is False
         and case["variants"]["simplified"]["candidateAcceptance"]=="REJECT_UNSAFE"
         for case in m["cases"])
    record={"status":"PASS_14_OF_14_BYTE_EXACT",
            "caseCount":3,"renderMode":"independent real Chrome SVG",
            "exactRasterParity":3,"simplifiedPromotion":False,
            "productionChanged":False,"files":outputs}
    report=replay/"v33_replay_sha_verify.json"
    report.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    assert json.loads(report.read_text(encoding="utf-8"))["caseCount"]==3
    print("V33_REPLAY_VERIFIED",len(outputs),flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--replay",type=Path,required=True)
    a=parser.parse_args()
    verify(a.repo,a.original,a.replay)
