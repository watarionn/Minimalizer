"""Source-pale goggle rim adjacency must not bridge orange hair."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_visible_rim_connectivity as m
def test_no_orange_bridge():
 rgb=np.full((340,340,3),[240,112,28],np.uint8)
 rgb[50:55,120:125]=[232,231,229]
 seed=np.zeros((340,340),np.uint8);seed[52,122]=255
 cand,components=m.audit(Image.fromarray(rgb),Image.fromarray(seed))
 assert cand.sum()==25 and len(components)==1
 assert not cand[55,122]
def test_render_authority_stays_false():
 s=Path(m.__file__).read_text(encoding="utf-8")
 assert '"hidden_bridge_inferred":False' in s
 assert '"filled_svg_generated":False' in s
 assert '"semantic_rim_verified":False' in s
