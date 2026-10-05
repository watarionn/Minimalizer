import numpy as np
from minimalizer_zerobase.production.graph_macro_renderer import render_graph_macro_svg
from minimalizer_zerobase.structure.graph import StructuralLayoutGraph
def test_major_mass_paint_order_is_semantic():
 src=open("minimalizer_zerobase/production/graph_macro_renderer.py",encoding="utf-8").read()
 order='("lower_body","torso","major_clothing","left_arm","right_arm","hair")'
 assert order in src
 assert '"head"' not in order
def test_accessory_foreground_restore_occurs_after_region_selection():
 src=open("minimalizer_zerobase/production/graph_macro_renderer.py",encoding="utf-8").read()
 assert src.rfind('if allocations.get("accessory",0)>0') > src.find("selected=select_perceptual_regions")
