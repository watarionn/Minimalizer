import numpy as np
from minimalizer_zerobase.production.semantic_edge_regions import EdgeRegion
from minimalizer_zerobase.production.perceptual_region_budget import select_perceptual_regions
def R(area,rgb=(30,40,50),edge=.2):
 m=np.zeros((20,20),bool);m.flat[:area]=1;return EdgeRegion(m,rgb,area,edge)
def test_budget_is_global_and_major_parts_get_first_claim():
 masks={"torso":np.ones((20,20),bool),"hair":np.ones((20,20),bool)}
 regs={"torso":[R(180),R(30,(240,240,240),.8)],"hair":[R(170,(200,80,20)),R(20,(250,10,10),.9)]}
 out=select_perceptual_regions(regs,masks,{"torso":(30,40,50),"hair":(200,80,20)},budget=2)
 assert len(out)==2 and {x.part for x in out}=={"torso","hair"}
def test_tiny_contrast_fragment_cannot_displace_major_mass():
 masks={"torso":np.ones((20,20),bool)}
 regs={"torso":[R(220,(30,30,40)),R(4,(255,0,0),1.0)]}
 out=select_perceptual_regions(regs,masks,{"torso":(30,30,40)},budget=1)
 assert out[0].region.area==220

def test_compact_high_contrast_edge_supported_accent_survives_budget():
 masks={"torso":np.ones((40,40),bool),"hair":np.ones((40,40),bool)}
 regs={"torso":[R(700,(30,35,50),.1),R(60,(40,220,60),.7),R(300,(235,235,230),.2)],"hair":[R(650,(200,80,20),.1),R(250,(150,50,20),.2)]}
 out=select_perceptual_regions(regs,masks,{"torso":(30,35,50),"hair":(200,80,20)},budget=4)
 assert any(x.accent and x.region.rgb==(40,220,60) for x in out)
