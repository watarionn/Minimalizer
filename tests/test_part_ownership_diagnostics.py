"""Part source-mask versus isolated SVG footprint diagnostic regression."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import part_ownership_diagnostics as m

def test_part_categories_cover_problem_regions():
    assert m.PARTS[0]=="face"
    assert "accessory_or_held_object" in m.PARTS
    assert "major_clothing" in m.PARTS
    assert "left_arm" in m.PARTS and "right_arm" in m.PARTS

def test_diagnostic_is_read_only_and_rejects_face_plate():
    content=Path(m.__file__).read_text(encoding="utf-8")
    assert "root.findall" in content
    assert "data-part='subject'" in content
    assert "data-part='face'" in content
    assert '"no_production_changes":True' in content
    assert "from diffusers" not in content
    assert "import torch" not in content
