"""Repeat v34 Chrome guarded vector study and SHA-verify all staged artifacts."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
import numpy as np
from PIL import Image
NAMES=("Kyoko","Noel","Ririka")
INPUT=Path(r"G:\マイドライブ\chatGPT及びCodex用\Minimalizer\ConnectedSourcePlanesV32_20261009")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(stage):
    report=json.loads((stage/"v34_metrics.json").read_text(encoding="utf-8"))
    assert report["status"]=="LOCAL_ROLLBACK_EXACT_CHROME_PARITY_PASS"
    assert len(report["cases"])==3
    for item in report["cases"]:
        name=item["case"];assert name in NAMES
        assert item["exactRgbaParity"] and item["pixelsDifferentFromV32"]==0
        assert not item["productionReady"] and not item["semanticPartAuthority"]
        assert item["attemptedGroups"]==item["acceptedGroups"]+item["rejectedGroups"]
        assert item["finalVertices"]==item["originalVertices"]-item["acceptedVertexSavings"]
        assert item["finalSVGBytes"]<=item["originalSVGBytes"]
        assert item["svgSHA256"]==sha(stage/(name+"_local_safe.svg"))
        assert item["chromePngSHA256"]==sha(stage/(name+"_local_safe_chrome.png"))
        src=np.asarray(Image.open(INPUT/(name+"_connected_fine.png")).convert("RGBA"))
        out=np.asarray(Image.open(stage/(name+"_local_safe_chrome.png")).convert("RGBA"))
        assert np.array_equal(src,out),(name,"Chrome pixel parity failed")
    return report

def replay(repo,stage,out,limit):
    if out.exists():raise FileExistsError("replay target already exists")
    subprocess.run([sys.executable,str(repo/"tools/optimize_browser_svg_v34.py"),
       "--out",str(out),"--epsilon","0.85","--candidate-limit",str(limit)],
       check=True,timeout=300)
    baseline=verify(stage)
    second=verify(out)
    assert baseline==second
    names=[n+"_"+ext for n in NAMES for ext in
      ("local_safe.svg","local_safe_chrome.png")]+["v34_metrics.json"]
    for name in names:
        assert sha(stage/name)==sha(out/name),name
        print("V34_REPLAY_SHA_PASS",name,sha(stage/name),flush=True)
    report={"status":"7_OF_7_INDEPENDENT_CHROME_SHA_PASS",
      "caseCount":3,"files":{n:sha(stage/n) for n in names},
      "everyPixelMatchesFrozenV32":True,"productionPromoted":False}
    (stage/"v34_replay_sha_verify.json").write_text(
       json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("V34_REPLAY_COMPLETE",len(names),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--stage",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--limit",type=int,default=25)
    a=p.parse_args()
    replay(a.repo,a.stage,a.out,a.limit)
