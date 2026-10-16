"""Synthetic fail-closed Local PWA cache policy tests. No real worker required."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
from local_l07_pwa_privacy_audit import (
 PrivacyHold,ALLOWED_SHELL,verify_serviceworker,verify_local_route,audit,
)
ROOT=Path(__file__).resolve().parents[1]
SW=(ROOT/"local_worker/frontend/sw.js").read_text(encoding="utf-8")
ROUTE=(ROOT/"local_worker/frontend/local-route.js").read_text(encoding="utf-8")

def test_actual_local_serviceworker_static_privacy_contract():
    r=verify_serviceworker(SW)
    assert r["shell_asset_count"]==len(ALLOWED_SHELL)
    assert r["cache_api_responses"] is False
    assert r["cache_user_images"] is False

def test_actual_local_route_stays_private_and_no_store():
    r=verify_local_route(ROUTE)
    assert r["no_browser_fallback"] is True
    assert r["live_iphone_e2e_verified"] is False

@pytest.mark.parametrize("evil",(
    '"/api/v2/minimalize",',
    '"/api/zerobase2/minimalize",',
    '"/uploads/personal.png",',
    '"/user/photos/h04.jpg",',
    '"/private/source.webp",',
    '"/static/proprietary-source.png",',
))
def test_added_private_or_api_cache_target_rejected(evil):
    bad=SW.replace('const ASSETS = [', 'const ASSETS = ['+evil)
    with pytest.raises(PrivacyHold):verify_serviceworker(bad)

def test_fetch_origin_check_removed_is_rejected():
    with pytest.raises(PrivacyHold):
        verify_serviceworker(SW.replace('url.origin !== self.location.origin', 'true'))

def test_get_only_check_removed_is_rejected():
    with pytest.raises(PrivacyHold):
        verify_serviceworker(SW.replace('event.request.method !== "GET"', 'false'))

def test_whitelist_check_removed_is_rejected():
    with pytest.raises(PrivacyHold):
        verify_serviceworker(SW.replace('!ASSETS.includes(url.pathname)', 'false'))

def test_dynamic_cache_put_rejected():
    with pytest.raises(PrivacyHold):
        verify_serviceworker(SW+'\ncache.put(event.request, response);\n')

def test_unexpected_second_fetch_event_handler_rejected():
    with pytest.raises(PrivacyHold):
        verify_serviceworker(SW+'\nself.addEventListener("fetch", event=>{});\n')

def test_browser_downshift_rejected():
    with pytest.raises(PrivacyHold):
        verify_local_route(ROUTE+'\nMinimalizerBrowserFallback;')

def test_missing_health_readiness_gate_rejected():
    with pytest.raises(PrivacyHold):
        verify_local_route(ROUTE.replace('fetch("/health"', 'fetch("/other"'))

def test_missing_best_pipeline_rejected():
    with pytest.raises(PrivacyHold):
        verify_local_route(ROUTE.replace('fetch("/api/zerobase2/minimalize"', 'fetch("/bad"'))

def test_reject_cross_project_root_contract():
    with pytest.raises(PrivacyHold):
        verify_serviceworker('const ASSETS = ["/"];')

def test_static_audit_never_claims_live_iphone_or_release():
    r=audit(ROOT)
    assert r["L07_actual_live_iphone"]=="NOT_TESTED"
    assert r["L08_release"]=="NOT_APPROVED"
