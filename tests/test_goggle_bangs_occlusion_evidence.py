"""Measured gaps never imply an approved bridge through bangs."""
from pathlib import Path
import sys,numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_bangs_occlusion_evidence as m
def test_two_disconnected_white_islands_remain_separate():
    rgb=np.full((340,340,3),[245,110,30],np.uint8)
    mask=np.zeros((340,340),np.uint8)
    mask[40:43,100:103]=255;mask[40:43,115:118]=255
    parts,gaps=m.analyze(Image.fromarray(rgb),Image.fromarray(mask))
    assert len(parts)==2 and len(gaps)==1
    assert gaps[0]["bridge_authorized"] is False
    assert gaps[0]["source_orange_samples"]>0
def test_diagnostics_never_create_frame():
    s=Path(m.__file__).read_text(encoding="utf-8")
    assert '"bridges_rendered":False' in s
    assert '"occlusion_verified":False' in s
    assert "from diffusers" not in s
