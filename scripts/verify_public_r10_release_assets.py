"""R10 disposable Public static release directories and source-derived fingerprints.

Only a research utility. Verifies immutable source R9 NO_GO and constructs
research-only versioned asset roots in temporary directories. No product
routines, Golden pixels, Local Worker or active deployment are modified.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import http.server
import importlib.util
import json
import re
import shutil
import tempfile
import threading
from pathlib import Path

from verify_public_r9_cache_rollback import (
    BROWSER_SAMPLE, ROUTES, RouteHandler, browser_rows, verify_no_go,
    VERSION as R9_VERSION)
from verify_public_v34_svgo_chrome import chrome_driver, check_sha
from verify_public_r5_route_chrome import JS_RUN as R5_CONVERSION_JS

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"web"/"static"
VERSION="public-r10-release-isolated-assets-v1"
HTML_ASSET_RE=re.compile(r'(?P<attr>\b(?:src|href)\s*=\s*["\x27])static/')
DOCUMENT_IMPORT_RE=re.compile(r'new URL\(["\x27]static/(public-[^"\x27]+)["\x27],\s*document\.baseURI\)')
DYNAMIC_MODULES=(
    "public-svgo-research.mjs","public-resvg-research.mjs",
    "public-clipper2-research.mjs","public-vtracer-research.mjs",
    "public-r5-shadow-gate.mjs")
PROBES=("static/app.js","static/styles.css",
        "static/public-route.js","static/browser-subject.js",
        "static/vendor/resvg-wasm/index_bg.wasm",
        "static/models/u2netp.onnx")

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def files_sha(root:Path)->dict:
    return {p.relative_to(root).as_posix():digest(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}

def source_release_id(source_static:Path)->str:
    # Derived from all original source bytes, BEFORE URL rewrites.
    # Not falsely advertised as hash of modified output files.
    entries=files_sha(source_static)
    if "app.js" not in entries or "index.html" not in entries:
        raise ValueError("invalid original Public static source")
    canonical=json.dumps(entries,sort_keys=True,separators=(",",":")).encode("ascii")
    return digest(canonical)[:24]

def stage_source(source_static:Path,root:Path)->dict:
    if root.exists():raise FileExistsError("R10 refuses overwrite")
    release=source_release_id(source_static)
    old=files_sha(source_static)
    assets=root/"assets"/release/"static"
    assets.parent.mkdir(parents=True)
    shutil.copytree(source_static,assets)
    # The static builder copies index to top-level, excludes static/index.html.
    (assets/"index.html").unlink()
    index=(source_static/"index.html").read_text(encoding="utf-8")
    originals=HTML_ASSET_RE.findall(index)
    if len(originals)<15:raise ValueError("unrecognized Public HTML entrypoints")
    transformed,count=HTML_ASSET_RE.subn(
        lambda m: m.group("attr")+"assets/"+release+"/static/",index)
    if count<15 or 'src="static/' in transformed or 'href="static/' in transformed:
        raise ValueError("not every Public HTML static link was versioned")
    (root/"index.html").write_text(transformed,encoding="utf-8")
    # Classic public-route.js uses document.baseURI for opt-in ESM imports.
    # Rewrite only copied research asset to release-relative URLs.
    route=assets/"public-route.js"
    code=route.read_text(encoding="utf-8")
    found=DOCUMENT_IMPORT_RE.findall(code)
    if sorted(found)!=sorted(DYNAMIC_MODULES):
        raise ValueError("unrecognized or missing dynamic observer imports")
    new,count_dynamic=DOCUMENT_IMPORT_RE.subn(
        lambda m: 'new URL("assets/'+release+'/static/'+m.group(1)+'", document.baseURI)',
        code)
    if count_dynamic!=len(DYNAMIC_MODULES):
        raise ValueError("dynamic imports were not fully versioned")
    route.write_text(new,encoding="utf-8")
    built=files_sha(assets)
    if "index.html" in built or set(built)!=set(old)-{"index.html"}:
        raise ValueError("asset output file set changed unexpectedly")
    changed={name for name in built if built[name]!=old[name]}
    if changed!={"public-route.js"}:
        raise ValueError("unexpected mutated source assets: "+repr(sorted(changed)))
    return {"releaseId":release,"originalSHA256":old,
            "stagedAssetSHA256":built,
            "changedSourceCopyFiles":sorted(changed),
            "htmlReferenceCount":count,"dynamicImportCount":count_dynamic,
            "indexHtmlSHA256":digest((root/"index.html").read_bytes())}

def assemble_two_releases(source_static:Path,root:Path)->dict:
    if root.exists():raise FileExistsError("R10 release root must be new")
    # two source snapshots; a simulated update changes only app and CSS comments.
    with tempfile.TemporaryDirectory(prefix="r10_source_versions_") as t:
        tmp=Path(t)
        old=tmp/"old";new=tmp/"new"
        shutil.copytree(source_static,old)
        shutil.copytree(source_static,new)
        for rel in ("app.js","styles.css"):
            with (new/rel).open("ab") as f:
                f.write(b"\n/* R10 synthetic version update; not production code */\n")
        old_id=source_release_id(old)
        new_id=source_release_id(new)
        if old_id==new_id:raise ValueError("content release ID collision")
        old_stage=stage_source(old,tmp/"old-stage")
        new_stage=stage_source(new,tmp/"new-stage")
        root.mkdir(parents=True)
        # Independent release directories retained, never overwritten on cutover.
        assets=root/"assets"
        assets.mkdir()
        shutil.copytree(tmp/"old-stage"/"assets"/old_id,assets/old_id)
        shutil.copytree(tmp/"new-stage"/"assets"/new_id,assets/new_id)
        a=tmp/"old-stage"/"index.html"
        b=tmp/"new-stage"/"index.html"
        (root/"old_index.html").write_bytes(a.read_bytes())
        (root/"new_index.html").write_bytes(b.read_bytes())
        (root/"index.html").write_bytes(a.read_bytes())
    return {"old":old_stage,"new":new_stage,
            "oldIndex":digest((root/"old_index.html").read_bytes()),
            "newIndex":digest((root/"new_index.html").read_bytes())}

class CacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(args[2].release_root),**kwargs)
    def log_message(self,*args):pass
    def do_GET(self):
        self.directory=str(self.server.release_root)
        super().do_GET()
    def end_headers(self):
        if self.path.startswith("/assets/"):
            self.send_header("Cache-Control","public, max-age=3600")
        else:
            self.send_header("Cache-Control","no-store")
        self.send_header("X-R10-Test","loopback-only")
        super().end_headers()

def browser_hashes(driver,release_id:str)->dict:
    links=[
        "assets/"+release_id+"/static/"+name
        for name in (p.removeprefix("static/") for p in PROBES)]
    return browser_rows(driver,links,"default")

def require_sha_matches(record:dict,release_id:str,assets:dict)->None:
    expected_prefix="assets/"+release_id+"/static/"
    if len(record["rows"])!=len(PROBES):raise ValueError("missing asset browser read")
    for row in record["rows"]:
        if not row["route"].startswith(expected_prefix):
            raise ValueError("cross-release asset URL")
        name=row["route"][len(expected_prefix):]
        if row["sha256"]!=assets[name]:
            raise ValueError("Chrome unexpected bytes: "+name)


def conversion_smoke(driver,source:bytes)->dict:
    event=driver.execute_async_script(R5_CONVERSION_JS,base64.b64encode(source).decode("ascii"))
    if not event.get("ok"):
        raise ValueError("versioned Public browser conversion failed: "+repr(event))
    png=base64.b64decode(event["png"],validate=True)
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("versioned Public returned non-PNG result")
    observed=event.get("shaStatus")
    actual=digest(png)
    if not observed or observed.get("status")!="ok" or observed.get("sha256")!=actual:
        raise ValueError("opt-in shadow module failed from versioned asset root")
    return {"pngSHA256":actual,"pngBytes":len(png),
            "shadowStatus":observed["status"],"byteExactObserver":True}

def run(r6:Path,r8:Path,r9:Path,v32:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R10 evidence output exists")
    provenance=verify_no_go(r6,r8)
    fixture=v32/'Kyoko_connected_fine.png'
    check_sha(v32,'v32_evidence_manifest.json',fixture)
    test_source=fixture.read_bytes()
    prior=json.loads(r9.read_text(encoding="utf-8"))
    if prior.get("version")!=R9_VERSION or (
        prior.get("status")!="CACHE_SIMULATION_VERIFIED_PRODUCTION_NO_GO" or
        prior.get("releaseAuthorized") is not False or
        prior.get("disposableTreeRestoredByteExact") is not True):
        raise ValueError("R10 requires real R9 stale-cache evidence")
    provenance["r9SHA256"]=digest(r9.read_bytes())
    builder_path=ROOT/"scripts"/"build_shin_static.py"
    spec=importlib.util.spec_from_file_location("r10_actual_static_build",builder_path)
    builder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    if builder.SOURCE.resolve()!=PUBLIC.resolve():
        raise ValueError("R10 must use original public static builder")
    with tempfile.TemporaryDirectory(prefix="r10_disposable_static_") as tmp:
        tmp=Path(tmp)
        builder.DESTINATION=tmp/"builder_output"
        builtin=builder.build()
        research=tmp/"candidate_versions"
        pair=assemble_two_releases(PUBLIC,research)
        old=pair["old"];new=pair["new"]
        # Guarantee every shipped source asset matches actual built file.
        frozen=files_sha(builtin/"static")
        for name,source_sha in old["originalSHA256"].items():
            if name=="index.html":continue
            if frozen[name]!=source_sha:
                raise ValueError("research baseline diverged from genuine builder "+name)
        srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),CacheHandler)
        srv.release_root=research
        worker=threading.Thread(target=srv.serve_forever,daemon=True)
        worker.start()
        driver=chrome_driver()
        origin=f"http://127.0.0.1:{srv.server_port}/"
        try:
            driver.set_script_timeout(120)
            driver.get(origin+"?browserFallbackQuality=lite&publicR5Shadow=1&r10=baseline")
            baseline_smoke=conversion_smoke(driver,test_source)
            baseline=browser_hashes(driver,old["releaseId"])
            require_sha_matches(baseline,old["releaseId"],old["stagedAssetSHA256"])
            (research/"index.html").write_bytes((research/"new_index.html").read_bytes())
            driver.get(origin+"?browserFallbackQuality=lite&publicR5Shadow=1&r10=cutover")
            canary_smoke=conversion_smoke(driver,test_source)
            current=browser_hashes(driver,new["releaseId"])
            require_sha_matches(current,new["releaseId"],new["stagedAssetSHA256"])
            # Old HTML browser tabs may still reference OLD immutable asset URLs.
            # Retaining old assets is what makes that safe.
            old_tab=browser_hashes(driver,old["releaseId"])
            require_sha_matches(old_tab,old["releaseId"],old["stagedAssetSHA256"])
            (research/"index.html").write_bytes((research/"old_index.html").read_bytes())
            driver.get(origin+"?browserFallbackQuality=lite&publicR5Shadow=1&r10=rollback")
            restored_smoke=conversion_smoke(driver,test_source)
            recovered=browser_hashes(driver,old["releaseId"])
            require_sha_matches(recovered,old["releaseId"],old["stagedAssetSHA256"])
            # No stale cross-release mixing, even while both asset generations
            # share the same simulated 1h browser cache.
            if not (baseline_smoke["pngSHA256"]==canary_smoke["pngSHA256"]==restored_smoke["pngSHA256"]):
                raise ValueError("Public PNG changed during asset-only release switching")
            chrome={"chromeVersion":driver.capabilities.get("browserVersion"),
                    "goldenInputIsAlreadyMinimalizedFixtureNotSourcePhoto":True,
                    "conversionSHA256UnchangedAcrossReleases":True,
                    "baselineBrowserConversion":baseline_smoke,
                    "canaryBrowserConversion":canary_smoke,
                    "rollbackBrowserConversion":restored_smoke,
                    "browserDpr":baseline["devicePixelRatio"],
                    "oldAssetsAfterCanaryStillAvailable":True,
                    "newAssetsAfterRollbackStillAvailable":True,
                    "originalVersionRestoredInBrowser":True,
                    "checkedAssetsPerPhase":len(PROBES),
                    "phasesChecked":4,
                    "browserCacheEnabled":True,
                    "simulatedHostingNotActualProvider":True,
                    "iphoneSafariRealDevice":False}
        finally:
            driver.quit()
            srv.shutdown()
            srv.server_close()
            worker.join(timeout=4)
    record={"version":VERSION,**provenance,
            "releaseIdOrigin":"all ORIGINAL source asset SHA digests, deterministic; not the staged transformed file hash",
            "baseReleaseId":old["releaseId"],"syntheticNewReleaseId":new["releaseId"],
            "releaseIdsDifferent":old["releaseId"]!=new["releaseId"],
            "oldAssetFileCount":len(old["stagedAssetSHA256"]),
            "newAssetFileCount":len(new["stagedAssetSHA256"]),
            "originalSourceAssetDigests":old["originalSHA256"],
            "stagedBaseAssetDigests":old["stagedAssetSHA256"],
            "stagedNewAssetDigests":new["stagedAssetSHA256"],
            "htmlStaticReferencesVersioned":old["htmlReferenceCount"],
            "dynamicDocumentImportsVersioned":old["dynamicImportCount"],
            "chrome":chrome,
            "stageDirectoryUsedOnly":True,
            "realProductionProviderValidated":False,
            "deviceIphoneSafariApproved":False,
            "semanticGoldenApproved":False,
            "stage8OriginalBudgetApproved":False,
            "resvgDpr2WholeSceneApproved":False,
            "legalRedistributionApproved":False,
            "realRollbackApproved":False,
            "localMinimalizerModified":False,
            "releaseAuthorized":False,"mergeOrDeployPerformed":False,
            "status":"RELEASE_VERSIONING_RESEARCH_PASS_PRODUCTION_NO_GO"}
    out.mkdir(parents=True)
    (out/"public_r10_asset_release_manifest.json").write_text(
        json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("R10_REAL_CHROME_RELEASE_ASSETS_PASS",
          record["oldAssetFileCount"],"assets",
          record["htmlStaticReferencesVersioned"],"HTML refs",
          record["dynamicDocumentImportsVersioned"],"dynamic imports; NO_GO",
          flush=True)
    return record

def main():
    p=argparse.ArgumentParser()
    for k in ("r6","r8","r9","v32","out"):
        p.add_argument("--"+k,required=True,type=Path)
    args=p.parse_args()
    run(args.r6,args.r8,args.r9,args.v32,args.out)

if __name__=="__main__":main()
