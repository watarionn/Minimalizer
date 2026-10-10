"""R10 disposable Public release asset identity, routing and fail-closed tests."""
from __future__ import annotations
import hashlib
import json
import shutil
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_r10_release_assets import (
    DOCUMENT_IMPORT_RE,DYNAMIC_MODULES,HTML_ASSET_RE,PUBLIC,PROBES,
    VERSION,files_sha,source_release_id,stage_source,assemble_two_releases,
    require_sha_matches)
from verify_public_r9_cache_rollback import verify_no_go

def synthetic(tmp_path):
    root=tmp_path/"src"
    root.mkdir()
    html='<html><head>'+''.join(
        f'<script src="static/script{i}.js"></script>' for i in range(18))
    html+='</head><body><link rel="stylesheet" href="static/styles.css"></body></html>'
    (root/"index.html").write_text(html,encoding="utf-8")
    (root/"app.js").write_text("window.r10 = true;",encoding="utf-8")
    (root/"styles.css").write_text("body {margin:0}",encoding="utf-8")
    (root/"public-route.js").write_text(
        "\n".join('new URL("static/'+name+'", document.baseURI)'
                   for name in DYNAMIC_MODULES),encoding="utf-8")
    for i in range(18):
        (root/f"script{i}.js").write_text("const x=1;")
    return root

def test_fingerprinted_release_id_is_repeatable_and_changes_with_bytes(tmp_path):
    source=synthetic(tmp_path)
    old=source_release_id(source)
    assert len(old)==24 and old==source_release_id(source)
    (source/"app.js").write_text("window.r10 = false;")
    assert source_release_id(source)!=old

def test_all_html_refs_and_document_dynamic_imports_stay_within_one_release(tmp_path):
    source=synthetic(tmp_path)
    frozen=files_sha(source)
    output=tmp_path/"staged"
    manifest=stage_source(source,output)
    release=manifest["releaseId"]
    assert files_sha(source)==frozen
    assert manifest["htmlReferenceCount"]==19
    assert manifest["dynamicImportCount"]==5
    assert manifest["changedSourceCopyFiles"]==["public-route.js"]
    text=(output/"index.html").read_text()
    assert 'src="static/' not in text and 'href="static/' not in text
    assert text.count("assets/"+release+"/static/")==19
    code=(output/"assets"/release/"static"/"public-route.js").read_text()
    assert code.count("assets/"+release+"/static/public-")==5
    assert all(item in code for item in DYNAMIC_MODULES)

def test_missing_dynamic_import_is_rejected(tmp_path):
    source=synthetic(tmp_path)
    (source/"public-route.js").write_text(
        'new URL("static/public-r5-shadow-gate.mjs", document.baseURI)')
    with pytest.raises(ValueError,match="missing dynamic observer"):
        stage_source(source,tmp_path/"invalid")

def test_existing_build_is_not_overwritten(tmp_path):
    source=synthetic(tmp_path)
    output=tmp_path/"exists"
    output.mkdir()
    with pytest.raises(FileExistsError):
        stage_source(source,output)

def test_canary_release_preserves_immutable_old_asset_urls(tmp_path):
    source=synthetic(tmp_path)
    original=files_sha(source)
    root=tmp_path/"two"
    versioned=assemble_two_releases(source,root)
    old=versioned["old"];new=versioned["new"]
    assert old["releaseId"]!=new["releaseId"]
    assert files_sha(source)==original
    for stage in (old,new):
        prefix=root/"assets"/stage["releaseId"]/"static"
        assert prefix.is_dir()
        assert (prefix/"app.js").is_file()
    assert versioned["oldIndex"]!=versioned["newIndex"]
    assert (root/"index.html").read_bytes()==(root/"old_index.html").read_bytes()

def test_browser_manifest_rejects_stale_or_other_release(tmp_path):
    source=synthetic(tmp_path)
    stage=stage_source(source,tmp_path/"release")
    rid=stage["releaseId"]
    record={"rows":[{"route":"assets/"+rid+"/static/"+name.removeprefix("static/"),
                     "sha256":stage["stagedAssetSHA256"][name.removeprefix("static/")]}
                   for name in ("static/app.js","static/styles.css")]}
    with pytest.raises(ValueError,match="missing asset browser read"):
        require_sha_matches(record,rid,stage["stagedAssetSHA256"])
    record["rows"]=[]
    with pytest.raises(ValueError):
        require_sha_matches(record,rid,stage["stagedAssetSHA256"])

def test_product_gate_is_unsigned_and_local_unchanged():
    script=(ROOT/"scripts/verify_public_r10_release_assets.py").read_text()
    assert '"releaseAuthorized":False' in script
    assert '"realRollbackApproved":False' in script
    assert '"deviceIphoneSafariApproved":False' in script
    assert '"semanticGoldenApproved":False' in script
    for path in ("web/static/public-route.js","web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "verify_public_r10_release_assets" not in (ROOT/path).read_text(encoding="utf-8")
