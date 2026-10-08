"""Rim topology audit preserves original masks and never bridges gaps."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_rim_connectivity as m
def test_original_is_not_mutated():
    src=Image.fromarray(np.full((340,340,3),[230,230,230],np.uint8))
    mask=np.zeros((340,340),np.uint8);mask[50,50]=255;mask[50,80]=255
    before=mask.copy()
    components,extension,metrics=m.audit(src,Image.fromarray(mask))
    assert np.array_equal(mask,before)
    assert metrics["original_components"]==2
    assert not extension[50,65]
def test_no_authorized_bridge():
    text=Path(m.__file__).read_text(encoding="utf-8")
    assert '"no_gap_filling":True' in text
    assert '"filled_svg_authorized":False' in text
    assert "from diffusers" not in text
