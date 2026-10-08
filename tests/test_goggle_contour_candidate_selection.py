"""Frozen source edge shortlist never grants semantic goggles authority."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_contour_candidate_selection as m

def test_long_upper_line_is_only_review_candidate():
    v={"points":[[115,50],[126,55],[136,65],[145,72]],"length":40.0}
    assert m.classify("left_lens",v)=="candidate_requires_semantic_review"

def test_source_bang_territory_is_rejected():
    v={"points":[[150,70],[155,80],[163,98]],"length":50.0}
    assert m.classify("frame",v)=="reject_bang_overlap_risk"

def test_no_filled_goggles_authority():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert '"fill":"none"' in source
    assert '"semantic_goggles_mask":False' in source
    assert '"filled_goggles_svg":False' in source
    assert "from diffusers" not in source
