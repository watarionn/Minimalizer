"""V29 independent deterministic SHA replay of sparse QA, not neural inference."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from audit_browser_anime_corpus_v29 import audit

def sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda:fp.read(1048576),b""):h.update(chunk)
    return h.hexdigest()

def replay(reference:Path,initial:Path,out:Path):
    if out.exists():raise FileExistsError("Existing v29 replay output must not be replaced")
    result=audit(reference,out)
    files=sorted(x.name for x in initial.iterdir()
       if x.is_file() and x.name!="v29_model_memory_preflight.json")
    second=sorted(x.name for x in out.iterdir() if x.is_file())
    if files!=second:raise AssertionError("missing/added replay stage files")
    assert len(files)==14,(len(files),files)
    hashes={}
    for filename in files:
        first=initial/filename;another=out/filename
        if sha(first)!=sha(another):raise AssertionError("v29 nondeterminism: "+filename)
        hashes[filename]=sha(first)
        print("V29_REPLAY_SHA_PASS",filename,hashes[filename],flush=True)
    assert len(result["cases"])==2
    report={"status":"PASS","caseCount":2,"fileCount":len(files),
       "recomputedModels":False,
       "sourceAnchorCoordinatesFrozen":True,
       "frozenV27ReferenceSHA":result["frozenV27ZipSHA"],
       "deterministicFiles":hashes,"notGroundTruth":True}
    dest=out/"v29_replay_sha_verify.json"
    dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    assert json.loads(dest.read_text(encoding="utf-8"))["fileCount"]==14
    print("V29_REPLAY_VERIFIED",len(files),"read-after-write OK",flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--v27-zip",required=True,type=Path)
    parser.add_argument("--initial",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    replay(a.v27_zip,a.initial,a.out)
