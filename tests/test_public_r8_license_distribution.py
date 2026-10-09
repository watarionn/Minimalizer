"""R8 source/build-license provenance and fail-closed distribution research."""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_r8_license_distribution import (
    EXPECTED, LEGACY_REQUIRED, STATIC, VERSION, audit_vendor_tree,
    check_built_source, run)

@pytest.fixture
def staged_vendor(tmp_path):
    root=tmp_path/"static"
    shutil.copytree(STATIC/"vendor",root/"vendor")
    return root

def test_actual_licensing_inventory_complete_and_versions_are_pinned():
    report=audit_vendor_tree(STATIC)
    assert report["researchLibrariesCount"]==9
    assert report["allDeclaredVendorAssets"]==40
    all_assets=report["assets"]
    assert "vendor/resvg-wasm/LICENSE" in all_assets
    assert "vendor/resvg-wasm/THIRD_PARTY.md" in all_assets
    assert "vendor/resvg-wasm/index_bg.wasm" in all_assets
    assert "vendor/licenses/onnxruntime-LICENSE.txt" in all_assets
    assert len({entry["name"] for entry in report["researchLibraries"]})==9
    assert all(entry["licenseReviewSigned"] is False
               for entry in report["researchLibraries"])

def test_missing_mpl_license_is_hard_failure(staged_vendor):
    (staged_vendor/"vendor/resvg-wasm/LICENSE").unlink()
    with pytest.raises(ValueError,match="missing pinned vendor file"):
        audit_vendor_tree(staged_vendor)

def test_corrupt_wasm_binary_rejects_vendor_before_bundling(staged_vendor):
    p=staged_vendor/"vendor/resvg-wasm/index_bg.wasm"
    with p.open("ab") as f:f.write(b"tampered")
    with pytest.raises(ValueError,match="binary provenance mismatch"):
        audit_vendor_tree(staged_vendor)

def test_modified_package_license_and_notice_are_detected(staged_vendor):
    p=staged_vendor/"vendor/resvg-wasm/package.json"
    pkg=json.loads(p.read_text(encoding="utf-8"))
    pkg["license"]="MIT"
    p.write_text(json.dumps(pkg),encoding="utf-8")
    with pytest.raises(ValueError,match="resvg package metadata mismatch"):
        audit_vendor_tree(staged_vendor)
    pkg["license"]="MPL-2.0"
    p.write_text(json.dumps(pkg),encoding="utf-8")
    (staged_vendor/"vendor/resvg-wasm/THIRD_PARTY.md").write_text(
        "# not enough attribution",encoding="utf-8")
    with pytest.raises(ValueError,match="provenance or attribution"):
        audit_vendor_tree(staged_vendor)

def test_unreviewed_new_vendor_subtree_fails_closed(staged_vendor):
    (staged_vendor/"vendor/unreviewed-download").mkdir()
    with pytest.raises(ValueError,match="unreviewed-download"):
        audit_vendor_tree(staged_vendor)

def test_build_missing_notice_or_modified_asset_is_detected(staged_vendor):
    source=audit_vendor_tree(STATIC)
    assert check_built_source(source,staged_vendor)["resvgMplLicenseIncluded"]
    (staged_vendor/"vendor/earcut/THIRD_PARTY.md").unlink()
    with pytest.raises(ValueError):
        check_built_source(source,staged_vendor)

def test_real_static_builder_disposable_output_and_unsigned_hold(tmp_path):
    out=tmp_path/"output"
    report=run(out)
    assert report["version"]==VERSION
    assert report["libraryCount"]==9
    assert report["fullVendorFileCount"]==40
    assert report["disposableBuildProof"]["buildVendorFilesByteExact"]==40
    assert report["disposableBuildProof"]["resvgMplLicenseIncluded"]
    assert report["disposableBuildProof"]["indexHtmlByteExact"]
    assert report["licenseComplianceLegallyApproved"] is False
    assert report["resvgMplRedistributionReviewSigned"] is False
    assert report["releaseAuthorized"] is False
    assert report["status"]=="INVENTORY_PASS_LEGAL_HOLD"
    assert (out/"RESVG_MPL_REVIEW_PENDING.md").is_file()
    with pytest.raises(FileExistsError):
        run(out)

def test_live_public_and_local_conversion_routes_untouched():
    for file in ("web/static/public-route.js",
                 "web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        data=(ROOT/file).read_text(encoding="utf-8")
        assert "verify_public_r8_license_distribution" not in data
    text=(ROOT/"scripts/verify_public_r8_license_distribution.py").read_text()
    assert "productionPromoted" in text and '"releaseAuthorized":False' in text
