"""R11 real-host read-only cache admission, trusted-source and fail-closed tests."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_r11_live_host import (
  VERSION,APP_BASE,ORIGIN,TARGETS,allowed_url,max_age,references,capture,
  assess,gate_sources,fetch_public,run)
from verify_public_r10_release_assets import VERSION as R10_VERSION

def fake_host(url,method):
    suffix=url.removeprefix(ORIGIN+APP_BASE)
    html='<html><head>'+''.join(
        '<script src="static/x'+str(i)+'.js"></script>' for i in range(12))
    html+='<link href="static/styles.css" rel="stylesheet">'
    html+='<script src="static/app.js?v=20261008-local-public"></script>'
    html+='</head><body>Minimalizer Public</body></html>'
    content=(html.encode() if suffix in ("",".") else
             (b"body{}" if suffix.startswith("static/styles.css") else
              b"window.r11=1;"))
    if "resvg-wasm" in suffix:return 404,{},b""
    headers={"Content-Type":"text/html" if not suffix or suffix=="." else "text/css",
             "Cache-Control":"max-age=604800",
             "ETag":'"fake-etag"',"Content-Length":str(len(content)),
             "Expires":"fake dynamic date"}
    return 200,headers,content if method=="GET" else b""

def fixture(tmp_path):
    p={}
    d=[
       ("r6",{"version":"public-r6-conservative-release-admission-v1",
              "status":"NO_GO","releaseAuthorized":False,"blockedGateCount":8}),
       ("r8",{"version":"public-r8-static-vendor-redistribution-inventory-v1",
              "status":"INVENTORY_PASS_LEGAL_HOLD","releaseAuthorized":False,
              "fullVendorFileCount":40,
              "loopbackStaticRollbackDryRun":{"loopbackRollbackByteExact":True}}),
       ("r9",{"status":"CACHE_SIMULATION_VERIFIED_PRODUCTION_NO_GO",
              "releaseAuthorized":False}),
       ("r10",{"version":R10_VERSION,
               "status":"RELEASE_VERSIONING_RESEARCH_PASS_PRODUCTION_NO_GO",
               "releaseAuthorized":False,"oldAssetFileCount":66,
               "chrome":{"conversionSHA256UnchangedAcrossReleases":True}}),
    ]
    for key,contents in d:
        target=tmp_path/(key+".json")
        target.write_text(json.dumps(contents),encoding="utf-8")
        p[key]=target
    return p

def test_same_origin_and_read_only_route_guards():
    assert allowed_url("static/styles.css")==ORIGIN+APP_BASE+"static/styles.css"
    assert allowed_url(".")==ORIGIN+APP_BASE
    for uri in ("https://example.net/","//evil.test/x","../other-site",
                "/admin","", "http://bad.invalid/file"):
        with pytest.raises(ValueError):allowed_url(uri)
    with pytest.raises(ValueError,match="read-only"):
        fetch_public(ORIGIN+APP_BASE,"POST")
    with pytest.raises(ValueError):
        fetch_public("https://invalid.example.com/","GET")

def test_cache_max_age_parser():
    assert max_age("public, max-age=604800")==604800
    assert max_age("MAX-AGE = 60, private")==60
    assert max_age("no-cache") is None
    assert max_age(None) is None

def test_html_asset_refs_are_explicit_and_bounded():
    text=(b'<script src="static/app.js"></script>'
          b'<link href="static/styles.css"/>'
          b'<img src="static/no.png"/>'
          b'<script src="https://thirdparty.invalid/foo"></script>')
    assert references(text)==["static/app.js","static/styles.css"]
    with pytest.raises(ValueError,match="size cap"):
        references(b"x"*320001)

def test_live_observations_do_not_persist_dynamic_expiry_and_honor_optional_404():
    result=capture(fetch=fake_host)
    assert result["index"]["status"]==200
    assert len(result["index"]["htmlStaticReferences"])==14
    assert result["css"]["maxAgeSeconds"]==604800
    assert result["css"]["expiresHeaderPresent"] is True
    assert "expires" not in result["css"]
    assert result["optionalResvgResearch"]["status"]==404
    decision=assess(result)
    assert decision["liveAssetReuseCacheRisk"] is True
    assert decision["optionalResvgNotPresentIsNotProductOutage"] is True
    assert decision["liveRollbackExecuted"] is False

def test_core_route_missing_is_fail_closed():
    captured=capture(fetch=fake_host)
    captured["app"]["status"]=404
    with pytest.raises(ValueError,match="app"):
        assess(captured)

def test_r10_forged_release_admission_is_rejected(tmp_path):
    p=fixture(tmp_path)
    expected=gate_sources(p["r6"],p["r8"],p["r9"],p["r10"])
    assert len(expected)==4
    altered=json.loads(p["r10"].read_text(encoding="utf-8"))
    altered["releaseAuthorized"]=True
    p["r10"].write_text(json.dumps(altered),encoding="utf-8")
    with pytest.raises(ValueError,match="R10 research"):
        gate_sources(p["r6"],p["r8"],p["r9"],p["r10"])

def test_out_existing_and_product_route_untouched(tmp_path):
    p=fixture(tmp_path)
    out=tmp_path/"already"
    out.mkdir()
    with pytest.raises(FileExistsError):
        run(p["r6"],p["r8"],p["r9"],p["r10"],out)
    code=(ROOT/"scripts/verify_public_r11_live_host.py").read_text(encoding="utf-8")
    assert '"releaseAuthorized":False' in code
    assert '"liveServerFileWrites":0' in code
    assert '"realIphoneSafariDprApproved":False' in code
    assert "POST" not in code.replace('("GET","HEAD")',"")
    for rel in ("web/static/public-route.js","web/static/browser-fallback.js",
                "local_worker/frontend/local-route.js"):
        assert "verify_public_r11_live_host" not in (ROOT/rel).read_text(encoding="utf-8")
