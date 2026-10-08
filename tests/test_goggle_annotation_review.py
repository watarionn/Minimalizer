"""Source-image-only eyewear annotation review and conservative render authority."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_annotation_review as m

def test_annotation_windows_do_not_become_true_masks():
    assert set(m.ZONES)=={"left_lens","right_lens","frame"}
    for coords in m.ZONES.values():
        x0,y0,x1,y1=coords
        assert 0<=x0<x1<=340 and 0<=y0<y1<=340

def test_unverified_annotations_cannot_render():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert '"actual_visible_boundaries_annotated":False' in code
    assert '"source_verified_lens_frame_mask":False' in code
    assert '"goggles_svg_generated":False' in code
    assert "from diffusers" not in code and "import torch" not in code
