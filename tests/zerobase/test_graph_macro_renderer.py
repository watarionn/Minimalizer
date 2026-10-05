import numpy as np
from minimalizer_zerobase.structure.graph import build_structural_layout_graph
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.production.graph_macro_renderer import render_graph_macro_svg
def test_graph_drives_attached_arm_geometry():
 masks={k:np.zeros((100,80),bool) for k in PART_NAMES}
 for k,b in {"head":(30,5,50,25),"face":(34,10,46,22),"hair":(27,2,53,27),"torso":(27,27,53,60),"left_arm":(15,30,27,58),"right_arm":(53,30,65,58),"lower_body":(30,60,50,95)}.items():
  x0,y0,x1,y1=b;masks[k][y0:y1,x0:x1]=1
 g=build_structural_layout_graph(masks);rgb=np.full((100,80,3),180,np.uint8)
 svg=render_graph_macro_svg(rgb,{k:v for k,v in masks.items() if k!="unknown"},g,{"head":1,"hair":1,"torso":1,"left_arm":1,"right_arm":1,"lower_body":1})
 assert svg.count("<polygon")>=6
 assert "<ellipse" not in svg
 assert "attachment" not in svg
