"""Stage8 historical owner-budget and release NO-GO fail-closed unit checks."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_r12_r16_source_release import (
    FILES, required_data, original_budget_gap, protected_owner_gate,
    cross_renderer_gate, human_gate, final_gate)

def actual():
    return required_data(FILES)

def test_authentic_source_stage8_counts_and_11_owners_are_explicit():
    r=original_budget_gap(actual())
    assert r["status"]=="ORIGINAL_STAGE8_BUDGET_MEASURED_HOLD"
    assert [(r["cases"][name]["actualAdaptiveOriginalRingVertices"],
             r["cases"][name]["oldHistoricalVertexCap"],
             r["cases"][name]["overrun"]) for name in ("GC001","Raden")] == [
             (3604,1887,1717),(2370,1412,958)]
    assert all(x["ownerCount"]==11 for x in r["cases"].values())
    assert all(x["originalSourceRingBudgetPass"] is False for x in r["cases"].values())
    assert not r["optionB_VersionedPolicyUserApproved"]

def test_compact_svg_count_cannot_forge_source_stage8_pass():
    d=actual()
    for case in ("GC001","Raden"):
        d["sa1060"]["case_summary"][case]["immutable_source_ring_vertices"]=(
            d["sa1060"]["case_summary"][case]["research_svg_vertices"])
    with pytest.raises(ValueError,match="original Stage8"):
        original_budget_gap(d)

def test_source_owner_list_missing_protected_face_is_rejected():
    d=actual()
    d["gc_gap"]["parts"][0]["owner"]="face"
    with pytest.raises(ValueError,match="protected source owners"):
        original_budget_gap(d)

def test_source_owner_vertex_bookkeeping_must_agree():
    d=actual()
    d["raden_gap"]["parts"][0]["adaptive_extra_vs_old"]+=1
    with pytest.raises(ValueError,match="vertex accounting"):
        original_budget_gap(d)

def test_actual_protected_face_and_two_arms_recorded_as_fail():
    r=protected_owner_gate(actual())
    assert r["status"]=="SOURCE_PROTECTED_PARTS_AUDITED_HOLD"
    assert r["cases"]["GC001"]["fullSceneChromeWrongPixels"]==3919
    assert r["cases"]["Raden"]["fullSceneChromeWrongPixels"]==2681
    assert r["cases"]["GC001"]["protectedFaceWrongPixels"]==140
    assert r["cases"]["Raden"]["rightArmWrongPixels"]==255
    assert r["compressedProposalChangesOriginalOwnerLabels"] is True
    assert r["faceMicrofeaturesDrawingAllowed"] is False

def test_claimed_owner_repair_without_real_evidence_is_rejected():
    d=actual()
    d["sa1041"]["source_protected_face_left_right_arm_browser_gate"]="PASS"
    with pytest.raises(ValueError,match="failures"):
        protected_owner_gate(d)

def synthetic_r4():
    cases=[];components=[]
    for name in ("Kyoko","Noel","Ririka"):
        cases.append({"case":name,"sourceSHA256":"a"*64,
          "chromeFrozenGoldenExact":True,
          "chromeVsResvg680":{"differentPixels":5}})
        components.append({"case":name,"sourceSHA256":"a"*64,
          "components":{"paths":{"differentPixels680":0,"exact680":True},
                        "facet":{"differentPixels680":12}}})
    return {"r4":{"cases":cases},"r4_components":{"cases":components}}

def test_renderer_path_exact_is_not_whole_scene_parity():
    evidence=cross_renderer_gate(synthetic_r4())
    assert evidence["pathOnlyDpr2Exact"] is True
    assert evidence["fullSceneDpr2Exact"] is False
    assert evidence["releaseAuthorized"] is False

def test_renderer_incomplete_facet_or_missing_case_is_rejected():
    obj=synthetic_r4()
    obj["r4_components"]["cases"][0]["components"]["facet"]["differentPixels680"]=0
    with pytest.raises(ValueError,match="renderer decomposition"):
        cross_renderer_gate(obj)
    obj=synthetic_r4()
    obj["r4"]["cases"].pop()
    with pytest.raises(ValueError,match="Golden lineup"):
        cross_renderer_gate(obj)

def test_unsigned_human_golden_and_live_cache_never_become_approval():
    cases=[{"case":name,"humanPartReview":{str(i):None for i in range(8)},
            "reviewStatus":"PENDING"} for name in ("Kyoko","Noel","Ririka")]
    ext={"r7":{"cases":cases},
         "r11":{"liveResponseMeasurements":{
             "css":{"maxAgeSeconds":604800},"app":{"maxAgeSeconds":604800}}}}
    r=human_gate(ext,actual())
    assert r["manualQualityReviewAllPending"]
    assert r["realLiveFixedUrlOneWeekCacheMeasured"]
    assert not r["physicalIphoneSafariTestObserved"]
    assert not r["mpl2RedistributionLegalApproval"]
    assert not r["releaseAuthorized"]
    ext["r7"]["cases"][0]["humanPartReview"]["2"]=True
    with pytest.raises(ValueError,match="may not be forged"):
        human_gate(ext,actual())

def test_final_gate_refuses_any_fake_stage_signoff():
    keys=("R12","R13","R14","R15")
    stages={k:{"status":k+"_HOLD","releaseAuthorized":False} for k in keys}
    blocked=[{"gate":"gate_"+str(i)} for i in range(8)]
    env={"r6":{"blockedGates":blocked}}
    decision=final_gate(stages,env)
    assert decision["status"]=="FINAL_RELEASE_GATE_NO_GO"
    assert decision["baselineR6GatesBlocked"]==8
    assert decision["productionPromoted"] is False
    stages["R12"]["releaseAuthorized"]=True
    with pytest.raises(ValueError,match="integrity mismatch"):
        final_gate(stages,env)

def test_static_public_local_isolation():
    script=(ROOT/"scripts/verify_public_r12_r16_source_release.py").read_text(encoding="utf-8")
    assert "noResvgReplacementApproved" in script
    assert "sourceExactRingVertices" in script
    assert "inventedSemanticROIs" in script
    for path in ("web/static/public-route.js",
                 "web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "verify_public_r12_r16_source_release" not in (ROOT/path).read_text(encoding="utf-8")
