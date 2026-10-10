"""R22-R24 gate never conflates SVG bytes, historic vertices or approval."""
from __future__ import annotations
import copy
import gzip
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_public_r22_r24_real_source_gate as r22
from research_public_r17_consecutive_vertex_prune import SCENE_SHA256
from research_public_r12_exact_raster_prune import SOURCE

def case_record(case):
    return {
      "case":case,
      "sourceStage8SHA256":SCENE_SHA256[case],
      "sourceRingVertices":SOURCE[case][2],
      "historicVertexCap":SOURCE[case][1],
      "ownersCertified":11,
      "realChromeWholeOwnerDpr1And2Exact":True,
      "fullOwnerSvgChangedPixels340":0,
      "fullOwnerSvgChangedPixels680":0,
      "historicalStage8BudgetPass":False,
      "performanceRegressionOrSpeedupSignoff":False,
      "releaseAuthorized":False,
    }

def frozen_inputs(tmp_path):
    r6=tmp_path/"r6.json"
    r11=tmp_path/"r11.json"
    r6.write_text(json.dumps({
       "version":"public-r6-conservative-release-admission-v1",
       "blockedGateCount":8,"status":"NO_GO","releaseAuthorized":False,
       "blockedGates":[{"gate":str(i)} for i in range(8)]}))
    r11.write_text(json.dumps({
       "status":"LIVE_HOST_HTTP_AUDIT_PASS_RELEASE_NO_GO",
       "releaseAuthorized":False,
       "liveResponseMeasurements":{"css":{"maxAgeSeconds":604800}}}))
    return r6,r11

def test_full_composite_gzip_is_deterministic_and_roundtrips():
    svg='<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 1L3 2Z"/></svg>'
    a=r22.compression_size(svg)
    b=r22.compression_size(svg)
    assert a==b
    assert a["svgBytes"]==len(svg.encode())
    assert len(a["svgSHA256"])==64
    assert len(a["gzip9SHA256"])==64
    assert a["gzip9Bytes"]>0
    assert gzip.decompress(gzip.compress(svg.encode(),mtime=0))==svg.encode()

def test_two_authentic_stage8_ids_keep_historical_budget_failure(tmp_path):
    r6,r11=frozen_inputs(tmp_path)
    result=r22.gate_final([case_record(c) for c in ("GC001","Raden")],r6,r11)
    assert result["R22RealOriginalSource11OwnerChrome340And680Pass"]
    assert result["R23RealSourceFullSvgAndGzipBenchmarksComplete"]
    assert result["R24ResearchIntegrationGateComplete"]
    assert result["blockedGateCount"]==8
    assert result["productionReleaseAuthorized"] is False
    assert result["originalVertexBudgetApproved"] is False
    assert result["originalSourceSemanticsApproved"] is False

@pytest.mark.parametrize("patch",[
    {"sourceRingVertices":20},
    {"historicVertexCap":4000},
    {"ownersCertified":10},
    {"realChromeWholeOwnerDpr1And2Exact":False},
    {"fullOwnerSvgChangedPixels340":1},
    {"fullOwnerSvgChangedPixels680":1},
    {"historicalStage8BudgetPass":True},
    {"performanceRegressionOrSpeedupSignoff":True},
    {"releaseAuthorized":True},
])
def test_fake_r22_chrome_or_policy_approval_rejected(tmp_path,patch):
    r6,r11=frozen_inputs(tmp_path)
    rows=[case_record(c) for c in ("GC001","Raden")]
    rows[0].update(patch)
    with pytest.raises(ValueError,match="forged"):
        r22.gate_final(rows,r6,r11)

def test_forged_r6_or_unverified_host_rejected(tmp_path):
    r6,r11=frozen_inputs(tmp_path)
    data=json.loads(r6.read_text());data["blockedGateCount"]=0
    r6.write_text(json.dumps(data))
    with pytest.raises(ValueError,match="held release"):
        r22.gate_final([case_record(c) for c in ("GC001","Raden")],r6,r11)
    data["blockedGateCount"]=8;r6.write_text(json.dumps(data))
    other=json.loads(r11.read_text());other["liveResponseMeasurements"]["css"]["maxAgeSeconds"]=0
    r11.write_text(json.dumps(other))
    with pytest.raises(ValueError,match="held release"):
        r22.gate_final([case_record(c) for c in ("GC001","Raden")],r6,r11)

def test_input_count_and_unexpected_source_rejected(tmp_path):
    r6,r11=frozen_inputs(tmp_path)
    with pytest.raises(ValueError,match="two"):
        r22.gate_final([case_record("GC001")],r6,r11)
    with pytest.raises(ValueError,match="two"):
        r22.gate_final([case_record("Raden"),case_record("GC001")],r6,r11)
    with pytest.raises(FileExistsError):
        r22.run({},r6,r11,tmp_path)

def test_not_implicitly_shipped_and_local_unmodified():
    source=(ROOT/"scripts/verify_public_r22_r24_real_source_gate.py").read_text()
    assert '"productionReleaseAuthorized":False' in source
    assert '"originalSourceSemanticsApproved":False' in source
    assert '"physicalIphoneSafariApproved":False' in source
    for rel in ("web/static/public-route.js","web/static/browser-fallback.js",
                "local_worker/frontend/local-route.js"):
        assert "verify_public_r22_r24_real_source_gate" not in (
            ROOT/rel).read_text(encoding="utf-8")
