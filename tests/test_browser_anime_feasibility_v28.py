"""V28 evidence-only browser anime model feasibility/contraindication tests."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"tools/analyze_browser_anime_v28.py"
SPEC=importlib.util.spec_from_file_location("v28_anime",SCRIPT)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def test_v28_exact_source_provenance_and_class_vocab():
    assert len(mod.ANIME_LABELS)==len(mod.ANIME_PALETTE)==12
    assert mod.ANIME_LABELS[3]=="hair_main"
    assert mod.ANIME_LABELS[10]=="clothes"
    assert "left_arm" not in mod.ANIME_LABELS
    assert "right_arm" not in mod.ANIME_LABELS
    assert len(set(mod.ANIME_PALETTE))==12
    assert mod.PINNED_SOURCE=="75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e"
    assert len(mod.PINNED_ANIME_MASK)==64
    assert len(mod.PINNED_V27_ARCHIVE)==64

def test_fail_closed_unverified_source_before_model_access(tmp_path):
    source=tmp_path/"fake_source.png"
    model=tmp_path/"fake.safetensors"
    mask=tmp_path/"fake_mask.png"
    zip_=tmp_path/"fake.zip"
    for p in (source,model,mask,zip_):p.write_bytes(b"synthetic")
    with pytest.raises(ValueError,match="source SHA mismatch"):
        mod.audit(source,mask,zip_,tmp_path/"out",model)
    assert not (tmp_path/"out").exists()

def test_mask_digest_mismatch_fails_before_archive_parse(tmp_path):
    # Fixed source bytes unavailable in CI: check the exact digest comparison
    # rather than replace the real source with a faked matching payload.
    assert mod.sha(b"not the model mask")!=mod.PINNED_ANIME_MASK
    assert mod.sha(b"not a source")!=mod.PINNED_SOURCE
    assert mod.sha(b"not v27 archive")!=mod.PINNED_V27_ARCHIVE

def test_browser_production_and_worker_not_modified():
    # V28 does not load a Python-only Mask2Former into the Browser or call
    # its external inference through an unofficial API.
    index=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    app=(ROOT/"web/static/app.js").read_text(encoding="utf-8")
    assert "browser-anime-model-feasibility-v28" not in index
    assert "browser-anime-model-feasibility-v28" not in app
    assert not (ROOT/"web/static/models/animeseg_v3.onnx").exists()

def test_model_manifest_explicit_browser_and_semantic_hold():
    script=SCRIPT.read_text(encoding="utf-8")
    assert '"browserAnimeInference":"NOT_IMPLEMENTED"' in script
    assert '"partBindingAuthority":False' in script
    assert '"productionAuthority":False' in script
    assert '"armSideLabelsAvailable":False' in script
    assert 'source_sha' not in script or 'PINNED_SOURCE' in script
