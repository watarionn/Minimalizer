"""Tests for accessory coordinates and source-only clothing contours."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import accessory_goggles_clothing_audit as m

def test_connected_components_preserve_xywh():
    mask=np.zeros((340,340),bool)
    mask[214:245,180:201]=True
    assert m.stats(mask)==[{"pixels":651,"xywh":[180,214,21,31]}]

def test_isolated_research_no_goggle_ground_truth_claim():
    text=Path(m.__file__).read_text(encoding="utf-8")
    assert '"goggles_roi_is_NOT_ground_truth":True' in text
    assert "data-part" in text
    assert '"not_production"' in text
    assert "from diffusers" not in text
    assert "import torch" not in text
