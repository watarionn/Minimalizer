import json
from pathlib import Path

def test_expanded_corpus_contains_general_landscape():
    root=Path(__file__).parents[1]
    manifest=json.loads((root/"tests/assets/corpus_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) >= 16
    assert any(x.get("category")=="general_landscape" for x in manifest)
    assert (root/"tests/assets/corpus/Night-River-City_general.webp").exists()

def test_engine_version_literal_is_rc11():
    root=Path(__file__).parents[1]
    text=(root/"minimalize_engine/pipeline.py").read_text(encoding="utf-8")
    assert '"engine_version":"0.3.0"' in text
