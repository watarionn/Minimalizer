"""R6 release gate must remain NO_GO without real external signoffs."""
from __future__ import annotations
import ast
import importlib.util
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/verify_public_r6_release_admission.py"
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("r6_release",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def test_release_gate_refuses_missing_or_forged_records():
    with pytest.raises(ValueError):
        m.evaluate({}, {})
    assert 'humanGoldenSigned":False' in SCRIPT.read_text(encoding="utf-8")
    assert '"releaseAuthorized":False' in SCRIPT.read_text(encoding="utf-8")

def test_frozen_evidence_read_preflight_fails_missing_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        m.execute(tmp_path,tmp_path/"out")
    assert not (tmp_path/"out").exists()
    assert not any(tmp_path.iterdir())

def test_no_overwrite_existing_decision(tmp_path):
    (tmp_path/"already").mkdir()
    with pytest.raises(FileExistsError):
        m.execute(tmp_path,tmp_path/"already")

def test_gate_has_no_merge_or_deploy_execution_path():
    source=SCRIPT.read_text(encoding="utf-8")
    ast.parse(source)
    assert "mergeOrDeployPerformed" in source
    for forbidden in ("git push","git merge","railway deploy",
                      "GenUI.openUrl","subprocess.run","start_process"):
        assert forbidden not in source
    for name in ("web/static/public-route.js",
                 "web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "verify_public_r6_release_admission" not in (ROOT/name).read_text(encoding="utf-8")

def make_mock_reports():
    cases=list(m.CASES)
    shas={name:"a"*64 for name in cases}
    r1={"version":m.VERSIONS["r1"],"cases":[{"case":n,"sourceSHA256":shas[n]} for n in cases],
        "allGoldenExact":True}
    sizes=[238,371,301]
    r2={"version":m.VERSIONS["r2"],"allGoldensExact":True,"allColorGroupsVisited":True,
        "cases":[{"case":n,"sourceSHA256":shas[n],"totalColorGroups":size,
                  "visitedColorGroups":size,"wholeColorGroupAuditComplete":True,"goldenExact":True}
                 for n,size in zip(cases,sizes)]}
    r3={"version":m.VERSIONS["r3"],"allExact":True,
        "cases":[{"case":n,"sourceSHA256":shas[n]} for n in cases]}
    r4={"version":m.VERSIONS["r4"],"chromeBaselinePass":True,
        "crossRendererExact":True,
        "cases":[{"case":n,"sourceSHA256":shas[n],
                  "fullSceneCrossRendererExact":True,
                  "chromeVsResvg340":{"differentPixels":0},
                  "chromeVsResvg680":{"differentPixels":0}}
                 for n in cases]}
    layer={"version":m.VERSIONS["r4_component"],
           "cases":[{"case":n,"components":{
             "paths":{"exact340":True,"exact680":True,
                      "differentPixels340":0,"differentPixels680":0},
             "facet":{"differentPixels680":0}
           }} for n in cases]}
    r5={"version":m.VERSIONS["r5"],"researchPass":True,
        "allOffOnByteExact":True,"missingObserverWasmFallbackByteExact":True,
        "cases":[{"case":n,"offAndOnByteExact":True,"offSHA256":"b"*64,
                  "onSHA256":"b"*64,"onDiagnosticSHA256":"b"*64} for n in cases]}
    return {"r1":r1,"r2":r2,"r3":r3,"r4":r4,"r4_component":layer,"r5":r5}

def test_aggregated_cross_renderer_flags_cannot_spoof_actual_dpr2_pixels():
    records=make_mock_reports()
    records["r4"]["cases"][0]["chromeVsResvg680"]["differentPixels"]=1
    decision=m.evaluate(records,{k:"a"*64 for k in records})
    assert not decision["gates"]["r4WholeSceneDpr2Exact"]
    assert decision["status"]=="NO_GO"
    assert not decision["releaseAuthorized"]

def test_aggregated_shadow_flags_cannot_spoof_changed_png_bytes():
    records=make_mock_reports()
    records["r5"]["cases"][2]["onSHA256"]="c"*64
    decision=m.evaluate(records,{k:"a"*64 for k in records})
    assert not decision["gates"]["r5PublicShadowCanarySafe"]
    assert decision["status"]=="NO_GO"
