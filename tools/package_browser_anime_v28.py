"""Package verified v28 Kyoko research and explicitly missing Noel/Ririka cases."""
from __future__ import annotations
import argparse,hashlib,json,zipfile,io
from pathlib import Path

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def pack(a):
    audit=Path(a.audit)
    out=Path(a.out)
    out.mkdir(parents=True,exist_ok=True)
    m=json.loads((audit/"v28_metrics.json").read_text(encoding="utf-8"))
    stage=json.loads((audit/"stage.json").read_text(encoding="utf-8"))
    assert m["browserAnimeInference"]=="NOT_IMPLEMENTED"
    assert m["casesAvailable"]=={"Kyoko":"cached_v3_mask","Noel":"unavailable","Ririka":"unavailable"}
    assert m["model"]["modelSha256"]=="f6764a379496712a92d1a85f852a81155cd79132a3e050b77c972be7e1cec394"
    assert m["partBindingAuthority"] is False
    assert stage["visibleOutputModified"] is False
    assert stage["previewSHA256"]==sha(audit/"v28_kyoko_anime_vs_photo.png")
    assert stage["metricsSHA256"]==sha(audit/"v28_metrics.json")
    src=Path(a.source);mask=Path(a.mask);frozen=Path(a.frozen)
    assert sha(src)==m["provenance"]["sourceSha256"]
    assert sha(mask)==m["provenance"]["cachedMaskSha256"]
    assert sha(frozen)==m["provenance"]["v27FrozenZipSha256"]
    with zipfile.ZipFile(frozen) as z:
        facet=z.read("Kyoko/facet.png")
        photo=z.read("Kyoko/part_classes.png")
    (out/"Kyoko_frozen_facet.png").write_bytes(facet)
    (out/"Kyoko_v27_photo_classes.png").write_bytes(photo)
    (out/"Kyoko_source.png").write_bytes(src.read_bytes())
    (out/"Kyoko_AnimeSeg_v3_cached_mask.png").write_bytes(mask.read_bytes())
    for name in ("v28_kyoko_anime_vs_photo.png","v28_metrics.json",
                 "v28_confusion.csv","stage.json"):
        (out/name).write_bytes((audit/name).read_bytes())
    report=[
    "# BrowserFallback v28 - anime parser feasibility",
    "",
    "Decision: **CACHED KYOKO MODEL REFERENCE PASS / BROWSER-READY HOLD**.",
    "No new heavy inference performed. Original local CPU AnimeSeg v3 artifact was reused.",
    "Kyoko source SHA exactly matches v27 frozen Kyoko source SHA.",
    "",
    "Existing SA10.27 AnimeSeg/Mask2Former v3 (12 classes):",
    "- 431,643,704-byte checkpoint, actual cached SHA-256 "+m["model"]["modelSha256"],
    "- Cached Kyoko source 340x340: hair 19,637 px, clothes 16,223 px",
    "- The source+mask+photo-model comparisons are image-aligned and checksum verified",
    "- The original v27 Photo model visualization has 0 accepted hair and clothes pixels on Kyoko",
    "- IMPORTANT: black v27 preview combines background and UNCLASSIFIED; it is not ground truth",
    "",
    "Visual audit: separate hair and clothing large masses appear useful on Kyoko;",
    "goggles/head accessories are broad and not precise. AnimeSeg is also an imperfect observer,",
    "NOT semantic truth. Its 12 classes have no left/right arm label.",
    "",
    "Browser feasibility: HOLD. This repository carries no verified browser-native",
    "AnimeSeg v3 ONNX checkpoint, no validated ONNX opset, and no measured Chrome",
    "WASM memory/runtime. Importing the 432 MB Python checkpoint into browser",
    "is not equivalent to deploying a tested ONNX model. No runtime was added.",
    "",
    "Resource safety: approximately 2 GB free physical RAM was observed at",
    "start of v28; no new 432 MB torch/Mask2Former inference or heavyweight",
    "model conversion was launched. Existing Qwen/other model workloads unaffected.",
    "",
    "Noel, Ririka: v27 benchmark exists, but no SHA-backed AnimeSeg v3 masks",
    "were available and they were NOT fabricated or substituted. Anime visual",
    "accuracy across 3 cases remains unmeasured.",
    "",
    "Next validation gate: produce independent masks for Noel/Ririka under",
    "an approved memory-safe compute route; evaluate false positives (hair",
    "versus clothes), accessory protection, left/right arm localization through",
    "separate pose evidence, and only then evaluate browser ONNX export/runtime.",
    "Any observer remains no-render, UNBOUND until corroborated.",
    "",
    "This study did not modify any image output, public app, or Local Worker.",
    ""]
    (out/"v28_report.md").write_text("\n".join(report),encoding="utf-8")
    paths=["Kyoko_source.png","Kyoko_frozen_facet.png",
           "Kyoko_v27_photo_classes.png","Kyoko_AnimeSeg_v3_cached_mask.png",
           "v28_kyoko_anime_vs_photo.png","v28_metrics.json","v28_confusion.csv",
           "stage.json","v28_report.md"]
    with zipfile.ZipFile(out/"v28_reference_and_metrics.zip","w",
                          zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in paths:z.write(out/name,name)
    payload={
        "state":"SINGLE_SOURCE_REFERENCE_PASS_BROWSER_HOLD",
        "availableCases":["Kyoko"],"missingCases":["Noel","Ririka"],
        "sourceSHA256":m["provenance"]["sourceSha256"],
        "checkpointSHA256":m["model"]["modelSha256"],
        "browserInferenceReady":False,"renderAuthority":False,
        "artifacts":[{"name":p,"sha256":sha(out/p),
                      "size":(out/p).stat().st_size} for p in paths+
            ["v28_reference_and_metrics.zip"]]}
    path=out/"v28_manifest.json"
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    assert all(sha(out/e["name"])==e["sha256"] for e in payload["artifacts"])
    print("V28_CASE_ARTIFACTS_SHA_PASS",len(payload["artifacts"]),"Kyoko; Noel and Ririka NOT AVAILABLE",flush=True)
    return payload

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--audit",type=Path,required=True)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--mask",type=Path,required=True)
    p.add_argument("--frozen",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    pack(p.parse_args())
