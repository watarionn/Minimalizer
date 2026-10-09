"""v29 strict sparse-anime QA and resource-safe inference preflight contracts."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"tools/audit_browser_anime_corpus_v29.py"
GATE=ROOT/"tools/gate_browser_anime_inference_v29.py"
def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,path)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module
def test_anchor_schema_and_non_semantic_scope():
    a=load(AUDIT)
    assert set(a.SPARSE_ANCHORS)=={"Noel","Ririka"}
    for case,points in a.SPARSE_ANCHORS.items():
        assert len(points)==10
        assert len({p[0] for p in points})==len(points)
        assert len({(p[1],p[2]) for p in points})==len(points)
        assert {p[-1] for p in points}=={"hair","clothes"}
        assert sum(p[-1]=="hair" for p in points)==5
        assert sum(p[-1]=="clothes" for p in points)==5
        assert all(0<=x<340 and 0<=y<340 for _,x,y,_ in points)
        assert case in a.EXPECTED_SOURCES and case in a.EXPECTED_FACETS
    assert (0,0,0) in a.CLASSES
    assert a.CLASSES[(0,0,0)]=="unclassified_or_background"
    assert len(a.CLASSES)==6

def test_bad_archive_fails_before_creating_qa_artifacts(tmp_path):
    a=load(AUDIT)
    fake=tmp_path/"fake.zip"
    fake.write_bytes(b"fake-not-a-trusted-corpus")
    target=tmp_path/"report"
    with pytest.raises(ValueError,match="v27 frozen reference SHA"):
        a.audit(fake,target)
    assert not target.exists()

def test_missing_or_wrong_weights_and_memory_fail_closed(tmp_path):
    g=load(GATE)
    bogus_zip=tmp_path/"frozen.zip"
    bogus_model=tmp_path/"v3.safetensors"
    bogus_zip.write_bytes(b"fake zip")
    bogus_model.write_bytes(b"fake weights")
    memory={"state":"measured","freePhysicalGiB":2.2}
    result=g.preflight(bogus_zip,bogus_model,memory)
    assert result["status"]=="HOLD_NO_HEAVY_MODEL_EXECUTION"
    assert set(result["blockers"])=={"frozen_corpus_sha_unverified",
       "cached_model_sha_unverified","insufficient_or_unmeasured_free_ram"}
    assert result["executedModel"] is False
    assert result["modelInferenceLaunched"] is False
    assert result["productionAuthority"] is False
    assert result["perCaseOutputs"]=={"Noel":"unavailable","Ririka":"unavailable"}

def test_ram_policy_cannot_be_silently_weakened(tmp_path):
    g=load(GATE)
    for threshold in (0,1,3.9,100):
        with pytest.raises(ValueError,match="floor"):
            g.preflight(tmp_path/"a",tmp_path/"b",{},threshold)
    no_device=g.preflight(tmp_path/"a",tmp_path/"b",
      {"state":"unavailable_non_windows","freePhysicalGiB":None})
    assert no_device["status"]=="HOLD_NO_HEAVY_MODEL_EXECUTION"
    assert "insufficient_or_unmeasured_free_ram" in no_device["blockers"]

def test_frozen_facet_and_production_contract_unchanged():
    # v29 adds only offline diagnostics. Browser renderer and worker stay
    # at inherited frozen v28 version; no generated arms/facial details.
    index=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    app=(ROOT/"web/static/app.js").read_text(encoding="utf-8")
    assert "browser-anime-corpus-gate-v29" not in index
    assert "browser-anime-corpus-gate-v29" not in app
    assert "minimalizer-v29" not in app
    assert "image_gen" not in AUDIT.read_text(encoding="utf-8")
    assert "torch" not in GATE.read_text(encoding="utf-8").split("if __name__")[0].split("import ")[1]
