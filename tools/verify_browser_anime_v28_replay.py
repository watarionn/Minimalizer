"""Replay v28 SHA-bound cached AnimeSeg audit (NOT a new neural inference)."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
NAMES=("v28_kyoko_anime_vs_photo.png","v28_metrics.json","v28_confusion.csv","stage.json")
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("source","mask","v27-zip","checkpoint","initial","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise RuntimeError("Replay target already exists")
    cmd=[sys.executable,str(Path(__file__).with_name("analyze_browser_anime_v28.py")),
         "--source",str(a.source),"--mask",str(a.mask),
         "--v27-zip",str(getattr(a,"v27_zip")),
         "--checkpoint",str(a.checkpoint),"--out",str(a.out)]
    subprocess.run(cmd,check=True)
    result={"status":"PASS","experiment":"same_cached_mask_reanalysis_not_new_inference",
            "cases":["Kyoko"],"missingCases":["Noel","Ririka"],"files":{}}
    for name in NAMES:
        first=a.initial/name;second=a.out/name
        if first.read_bytes()!=second.read_bytes():
            raise RuntimeError("v28 not deterministic: "+name)
        result["files"][name]=sha(first)
        print("V28_REPLAY_SHA_PASS",name,result["files"][name],flush=True)
    result["byteExactFileCount"]=len(NAMES)
    target=a.out/"v28_replay_sha_verify.json"
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    assert json.loads(target.read_text(encoding="utf-8"))["byteExactFileCount"]==4
    print("V28_REPLAY_ALL_PASS",len(NAMES),flush=True)
