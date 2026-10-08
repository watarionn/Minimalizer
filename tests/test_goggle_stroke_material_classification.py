"""Goggle stroke material hypotheses must remain non-authoritative."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_stroke_material_classification as m

def test_observed_source_orange_cannot_promote_goggles():
    rgb=np.full((340,340,3),[236,113,40],np.uint8)
    curve={"points":[[130,55],[131,56],[132,57],[133,58]],"length":20}
    assert m.material(rgb,curve)=="likely_hair_or_warm_material"

def test_source_white_is_still_only_candidate():
    rgb=np.full((340,340,3),[238,239,240],np.uint8)
    curve={"points":[[130,55],[131,56],[132,57],[133,58]],"length":20}
    assert m.material(rgb,curve)=="possible_white_frame"

def test_no_filled_semantic_svg_or_production_changes():
    s=Path(m.__file__).read_text(encoding="utf-8")
    assert '"fill":"none"' in s
    assert '"verified_goggles_strokes":0' in s
    assert '"semantic_lens_frame_mask":False' in s
    assert '"filled_svg":False' in s
    assert "from diffusers" not in s
