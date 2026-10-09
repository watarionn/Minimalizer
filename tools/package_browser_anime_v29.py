"""v29 source-locked research evidence package and canonical Drive read-after-write SHA."""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path

BRANCH="research/browser-anime-corpus-gate-v29-20261009"
SOURCE_SHA="91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39"

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()

def preserve(repo:Path,audit:Path,replay:Path,dest:Path,ref:Path)->dict:
    assert dest.is_dir(),"canonical destination must exist"
    assert sha(ref)==SOURCE_SHA,"frozen v27 source mismatch"
    state=json.loads((audit/"v29_metrics.json").read_text(encoding="utf-8"))
    gate=json.loads((audit/"v29_model_memory_preflight.json").read_text(encoding="utf-8"))
    check=json.loads((replay/"v29_replay_sha_verify.json").read_text(encoding="utf-8"))
    assert state["status"]=="SPARSE_SOURCE_QA_PASS_SEMANTIC_GLOBAL_HOLD"
    assert state["anchorCount"]==20 and len(state["cases"])==2
    assert gate["modelVerified"] and gate["corpusVerified"] and gate["modelInferenceLaunched"] is False
    assert gate["status"]=="HOLD_NO_HEAVY_MODEL_EXECUTION"
    assert check["status"]=="PASS" and check["fileCount"]==14
    assert all(sha(audit/name)==code for name,code in check["deterministicFiles"].items())
    head=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
    remote=subprocess.check_output(["git","-C",str(repo),"rev-parse","origin/"+BRANCH],text=True).strip()
    name=subprocess.check_output(["git","-C",str(repo),"branch","--show-current"],text=True).strip()
    status=subprocess.check_output(["git","-C",str(repo),"status","--porcelain"],text=True).strip()
    if head!=remote or name!=BRANCH or status:
        raise ValueError("Unverified dirty/divergent repository")
    assets={p.name:p for p in audit.iterdir() if p.is_file()}
    assets["v29_replay_sha_verify.json"]=replay/"v29_replay_sha_verify.json"
    for relative in (
        "tools/audit_browser_anime_corpus_v29.py",
        "tools/gate_browser_anime_inference_v29.py",
        "tools/verify_browser_anime_corpus_v29.py",
        "tools/package_browser_anime_v29.py",
        "tests/test_browser_anime_corpus_v29.py",
        "docs/zerobase/BROWSER_ANIME_CORPUS_V29_HOLD_20261009.md",
    ):
        p=repo/relative
        assert p.is_file()
        assets[p.name]=p
    assert len(assets)==22,(len(assets),list(assets))
    bundle=dest/"v29_original_source_qa_bundle.zip"
    if bundle.exists():raise FileExistsError("do not replace existing research bundle")
    with zipfile.ZipFile(bundle,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for key,path in sorted(assets.items()):
            archive.write(path,key)
    with zipfile.ZipFile(bundle) as archive:
        assert len(archive.namelist())==len(assets)
    indexed=[]
    for name,source in sorted(assets.items()):
        assert source.is_file()
        target=dest/name
        if target.exists():
            if sha(target)!=sha(source):raise FileExistsError("existing mismatched artifact: "+name)
        else:
            shutil.copy2(source,target)
        if sha(target)!=sha(source) or source.stat().st_size!=target.stat().st_size:
            raise AssertionError("Drive mounted copy checksum mismatch: "+name)
        indexed.append({"name":name,"size":target.stat().st_size,"sha256":sha(target)})
    indexed.append({"name":bundle.name,"size":bundle.stat().st_size,"sha256":sha(bundle)})
    record={
      "phase":"nonlocal-browser-v29","result":"SPARSE_QA_COMPLETE_GLOBAL_SEMANTIC_HOLD",
      "branch":BRANCH,"headSHA":head,"PR":299,
      "referenceZipSHA":SOURCE_SHA,
      "caseNames":["Noel","Ririka"],"reviewAnchorCount":20,
      "sparseSourceOnly":True,"fullPixelGroundTruth":False,
      "newAnimeSegMasks":{"Noel":False,"Ririka":False},
      "poseSidesVerified":False,"sourceMaskArtifactRepeatSHA":14,
      "modelInferencePerformed":False,"productionPromoted":False,
      "freeRAMGiBAtPreflight":gate["memory"].get("freePhysicalGiB"),
      "artifactReadAfterWriteSHA":True,
      "artifacts":indexed,
    }
    target=dest/"v29_evidence_manifest.json"
    if target.exists():raise FileExistsError("existing v29 manifest")
    target.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    verify=json.loads(target.read_text(encoding="utf-8"))
    assert len(verify["artifacts"])==23
    assert all(sha(dest/x["name"])==x["sha256"] for x in verify["artifacts"])
    print("V29_PRESERVE_SHA_PASS",len(indexed)+1,"files",
        "repoHEAD",head,"freeGiB",record["freeRAMGiBAtPreflight"],flush=True)
    for item in indexed:print(item["name"],item["size"],item["sha256"],flush=True)
    return record

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("repo","audit","replay","dest","reference"):
        p.add_argument("--"+name,type=Path,required=True)
    v=p.parse_args()
    preserve(v.repo,v.audit,v.replay,v.dest,v.reference)
