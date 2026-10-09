"""Independently replay v32 source-plane research and verify all nine PNG/JSON/CSV bytes."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path

OUTPUT_NAMES=[
 "Kyoko_connected_coarse.png","Kyoko_connected_fine.png",
 "Noel_connected_coarse.png","Noel_connected_fine.png",
 "Ririka_connected_coarse.png","Ririka_connected_fine.png",
 "v32_source_contiguous_comparison.png","v32_metrics.json","v32_metrics.csv"
]
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def replay(script:Path,baseline:Path,dest:Path):
    if dest.exists():raise FileExistsError("v32 replay destination already exists")
    for name in OUTPUT_NAMES:
        if not (baseline/name).is_file():raise FileNotFoundError(name)
    env=os.environ.copy()
    env["MINIMALIZER_V32_OUT"]=str(dest)
    subprocess.run([sys.executable,str(script)],check=True,env=env,timeout=240)
    assert sorted(x.name for x in dest.iterdir())==sorted(OUTPUT_NAMES)
    hashes={}
    for filename in OUTPUT_NAMES:
        first=baseline/filename
        second=dest/filename
        assert sha(first)==sha(second),(filename,"v32 nondeterministic")
        hashes[filename]=sha(first)
        print("V32_REPLAY_SHA_PASS",filename,hashes[filename],flush=True)
    meta=json.loads((dest/"v32_metrics.json").read_text(encoding="utf-8"))
    assert len(meta["cases"])==6
    assert all(r["changedOutsideGarment"]==0 and r["alphaChanges"]==0
               and r["sourceRGBMAECandidate"]<=r["sourceRGBMAEFacet"]
               and not r["productionAuthority"]
               for r in meta["cases"])
    proof={"state":"RESEARCH_REPLAY_SHA_PASS","variants":6,"caseCount":3,
      "byteIdenticalOutputs":len(OUTPUT_NAMES),"sha256":hashes,
      "productionPromoted":False,"realSourceInferencePerformed":False}
    dest.joinpath("v32_replay_sha_verify.json").write_text(
       json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("V32_REPLAY_COMPLETE",len(hashes),"files",flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--script",type=Path,required=True)
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    replay(a.script,a.baseline,a.out)
