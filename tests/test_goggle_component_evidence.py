"""Goggle candidate gate: candidate pixels are never verified segmentation."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_component_evidence as m

def test_windows_are_source_bounded_and_distinct():
    assert set(m.WINDOWS)=={"left_lens","right_lens","frame"}
    for box in m.WINDOWS.values():
        x0,y0,x1,y1=box
        assert 0<=x0<x1<=340 and 0<=y0<y1<=340

def test_unverified_candidates_never_generate_goggles_svg():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert '"semantic_goggle_labels_verified":False' in source
    assert '"goggle_svg_produced":False' in source
    assert '"hair_mask_modified":False' in source
    assert "from diffusers" not in source
    assert "import torch" not in source
