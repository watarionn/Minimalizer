from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_r9_cache_rollback import (
 MARKERS,ROUTES,compare_rows,snapshot,staged_releases,verify_no_go)

def fixture(tmp_path):
    root=tmp_path/"built"
    for name,payload in {
      "index.html":b"<html><body>Minimalizer</body></html>",
      "static/app.js":b"window.Minimalizer=1;",
      "static/styles.css":b"body{}",
      "static/vendor/resvg-wasm/index_bg.wasm":b"fixture-no-wasm"}.items():
        f=root/name
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_bytes(payload)
    return root

def test_r9_only_disposable_artifacts_are_modified(tmp_path):
    built=fixture(tmp_path)
    original=snapshot(built)
    base,canary,recovered=(tmp_path/x for x in ("base","canary","recovered"))
    b,c=staged_releases(built,base,canary,recovered)
    assert original==b==snapshot(recovered)==snapshot(base)
    assert {x for x in b if b[x]!=c[x]}==set(MARKERS)
    assert built.joinpath("index.html").read_bytes()==base.joinpath("index.html").read_bytes()

def test_r9_frozen_release_gate_cannot_be_overridden(tmp_path):
    a=tmp_path/"r6.json"
    b=tmp_path/"r8.json"
    a.write_text(json.dumps({"version":"public-r6-conservative-release-admission-v1",
      "status":"NO_GO","releaseAuthorized":False,"blockedGateCount":8}))
    b.write_text(json.dumps({"version":"public-r8-static-vendor-redistribution-inventory-v1",
      "status":"INVENTORY_PASS_LEGAL_HOLD","releaseAuthorized":False,
      "fullVendorFileCount":40,
      "loopbackStaticRollbackDryRun":{"loopbackRollbackByteExact":True}}))
    assert len(verify_no_go(a,b)["r6SHA256"])==64
    a.write_text(a.read_text().replace("NO_GO","GO"))
    with pytest.raises(ValueError,match="R6"):
        verify_no_go(a,b)

def test_r9_detects_stale_route_instead_of_approving(tmp_path):
    built=fixture(tmp_path)
    lookup=snapshot(built)
    rows=[{"route":u,"sha256":lookup[u.split("?",1)[0].lstrip("/")]}
          for u in ROUTES]
    assert compare_rows({"rows":rows},lookup)==[]
    rows[0]["sha256"]="0"*64
    assert compare_rows({"rows":rows},lookup)==[ROUTES[0]]
    with pytest.raises(ValueError):
        compare_rows({"rows":[]},lookup)

def test_r9_no_production_or_safari_claims():
    code=(ROOT/"scripts/verify_public_r9_cache_rollback.py").read_text(encoding="utf8")
    assert '"releaseAuthorized":False' in code
    assert '"iphoneSafariDprSigned":False' in code
    assert '"fullProductionRollbackSigned":False' in code
    assert "Cache-Control" in code
    for name in ("web/static/public-route.js","local_worker/frontend/local-route.js"):
        assert "verify_public_r9_cache_rollback" not in (ROOT/name).read_text(encoding="utf8")
