"""MinimalizerPublic R8: source- and build-verified THIRD PARTY inventory.

NO legal sign-off or production changes. Audits exactly the pinned nine Public
research libraries plus pre-existing ONNX runtime notices, then calls the actual
static build function with a disposable destination and verifies byte identity.
Any unreviewed vendor subtree, missing notice, altered binary or missing MPL
provenance fails closed.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import re
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/"web"/"static"
VERSION="public-r8-static-vendor-redistribution-inventory-v1"
EXPECTED={
    "polygon-clipping":{
        "files":["polygon-clipping.umd.min.js","LICENSE.md","THIRD_PARTY.md"],
        "license":"MIT"},
    "simplify-js":{
        "files":["simplify.js","LICENSE","THIRD_PARTY.md"],
        "license":"BSD-2-Clause"},
    "delaunator":{
        "files":["delaunator.min.js","LICENSE","ROBUST_PREDICATES_LICENSE","THIRD_PARTY.md"],
        "license":"ISC"},
    "earcut":{
        "files":["earcut.min.js","LICENSE","THIRD_PARTY.md"],
        "license":"ISC"},
    "svg-path-commander":{
        "files":["index.min.js","LICENSE","THIRD_PARTY.md"],
        "license":"MIT"},
    "svgo":{
        "files":["svgo.browser.js","LICENSE","THIRD_PARTY.md"],
        "license":"MIT"},
    "resvg-wasm":{
        "files":["index.mjs","index_bg.wasm","LICENSE","THIRD_PARTY.md","package.json"],
        "license":"MPL-2.0","package":"@resvg/resvg-wasm","version":"2.6.2",
        "wasmSHA256":"22bf6e9f9a100d972da0411a69c5ba504367fc1fa87b3b64e3f35e53926d2d70"},
    "clipper2-wasm":{
        "files":["clipper2z.mjs","clipper2z.wasm","LICENSE","THIRD_PARTY.md","package.json"],
        "license":"BSL-1.0"},
    "vtracer-wasm":{
        "files":["vtracer.mjs","vtracer.wasm","LICENSE","LICENSE-VTRACER-UPSTREAM",
                 "THIRD_PARTY.md","package.json"],
        "license":"MIT",
        "wasmSHA256":"b93108af0f23e13a64f4b23f2582312a325be9d7ff833e49d04554cd99606f0b"},
}
LEGACY_REQUIRED={
    "onnxruntime":["ort-wasm-simd-threaded.mjs","ort-wasm-simd-threaded.wasm","ort.wasm.min.mjs"],
    "licenses":["onnxruntime-LICENSE.txt","u2net-LICENSE.txt"],
}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def safe_text(p:Path)->str:
    return p.read_text(encoding="utf-8")

def audit_vendor_tree(static:Path)->dict:
    root=static/"vendor"
    if not root.is_dir():raise ValueError("vendored static assets are missing")
    all_dirs={p.name for p in root.iterdir() if p.is_dir()}
    allowed=set(EXPECTED)|set(LEGACY_REQUIRED)
    if all_dirs!=allowed:
        raise ValueError(f"unexpected/missing vendor subtree: {sorted(all_dirs^allowed)}")
    files={}
    libs=[]
    for name,meta in EXPECTED.items():
        folder=root/name
        if {p.name for p in folder.iterdir() if p.is_file()}!=set(meta["files"]):
            raise ValueError("unexpected/missing pinned vendor file: "+name)
        notice=safe_text(folder/"THIRD_PARTY.md")
        if len(notice)<180 or "http" not in notice or name.replace("-wasm","").lower() not in notice.lower().replace("_","-"):
            raise ValueError("missing provenance or attribution content: "+name)
        entry={"name":name,"licenseDeclared":meta["license"],
               "licenseReviewSigned":False,"files":[]}
        for filename in meta["files"]:
            p=folder/filename
            contents=p.read_bytes()
            if not contents:
                raise ValueError("empty vendor asset: "+str(p))
            if filename in {"LICENSE","LICENSE.md","ROBUST_PREDICATES_LICENSE","LICENSE-VTRACER-UPSTREAM"} and len(contents)<250:
                raise ValueError("incomplete license text: "+str(p))
            if filename=="THIRD_PARTY.md" and len(contents)<180:
                raise ValueError("missing meaningful vendor notice")
            rel=str(p.relative_to(static)).replace("\\","/")
            record={"path":rel,"bytes":len(contents),"sha256":sha(contents)}
            files[rel]=record
            entry["files"].append(rel)
        if "wasmSHA256" in meta:
            wasm="index_bg.wasm" if name=="resvg-wasm" else "vtracer.wasm"
            if sha((folder/wasm).read_bytes())!=meta["wasmSHA256"]:
                raise ValueError("pinned binary provenance mismatch: "+name)
            if meta["wasmSHA256"] not in notice:
                raise ValueError("WASM provenance not in third-party notice: "+name)
        if "package" in meta:
            pkg=json.loads(safe_text(folder/"package.json"))
            if (pkg.get("name")!=meta["package"] or
                pkg.get("version")!=meta["version"] or
                pkg.get("license")!=meta["license"]):
                raise ValueError("pinned resvg package metadata mismatch")
        if name=="resvg-wasm":
            lic=safe_text(folder/"LICENSE")
            if not lic.startswith("Mozilla Public License Version 2.0"):
                raise ValueError("MPL 2.0 text mismatch")
            if "@resvg/resvg-wasm@2.6.2" not in notice or "upstream" not in notice.lower():
                raise ValueError("resvg upstream source provenance missing")
        libs.append(entry)
    for sub,names in LEGACY_REQUIRED.items():
        folder=root/sub
        if {p.name for p in folder.iterdir() if p.is_file()}!=set(names):
            raise ValueError("legacy runtime/notice inventory mismatch: "+sub)
        for name in names:
            p=folder/name
            raw=p.read_bytes()
            if len(raw)<100:raise ValueError("empty/short legacy license or runtime")
            rel=str(p.relative_to(static)).replace("\\","/")
            files[rel]={"path":rel,"bytes":len(raw),"sha256":sha(raw)}
    return {"researchLibraries":libs,"assets":files,
            "researchLibrariesCount":len(libs),"allDeclaredVendorAssets":len(files)}

def check_built_source(source:dict, built_static:Path)->dict:
    actual=audit_vendor_tree(built_static)
    required=source["assets"]
    if set(actual["assets"])!=set(required):
        raise ValueError("built inventory dropped or gained vendor files")
    for filename,record in required.items():
        if record["sha256"]!=actual["assets"][filename]["sha256"]:
            raise ValueError("built artifact altered source bytes: "+filename)
    return {
        "buildVendorFilesByteExact":len(required),
        "resvgMplLicenseIncluded":True,
        "allNineNoticeFilesIncluded":True,
        "legacyOnnxAndModelNoticesIncluded":True}

def run(out:Path, source_static:Path=STATIC)->dict:
    if out.exists():raise FileExistsError("R8 refuses to overwrite evidence")
    report_source=audit_vendor_tree(source_static)
    builder_path=ROOT/"scripts"/"build_shin_static.py"
    spec=importlib.util.spec_from_file_location("r8_static_builder",builder_path)
    builder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    if builder.SOURCE.resolve()!=source_static.resolve():
        raise ValueError("R8 refuses to substitute fake source into production builder")
    # Build uses exact existing script, but redirects output to disposable tmp.
    with tempfile.TemporaryDirectory(prefix="r8_public_static_build_") as t:
        builder.DESTINATION=Path(t)/"shin"
        destination=builder.build()
        built=check_built_source(report_source,destination/"static")
        # The builder's actual public entry HTML must also ship byte-identically.
        index=(source_static/"index.html").read_bytes()
        if (destination/"index.html").read_bytes()!=index:
            raise ValueError("built index.html modified")
        built["indexHtmlByteExact"]=True
    report={
        "version":VERSION,
        "source":"existing web/static vendor source, actual static build via isolated DESTINATION",
        "libraries":report_source["researchLibraries"],
        "sourceVendorAssets":report_source["assets"],
        "libraryCount":report_source["researchLibrariesCount"],
        "fullVendorFileCount":report_source["allDeclaredVendorAssets"],
        "disposableBuildProof":built,
        "resvgMplRedistributionReviewSigned":False,
        "transitiveWasmDependencyRightsReviewed":False,
        "sourceOfferAndRecipientNoticeReviewed":False,
        "productionRollbackSigned":False,
        "existingR6BlockedGatesCleared":0,
        "licenseComplianceLegallyApproved":False,
        "productionPromoted":False,"localMinimalizerTouched":False,
        "releaseAuthorized":False,
        "status":"INVENTORY_PASS_LEGAL_HOLD",
    }
    out.mkdir(parents=True)
    (out/"public_r8_vendor_inventory.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"RESVG_MPL_REVIEW_PENDING.md").write_text(
        "# MinimalizerPublic R8 license review remains PENDING\n\n"
        "Full MPL-2.0 text and THIRD_PARTY.md were verified in the disposable static build.\n"
        "Vendored index.mjs / index_bg.wasm matched checked source bytes.\n"
        "Source: https://github.com/yisibl/resvg-js\n"
        "License text: https://www.mozilla.org/en-US/MPL/2.0/\n"
        "Mozilla FAQ: https://www.mozilla.org/en-US/MPL/2.0/FAQ/\n\n"
        "This is a **machine inventory only**, not a legal or release approval.\n"
        "Review source availability for WASM and any covered modifications,\n"
        "recipient notices, transitive Rust component attributions and redistribution\n"
        "rights before enabling this library in public shipped output.\n"
        "Current full-scene DPR2 cross-renderer exactness still FAILS;\n"
        "production and Local Minimalizer were not modified.\n",
        encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    data=run(a.out)
    print("R8_STATIC_VENDOR_INVENTORY_PASS",data["libraryCount"],
          "libraries",data["fullVendorFileCount"],
          "files; LICENSE_REVIEW_HOLD",flush=True)
if __name__=="__main__":main()
