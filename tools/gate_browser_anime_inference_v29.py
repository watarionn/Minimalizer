"""Non-local BrowserFallback v29: fail-closed heavy observer execution preflight.

Read-only preflight, NOT an inference runner. Does not import torch, download
models, alter processes, set system limits or allocate GPU/large tensors.
"""
from __future__ import annotations
import argparse,ctypes,hashlib,importlib.util,json,sys
from pathlib import Path

EXPECTED_MODEL_SHA="f6764a379496712a92d1a85f852a81155cd79132a3e050b77c972be7e1cec394"
EXPECTED_MODEL_BYTES=431643704
EXPECTED_CORPUS_SHA="91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39"
CONSERVATIVE_FREE_GIB=5.0
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_=[("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
      ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
      ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
      ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
      ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
def read_windows_memory()->dict:
    if sys.platform!="win32":
        return {"state":"unavailable_non_windows","freePhysicalGiB":None}
    state=MEMORYSTATUSEX()
    state.dwLength=ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
        raise OSError("GlobalMemoryStatusEx failed")
    return {"state":"measured",
      "freePhysicalGiB":round(state.ullAvailPhys/(1024**3),4),
      "totalPhysicalGiB":round(state.ullTotalPhys/(1024**3),4),
      "freeCommitGiB":round(state.ullAvailPageFile/(1024**3),4),
      "loadPercent":int(state.dwMemoryLoad)}
def hash_file(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def preflight(corpus:Path,checkpoint:Path,memory:dict,minimum_gib:float=CONSERVATIVE_FREE_GIB)->dict:
    if not(4<=minimum_gib<=64):raise ValueError("conservative safe floor 4..64GiB")
    corpus_valid=corpus.is_file() and hash_file(corpus)==EXPECTED_CORPUS_SHA
    model_valid=(checkpoint.is_file() and checkpoint.stat().st_size==EXPECTED_MODEL_BYTES
        and hash_file(checkpoint)==EXPECTED_MODEL_SHA)
    ram=memory.get("freePhysicalGiB")
    ram_ok=(memory.get("state")=="measured" and isinstance(ram,(int,float))
       and ram>=minimum_gib)
    blockers=[]
    if not corpus_valid:blockers.append("frozen_corpus_sha_unverified")
    if not model_valid:blockers.append("cached_model_sha_unverified")
    if not ram_ok:blockers.append("insufficient_or_unmeasured_free_ram")
    return {
      "phase":"v29_preflight_only",
      "status":"PRECHECK_PASS_INFERENCE_NOT_EXECUTED" if not blockers
         else "HOLD_NO_HEAVY_MODEL_EXECUTION",
      "memory":memory,"conservativeFreeRAMPolicyGiB":minimum_gib,
      "policyBasis":"research protection threshold, NOT measured peak model requirement",
      "corpusVerified":corpus_valid,
      "modelVerified":model_valid,
      "expectedModelBytes":EXPECTED_MODEL_BYTES,
      "expectedModelSHA256":EXPECTED_MODEL_SHA,
      "expectedCorpusSHA256":EXPECTED_CORPUS_SHA,
      "rtmlibDefaultInterpreterInstalled":bool(importlib.util.find_spec("rtmlib")),
      "poseEngineVerifiedForCurrentCorpus":False,
      "animeSegBrowserOnnxVerified":False,
      "perCaseOutputs":{"Noel":"unavailable","Ririka":"unavailable"},
      "blockers":blockers,
      "executedModel":False,"modelInferenceLaunched":False,
      "generatedPixels":False,"productionAuthority":False,
      "nextGate":"Resource-safe independent Noel/Ririka AnimeSeg v3 masks plus held-out input, and source-aligned pose review",
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--v27-zip",type=Path,required=True)
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    data=preflight(args.v27_zip,args.checkpoint,read_windows_memory())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    if args.out.exists():raise FileExistsError("Preflight existing output; no overwrite")
    args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    assert json.loads(args.out.read_text(encoding="utf-8"))["executedModel"] is False
    print("V29_MEMORY_GUARD",data["status"],
        "freeGiB",data["memory"]["freePhysicalGiB"],
        "modelSha",data["modelVerified"],
        "corpusSha",data["corpusVerified"],flush=True)
