"""Source pale-rim candidate is not an approved goggle region."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_rim_source_area as m
def test_orange_hair_is_not_white_rim():
    img=np.full((340,340,3),[242,110,30],np.uint8)
    assert not m.local_rim(img,[[120,65],[121,65]]).any()
def test_pale_source_near_actual_edge_is_candidate_only():
    img=np.full((340,340,3),[230,235,239],np.uint8)
    assert m.local_rim(img,[[120,65]]).sum()>0
def test_no_render_authority():
    s=Path(m.__file__).read_text(encoding="utf-8")
    assert '"filled_svg_authorized":False' in s
    assert '"semantic_verified":False' in s
    assert "from diffusers" not in s
