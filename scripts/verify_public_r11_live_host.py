"""R11: read-only production host HTTP cache and static release preflight.

The canonical public origin comes from docs/BROWSER_FALLBACK_V12.md.
Never uploads, switches live hosting, purges caches or approves a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from verify_public_r9_cache_rollback import verify_no_go
from verify_public_r10_release_assets import VERSION as R10_VERSION

VERSION="public-r11-real-host-readonly-cache-admission-v1"
ORIGIN="https://cf278796.cloudfree.jp"
APP_BASE="/minimalizer/"
# No private endpoints, account/cookie access, or active path probes.
TARGETS=(
    ("index","", "GET"),
    ("css","static/styles.css","GET"),
    ("app","static/app.js?v=20261008-local-public","GET"),
    ("route","static/public-route.js?v=20261008-local-public","GET"),
    ("subject","static/browser-subject.js","HEAD"),
    ("model","static/models/u2netp.onnx","HEAD"),
    # Optional R4-only research library, not a currently required live component.
    ("optionalResvgResearch","static/vendor/resvg-wasm/index_bg.wasm","HEAD"),
)
MAX_READ=320_000
ALLOWED_PATH=APP_BASE

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

class HTMLAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets=[]
    def handle_starttag(self,tag,attrs):
        if tag not in ("script","link"):return
        data=dict(attrs)
        key="src" if tag=="script" else "href"
        link=data.get(key,"")
        if link.startswith("static/"):
            self.assets.append(link)

def references(html:bytes)->list[str]:
    if len(html)>MAX_READ:raise ValueError("HTML size cap exceeded")
    text=html.decode("utf-8-sig")
    parser=HTMLAssets()
    parser.feed(text)
    return parser.assets

def max_age(header:str|None)->int|None:
    if header is None:return None
    match=re.search(r"(?:^|[, ])max-age\s*=\s*(\d+)(?:[, ]|$)",header,re.I)
    return int(match.group(1)) if match else None

def allowed_url(path:str)->str:
    if not path or path.startswith(("//","http:","https:")):
        raise ValueError("R11 same-origin route guard")
    resolved=urllib.parse.urljoin(ORIGIN+APP_BASE,path)
    parsed=urllib.parse.urlsplit(resolved)
    if parsed.scheme!="https" or parsed.netloc!="cf278796.cloudfree.jp" or (
        not parsed.path.startswith(APP_BASE)):
        raise ValueError("R11 blocked cross-origin or out-of-scope route")
    return resolved

class BoundedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        p=urllib.parse.urlsplit(newurl)
        if p.scheme!="https" or p.netloc!="cf278796.cloudfree.jp" or (
            not p.path.startswith(APP_BASE)):
            raise ValueError("redirect escaped allowed Public origin")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch_public(url:str,method:str)->tuple[int,dict[str,str],bytes]:
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.netloc!="cf278796.cloudfree.jp" or (
        not p.path.startswith(APP_BASE)):
        raise ValueError("R11 forbidden HTTP destination")
    if method not in ("GET","HEAD"):raise ValueError("R11 read-only HTTP only")
    request=urllib.request.Request(
        url,method=method,headers={"User-Agent":"MinimalizerPublicR11Readonly/1.0",
                                    "Accept":"*/*"})
    opener=urllib.request.build_opener(BoundedRedirect())
    try:
        with opener.open(request,timeout=18) as response:
            final=urllib.parse.urlsplit(response.geturl())
            if final.scheme!="https" or final.netloc!="cf278796.cloudfree.jp" or (
                not final.path.startswith(APP_BASE)):
                raise ValueError("R11 response origin escaped")
            contents=response.read(MAX_READ+1) if method=="GET" else b""
            if len(contents)>MAX_READ:raise ValueError("R11 read exceeded cap")
            return response.status,dict(response.headers.items()),contents
    except urllib.error.HTTPError as error:
        # 404 for not-shipped optional resvg must not be disguised as deployed.
        return error.code,dict(error.headers.items()),b""

def capture(targets=TARGETS, fetch=fetch_public)->dict:
    collected={}
    for key,path,method in targets:
        url=allowed_url(path or ".")
        status,headers,body=fetch(url,method)
        selected={k.lower():v for k,v in headers.items()}
        # Volatile Expires and Date timestamps are intentionally NOT persisted;
        # status, ETag, Last-Modified, static SHA and max-age are reproducible.
        data={"status":status,"method":method,
              "path":urllib.parse.urlsplit(url).path,
              "query":urllib.parse.urlsplit(url).query,
              "contentType":selected.get("content-type"),
              "cacheControl":selected.get("cache-control"),
              "maxAgeSeconds":max_age(selected.get("cache-control")),
              "etag":selected.get("etag"),
              "lastModified":selected.get("last-modified"),
              "expiresHeaderPresent":"expires" in selected,
              "vary":selected.get("vary"),
              "contentLengthHeader":selected.get("content-length"),
              "bodyBytes":len(body) if method=="GET" and status==200 else None,
              "bodySHA256":sha(body) if method=="GET" and status==200 else None}
        collected[key]=data
        if key=="index":
            if status!=200 or b"Minimalizer Public" not in body:
                raise ValueError("real host no longer serves expected Minimalizer Public HTML")
            assets=references(body)
            if len(assets)<10 or not any(x.startswith("static/styles.css") for x in assets):
                raise ValueError("real public HTML no longer has expected assets")
            collected[key]["htmlStaticReferences"]=assets
    return collected

def gate_sources(r6:Path,r8:Path,r9:Path,r10:Path)->dict:
    base=verify_no_go(r6,r8)
    obj9=json.loads(r9.read_text(encoding="utf-8"))
    obj10=json.loads(r10.read_text(encoding="utf-8"))
    if obj9.get("status")!="CACHE_SIMULATION_VERIFIED_PRODUCTION_NO_GO" or (
        obj9.get("releaseAuthorized") is not False):
        raise ValueError("missing held R9 actual Chrome cache simulation")
    if obj10.get("version")!=R10_VERSION or (
        obj10.get("status")!="RELEASE_VERSIONING_RESEARCH_PASS_PRODUCTION_NO_GO" or
        obj10.get("releaseAuthorized") is not False or
        obj10.get("oldAssetFileCount")!=66 or
        obj10.get("chrome",{}).get("conversionSHA256UnchangedAcrossReleases") is not True):
        raise ValueError("R11 requires real R10 research release verified")
    base["r9SHA256"]=sha(r9.read_bytes())
    base["r10SHA256"]=sha(r10.read_bytes())
    return base

def assess(captured:dict)->dict:
    for name in ("index","css","app","route","subject","model"):
        if captured.get(name,{}).get("status")!=200:
            raise ValueError("public core route cannot be confirmed: "+name)
    css=captured["css"];js=captured["app"]
    refs=captured["index"]["htmlStaticReferences"]
    fixed_css=any(x=="static/styles.css" for x in refs)
    fixed_js=any(x.startswith("static/app.js?v=20261008-local-public") for x in refs)
    cache_risk=(fixed_css and fixed_js and
                (css.get("maxAgeSeconds") or 0)>0 and
                (js.get("maxAgeSeconds") or 0)>0)
    return {
        "liveHostReadOnlyConfirmed":True,
        "legacyCssFixedUrlDetected":fixed_css,
        "legacyAppFixedQueryDetected":fixed_js,
        "legacyCssMaxAgeSeconds":css.get("maxAgeSeconds"),
        "legacyAppMaxAgeSeconds":js.get("maxAgeSeconds"),
        "liveAssetReuseCacheRisk":cache_risk,
        "liveOptionalResvgStatus":captured.get("optionalResvgResearch",{}).get("status"),
        "optionalResvgNotPresentIsNotProductOutage":captured.get("optionalResvgResearch",{}).get("status")==404,
        "versionedReleaseDirectoryLiveDeployed":False,
        "hostAtomicReleasePointerSupportedProven":False,
        "hostCachePurgeCapabilityProven":False,
        "liveRollbackExecuted":False,
    }

def run(r6:Path,r8:Path,r9:Path,r10:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("R11 never overwrites evidence")
    proofs=gate_sources(r6,r8,r9,r10)
    measurements=capture()
    assessment=assess(measurements)
    result={
        "version":VERSION,"origin":ORIGIN,"applicationPath":APP_BASE,
        "sourceEvidenceSHA256":proofs,
        "liveResponseMeasurements":measurements,
        "preflightAssessment":assessment,
        "researchLiveReadOnlyComplete":True,
        "liveServerFileWrites":0,"liveCacheInvalidations":0,
        "releaseAuthorized":False,"mergeOrDeployPerformed":False,
        "realProductionRollbackApproved":False,
        "realIphoneSafariDprApproved":False,
        "humanGoldenApproved":False,
        "semanticSourceOwnersApproved":False,
        "stage8OriginalBudgetApproved":False,
        "resvgWholeSceneDpr2Approved":False,
        "resvgMplRedistributionApproved":False,
        "status":"LIVE_HOST_HTTP_AUDIT_PASS_RELEASE_NO_GO",
    }
    out.mkdir(parents=True)
    (out/"public_r11_live_host_readonly.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    for x in ("r6","r8","r9","r10","out"):
        p.add_argument("--"+x,type=Path,required=True)
    args=p.parse_args()
    report=run(args.r6,args.r8,args.r9,args.r10,args.out)
    print("R11_REAL_HOST_READONLY",report["liveResponseMeasurements"]["css"]["maxAgeSeconds"],
          report["liveResponseMeasurements"]["app"]["maxAgeSeconds"],
          "RISK",report["preflightAssessment"]["liveAssetReuseCacheRisk"],
          "RELEASE_NO_GO",flush=True)

if __name__=="__main__":main()
