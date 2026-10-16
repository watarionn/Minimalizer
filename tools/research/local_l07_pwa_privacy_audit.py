"""L07 read-only Local PWA Service Worker privacy policy audit.

This is a static, fail-closed source contract, NOT an iPhone/browser/network test.
Must never mutate frontend/production files, cache private image/API responses,
or grant release approval. Full browser/owner/Origin/429 gates remain separate.
"""
from __future__ import annotations
import json,re
from pathlib import Path

ALLOWED_SHELL=frozenset((
    "/", "/static/styles.css", "/static/color-strip.css", "/static/app.js",
    "/static/browser-feature-palette.js", "/static/browser-color-strip.js",
    "/local-static/local-route.js", "/local-static/icon.svg",
))
FORBIDDEN_ASSET_PREFIXES=("/api/","/uploads/","/private/","/artifacts/","/user/")
BLOCKED_APIS=("cache.put(","caches.put(","cache.add(","importScripts(","eval(","new Function(")

class PrivacyHold(ValueError):pass

def _strip_line_comments(source:str)->str:
    return "\n".join(line.split("//",1)[0] for line in source.splitlines())

def verify_serviceworker(source:str):
    if not isinstance(source,str) or len(source)>200000:
        raise PrivacyHold("SW_SOURCE_INVALID")
    code=_strip_line_comments(source)
    m=re.search(r"\bconst\s+ASSETS\s*=\s*(\[[\s\S]*?\])\s*;",code)
    if not m:raise PrivacyHold("SW_SHELL_ASSET_ARRAY_MISSING")
    try:assets=json.loads(m.group(1))
    except json.JSONDecodeError as exc:raise PrivacyHold("SW_ASSET_ARRAY_UNPARSEABLE") from exc
    if (not isinstance(assets,list) or not assets or
        any(not isinstance(p,str) or not p.startswith("/") or
            p.startswith(FORBIDDEN_ASSET_PREFIXES) or
            p.endswith((".png",".jpg",".jpeg",".webp",".svg")) and p!="/local-static/icon.svg"
            for p in assets)):
        raise PrivacyHold("SW_UNTRUSTED_CACHE_ASSET")
    if len(set(assets))!=len(assets) or frozenset(assets)!=ALLOWED_SHELL:
        raise PrivacyHold("SW_SHELL_ALLOWLIST_CHANGED_REVIEW_REQUIRED")
    tight=code.replace(" ","").replace("\n","").replace("\t","")
    if any(api.replace(" ","") in tight for api in BLOCKED_APIS):
        raise PrivacyHold("SW_DYNAMIC_CACHE_OR_SCRIPT_EXECUTION")
    for fragment in (
        'event.request.method!=="GET"',
        'url.origin!==self.location.origin',
        '!ASSETS.includes(url.pathname)',
        'cache.addAll(ASSETS)',
        'event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)))',
    ):
        if fragment not in tight:raise PrivacyHold("SW_PRIVACY_GUARD_MISSING:"+fragment)
    if tight.count('self.addEventListener("fetch"')!=1:
        raise PrivacyHold("SW_UNEXPECTED_EXTRA_FETCH_HANDLER")
    return {"status":"STATIC_SW_PRIVACY_CONTRACT_PASS",
            "shell_asset_count":len(assets),
            "cache_user_images":False,"cache_api_responses":False,
            "offline_shell_fallback":True,
            "live_browser_e2e_verified":False}

def verify_local_route(source:str):
    if not isinstance(source,str) or len(source)>100000:raise PrivacyHold("LOCAL_ROUTE_INVALID")
    code=_strip_line_comments(source)
    required=('window.MinimalizerComputeRoute = Object.freeze({',
              'fetch("/health"', 'fetch("/api/zerobase2/minimalize"',
              'fetch("/api/v2/minimalize"','cache:"no-store"')
    if any(piece not in code for piece in required):
        raise PrivacyHold("LOCAL_ROUTE_CONTRACT_MISSING")
    if "MinimalizerBrowserFallback" in code or "browser-fallback.js" in code:
        raise PrivacyHold("LOCAL_ROUTE_BROWSER_DOWNGRADE")
    return {"status":"STATIC_LOCAL_ROUTE_ISOLATED","no_browser_fallback":True,
            "no_store_requests":True,"live_iphone_e2e_verified":False}

def audit(repo_root:Path):
    if not isinstance(repo_root,Path):raise PrivacyHold("REPO_ROOT_REQUIRED")
    sw=(repo_root/"local_worker/frontend/sw.js").read_text(encoding="utf-8")
    route=(repo_root/"local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    return {"schema":"minimalizer/local-l07/privacy-static/v1",
            "serviceworker":verify_serviceworker(sw),
            "route":verify_local_route(route),
            "production_changes":False,
            "L07_actual_live_iphone":"NOT_TESTED",
            "L08_release":"NOT_APPROVED"}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("repository_root",type=Path)
    a=p.parse_args()
    print(json.dumps(audit(a.repository_root),ensure_ascii=False,sort_keys=True,indent=2))
