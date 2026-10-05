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


def test_renderer_emits_fine_semantic_identity_geometry():
 masks={k:np.zeros((120,100),bool) for k in PART_NAMES}
 for k,b in {"head":(20,5,80,65),"hair":(15,3,85,70),"face":(32,30,68,62),"major_clothing":(18,65,82,115),"accessory_or_held_object":(75,72,92,88),"torso":(20,65,80,110),"left_arm":(8,67,20,105),"right_arm":(80,67,92,105),"lower_body":(25,108,75,120)}.items():
  x0,y0,x1,y1=b;masks[k][y0:y1,x0:x1]=1
 rgb=np.full((120,100,3),220,np.uint8);rgb[24:34,24:76]=(35,45,55);rgb[68:83,44:56]=(80,210,45)
 g=build_structural_layout_graph(masks)
 svg=render_graph_macro_svg(rgb,masks,g,{"head":1,"hair":1,"torso":1,"left_arm":1,"right_arm":1,"lower_body":1,"major_clothing":1,"accessory":1})
 assert 'data-semantic="eyewear"' in svg
 assert svg.count('data-semantic="eyewear"')>=2
 assert 'data-semantic="face"' not in svg
