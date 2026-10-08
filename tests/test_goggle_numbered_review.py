"""Review-ready source goggles fragments stay separate from filled segmentation."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_numbered_review as m
def test_prior_six_white_rim_candidates_are_stable():
    assert m.ROLES==("left_lens","right_lens","frame")
def test_visual_review_deduplicates_fragments_and_does_not_authorize_fill():
    path=Path(__file__).resolve().parents[1]/"docs/research/GC001_GOGGLE_WHITE_RIM_FRAGMENT_REVIEW_20261009.json"
    report=json.loads(path.read_text(encoding="utf-8"))
    assert len(report["reviewed_fragments"])==6
    assert report["distinct_reviewed_fragment_groups"]==3
    assert report["render_authority"] is False
    assert report["complete_frame_polygon_verified"] is False
    assert all(x["duplicates_with"] for x in report["reviewed_fragments"])
def test_no_renderer_promotion_from_numbered_review():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert '"approved":[]' in code
    assert '"filled_svg_generated":False' in code
    assert "from diffusers" not in code
